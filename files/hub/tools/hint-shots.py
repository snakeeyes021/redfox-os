#!/usr/bin/env python3
"""Screenshot every Hub screen, dialog and state, for the copy pass.

    REDFOX_HUB_COPY_HINTS=1 python3 files/hub/tools/hint-shots.py OUT_DIR

Run inside a desktop session (it opens Hub's windows). Commands that only
read (the software list, layouts, start-at-login apps) run for real; the
update tooling's answers are made up, one state per shot, and nothing that
changes the system is run. Each shot is the window rendered by GTK itself,
so it doesn't matter what else is on the screen. Writes OUT_DIR/NN-name.png
and OUT_DIR/shots.json (file, screen, caption) in reading order.
"""

import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("REDFOX_HUB_COPY_HINTS", "1")  # before Hub reads it
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Graphene", "1.0")
from gi.repository import Adw, Gio, GLib, Graphene, Gtk  # noqa: E402

from redfox_hub import host, manual  # noqa: E402
from redfox_hub.app import HubApplication  # noqa: E402

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "hint-shots")
OUT.mkdir(parents=True, exist_ok=True)
NOW = int(time.time())
DAY = 86400

# --- Made-up answers -------------------------------------------------------

REAL_RUN, REAL_JSON = host.run, host.run_json
FAKE_JSON = {}      # argv prefix -> (data, error), or PENDING
PENDING = object()  # never answers: the "still loading" states


def status(**changes):
    st = {
        "version": 1,
        "auto": {"enabled": True, "running": False, "next": NOW + 14 * 3600,
                 "last_run": NOW - 3 * 3600, "last_result": "success"},
        "now": {"running": False, "last_run": NOW - 2 * DAY, "last_ok": True},
        "busy": False, "restart_pending": False, "restart_for": None,
        "booted": {"image": "redfox-os", "tag": "latest", "channel": "latest",
                   "version": "45.20261105", "timestamp": NOW - DAY},
        "staged": None,
        "rollback": {"image": "redfox-os", "tag": "latest", "channel": "latest",
                     "version": "45.20261104", "timestamp": NOW - 2 * DAY},
    }
    for key, value in changes.items():
        if isinstance(value, dict) and isinstance(st.get(key), dict):
            st[key] = dict(st[key], **value)
        else:
            st[key] = value
    return st


IMAGES = {
    "version": 1, "booted": {"image": "redfox-os", "channel": "latest"},
    "images": [
        {"id": "redfox-os", "name": "Mainline", "description": "Intel and AMD graphics"},
        {"id": "redfox-os-nvidia", "name": "NVIDIA", "description": "NVIDIA GTX 16xx, RTX 20xx and newer"},
        {"id": "redfox-os-nvidia-legacy", "name": "NVIDIA legacy", "description": "NVIDIA GTX 10xx and older"},
    ],
    "recommended": "redfox-os",
}
BRANCHES = {"version": 1, "image": "redfox-os", "branches": [
    {"branch": "feature/quiet-boot", "title": "feature/quiet-boot", "tag": "br-feature_quiet-boot-45",
     "updated": "2026-11-04", "description": ""},
    {"branch": "feature/hub-search", "title": "#41 Search across the Manual and settings",
     "tag": "pr-41-45", "updated": "2026-11-03", "description": "Adds one search box for everything."},
]}
BUILDS = {"version": 1, "image": "redfox-os", "channel": "latest", "builds": [
    {"tag": "latest", "commit": "fb19436", "date": "2026-11-05", "message": "Image picker: recommended graphics"},
    {"tag": "e9f2b9a-45", "commit": "e9f2b9a", "date": "2026-11-04", "message": "Feature branches: cut descriptions at a word"},
    {"tag": "4287a86-45", "commit": "4287a86", "date": "2026-11-03", "message": "Feature branches: pluggable sources"},
    {"tag": "f270cfd-44", "commit": "f270cfd", "date": "2026-11-01", "message": "docs: commit to unstable, not main"},
]}


