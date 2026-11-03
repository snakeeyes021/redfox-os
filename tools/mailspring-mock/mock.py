#!/usr/bin/python3
"""What a GNOME-native (GTK 4 / libadwaita) front end for Mailspring would look
like: a static mock with fake data, used as the target the RedFox Adwaita theme
is compared against. Not shipped in the image.

    mock.py [--dark] [--screenshot FILE] [--size WIDTHxHEIGHT]

With --screenshot it renders the window to FILE once it's drawn, then quits.
Run it on a hidden display (see compare.sh) so nothing opens on the desktop.
"""
import argparse
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GLib, Gtk  # noqa: E402

# The same fake mailbox as the test account in the VM (see compare.sh).
ACCOUNT = "tester@redfox.test"
FOLDERS = [("folder-download-symbolic", "Inbox", 6), ("mail-unread-symbolic", "Unread", 6),
           ("starred-symbolic", "Starred", 0), ("document-edit-symbolic", "Drafts", 0),
           ("mail-send-symbolic", "Sent", 0), ("user-trash-symbolic", "Trash", 0)]
THREADS = [
    ("Ada Lovelace", "Notes on the Analytical Engine",
     "I have attached my notes, with the table for Bernoulli numbers.", "11:05 AM", True, True),
    ("Linus", "Re: patch v3", "Applied, thanks. Looks good.", "11:04 AM", True, False),
    ("Margaret Hamilton", "Lunar module checklist", "Final review of the priority display logic.", "11:03 AM", True, False),
    ("RedFox Labs", "Welcome to RedFoxOS", "Your desktop is ready. Here are a few tips to get started.", "11:02 AM", True, False),
    ("Dewy", "Weekend plans?", "Hiking on Saturday if the weather holds.", "11:01 AM", True, False),
    ("Grace Hopper", "Compiler meeting moved to Thursday", "Room 4B, bring the punch cards.", "11:00 AM", True, False),
]

CSS = """
.thread-row { padding: 10px 12px; }
.thread-row .sender { font-weight: 700; }
.thread-row .snippet { opacity: 0.55; }
.thread-row .time { font-size: 0.85em; opacity: 0.55; }
.unread-dot { min-width: 8px; min-height: 8px; border-radius: 4px; background: var(--accent-bg-color); }
.message-card { padding: 18px 22px; }
.message-body { font-size: 1.05em; }
"""


def label(text, *classes, xalign=0.0, ellipsize=True, wrap=False):
    lab = Gtk.Label(label=text, xalign=xalign)
    if ellipsize:
        lab.set_ellipsize(3)  # Pango.EllipsizeMode.END
    if wrap:
        lab.set_wrap(True)
        lab.set_ellipsize(0)
    for c in classes:
        lab.add_css_class(c)
    return lab


def sidebar():
    view = Adw.ToolbarView()
    header = Adw.HeaderBar()
    header.set_title_widget(Adw.WindowTitle(title="Mail"))
    compose = Gtk.Button(icon_name="mail-message-new-symbolic", tooltip_text="Compose")
    header.pack_start(compose)
    header.pack_end(Gtk.MenuButton(icon_name="open-menu-symbolic", tooltip_text="Main Menu"))
    view.add_top_bar(header)

    box = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
    box.add_css_class("navigation-sidebar")
    head = label(ACCOUNT, "heading", "dim-label")
    head.set_margin_start(12)
    head.set_margin_top(6)
    head.set_margin_bottom(6)
    hrow = Gtk.ListBoxRow(activatable=False, selectable=False, child=head)
    box.append(hrow)
    first = None
    for icon, name, count in FOLDERS:
        row = Gtk.Box(spacing=12)
        row.append(Gtk.Image(icon_name=icon))
        row.append(label(name, xalign=0.0))
        row.get_last_child().set_hexpand(True)
        if count:
            badge = label(str(count), "dim-label", "caption-heading", ellipsize=False)
            row.append(badge)
        lbr = Gtk.ListBoxRow(child=row)
        box.append(lbr)
        first = first or lbr
    box.select_row(first)
    scroll = Gtk.ScrolledWindow(child=box, vexpand=True)
    view.set_content(scroll)
    return Adw.NavigationPage(title="Mail", child=view)


def thread_row(sender, subject, snippet, time, unread, starred):
    grid = Gtk.Grid(column_spacing=10, row_spacing=2)
    grid.add_css_class("thread-row")
    dot = Gtk.Box(valign=Gtk.Align.CENTER)
    if unread:
        dot.add_css_class("unread-dot")
    else:
        dot.set_size_request(8, 8)
    grid.attach(dot, 0, 0, 1, 1)
    s = label(sender, "sender")
    s.set_hexpand(True)
    grid.attach(s, 1, 0, 1, 1)
    grid.attach(label(time, "time", xalign=1.0, ellipsize=False), 2, 0, 1, 1)
    grid.attach(label(subject), 1, 1, 1, 1)
    star = Gtk.Image(icon_name="starred-symbolic" if starred else "non-starred-symbolic")
    if not starred:
        star.add_css_class("dim-label")
    else:
        star.add_css_class("accent")
    grid.attach(star, 2, 1, 1, 1)
    grid.attach(label(snippet, "snippet"), 1, 2, 2, 1)
    return Gtk.ListBoxRow(child=grid)


