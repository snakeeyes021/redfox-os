"""Software: RedFox's software packs, ticked and installed from a list.

A front end to redfox-software, which reads the catalog in
/usr/share/redfox/software.yaml (the same lists the install-* recipes use).
Each pack's `section` puts it on one of the tabs below.
"""

from gi.repository import Adw, Gtk

from . import host
from .window import Section

BAZAAR = "io.github.kolunmi.Bazaar"

# Catalog sections, in tab order: id, title, icon.
SECTIONS = [
    ("packs", "Packs", "view-app-grid-symbolic"),
    ("dev", "Dev", "utilities-terminal-symbolic"),
    ("gaming", "Gaming", "input-gaming-symbolic"),
    ("hardware", "Hardware", "computer-symbolic"),
    ("other", "Other", "view-more-symbolic"),
]


class AppsSection(Section):
    def __init__(self, window):
        self.items = {}        # id -> item dict
        self.checks = {}       # id -> [Gtk.CheckButton]
        self.spinners = {}     # id -> [Adw.Spinner]
        self.wanted = {}       # id -> bool, only where it differs from installed
        self.running = False
        self._guard = False

        self.stack = Gtk.Stack()
        self.stack.add_named(Adw.Spinner(), "loading")
        self.error = Adw.StatusPage(icon_name="dialog-warning-symbolic",
                                    title="Couldn't List the Apps")
        retry = Gtk.Button(label="Try Again", halign=Gtk.Align.CENTER)
        retry.add_css_class("pill")
        retry.connect("clicked", lambda *_: self.load())
        self.error.set_child(retry)
        self.stack.add_named(self.error, "error")

        # One page per section, shown as tabs; a tab only appears once its
        # section has something in it.
        self.tabs = Adw.ViewStack(vexpand=True)
        self.pages = {}
        for section_id, title, icon in SECTIONS:
            page = Adw.PreferencesPage(
                description="Ticked items are installed: tick or untick, then Apply."
                if section_id == "packs" else None)
            self.tabs.add_titled_with_icon(page, section_id, title, icon)
            self.pages[section_id] = page
        switcher = Adw.InlineViewSwitcher(stack=self.tabs, halign=Gtk.Align.CENTER,
                                          margin_top=12, margin_start=12, margin_end=12)
        tabbed = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        tabbed.append(switcher)
        tabbed.append(self.tabs)
        self.page = self.pages["packs"]
        self.stack.add_named(tabbed, "list")
        self.groups = []

        # Bazaar, if it's installed.
        more = Adw.PreferencesGroup(visible=False)
        row = Adw.ActionRow(title="Find More Apps in Bazaar",
                            subtitle="Thousands of apps from Flathub", activatable=True)
        icon = Gtk.Image(icon_name=BAZAAR, pixel_size=32)
        icon.add_css_class("lowres-icon")
        row.add_prefix(icon)
        row.add_suffix(Gtk.Image(icon_name="adw-external-link-symbolic"))
        row.connect("activated", lambda *_: host.run(["flatpak", "run", BAZAAR]))
        more.add(row)
        self.page.add(more)
        host.run(["flatpak", "info", "--show-ref", BAZAAR],
                 on_done=lambda rc, _out: more.set_visible(rc == 0))

        self.summary = Gtk.Label(xalign=0, hexpand=True)
        self.apply_button = Gtk.Button(label="Apply")
        self.apply_button.add_css_class("suggested-action")
        self.apply_button.connect("clicked", self.on_apply)
        reset = Gtk.Button(label="Undo Changes")
        reset.connect("clicked", lambda *_: self.reset())
        self.reset_button = reset
        bar = Gtk.ActionBar()
        bar.add_css_class("hub-action-bar")
        bar.pack_start(self.summary)
        bar.pack_end(self.apply_button)
        bar.pack_end(reset)
        self.bar = Gtk.Revealer(child=bar, reveal_child=False,
                                transition_type=Gtk.RevealerTransitionType.SLIDE_UP)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.stack.set_vexpand(True)
        root.append(self.stack)
        root.append(self.bar)
        super().__init__(window, "Software", root)
        self.loaded = False

    def shown(self):
        if not self.loaded and not self.running:
            self.load()

    def load(self):
        self.stack.set_visible_child_name("loading")
        host.run_json(["redfox-software", "list", "--json"], self._on_list)

    def _on_list(self, data, error):
        if error:
            self.error.set_description(error)
            self.stack.set_visible_child_name("error")
            return
        self.loaded = True
        for page, group in self.groups:
            page.remove(group)
        self.groups, self.items, self.checks, self.spinners = [], {}, {}, {}
        self.wanted = {}
        used = set()
        for pack in data.get("packs", []):
            if pack.get("hidden") or not pack.get("items"):
                continue
            page = self.pages.get(pack.get("section"), self.pages["packs"])
            group = Adw.PreferencesGroup(title=pack["name"],
                                         description=pack.get("description"))
            all_button = Gtk.Button(label="Tick All", valign=Gtk.Align.CENTER)
            all_button.add_css_class("flat")
            all_button.connect("clicked", self._on_tick_all, pack)
            group.set_header_suffix(all_button)
            for item in pack["items"]:
                group.add(self._row(item))
            page.add(group)
            self.groups.append((page, group))
            used.add(page)
        for section_id, page in self.pages.items():
            self.tabs.get_page(page).set_visible(section_id == "packs" or page in used)
        self._update_bar()
        self.stack.set_visible_child_name("list")

    def _row(self, item):
        self.items[item["id"]] = item
        row = Adw.ActionRow(title=item["name"], subtitle=item.get("summary") or "")
        icon_name = item.get("icon")
        if icon_name and icon_name.startswith("/"):
            icon = Gtk.Image.new_from_file(icon_name)
        else:
            icon = Gtk.Image(icon_name=icon_name or "application-x-executable-symbolic")
        icon.set_pixel_size(32)
        icon.add_css_class("lowres-icon")
        row.add_prefix(icon)
        spinner = Adw.Spinner(visible=False)
        row.add_suffix(spinner)
        check = Gtk.CheckButton(active=item["installed"], valign=Gtk.Align.CENTER)
        check.connect("toggled", self._on_toggled, item["id"])
        row.add_suffix(check)
        row.set_activatable_widget(check)
        self.checks.setdefault(item["id"], []).append(check)
        self.spinners.setdefault(item["id"], []).append(spinner)
        return row

    def _set_check(self, item_id, active):
        self._guard = True
        for check in self.checks.get(item_id, []):
            check.set_active(active)
        self._guard = False

    def _on_toggled(self, check, item_id):
        if self._guard:
            return
        active = check.get_active()
        self._set_check(item_id, active)   # the same app can be in two packs
        if active == self.items[item_id]["installed"]:
            self.wanted.pop(item_id, None)
        else:
            self.wanted[item_id] = active
        self._update_bar()

    def _on_tick_all(self, _button, pack):
        for item in pack["items"]:
            if not item["installed"]:
                self._set_check(item["id"], True)
                self.wanted[item["id"]] = True
        self._update_bar()

    def reset(self):
        for item_id in list(self.wanted):
            self._set_check(item_id, self.items[item_id]["installed"])
        self.wanted = {}
        self._update_bar()

    def _update_bar(self):
        add = [i for i, w in self.wanted.items() if w]
        remove = [i for i, w in self.wanted.items() if not w]
        parts = []
        if add:
            parts.append(f"Install {len(add)}")
        if remove:
            parts.append(f"remove {len(remove)}" if add else f"Remove {len(remove)}")
        self.summary.set_label(", ".join(parts))
        self.bar.set_reveal_child(bool(self.wanted) or self.running)

    # Applying

    def on_apply(self, _button):
        remove = [i for i, w in self.wanted.items() if not w]
        if not remove:
            self._run()
            return
        names = ", ".join(self.items[i]["name"] for i in remove)
        dialog = Adw.AlertDialog(
            heading="Remove Apps?",
            body=f"{names}\n\nTheir settings and data stay, in case you install them again.")
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("remove", "Remove")
        dialog.set_response_appearance("remove", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", lambda _d, r: r == "remove" and self._run())
        dialog.present(self.window)

    def _run(self):
        add = [i for i, w in self.wanted.items() if w]
        remove = [i for i, w in self.wanted.items() if not w]
        self.running = True
        self.apply_button.set_sensitive(False)
        self.reset_button.set_sensitive(False)
        for checks in self.checks.values():
            for check in checks:
                check.set_sensitive(False)
        self.failed = []
        steps = []
        if add:
            steps.append(["redfox-software", "install", "--json", *add])
        if remove:
            steps.append(["redfox-software", "remove", "--json", *remove])
        self.summary.set_label("Working…")
        self._next_step(steps)

    def _next_step(self, steps):
        if not steps:
            self._finished()
            return
        argv = steps.pop(0)
        host.run_events(argv, self._on_event, on_done=lambda *_: self._next_step(steps))

    def _on_event(self, event):
        item_id = event.get("id")
        kind = event.get("event")
        if kind == "start" and item_id in self.items:
            for spinner in self.spinners.get(item_id, []):
                spinner.set_visible(True)
            self.summary.set_label(f"{self.items[item_id]['name']}…")
        elif kind == "done" and item_id in self.items:
            for spinner in self.spinners.get(item_id, []):
                spinner.set_visible(False)
            if event.get("ok"):
                self.items[item_id]["installed"] = self.wanted.get(
                    item_id, self.items[item_id]["installed"])
                self.wanted.pop(item_id, None)
            else:
                self.failed.append(self.items[item_id]["name"])

    def _finished(self):
        self.running = False
        for item_id in list(self.wanted):
            self._set_check(item_id, self.items[item_id]["installed"])
        self.wanted = {}
        for checks in self.checks.values():
            for check in checks:
                check.set_sensitive(True)
        self.apply_button.set_sensitive(True)
        self.reset_button.set_sensitive(True)
        for spinners in self.spinners.values():
            for spinner in spinners:
                spinner.set_visible(False)
        self._update_bar()
        if self.failed:
            self.window.toast("Didn't finish: " + ", ".join(self.failed))
        else:
            self.window.toast("Done")
        # Refresh icons and states from the system.
        self.loaded = False
        self.load()
