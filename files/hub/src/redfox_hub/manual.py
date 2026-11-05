"""Manual: short help pages, from the Markdown files in Hub's data/manual.

The pages use a small subset of Markdown (see docs/redfox-apps-design.md,
"Manual"): a `# Title` line, a one-sentence summary, `## Section` headings,
paragraphs, `-` and `1.` lists, **bold**, `code`, links, and ```sh blocks
of commands, which get a copy button. Links to `manual:slug` open another
page; `hub:updates` and the like open a part of Hub.
"""

import html
import re

from gi.repository import Adw, Gdk, Gtk

from .paths import MANUAL as MANUAL_DIR
from .strings import HINT_MODE, data as copy_data, s
from .window import Section


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
    pattern = re.compile(r"`([^`]+)`|\*\*(.+?)\*\*|\[([^\]]+)\]\(([^)\s]+)\)")
    for match in pattern.finditer(text):
        out.append(html.escape(text[pos:match.start()], quote=False))
        code, bold, link_text, url = match.groups()
        if code is not None:
            out.append(f"<tt>{html.escape(code, quote=False)}</tt>")
        elif bold is not None:
            out.append(f"<b>{inline(bold)}</b>")  # bold can hold a link or code
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
                          tooltip_text=s("H-295"))
        copy.add_css_class("flat")

        def on_copy(button):
            Gdk.Display.get_default().get_clipboard().set(code)
            button.set_icon_name("object-select-symbolic")
            button.set_tooltip_text(s("H-296"))

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
        box.append(self.label(prose(page, "title", page.title, escape=True), ["title-1"]))
        if page.summary:
            box.append(self.label(prose(page, "summary", page.summary),
                                  ["manual-summary", "dim-label"]))
        items = None
        for n, (kind, text, marker) in enumerate(blocks(page.body), 1):
            if kind != "item":
                items = None
            if kind == "code":
                box.append(self.code_block(text))
            elif kind == "heading":
                heading = self.label(prose(page, n, text), ["title-4"])
                heading.set_margin_top(12)
                box.append(heading)
            elif kind == "item":
                if items is None:
                    items = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
                    box.append(items)
                items.append(self.list_item(marker, prose(page, n, text)))
            else:
                box.append(self.label(prose(page, n, text)))
        return box


def blocks(body):
    """The page body as (kind, text, marker) blocks, in reading order: kind is
    "heading", "paragraph", "item" (a list item; marker is its bullet or
    number) or "code" (commands, not prose). The copy pass numbers the
    blocks in this order, so keep it stable."""
    lines = body.splitlines()
    i = 0
    paragraph = []
    out = []

    def flush():
        if paragraph:
            out.append(("paragraph", " ".join(paragraph), None))
            paragraph.clear()

    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("```"):
            flush()
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            out.append(("code", "\n".join(code), None))
        elif stripped.startswith("## "):
            flush()
            out.append(("heading", stripped[3:], None))
        elif re.match(r"^(-|\d+\.)\s+", stripped):
            flush()
            while i < len(lines) and re.match(r"^(-|\d+\.)\s+", lines[i].strip()):
                marker, rest = re.match(r"^(-|\d+\.)\s+(.*)", lines[i].strip()).groups()
                # A list item can wrap onto indented lines.
                while (i + 1 < len(lines) and lines[i + 1].startswith("  ")
                       and lines[i + 1].strip()):
                    i += 1
                    rest += " " + lines[i].strip()
                out.append(("item", rest, "•" if marker == "-" else marker))
                i += 1
            continue
        elif not stripped:
            flush()
        else:
            paragraph.append(stripped)
        i += 1
    flush()
    return out


def prose(page, part, text, escape=False):
    """A Manual page's text as markup, or its copy-pass hint (H-M-<slug>-<part>)."""
    if HINT_MODE:
        return html.escape(copy_data("M", f"{page.slug}-{part}", text, "Manual text"))
    return html.escape(text) if escape else inline(text)


class ManualSection(Section):
    def __init__(self, window):
        self.pages = load_pages()
        self.renderer = Renderer(self.on_link)

        self.search = Gtk.SearchEntry(placeholder_text=s("H-291"),
                                      hexpand=True)
        self.search.connect("search-changed", self._on_search)
        self.list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self.list.add_css_class("boxed-list")
        self.rows = []
        for page in self.pages:
            row = Adw.ActionRow(title=prose(page, "title", page.title, escape=True),
                                subtitle=prose(page, "summary", page.summary), activatable=True)
            row.add_suffix(Gtk.Image(icon_name="go-next-symbolic"))
            row.connect("activated", lambda _r, p=page: self.show(p))
            row.page = page
            self.list.append(row)
            self.rows.append(row)
        self.list.set_filter_func(self._filter)
        self.empty = Adw.StatusPage(icon_name="edit-find-symbolic",
                                    title=s("H-292"), visible=False)
        self.empty.add_css_class("compact")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18,
                      margin_top=24, margin_bottom=24, margin_start=12, margin_end=12)
        intro = Gtk.Label(
            label=s("H-290"), wrap=True, xalign=0)
        intro.add_css_class("dim-label")
        box.append(intro)
        box.append(self.search)
        box.append(self.list)
        box.append(self.empty)
        if not self.pages:
            self.empty.set_title(s("H-293"))
            self.empty.set_description(s("H-294", folder=MANUAL_DIR))
            self.empty.set_visible(True)
            self.list.set_visible(False)
        root = Gtk.ScrolledWindow(child=Adw.Clamp(maximum_size=720, child=box),
                                  hscrollbar_policy=Gtk.PolicyType.NEVER)
        super().__init__(window, s("H-024"), root)

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
        self.push(copy_data("M", f"{page.slug}-title", page.title, "Manual text"),
                  scroller, tag=f"page-{page.slug}")

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