def thread_list():
    view = Adw.ToolbarView()
    header = Adw.HeaderBar()
    header.set_title_widget(Adw.WindowTitle(title="Inbox", subtitle="6 unread"))
    header.pack_end(Gtk.ToggleButton(icon_name="system-search-symbolic", tooltip_text="Search"))
    header.pack_start(Gtk.Button(icon_name="selection-mode-symbolic", tooltip_text="Select"))
    view.add_top_bar(header)
    box = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
    box.add_css_class("navigation-sidebar")
    rows = [thread_row(*t) for t in THREADS]
    for r in rows:
        box.append(r)
    box.select_row(rows[0])
    view.set_content(Gtk.ScrolledWindow(child=box, vexpand=True))
    return Adw.NavigationPage(title="Inbox", child=view)


def message_pane():
    view = Adw.ToolbarView()
    header = Adw.HeaderBar(show_title=False)
    for icon, tip in (("mail-reply-sender-symbolic", "Reply"), ("mail-reply-all-symbolic", "Reply All"),
                      ("mail-forward-symbolic", "Forward")):
        header.pack_start(Gtk.Button(icon_name=icon, tooltip_text=tip))
    header.pack_end(Gtk.MenuButton(icon_name="view-more-symbolic", tooltip_text="More"))
    header.pack_end(Gtk.Button(icon_name="user-trash-symbolic", tooltip_text="Delete"))
    header.pack_end(Gtk.Button(icon_name="package-x-generic-symbolic", tooltip_text="Archive"))
    view.add_top_bar(header)

    sender, subject, _snippet, time, _u, _s = THREADS[0]
    col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
    col.set_margin_top(18)
    col.set_margin_bottom(18)
    col.set_margin_start(12)
    col.set_margin_end(12)
    col.append(label(subject, "title-2", wrap=True))

    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
    card.add_css_class("card")
    card.add_css_class("message-card")
    who = Gtk.Box(spacing=12)
    who.append(Adw.Avatar(size=40, text=sender, show_initials=True))
    names = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, hexpand=True, valign=Gtk.Align.CENTER)
    names.append(label(sender, "heading"))
    names.append(label("To: you", "dim-label", "caption"))
    who.append(names)
    who.append(label(time, "dim-label", "caption", ellipsize=False))
    card.append(who)
    card.append(Gtk.Separator())
    # In a real front end this is a WebKitGTK view showing the message's HTML.
    body = label(THREADS[0][2], "message-body", wrap=True)
    body.set_selectable(True)
    card.append(body)
    col.append(card)

    reply = Gtk.Button(label="Reply", halign=Gtk.Align.START)
    reply.add_css_class("pill")
    reply.add_css_class("suggested-action")
    col.append(reply)

    clamp = Adw.Clamp(maximum_size=760, child=col)
    view.set_content(Gtk.ScrolledWindow(child=clamp, vexpand=True))
    return Adw.NavigationPage(title=subject, child=view)


class MockApp(Adw.Application):
    def __init__(self, args):
        super().__init__(application_id="tech.redfoxlabs.MailMock")
        self.args = args

    def do_activate(self):
        Adw.StyleManager.get_default().set_color_scheme(
            Adw.ColorScheme.FORCE_DARK if self.args.dark else Adw.ColorScheme.FORCE_LIGHT)
        # Window buttons on the right, as in the VM's GNOME session.
        Gtk.Settings.get_default().set_property("gtk-decoration-layout", ":minimize,maximize,close")
        provider = Gtk.CssProvider()
        provider.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        w, h = self.args.size
        inner = Adw.NavigationSplitView(sidebar=thread_list(), content=message_pane(),
                                        min_sidebar_width=300, max_sidebar_width=360, sidebar_width_fraction=0.36)
        outer = Adw.NavigationSplitView(sidebar=sidebar(),
                                        content=Adw.NavigationPage(title="Inbox", child=inner),
                                        min_sidebar_width=200, max_sidebar_width=240, sidebar_width_fraction=0.2)
        win = Adw.ApplicationWindow(application=self, default_width=w, default_height=h,
                                    title="Mail", content=outer)
        win.present()
        if self.args.screenshot:
            GLib.timeout_add(1500, self.capture, win)

    def capture(self, win):
        # Render the whole window (its background included), then cut away the
        # shadow round it, so the PNG is exactly the window's frame.
        w, h = win.get_width(), win.get_height()
        paintable = Gtk.WidgetPaintable(widget=win)
        pw, ph = paintable.get_intrinsic_width(), paintable.get_intrinsic_height()
        snap = Gtk.Snapshot()
        paintable.snapshot(snap, pw, ph)
        texture = win.get_native().get_renderer().render_texture(snap.to_node(), None)
        ok, bounds = win.get_content().compute_bounds(win)
        full = self.args.screenshot + ".full.png"
        texture.save_to_png(full)
        from PIL import Image
        img = Image.open(full)
        ox = (img.width - w) // 2 if img.width > w else 0
        oy = (img.height - h) // 2 if img.height > h else 0
        x0, y0 = int(bounds.get_x()), int(bounds.get_y())
        img.crop((x0, y0, x0 + w, y0 + h)).save(self.args.screenshot)
        import os
        os.remove(full)
        print(f"saved {self.args.screenshot} ({w}x{h}; texture {img.width}x{img.height}, content at {x0},{y0})")
        self.quit()
        return GLib.SOURCE_REMOVE


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dark", action="store_true")
    p.add_argument("--screenshot")
    p.add_argument("--size", default="1280x800", type=lambda s: tuple(int(v) for v in s.split("x")))
    args = p.parse_args()
    return MockApp(args).run([sys.argv[0]])


if __name__ == "__main__":
    sys.exit(main())
