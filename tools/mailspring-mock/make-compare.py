#!/usr/bin/python3
"""Write the Mailspring comparison page: one row per theme iteration (newest
first), three columns (vanilla | our theme vN | native mock), a light/dark
toggle and click-to-zoom.

    make-compare.py OUTDIR

OUTDIR holds vanilla/, mock/ and v1/, v2/, ... each with light.png and
dark.png (from capture-mailspring.sh and mock.py). The notes for each
iteration come from iterations.json next to this script.
"""
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mailspring: vanilla, RedFox Adwaita, native mock</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ margin: 0; padding: 20px; font-family: "Adwaita Sans", Cantarell, "Noto Sans", sans-serif;
         background: #fafafb; color: #323233; }}
  body.dark {{ background: #222226; color: #fff; }}
  header {{ display: flex; align-items: center; gap: 16px; flex-wrap: wrap; margin-bottom: 12px; }}
  h1 {{ font-size: 20px; margin: 0; }}
  button {{ font: inherit; border: 0; border-radius: 6px; padding: 6px 14px; cursor: pointer;
           background: rgba(0,0,6,.08); color: inherit; }}
  body.dark button {{ background: rgba(255,255,255,.1); }}
  button.on {{ background: #3584e4; color: #fff; }}
  .cols {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }}
  .colhead {{ font-weight: 700; font-size: 14px; opacity: .7; }}
  .row {{ margin: 18px 0 30px; }}
  .row h2 {{ font-size: 16px; margin: 0 0 8px; }}
  figure {{ margin: 0; }}
  img {{ width: 100%; height: auto; display: block; border-radius: 8px; cursor: zoom-in;
        box-shadow: 0 0 0 1px rgba(0,0,6,.15); }}
  .notes {{ font-size: 14px; line-height: 1.45; margin-top: 8px; max-width: 75em; }}
  .notes b {{ font-weight: 700; }}
  #zoom {{ position: fixed; inset: 0; background: rgba(0,0,0,.85); display: none; cursor: zoom-out;
          align-items: center; justify-content: center; padding: 12px; }}
  #zoom img {{ max-width: 100%; max-height: 100%; width: auto; border-radius: 0; box-shadow: none; }}
  @media (max-width: 800px) {{ .cols {{ grid-template-columns: 1fr; }} body {{ padding: 10px; }} }}
</style></head>
<body>
<header>
  <h1>Mailspring: vanilla · RedFox Adwaita · native mock</h1>
  <span><button id="light" class="on">Light</button> <button id="dark">Dark</button></span>
</header>
<p class="notes">Same window size (1280×800), same fake mailbox, same message open. Columns: Mailspring
with its own theme, RedFox's Adwaita theme at each iteration, and a GTK 4 / libadwaita mock of what a
native front end would look like. Newest iteration first. Click a picture to zoom.</p>
<div class="cols"><div class="colhead">Vanilla Mailspring</div><div class="colhead">RedFox Adwaita theme</div><div class="colhead">Native mock (target)</div></div>
{rows}
<div id="zoom"><img alt=""></div>
<script>
  const setMode = m => {{
    document.body.classList.toggle('dark', m === 'dark');
    document.getElementById('light').classList.toggle('on', m === 'light');
    document.getElementById('dark').classList.toggle('on', m === 'dark');
    for (const img of document.querySelectorAll('img[data-base]')) img.src = img.dataset.base + m + '.png';
    localStorage.setItem('mode', m);
  }};
  document.getElementById('light').onclick = () => setMode('light');
  document.getElementById('dark').onclick = () => setMode('dark');
  const zoom = document.getElementById('zoom');
  for (const img of document.querySelectorAll('img[data-base]'))
    img.onclick = () => {{ zoom.querySelector('img').src = img.src; zoom.style.display = 'flex'; }};
  zoom.onclick = () => zoom.style.display = 'none';
  setMode(localStorage.getItem('mode') || 'light');
</script>
</body></html>
"""

ROW = """<section class="row">
<h2>{id} <span style="font-weight:400;opacity:.6">· {date} · {commit}</span></h2>
<div class="cols">
  <figure><img data-base="vanilla/" src="vanilla/light.png" alt="Vanilla Mailspring"></figure>
  <figure><img data-base="{id}/" src="{id}/light.png" alt="RedFox Adwaita {id}"></figure>
  <figure><img data-base="mock/" src="mock/light.png" alt="Native mock"></figure>
</div>
<div class="notes"><b>Changed:</b> {changed}<br><b>Gaps left:</b> {gaps}{extra}</div>
</section>"""


def main():
    out = sys.argv[1]
    with open(os.path.join(HERE, "iterations.json")) as f:
        iterations = json.load(f)
    rows = []
    for it in reversed(iterations):
        missing = [p for p in (f"{it['id']}/light.png", f"{it['id']}/dark.png") if not os.path.exists(os.path.join(out, p))]
        if missing:
            sys.exit(f"missing screenshots for {it['id']}: {missing}")
        fields = {k: html.escape(str(v)) for k, v in it.items() if k != "extra"}
        links = "".join(f'<br><a href="{html.escape(href)}">{html.escape(text)}</a>'
                        for text, href in it.get("extra", {}).items())
        rows.append(ROW.format(extra=links, **fields))
    with open(os.path.join(out, "index.html"), "w") as f:
        f.write(PAGE.format(rows="\n".join(rows)))
    print(f"wrote {out}/index.html ({len(rows)} iterations)")


if __name__ == "__main__":
    main()