def fake_json(argv, on_done):
    for prefix, answer in FAKE_JSON.items():
        if tuple(argv[:len(prefix)]) == prefix:
            if answer is not PENDING:
                GLib.idle_add(on_done, *answer)
            return
    REAL_JSON(argv, on_done)


SAFE = {("flatpak", "info"), ("gsettings", "get")}


def fake_run(argv, on_done=None, on_line=None, on_partial=None):
    if tuple(argv[:2]) in SAFE:
        return REAL_RUN(argv, on_done, on_line, on_partial)
    # Anything that would change the system: pretend it's still running.
    return None


host.run_json, host.run = fake_json, fake_run


def standard():
    FAKE_JSON.clear()
    FAKE_JSON.update({
        ("redfox-updates", "status"): (status(), None),
        ("redfox-rollback-helper", "--json", "images"): (IMAGES, None),
        ("redfox-rollback-helper", "--json", "branches"): (BRANCHES, None),
        ("redfox-rollback-helper", "--json", "list"): (BUILDS, None),
        ("midikeep", "data-dir"): ({"data_dir": "/home/tester/Music/MIDI"}, None),
    })


# --- Capturing --------------------------------------------------------------

SHOTS = []


def render(widget, path):
    w, h = widget.get_width(), widget.get_height()
    snapshot = Gtk.Snapshot()
    Gtk.WidgetPaintable.new(widget).snapshot(snapshot, w, h)
    node = snapshot.to_node()
    rect = Graphene.Rect().init(0, 0, w, h)
    texture = widget.get_native().get_renderer().render_texture(node, rect)
    texture.save_to_png(str(path))


def find(widget, kind, start=None):
    """The first descendant of widget that is a kind."""
    child = widget.get_first_child()
    while child:
        if isinstance(child, kind):
            return child
        found = find(child, kind)
        if found:
            return found
        child = child.get_next_sibling()
    return None


def scroll_to(widget, fraction=None):
    """Scroll widget's nearest scrolled window: to widget, or to a fraction."""
    parent = widget
    while parent and not isinstance(parent, Gtk.ScrolledWindow):
        parent = parent.get_parent()
    if parent is None:
        return
    adj = parent.get_vadjustment()
    if fraction is not None:
        adj.set_value((adj.get_upper() - adj.get_page_size()) * fraction)
        return
    ok, point = widget.compute_point(parent.get_child(), Graphene.Point().init(0, 0))
    if ok:
        adj.set_value(min(point.y - 12, adj.get_upper() - adj.get_page_size()))


def page_scroller(section):
    page = section.view.get_visible_page()
    return find(page, Gtk.ScrolledWindow)


class Runner:
    def __init__(self, app):
        self.app = app
        self.steps = []

    def shot(self, screen, caption, setup, wait=500, target=None):
        self.steps.append((screen, caption, setup, wait, target))

    def start(self):
        GLib.timeout_add(1500, self._next)

    def _next(self):
        if not self.steps:
            (OUT / "shots.json").write_text(json.dumps(SHOTS, indent=2, ensure_ascii=False) + "\n")
            print(f"{len(SHOTS)} shots in {OUT}")
            self.app.quit()
            return False
        screen, caption, setup, wait, target = self.steps.pop(0)
        try:
            result = setup()
        except Exception as error:  # keep going; the gap shows in shots.json
            print(f"setup failed for {screen}: {caption}: {error!r}", file=sys.stderr)
            result = None
        GLib.timeout_add(wait, self._capture, screen, caption, target or result)
        return False

    def _capture(self, screen, caption, target):
        widget = target() if callable(target) else (target if isinstance(target, Gtk.Widget) else win)
        name = f"{len(SHOTS) + 1:03d}.png"
        try:
            render(widget, OUT / name)
            SHOTS.append({"file": name, "screen": screen, "caption": caption})
            print(name, screen, "·", caption)
        except Exception as error:
            print(f"capture failed for {screen}: {caption}: {error!r}", file=sys.stderr)
        GLib.timeout_add(100, self._next)
        return False


win = None


def close_dialogs():
    dialog = win.get_visible_dialog()
    while dialog:
        dialog.force_close()
        dialog = win.get_visible_dialog()
    if hasattr(win.toasts, "dismiss_all"):
        win.toasts.dismiss_all()


