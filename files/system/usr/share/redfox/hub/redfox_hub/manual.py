"""Manual: short help pages, from Markdown files in /usr/share/redfox/manual.

The pages use a small subset of Markdown (see docs/redfox-apps-design.md,
"Manual"): a `# Title` line, a one-sentence summary, `## Section` headings,
paragraphs, `-` and `1.` lists, **bold**, `code`, links, and ```sh blocks
of commands, which get a copy button. Links to `manual:slug` open another
page; `hub:updates` and the like open a part of Hub.
"""

import html
import os
import re
from pathlib import Path

from gi.repository import Adw, Gdk, Gtk

from .window import Section

MANUAL_DIR = Path(os.environ.get("REDFOX_MANUAL_DIR", "/usr/share/redfox/manual"))


class ManualPage:
    def __init__(self, path):
        self.slug = re.sub(r"^\d+-", "", path.stem)
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        self.title = lines[0].lstrip("# ").strip() if lines else self.slug
        body = lines[1:]
        while body and not body[0].strip():
            body.pop(0)
        summary = []
        while body and body[0].strip():
            summary.append(body.pop(0).strip())
        self.summary = " ".join(summary)
        self.body = "\n".join(body)
        self.search_text = f"{self.title} {self.summary} {self.body}".lower()


def load_pages():
    if not MANUAL_DIR.is_dir():
        return []
    return [ManualPage(p) for p in sorted(MANUAL_DIR.glob("[0-9]*.md"))]


def inline(text):
    """The inline subset to Pango markup."""
    out = []
    pos = 0
    pattern = re.compile(r"`([^`]+)`|\*\*([^*]+)\*\*|\[([^\]]+)\]\(([^)\s]+)\)")
    for match in pattern.finditer(text):
        out.append(html.escape(text[pos:match.start()], quote=False))
        code, bold, link_text, url = match.groups()
        if code is not None:
            out.append(f"<tt>{html.escape(code, quote=False)}</tt>")
        elif bold is not None:
            out.append(f"<b>{html.escape(bold, quote=False)}</b>")
        else:
            out.append(f'<a href="{html.escape(url)}">{html.escape(link_text, quote=False)}</a>')
        pos = match.end()
    out.append(html.escape(text[pos:], quote=False))
    return "".join(out)


class Renderer:
    def __init__(self, on_link):
        self.on_link = on_link

    def label(self, markup, css=None):
        label = Gtk.Label(label=markup, use_markup=True, wrap=True, xalign=0,
                          selectable=False)
        label.connect("activate-link", self._link)
        for c in css or []:
            label.add_css_class(c)
        return label

    def _link(self, _label, uri):
        return self.on_link(uri)

    def code_block(self, code):
        box = Gtk.Box(spacing=6)
        box.add_css_class("card")
        box.add_css_class("manual-code")
        text = Gtk.Label(label=code, xalign=0, selectable=True, hexpand=True,
                         wrap=True, wrap_mode=2)
        text.add_css_class("monospace")
        box.append(text)
        copy = Gtk.Button(icon_name="edit-copy-symbolic", valign=Gtk.Align.START,
                          tooltip_text="Copy")
        copy.add_css_class("flat")

        def on_copy(button):
            Gdk.Display.get_default().get_clipboard().set(code)
            button.set_icon_name("object-select-symbolic")
            button.set_tooltip_text("Copied")

        copy.connect("clicked", on_copy)
        box.append(copy)
        return box

    def list_item(self, marker, markup):
        row = Gtk.Box(spacing=8)
        bullet = Gtk.Label(label=marker, valign=Gtk.Align.START, xalign=1,
                           width_chars=2)
        row.append(bullet)
        item = self.label(markup)
        item.set_hexpand(True)
        row.append(item)
        return row

    def render(self, page):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        title = self.label(html.escape(page.title), ["title-1"])
        box.append(title)
        if page.summary:
            box.append(self.label(inline(page.summary), ["manual-summary", "dim-label"]))
        lines = page.body.splitlines()
        i = 0
        paragraph = []

        def flush():
            if paragraph:
                box.append(self.label(inline(" ".join(paragraph))))
                paragraph.clear()

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            if stripped.startswith("```"):
                flush()
                code = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    code.append(lines[i])
                    i += 1
                box.append(self.code_block("\n".join(code)))
            elif stripped.startswith("## "):
                flush()
                heading = self.label(inline(stripped[3:]), ["title-4"])
                heading.set_margin_top(12)
                box.append(heading)
            elif re.match(r"^(-|\d+\.)\s+", stripped):
                flush()
                items = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
                while i < len(lines) and re.match(r"^(-|\d+\.)\s+", lines[i].strip()):
                    marker, rest = re.match(r"^(-|\d+\.)\s+(.*)", lines[i].strip()).groups()
                    # A list item can wrap onto indented lines.
                    while (i + 1 < len(lines) and lines[i + 1].startswith("  ")
                           and lines[i + 1].strip()):
                        i += 1
                        rest += " " + lines[i].strip()
                    items.append(self.list_item("•" if marker == "-" else marker, inline(rest)))
                    i += 1
                box.append(items)
                continue
            elif not stripped:
                flush()
            else:
                paragraph.append(stripped)
            i += 1
        flush()
        return box


