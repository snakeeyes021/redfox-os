#!/usr/bin/env bash
# Tests the downloads Worker. Usage: test.sh <base url> [local test.iso to compare]
#   test.sh http://127.0.0.1:8799 test.iso
set -u
B=$1
SRC=${2:-}
KEY=redfox-os.iso
pass=0 fail=0
ok() { echo "ok    $*"; pass=$((pass + 1)); }
bad() { echo "FAIL  $*"; fail=$((fail + 1)); }
status() { curl -s -o /dev/null -w '%{http_code}' "$@"; }
hdr() { curl -s -D - -o /dev/null "${@:2}" | tr -d '\r' | awk -v h="$1" 'tolower($0) ~ "^"tolower(h)":" {sub(/^[^:]*: */, ""); print}'; }

[ "$(status "$B/missing.iso")" = 404 ] && ok "404 for a missing key" || bad "missing key"
[ "$(status "$B/")" = 404 ] && ok "404 for / (no listing)" || bad "root"
[ "$(status "$B/?list-type=2")" = 404 ] && ok "404 for an S3-style list query" || bad "list query"
[ "$(status "$B/a/b.iso")" = 404 ] && ok "404 for a nested path" || bad "nested path"
[ "$(status "$B/staging/$KEY")" = 404 ] && ok "404 for staging/" || bad "staging"
[ "$(status "$B/previous/a/$KEY")" = 404 ] && ok "404 for a path nested under previous/" || bad "previous nested"
[ "$(status "$B/previous/")" = 404 ] && ok "404 for previous/ (no listing)" || bad "previous root"
[ "$(status -I "$B/previous/$KEY")" = 200 ] && ok "previous/ serves the older build" || bad "previous build"
[ "$(status -X POST "$B/$KEY")" = 405 ] && ok "405 for POST" || bad "POST"
[ "$(status -X PUT --data x "$B/$KEY")" = 405 ] && ok "405 for PUT" || bad "PUT"
[ "$(status -X DELETE "$B/$KEY")" = 405 ] && ok "405 for DELETE" || bad "DELETE"
[ "$(hdr allow -X OPTIONS "$B/$KEY")" = "GET, HEAD" ] && ok "Allow: GET, HEAD on 405" || bad "Allow header"

# HEAD
size=$(hdr content-length -I "$B/$KEY")
etag=$(hdr etag -I "$B/$KEY")
[ "$(status -I "$B/$KEY")" = 200 ] && [ -n "$size" ] && ok "HEAD 200, Content-Length $size" || bad "HEAD"
[ -n "$SRC" ] && { [ "$size" = "$(stat -c %s "$SRC")" ] && ok "HEAD size matches the file" || bad "HEAD size"; }
[ -n "$etag" ] && ok "ETag $etag" || bad "no ETag"
[ "$(hdr accept-ranges -I "$B/$KEY")" = bytes ] && ok "Accept-Ranges: bytes" || bad "Accept-Ranges"
case "$(hdr content-disposition -I "$B/$KEY")" in attachment*) ok "Content-Disposition: attachment for the ISO" ;; *) bad "disposition" ;; esac
case "$(hdr content-type -I "$B/$KEY")" in application/*) ok "Content-Type $(hdr content-type -I "$B/$KEY")" ;; *) bad "content-type" ;; esac
case "$(hdr content-type -I "$B/$KEY-CHECKSUM")" in text/plain*) ok "checksum is text/plain" ;; *) bad "checksum type" ;; esac
[ "$(status -I -H "If-None-Match: $etag" "$B/$KEY")" = 304 ] && ok "HEAD If-None-Match -> 304" || bad "HEAD 304"

# Ranges
check_range() {  # $1 = Range header, $2 = expected status, $3 = first byte, $4 = length
    local out=/tmp/rng.$$ code cr len
    code=$(curl -s -o $out -D /tmp/rngh.$$ -w '%{http_code}' -H "Range: $1" "$B/$KEY")
    cr=$(tr -d '\r' < /tmp/rngh.$$ | awk 'tolower($0) ~ /^content-range:/ {print $2" "$3}')
    len=$(stat -c %s $out)
    if [ "$code" != "$2" ] || [ "$len" != "$4" ]; then bad "Range $1: got $code, $len bytes ($cr)"; return; fi
    if [ -n "$SRC" ] && ! cmp -s $out <(tail -c +$(( $3 + 1 )) "$SRC" | head -c "$4"); then bad "Range $1: bytes differ"; return; fi
    if [ "$2" = 206 ] && [ "$cr" != "bytes $3-$(( $3 + $4 - 1 ))/$size" ]; then bad "Range $1: Content-Range $cr"; return; fi
    ok "Range $1 -> $code, $len bytes, $cr"
    rm -f $out /tmp/rngh.$$
}
check_range "bytes=0-0" 206 0 1
check_range "bytes=0-1023" 206 0 1024
check_range "bytes=1000000-2000000" 206 1000000 1000001
check_range "bytes=$((size - 100))-" 206 $((size - 100)) 100
check_range "bytes=-4096" 206 $((size - 4096)) 4096
check_range "bytes=$((size - 10))-$((size + 1000))" 206 $((size - 10)) 10
check_range "bytes=0-1,5-6" 200 0 "$size"
[ "$(status -H "Range: bytes=$size-" "$B/$KEY")" = 416 ] && ok "Range past the end -> 416" || bad "416 past end"
[ "$(hdr content-range -H "Range: bytes=$((size + 5))-" "$B/$KEY")" = "bytes */$size" ] && ok "416 carries Content-Range: bytes */$size" || bad "416 Content-Range"
[ "$(status -H "Range: bytes=-0" "$B/$KEY")" = 416 ] && ok "Range bytes=-0 -> 416" || bad "416 suffix 0"

# Conditionals
[ "$(status -H "If-None-Match: $etag" "$B/$KEY")" = 304 ] && ok "GET If-None-Match (same) -> 304" || bad "GET 304"
[ "$(status -H 'If-None-Match: "nope"' -H "Range: bytes=0-9" "$B/$KEY")" = 206 ] && ok "GET If-None-Match (other) + Range -> 206" || bad "INM other"
[ "$(status -H "If-Range: $etag" -H "Range: bytes=0-9" "$B/$KEY")" = 206 ] && ok "If-Range (same etag) -> 206" || bad "If-Range same"
code=$(curl -s -o /tmp/ir.$$ -w '%{http_code}' -H 'If-Range: "old"' -H "Range: bytes=0-9" "$B/$KEY")
[ "$code" = 200 ] && [ "$(stat -c %s /tmp/ir.$$)" = "$size" ] && ok "If-Range (changed file) -> 200 with the whole file" || bad "If-Range changed: $code"
rm -f /tmp/ir.$$
lm=$(hdr last-modified -I "$B/$KEY")
[ "$(status -H "If-Modified-Since: $lm" "$B/$KEY")" = 304 ] && ok "If-Modified-Since (same) -> 304" || bad "IMS"

# Whole file
if [ -n "$SRC" ]; then
    curl -s "$B/$KEY" | cmp -s - "$SRC" && ok "full GET matches the file byte for byte" || bad "full GET differs"
fi
echo "$pass passed, $fail failed"
[ "$fail" = 0 ]