def toast(text):
    close_dialogs()
    win.toast(text)


def plan(r, app):
    global win
    from redfox_hub.strings import s
    from redfox_hub.updates import BuildsPage, UpdatesSection
    from redfox_hub.welcome import WelcomeWindow

    # Launcher and About
    def about():
        close_dialogs()
        app.on_about()
    r.shot("Launcher and About", "About dialog (from the sidebar menu)", about, wait=800)

    # Window and sidebar
    def menu():
        close_dialogs()
        win.show_section("welcome")
        button = find(win.split.get_sidebar(), Gtk.MenuButton)
        button.popup()
        return button.get_popover()
    r.shot("Window and sidebar", "Sidebar menu (the ☰ button)", menu, wait=600)

    def unmenu():
        button = find(win.split.get_sidebar(), Gtk.MenuButton)
        button.popdown()
    # Welcome tour, inside the window, then on its own.
    tour = lambda: win.section("welcome").tour  # noqa: E731
    for n in range(5):
        def step(n=n):
            unmenu()
            win.show_section("welcome")
            carousel = tour().carousel
            carousel.scroll_to(carousel.get_nth_page(n), False)
        r.shot("Welcome tour", f"Tour page {n + 1} of 5, in the main window", step, wait=700)

    def own_window(last=False):
        def setup():
            app.welcome = app.welcome or WelcomeWindow(application=app)
            app.welcome.present()
            t = find(app.welcome, type(tour()))
            t.carousel.scroll_to(t.carousel.get_nth_page(4 if last else 0), False)
            return app.welcome
        return setup
    r.shot("Welcome tour", "The tour in its own window (first login, or ☰ › tour): first page", own_window(), wait=900)
    r.shot("Welcome tour", "The tour in its own window: last page", own_window(True), wait=700)

    def close_welcome():
        if app.welcome:
            app.welcome.destroy()
            app.welcome = None
        win.present()

    # Apps
    def apps_top():
        close_welcome()
        sec = win.show_section("apps")
        scroll_to(sec.page, 0)
    r.shot("Apps", "Apps page, top", apps_top, wait=2500)

    def apps_ticked():
        sec = win.sections["apps"]
        items = [i for i in sec.items.values()]
        adds = [i for i in items if not i["installed"]][:3]
        removes = [i for i in items if i["installed"]][:1]
        for i in adds + removes:
            sec._set_check(i["id"], not i["installed"])
            sec.wanted[i["id"]] = not i["installed"]
        sec._update_bar()
    r.shot("Apps", "Some apps ticked and one unticked: the bar at the bottom", apps_ticked, wait=700)

    def apps_remove_only():
        sec = win.sections["apps"]
        sec.reset()
        removes = [i for i in sec.items.values() if i["installed"]][:2]
        for i in removes:
            sec._set_check(i["id"], False)
            sec.wanted[i["id"]] = False
        sec._update_bar()
    r.shot("Apps", "Only removals ticked", apps_remove_only, wait=700)
    r.shot("Apps", "Confirming a removal", lambda: win.sections["apps"].on_apply(None), wait=700)

    def apps_running():
        close_dialogs()
        sec = win.sections["apps"]
        sec._run()
        first = next(iter(sec.wanted))
        sec._on_event({"event": "start", "id": first})
        scroll_to(sec.checks[first][0])
    r.shot("Apps", "Installing: the bar while it works", apps_running, wait=700)

    def apps_done(failed):
        def setup():
            sec = win.sections["apps"]
            sec.failed = [list(sec.items.values())[0]["name"]] if failed else []
            sec._finished()
        return setup
    r.shot("Apps", "Finished, all worked (toast)", apps_done(False), wait=900)
    r.shot("Apps", "Finished, one failed (toast)", apps_done(True), wait=900)

    def apps_error():
        close_dialogs()
        sec = win.sections["apps"]
        REAL_RUN(["redfox-software-missing", "list"], on_done=lambda _rc, out: sec._on_list(None, out))
    r.shot("Apps", "The catalog can't be read (here: the tool is missing)", apps_error, wait=1200)

    # Updates
    upd = lambda: win.sections["updates"]  # noqa: E731

    def updates(st=None, fraction=0.0, images=None):
        def setup():
            close_dialogs()
            standard()
            if images is not None:
                FAKE_JSON[("redfox-rollback-helper", "--json", "images")] = images
            if st is not None:
                FAKE_JSON[("redfox-updates", "status")] = st
            sec = win.show_section("updates")
            sec.view.pop_to_tag("root")
            sec.updating = False
            sec.log_expander.set_visible(False)
            sec.images = []
            sec.shown()
            GLib.timeout_add(250, lambda: scroll_to(page_scroller(sec).get_child(), fraction) and False)
        return setup

    r.shot("Updates: status", "All well (the usual state), top of the page", updates(), wait=1200)
    r.shot("Updates: status", "The status can't be read",
           updates((None, "redfox-updates: something went wrong")), wait=900)
    r.shot("Updates: status", "Brand new: no update has run yet",
           updates((status(auto={"last_run": None, "last_result": None}, now={"last_run": None}), None)), wait=900)
    r.shot("Updates: status", "The last update failed",
           updates((status(auto={"last_result": "failed"}), None)), wait=900)
    r.shot("Updates: status", "Automatic updates switched off",
           updates((status(auto={"enabled": False}), None)), wait=900)
    r.shot("Updates: status", "The automatic update is running right now",
           updates((status(busy=True, auto={"running": True}), None)), wait=900)
    r.shot("Updates: status", "Update downloaded, restart to finish (version known)",
           updates((status(restart_pending=True, staged={"version": "45.20261106"}), None)), wait=900)
    r.shot("Updates: status", "Update downloaded, restart to finish (version unknown)",
           updates((status(restart_pending=True, staged=None), None)), wait=900)
    r.shot("Updates: status", "Going back chosen, restart to finish",
           updates((status(restart_pending=True, restart_for="rollback"), None)), wait=900)

    def updating():
        updates()()
        sec = upd()
        sec.on_update_now(None)
        for line in ("==> System update", "Pulling ghcr.io/snakeeyes021/redfox-os:latest",
                     "Fetching 41/88 layers", "==> Flatpak", "Nothing to do."):
            sec._append_log(line)
        sec.log_expander.set_expanded(True)
    r.shot("Updates: status", "Update now pressed: running, with the output open", updating, wait=900)

    def downloading():
        updates()()
        sec = upd()
        sec.rebase("unstable")
        sec.log_expander.set_expanded(False)
    r.shot("Updates: status", "Downloading a different build or channel", downloading, wait=900)

    r.shot("Updates: automatic updates", "Automatic updates group", updates(fraction=0.25), wait=1000)
    r.shot("Updates: automatic updates", "Automatic updates group, last run failed",
           updates((status(auto={"last_result": "failed", "last_run": NOW - DAY}), None), fraction=0.25), wait=1000)
    r.shot("Updates: automatic updates", "Automatic updates group, switched off",
           updates((status(auto={"enabled": False, "last_run": NOW - 4 * DAY}), None), fraction=0.25), wait=1000)
    r.shot("Updates: system image", "System image group", updates(fraction=0.55), wait=1000)

    def dropdown():
        updates(fraction=0.55)()
        GLib.timeout_add(800, lambda: upd().graphics_row.activate() and False)
    r.shot("Updates: system image", "The graphics dropdown, open (it marks the variant that suits this computer)",
           dropdown, wait=1500, target=lambda: find(upd().graphics_row, Gtk.Popover))

    def graphics_unreadable():
        popover = find(upd().graphics_row, Gtk.Popover)
        if popover:
            popover.popdown()
        updates(fraction=0.55, images=(None, "no"))()
    r.shot("Updates: system image", "The variants can't be read", graphics_unreadable, wait=1000)
    r.shot("Updates: system image", "Held on one build (pinned)",
           updates((status(booted={"channel": "pinned", "tag": "f270cfd-44"}), None), fraction=0.55), wait=1000)

    def variant_dialog():
        updates(fraction=0.55)()
        GLib.timeout_add(600, lambda: upd().graphics_row.set_selected(1) and False)
    r.shot("Updates: system image", "Switching graphics variant: confirm", variant_dialog, wait=1400)

    def channel_dialog(channel):
        def setup():
            updates(fraction=0.55)()
            GLib.timeout_add(600, lambda: upd().on_channel_toggled(
                type("C", (), {"get_active": lambda self: True})(), channel) and False)
        return setup
    r.shot("Updates: system image", "Switching to unstable: confirm", channel_dialog("unstable"), wait=1400)
    r.shot("Updates: system image", "Switching to stable: confirm", channel_dialog("latest"), wait=1400)

    r.shot("Updates: going back", "Going back group", updates(fraction=0.85), wait=1000)
    r.shot("Updates: going back", "No earlier system yet",
           updates((status(rollback=None), None), fraction=0.85), wait=1000)
    r.shot("Updates: going back", "System details unknown",
           updates((status(booted={}, rollback={}), None), fraction=0.85), wait=1000)

    def rollback_dialog():
        updates(fraction=0.85)()
        GLib.timeout_add(600, lambda: upd().on_rollback(None) and False)
    r.shot("Updates: going back", "Going back: confirm", rollback_dialog, wait=1400)

    def restart_dialog():
        updates((status(restart_pending=True, staged={"version": "45.20261106"}), None))()
        GLib.timeout_add(600, lambda: upd().on_restart(None) and False)
    r.shot("Updates: restart", "Restart: confirm", restart_dialog, wait=1400)

    def advanced(answer):
        def setup():
            updates(fraction=1.0)()
            row = upd().branches_row
            row.set_expanded(False)
            FAKE_JSON[("redfox-rollback-helper", "--json", "branches")] = answer
            row.set_expanded(True)
            GLib.timeout_add(400, lambda: scroll_to(page_scroller(upd()).get_child(), 1.0) and False)
        return setup
    r.shot("Updates: advanced", "Advanced, closed", updates(fraction=1.0), wait=1000)
    r.shot("Updates: advanced", "Test builds, loading", advanced(PENDING), wait=1200)
    r.shot("Updates: advanced", "Test builds, list", advanced((BRANCHES, None)), wait=1200)
    r.shot("Updates: advanced", "Test builds, none at the moment",
           advanced(({"version": 1, "image": "redfox-os", "branches": []}, None)), wait=1200)
    r.shot("Updates: advanced", "Test builds, can't be fetched",
           advanced((None, "GitHub didn't answer (offline?)")), wait=1200)

    def try_dialog():
        advanced((BRANCHES, None))()
        GLib.timeout_add(700, lambda: upd()._on_try_branch(None, "redfox-os", BRANCHES["branches"][1]) and False)
    r.shot("Updates: advanced", "Trying a test build: confirm", try_dialog, wait=1500)

    for text, caption in (("H-225", "Update finished (toast)"), ("H-226", "Update had problems (toast)"),
                          ("H-227", "Password prompt dismissed (toast)"),
                          ("H-228", "Automatic updates switch didn't change (toast)"),
                          ("H-229", "Switched, restart needed (toast)"), ("H-230", "Switch failed (toast)"),
                          ("H-231", "Going back set up, restart (toast)"),
                          ("H-232", "Something failed, nothing more to say (toast, shared)")):
        r.shot("Updates: toasts", caption, lambda t=text: (updates()(), toast(s(t))), wait=900)

    # Other builds
    def builds(answer=None):
        def setup():
            updates()()
            if answer is not None:
                FAKE_JSON[("redfox-rollback-helper", "--json", "list")] = answer
            GLib.timeout_add(300, lambda: upd().open("builds") and False)
        return setup
    r.shot("Other builds", "Other builds page", builds(), wait=1400)
    r.shot("Other builds", "Other builds, loading", builds(PENDING), wait=1400)
    r.shot("Other builds", "Other builds can't be listed", builds((None, "ghcr.io: no route to host")), wait=1400)

    def build_dialog():
        builds()()
        GLib.timeout_add(900, lambda: upd().view.get_visible_page()._on_switch(None, BUILDS["builds"][2]) and False)
    r.shot("Other builds", "Switching to a build: confirm", build_dialog, wait=1600)

    # Settings
    def settings(autostart=None):
        def setup():
            close_dialogs()
            standard()
            if autostart is not None:
                FAKE_JSON[("redfox-autostart", "list")] = autostart
            sec = win.show_section("settings")
            sec.view.pop_to_tag("root")
        return setup
    r.shot("Settings", "Settings page", settings(), wait=1500)
    r.shot("Settings", "Settings, an app that isn't installed",
           settings(({"apps": [{"id": "com.valvesoftware.Steam", "name": "Steam", "installed": True, "on": True},
                               {"id": "com.discordapp.Discord", "name": "Discord", "installed": False, "on": False}]},
                     None)), wait=1200)
    r.shot("Settings", "Settings, start-at-login apps can't be read",
           settings((None, "redfox-autostart: something went wrong")), wait=1200)
    r.shot("Settings", "Recordings folder changed (toast)", lambda: (settings()(), toast(s("H-262"))), wait=1200)

    # Layout page
    def layout():
        close_dialogs()
        standard()
        sec = win.show_section("settings")
        sec.open("layout")
    r.shot("Layout page", "Layout page, top", layout, wait=2000)
    def layout_error():
        close_dialogs()
        standard()
        FAKE_JSON[("redfox-layout", "list")] = (None, "redfox-layout: something went wrong")
        sec = win.show_section("settings")
        sec.layout_page = None
        sec.open("layout")
    r.shot("Layout page", "The layouts can't be listed", layout_error, wait=1200)

    def layout_toast():
        sec = win.sections["settings"]
        sec.view.pop_to_tag("root")
        sec.layout_page = None
        layout()
        GLib.timeout_add(1200, lambda: toast(s("H-277")) and False)
    r.shot("Layout page", "Picking a layout failed (toast)", layout_toast, wait=2200)

    # Manual
    def manual_index(query=""):
        def setup():
            close_dialogs()
            sec = win.show_section("manual")
            sec.view.pop_to_tag("root")
            sec.search.set_text(query)
        return setup
    r.shot("Manual", "Manual, the list of pages", manual_index(), wait=900)
    r.shot("Manual", "Manual, a search that finds nothing", manual_index("zzzz"), wait=900)

    def manual_missing():
        manual_index()()
        real = manual.load_pages
        manual.load_pages = lambda: []
        sec = manual.ManualSection(win)
        manual.load_pages = real
        toolbar = sec.view.get_visible_page().get_child()
        content = toolbar.get_content()
        toolbar.set_content(None)
        win.sections["manual"].push(s("H-024"), content)
    r.shot("Manual", "Manual, the help pages are missing", manual_missing, wait=900)

    for page in manual.load_pages():
        for n, fraction in enumerate((0.0, 0.5, 1.0)):
            def step(page=page, fraction=fraction):
                sec = win.show_section("manual")
                sec.search.set_text("")
                if fraction == 0.0:
                    sec.open(page.slug)
                GLib.timeout_add(300, lambda: scroll_to(
                    find(sec.view.get_visible_page(), Gtk.ScrolledWindow).get_child(), fraction) and False)
            r.shot(f"Manual: {page.slug}", f"{page.slug}, {('top', 'middle', 'end')[n]}", step, wait=900)


def main():
    standard()
    app = HubApplication()
    app.set_flags(app.get_flags() | Gio.ApplicationFlags.NON_UNIQUE)

    def begin():
        global win
        win = app.main_window()
        win.present()
        runner = Runner(app)
        plan(runner, app)
        runner.start()
        return False

    def on_startup(*_):
        Gtk.Settings.get_default().set_property("gtk-enable-animations", False)
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        GLib.idle_add(begin)

    app.connect("startup", on_startup)
    app.hold()
    return app.run([sys.argv[0]])


if __name__ == "__main__":
    sys.exit(main())