class ManualSection(Section):
    def __init__(self, window):
        self.pages = load_pages()
        self.renderer = Renderer(self.on_link)

        self.search = Gtk.SearchEntry(placeholder_text="Search the Manual",
                                      hexpand=True)
        self.search.connect("search-changed", self._on_search)
        self.list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self.list.add_css_class("boxed-list")
        self.rows = []
        for page in self.pages:
            row = Adw.ActionRow(title=page.title, subtitle=page.summary, activatable=True)
            row.add_suffix(Gtk.Image(icon_name="go-next-symbolic"))
            row.connect("activated", lambda _r, p=page: self.show(p))
            row.page = page
            self.list.append(row)
            self.rows.append(row)
        self.list.set_filter_func(self._filter)
        self.empty = Adw.StatusPage(icon_name="edit-find-symbolic",
                                    title="No Results", visible=False)
        self.empty.add_css_class("compact")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18,
                      margin_top=24, margin_bottom=24, margin_start=12, margin_end=12)
        intro = Gtk.Label(
            label="Short help for where RedFoxOS works differently from other "
                  "Linux systems.", wrap=True, xalign=0)
        intro.add_css_class("dim-label")
        box.append(intro)
        box.append(self.search)
        box.append(self.list)
        box.append(self.empty)
        if not self.pages:
            self.empty.set_title("No Manual Pages")
            self.empty.set_description(f"Nothing found in {MANUAL_DIR}.")
            self.empty.set_visible(True)
            self.list.set_visible(False)
        root = Gtk.ScrolledWindow(child=Adw.Clamp(maximum_size=720, child=box),
                                  hscrollbar_policy=Gtk.PolicyType.NEVER)
        super().__init__(window, "Manual", root)

    def _filter(self, row):
        query = self.search.get_text().strip().lower()
        return not query or all(word in row.page.search_text for word in query.split())

    def _on_search(self, _entry):
        self.list.invalidate_filter()
        visible = any(self._filter(row) for row in self.rows)
        self.empty.set_visible(not visible)
        self.list.set_visible(visible)

    def show(self, page):
        content = self.renderer.render(page)
        content.set_margin_top(24)
        content.set_margin_bottom(36)
        content.set_margin_start(12)
        content.set_margin_end(12)
        scroller = Gtk.ScrolledWindow(child=Adw.Clamp(maximum_size=720, child=content),
                                      hscrollbar_policy=Gtk.PolicyType.NEVER)
        self.push(page.title, scroller, tag=f"page-{page.slug}")

    def open(self, subpath):
        for page in self.pages:
            if page.slug == subpath:
                self.view.pop_to_tag("root")
                self.show(page)
                return

    def on_link(self, uri):
        if uri.startswith("manual:"):
            self.open(uri[len("manual:"):])
            return True
        if uri.startswith("hub:"):
            self.window.open_page(uri[len("hub:"):])
            return True
        return False  # GTK opens web links itself.
