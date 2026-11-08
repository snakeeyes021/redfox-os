// RedFoxOS downloads: serves the live ISOs, their checksums and signatures
// from the R2 bucket bound as DOWNLOADS, at download.redfoxlabs.tech.
//
// Read-only and nothing else: GET and HEAD of a known file name, with Range
// (one range), If-Range, If-None-Match and If-Modified-Since. No listing; any
// other name is 404, any other method 405. The body is R2's stream handed
// straight to the response, so a multi-gigabyte download uses no more CPU
// than a small one. See docs/iso.md.

// Flat file names, e.g. redfox-os.iso, redfox-os.iso-CHECKSUM, optionally under
// previous/ (the release before the current one). Nothing else is reachable.
const KEY = /^(previous\/)?[A-Za-z0-9][A-Za-z0-9._-]{0,200}$/;

function contentType(key, stored) {
  if (stored) return stored;
  if (key.endsWith(".iso")) return "application/x-iso9660-image";
  if (key === "RELEASE" || key.endsWith("-CHECKSUM") || key.endsWith(".sig") || key.endsWith(".txt")) {
    return "text/plain; charset=utf-8";
  }
  return "application/octet-stream";
}

function baseHeaders(key, object) {
  const headers = new Headers();
  object.writeHttpMetadata(headers);
  headers.set("Content-Type", contentType(key, object.httpMetadata?.contentType));
  if (!headers.has("Content-Disposition")) {
    // The ISO downloads as a file; the small text files open in the browser.
    const disposition = key.endsWith(".iso") ? "attachment" : "inline";
    headers.set("Content-Disposition", `${disposition}; filename="${key}"`);
  }
  headers.set("ETag", object.httpEtag);
  headers.set("Last-Modified", object.uploaded.toUTCString());
  headers.set("Accept-Ranges", "bytes");
  // Same names are replaced at each release: always revalidate (ETag).
  headers.set("Cache-Control", "no-cache");
  headers.set("X-Content-Type-Options", "nosniff");
  return headers;
}

function textResponse(status, text, extra = {}) {
  return new Response(`${text}\n`, {
    status,
    headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store", ...extra },
  });
}

// "bytes=a-b", "bytes=a-" or "bytes=-n" -> an R2Range; null if absent or not
// a single range we can serve (the whole file is sent instead, as RFC 9110
// allows); "invalid" if it can never be satisfied.
function parseRange(header) {
  if (!header) return null;
  const m = /^bytes=(\d*)-(\d*)$/.exec(header.trim());
  if (!m || (m[1] === "" && m[2] === "")) return null;
  if (m[1] === "") {
    const suffix = Number(m[2]);
    return suffix > 0 ? { suffix } : "invalid";
  }
  const offset = Number(m[1]);
  if (m[2] === "") return { offset };
  const end = Number(m[2]);
  if (end < offset) return null;
  return { offset, length: end - offset + 1 };
}

// If-None-Match: "*" or a list of (weak or strong) etags; R2 wants them bare.
function noneMatchTags(header) {
  if (!header) return null;
  if (header.trim() === "*") return ["*"];
  return header.split(",").map((t) => t.trim().replace(/^W\//, "").replace(/^"(.*)"$/, "$1")).filter(Boolean);
}

function notModified(key, object) {
  const headers = baseHeaders(key, object);
  headers.delete("Content-Length");
  return new Response(null, { status: 304, headers });
}

async function handle(request, env) {
  if (request.method !== "GET" && request.method !== "HEAD") {
    return textResponse(405, "Method not allowed", { Allow: "GET, HEAD" });
  }
  const url = new URL(request.url);
  let key;
  try {
    key = decodeURIComponent(url.pathname.slice(1));
  } catch {
    return textResponse(404, "Not found");
  }
  if (!KEY.test(key)) return textResponse(404, "Not found");

  const ifNoneMatch = noneMatchTags(request.headers.get("If-None-Match"));
  const ifModifiedSince = request.headers.get("If-Modified-Since");

  if (request.method === "HEAD") {
    const object = await env.DOWNLOADS.head(key);
    if (!object) return textResponse(404, "Not found");
    if (ifNoneMatch && (ifNoneMatch.includes("*") || ifNoneMatch.includes(object.etag))) {
      return notModified(key, object);
    }
    if (!ifNoneMatch && ifModifiedSince && Math.floor(object.uploaded / 1000) * 1000 <= Date.parse(ifModifiedSince)) {
      return notModified(key, object);
    }
    const headers = baseHeaders(key, object);
    headers.set("Content-Length", String(object.size));
    return new Response(null, { status: 200, headers });
  }

  // GET. Conditions go to R2 with the read, so a normal download is one
  // R2 operation.
  let range = parseRange(request.headers.get("Range"));
  if (range === "invalid") {
    const head = await env.DOWNLOADS.head(key);
    if (!head) return textResponse(404, "Not found");
    return textResponse(416, "Range not satisfiable", { "Content-Range": `bytes */${head.size}` });
  }
  const ifRange = request.headers.get("If-Range");
  const onlyIf = {};
  if (ifNoneMatch && !ifNoneMatch.includes("*")) onlyIf.etagDoesNotMatch = ifNoneMatch[0];
  else if (!ifNoneMatch && ifModifiedSince && !Number.isNaN(Date.parse(ifModifiedSince))) {
    // Whole seconds, as in HTTP dates: modified means a later second.
    onlyIf.uploadedAfter = new Date(Date.parse(ifModifiedSince) + 999);
  }
  // If-Range: the range only if the file is unchanged (an etag, not a weak one).
  if (range && ifRange) {
    if (ifRange.startsWith('"')) onlyIf.etagMatches = ifRange.replace(/^"(.*)"$/, "$1");
    else range = null; // a date or weak tag: send the whole file
  }

  let object;
  try {
    object = await env.DOWNLOADS.get(key, {
      onlyIf: Object.keys(onlyIf).length ? onlyIf : undefined,
      range: range ?? undefined,
    });
  } catch (error) {
    // R2 refuses a range that starts past the end of the file.
    if (range) {
      const head = await env.DOWNLOADS.head(key);
      if (!head) return textResponse(404, "Not found");
      return textResponse(416, "Range not satisfiable", { "Content-Range": `bytes */${head.size}` });
    }
    throw error;
  }
  if (!object) return textResponse(404, "Not found");

  if (!("body" in object) || !object.body) {
    // A condition failed. If the client already has this version: 304.
    if (ifNoneMatch?.includes(object.etag) || onlyIf.uploadedAfter) return notModified(key, object);
    // Otherwise If-Range didn't match: the whole, current file.
    object = await env.DOWNLOADS.get(key);
    if (!object) return textResponse(404, "Not found");
    range = null;
  }
  if (ifNoneMatch?.includes("*")) return notModified(key, object);

  const headers = baseHeaders(key, object);
  if (range) {
    // Worked out from the request: what R2 returns for the range varies.
    const size = object.size;
    let start;
    let length;
    if (range.suffix !== undefined) {
      length = Math.min(range.suffix, size);
      start = size - length;
    } else {
      start = range.offset;
      length = Math.min(range.length ?? size - start, size - start);
    }
    headers.set("Content-Range", `bytes ${start}-${start + length - 1}/${size}`);
    headers.set("Content-Length", String(length));
    return new Response(object.body, { status: 206, headers });
  }
  headers.set("Content-Length", String(object.size));
  return new Response(object.body, { status: 200, headers });
}

export default {
  async fetch(request, env) {
    try {
      return await handle(request, env);
    } catch {
      return textResponse(500, "Something went wrong");
    }
  },
};
