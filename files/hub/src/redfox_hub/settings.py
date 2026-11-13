"""Settings: the layout picker, extra dimming, apps at login, services,
storage, and sound & music (with the MIDI archive).

The on/off settings in Services, Storage and Sound & Music come from
`redfox-toggles`, which also changes them (asking for a password through
polkit for the system-wide ones)."""

from gi.repository import Adw, Gio, GLib, Gtk

from . import actions, host
from .paths import LAYOUTS
from .window import Section

# The layout helper extension's settings, read and written with gsettings
# (the command, so Hub needs no compiled schema of its own).
RFL = "org.gnome.shell.extensions.redfox-layouts"
# RedFox Dim, turned on and off with gnome-extensions like any extension.
DIM = "redfox-dim@redfoxlabs.tech"
# redfox-toggles groups, in page order: id, title.
TOGGLE_GROUPS = [("terminal", "Terminal"), ("services", "Services"),
                 ("storage", "Storage"), ("sound", "Sound & Music")]
# What clicking an open app in the taskbar or dock does: name, explanation,
# Dash to Panel's value, Dash to Dock's. Each layout starts with its own
# default (see redfox-layout); the row shows the current layout's dock and
# sets both docks. Dash to Dock has no exact match for the two cycle
# choices; it cycles.
CLICK_PATHS = ("/org/gnome/shell/extensions/dash-to-panel/click-action",
               "/org/gnome/shell/extensions/dash-to-dock/click-action")
# Layouts whose taskbar is Dash to Panel; the others use Dash to Dock, except
# GNOME's, which has no dock to set.
PANEL_LAYOUTS = ("wash", "nostalgia")
NO_DOCK_LAYOUTS = ("gnome",)
CLICK_CHOICES = [
    ("Previews", "One window: show or minimize it. Several: show their previews to pick one",
     "TOGGLE-SHOWPREVIEW", "focus-minimize-or-previews"),
    ("App Spread", "One window: show or minimize it. Several: spread them out to pick one",
     "TOGGLE-SPREAD", "focus-minimize-or-appspread"),
    ("Focus or App Spread", "Bring the app forward; if it's already in front, spread its "
     "windows out to pick one", "TOGGLE-SPREAD", "focus-or-appspread"),
    ("Bring Forward", "Bring the app's windows to the front; clicking again doesn't minimize them",
     "RAISE", "skip"),
    ("Cycle", "One window: show or minimize it. Several: show the next one with each click",
     "TOGGLE-CYCLE", "cycle-windows"),
    ("Cycle, Then Minimize", "Each click shows the next window; after the last, they're minimized",
     "CYCLE-MIN", "cycle-windows"),
]
# Shown when the docks are set to something else (in their own settings).
CLICK_OTHER = ("Other", "Set in the taskbar or dock's own settings")
TERMINAL_NOTE = ("Each works in bash, zsh and fish, in any terminal app. "
                 "New terminal windows show the change.")


class SettingsSection(Section):
    def __init__(self, window):
        page = Adw.PreferencesPage()
        super().__init__(window, "Settings", page)

        # Full Setup: a whole profile in one go (redfox-bootstrap).
        full = Adw.PreferencesGroup(title="Full Setup")
        setup_row = Adw.ActionRow(title="Set Up From a Profile",
                                  subtitle="Apps, settings and layout in one go",
                                  activatable=True)
        setup_row.add_prefix(Gtk.Image(icon_name="emblem-system-symbolic"))
        setup_row.add_suffix(Gtk.Image(icon_name="go-next-symbolic"))
        setup_row.connect("activated", lambda *_: self.open("setup"))
        full.add(setup_row)
        page.add(full)

        desktop = Adw.PreferencesGroup(title="Desktop")
        layout_row = Adw.ActionRow(title="Layout",
                                   subtitle="Where the dock, the top bar and the taskbar go",
                                   activatable=True)
        layout_row.add_prefix(Gtk.Image(icon_name="view-dual-symbolic"))
        layout_row.add_suffix(Gtk.Image(icon_name="go-next-symbolic"))
        layout_row.connect("activated", lambda *_: self.open("layout"))
        desktop.add(layout_row)

        # RedFox Dim, the image's own shell extension. Shown once
        # `gnome-extensions info` has answered for it.
        self.dim_row = Adw.SwitchRow(
            title="Extra Dimming", visible=False, sensitive=False,
            subtitle="Let the brightness slider go darker than the screen's lowest setting")
        self.dim_row.add_prefix(Gtk.Image(icon_name="display-brightness-symbolic"))
        self.dim_row.connect("notify::active", self._on_dim_toggled)
        desktop.add(self.dim_row)

        # What clicking an open app in the taskbar or dock does. Shown once
        # dconf has answered.
        self.click_row = Adw.ComboRow(
            title="Clicking an Open App", visible=False,
            model=Gtk.StringList.new([name for name, *_ in CLICK_CHOICES]))
        self.click_row.add_prefix(Gtk.Image(icon_name="input-mouse-symbolic"))
        self.click_row.set_use_markup(False)
        self._click_guard = True
        self.click_row.connect("notify::selected", self._on_click_selected)
        desktop.add(self.click_row)

        page.add(desktop)

        self.login_group = Adw.PreferencesGroup(
            title="Start at Login",
            description="Start these apps in the background when you log in, "
                        "ready in the top bar. Opened any other way, they open normally.")
        self.login_rows = []
        page.add(self.login_group)

        # On/off settings from redfox-toggles, in these groups. A group shows
        # once it has rows.
        self.toggle_groups = {}
        for group_id, title in TOGGLE_GROUPS:
            # Group titles are markup ("Sound & Music").
            group = Adw.PreferencesGroup(title=GLib.markup_escape_text(title), visible=False,
                                         description=TERMINAL_NOTE
                                         if group_id == "terminal" else None)
            page.add(group)
            self.toggle_groups[group_id] = group
        self.toggle_rows = []
        # The styled prompt is a choice of theme rather than a switch: Off,
        # then redfox-terminal's themes. It takes the prompt switch's place.
        self.prompt_row = Adw.ComboRow(visible=False)
        self.prompt_row.add_prefix(Gtk.Image(icon_name="utilities-terminal-symbolic"))
        self.prompt_row.set_use_markup(False)
        self.prompt_ids = []
        self.prompt_subtitle = ""
        self._prompt_guard = True
        self.prompt_row.connect("notify::selected", self._on_prompt_selected)
        # One-off actions (redfox-actions) after the switches in their group.
        self.actions = []
        self.action_rows = []

        # The MIDI archive folder sits under the Midikeep switch, in Sound &
        # Music. It shows once `midikeep data-dir` answers.
        self.midi_row = Adw.ActionRow(title="MIDI Archive Folder", subtitle="…",
                                      visible=False)
        self.midi_row.add_css_class("property")
        choose = Gtk.Button(label="Choose…", valign=Gtk.Align.CENTER)
        choose.connect("clicked", self._on_choose_midi)
        self.midi_row.add_suffix(choose)
        self.midi_dir = None

    def shown(self):
        host.run_json(["redfox-autostart", "list", "--json"], self._on_autostart)
        host.run_json(["redfox-toggles", "list", "--json"], self._on_toggles)
        actions.load(self._on_actions)
        host.run_json(["midikeep", "data-dir", "--json"], self._on_midi)
        host.run(["gnome-extensions", "info", DIM], on_done=self._on_dim_info)
        host.run(["redfox-layout", "get"], on_done=self._on_click_layout)

    # Clicking an open app

    def _on_click_layout(self, returncode, output):
        layout = output.strip() if returncode == 0 else ""
        if layout in NO_DOCK_LAYOUTS:
            self.click_row.set_visible(False)
            return
        panel = layout in PANEL_LAYOUTS
        host.run(["dconf", "read", CLICK_PATHS[0 if panel else 1]],
                 on_done=lambda rc, out: self._on_click_read(rc, out, panel))

    def _on_click_read(self, returncode, output, panel):
        value = output.strip().strip("'") if returncode == 0 else ""
        # Nothing written means the image's default, which is Previews.
        column = 2 if panel else 3
        index = next((i for i, choice in enumerate(CLICK_CHOICES) if choice[column] == value),
                     0 if not value else len(CLICK_CHOICES))
        # "Other" is in the list only while it's what the docks are set to.
        model = self.click_row.get_model()
        if index == len(CLICK_CHOICES) and model.get_n_items() == len(CLICK_CHOICES):
            model.append(CLICK_OTHER[0])
        elif index < len(CLICK_CHOICES) and model.get_n_items() > len(CLICK_CHOICES):
            model.remove(len(CLICK_CHOICES))
        self._click_guard = True
        self.click_row.set_selected(index)
        self._click_guard = False
        self._show_click_subtitle()
        self.click_row.set_visible(True)

    def _show_click_subtitle(self):
        index = self.click_row.get_selected()
        self.click_row.set_subtitle(CLICK_CHOICES[index][1] if index < len(CLICK_CHOICES)
                                    else CLICK_OTHER[1])

    def _on_click_selected(self, row, _param):
        self._show_click_subtitle()
        if self._click_guard or row.get_selected() >= len(CLICK_CHOICES):
            return
        # A choice replaces "Other".
        model = row.get_model()
        if model.get_n_items() > len(CLICK_CHOICES):
            self._click_guard = True
            model.remove(len(CLICK_CHOICES))
            self._click_guard = False
        _name, _text, panel, dock = CLICK_CHOICES[row.get_selected()]
        def done(returncode, _output):
            if returncode != 0:
                self.window.toast("The click setting wasn't changed")

        for path, value in zip(CLICK_PATHS, (panel, dock)):
            host.run(["dconf", "write", path, f"'{value}'"], on_done=done)

    # Extra dimming

    def _on_dim_info(self, returncode, output):
        if returncode != 0:
            self.dim_row.set_visible(False)
            return
        enabled = any(line.strip().lower() == "enabled: yes" for line in output.splitlines())
        self.dim_row.set_sensitive(False)  # setting it isn't the user's toggle
        self.dim_row.set_active(enabled)
        self.dim_row.set_sensitive(True)
        self.dim_row.set_visible(True)

    def _on_dim_toggled(self, row, _param):
        if not row.get_sensitive():
            return
        verb = "enable" if row.get_active() else "disable"

        def done(returncode, output):
            if returncode != 0:
                lines = output.strip().splitlines()
                self.window.toast(lines[-1] if lines else "That didn't work")
            host.run(["gnome-extensions", "info", DIM], on_done=self._on_dim_info)

        host.run(["gnome-extensions", verb, DIM], on_done=done)

    # Services, Storage, Sound & Music

    def _on_toggles(self, data, error):
        for group, row in self.toggle_rows:
            group.remove(row)
        self.toggle_rows = []
        if self.prompt_row.get_parent():
            self.toggle_groups["terminal"].remove(self.prompt_row)
        if self.midi_row.get_parent():
            self.toggle_groups["sound"].remove(self.midi_row)
        if error:
            return
        for toggle in data.get("toggles", []):
            group = self.toggle_groups.get(toggle["group"])
            if group is None:
                continue
            if toggle["id"] == "prompt":
                self.prompt_row.set_title(toggle["title"])
                self.prompt_subtitle = toggle["subtitle"]
                group.add(self.prompt_row)
                group.set_visible(True)
                host.run_json(["redfox-terminal", "prompt", "themes", "--json"],
                              self._on_prompt_themes)
                continue
            row = Adw.SwitchRow(title=toggle["title"], subtitle=toggle["subtitle"])
            if toggle["on"] is None:
                row.set_sensitive(False)
            else:
                row.set_active(toggle["on"])
            row.connect("notify::active", self._on_toggled, toggle["id"])
            group.add(row)
            group.set_visible(True)
            self.toggle_rows.append((group, row))
            if toggle["id"] == "midikeep":
                group.add(self.midi_row)
        self._place_actions()

    # The prompt's theme

    def _on_prompt_themes(self, data, error):
        if error or not data:
            self.prompt_row.set_visible(False)
            return
        themes = data.get("themes", [])
        self.prompt_ids = [None] + [t["id"] for t in themes]
        names = ["Off"] + [t["name"] for t in themes]
        index = self.prompt_ids.index(data["current"]) if data.get("on") and \
            data.get("current") in self.prompt_ids else 0
        self._prompt_guard = True
        self.prompt_row.set_model(Gtk.StringList.new(names))
        self.prompt_row.set_selected(index)
        self._prompt_guard = False
        subtitle = self.prompt_subtitle
        if data.get("own_config"):
            subtitle += " Your own ~/.config/starship.toml is used while it exists."
        self.prompt_row.set_subtitle(subtitle)
        self.prompt_row.set_sensitive(True)
        self.prompt_row.set_visible(True)

    def _on_prompt_selected(self, row, _param):
        if self._prompt_guard or row.get_selected() >= len(self.prompt_ids):
            return
        theme = self.prompt_ids[row.get_selected()]
        argv = (["redfox-terminal", "prompt", "off"] if theme is None
                else ["redfox-terminal", "prompt", "theme", theme])
        row.set_sensitive(False)

        def done(returncode, output):
            if returncode != 0:
                lines = output.strip().splitlines()
                self.window.toast(lines[-1] if lines else "That didn't change")
            host.run_json(["redfox-terminal", "prompt", "themes", "--json"],
                          self._on_prompt_themes)

        host.run(argv, on_done=done)

    def _on_actions(self, found):
        self.actions = found
        self._place_actions()

    def _place_actions(self):
        """The actions go last in their group, so after every (re)load of
        the switches they're taken out and added again."""
        for group, row in self.action_rows:
            group.remove(row)
        self.action_rows = []
        for action in self.actions:
            group = self.toggle_groups.get(action["group"])
            if group is None:
                continue
            row = actions.ActionRow(self.window, action)
            group.add(row)
            group.set_visible(True)
            self.action_rows.append((group, row))

    def _on_toggled(self, row, _param, toggle_id):
        if not row.get_sensitive() or getattr(row, "_busy", False):
            return
        row._busy = True
        row.set_sensitive(False)
        verb = "on" if row.get_active() else "off"

        def done(returncode, output):
            if returncode != 0:
                lines = output.strip().splitlines()
                self.window.toast(lines[-1] if lines else "That didn't change")
            # Read every state back: a change can turn on something else
            # (Cockpit turns on remote login).
            host.run_json(["redfox-toggles", "list", "--json"], self._on_toggles)

        host.run(["redfox-toggles", verb, toggle_id], on_done=done)

    # MIDI archive

    def _on_midi(self, data, error):
        self.midi_row.set_visible(not error)
        if not error:
            self.midi_row.set_subtitle(data["data_dir"])
            self.midi_dir = data["data_dir"]

    def _on_choose_midi(self, _button):
        dialog = Gtk.FileDialog(title="Choose the MIDI Archive Folder", modal=True)
        if self.midi_dir:
            dialog.set_initial_folder(Gio.File.new_for_path(self.midi_dir))
        dialog.select_folder(self.window, None, self._on_midi_chosen)

    def _on_midi_chosen(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
        except Exception:  # cancelled
            return
        if not folder or not folder.get_path():
            return

        def done(returncode, output):
            lines = output.strip().splitlines()
            self.window.toast(lines[-1] if lines else
                              ("Folder changed" if returncode == 0 else "That didn't work"))
            self.shown()

        host.run(["midikeep", "data-dir", folder.get_path()], on_done=done)

    def open(self, subpath):
        if subpath == "setup":
            from .setup import SetupPage
            self.view.pop_to_tag("root")
            self.view.push(SetupPage(self))
            return
        if subpath == "layout":
            self.view.pop_to_tag("root")
            if getattr(self, "layout_page", None) is None:
                self.layout_page = LayoutPage(self)
            else:
                self.layout_page.reload()
            self.view.push(self.layout_page)

    # Start at login

    def _on_autostart(self, data, error):
        for row in self.login_rows:
            self.login_group.remove(row)
        self.login_rows = []
        if error:
            row = Adw.ActionRow(title="Couldn't read the login apps", subtitle=error)
            self.login_group.add(row)
            self.login_rows.append(row)
            return
        for app in data["apps"]:
            row = Adw.SwitchRow(title=app["name"])
            icon = Gtk.Image(icon_name=app["id"], pixel_size=32)
            icon.add_css_class("lowres-icon")
            row.add_prefix(icon)
            if app["installed"]:
                row.set_active(app["on"])
            else:
                row.set_sensitive(False)
                row.set_subtitle("Not installed")
            row.connect("notify::active", self._on_login_toggled, app["id"])
            self.login_group.add(row)
            self.login_rows.append(row)

    def _on_login_toggled(self, row, _param, app_id):
        if not row.get_sensitive():
            return
        verb = "on" if row.get_active() else "off"

        def done(returncode, output):
            if returncode != 0:
                self.window.toast(output.strip().splitlines()[-1] if output.strip()
                                  else "That didn't work")
                self.shown()

        host.run(["redfox-autostart", verb, app_id], on_done=done)


class Preview(Gtk.Picture):
    """A layout preview whose height always follows its width (8:5, like
    the drawings), so every card's picture is the same size however much
    text is under it."""

    RATIO = 150 / 240

    def do_measure(self, orientation, for_size):
        if orientation == Gtk.Orientation.HORIZONTAL:
            return 160, 240, -1, -1
        height = round(for_size * self.RATIO) if for_size > 0 else 150
        return height, height, -1, -1


class LayoutCard(Gtk.FlowBoxChild):
    def __init__(self, layout):
        super().__init__()
        self.layout_id = layout["id"]
        self.add_css_class("layout-card")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        picture = Preview(file=Gio.File.new_for_path(str(LAYOUTS / f"{layout['id']}.svg")),
                          can_shrink=True, content_fit=Gtk.ContentFit.FILL)
        picture.add_css_class("layout-preview")
        overlay = Gtk.Overlay(child=picture)
        self.current = False
        self.spinner = Adw.Spinner(halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER,
                                   width_request=32, height_request=32, visible=False)
        overlay.add_overlay(self.spinner)
        box.append(overlay)
        title = Gtk.Label(label=layout["title"], xalign=0)
        title.add_css_class("heading")
        box.append(title)
        description = Gtk.Label(label=layout["description"], xalign=0, wrap=True,
                                max_width_chars=28, lines=3)
        description.add_css_class("caption")
        description.add_css_class("dim-label")
        box.append(description)
        self.set_child(box)
        self.update_property([Gtk.AccessibleProperty.LABEL],
                             [f"{layout['title']}: {layout['description']}"])

    def set_current(self, current):
        self.current = current
        if current:
            self.add_css_class("current")
        else:
            self.remove_css_class("current")

    def set_busy(self, busy):
        self.spinner.set_visible(busy)


class LayoutPage(Adw.NavigationPage):
    def __init__(self, section):
        self.section = section
        self.cards = {}
        self.busy = False

        self.flow = Gtk.FlowBox(
            selection_mode=Gtk.SelectionMode.NONE, homogeneous=True,
            min_children_per_line=3, max_children_per_line=3,
            column_spacing=18, row_spacing=18, activate_on_single_click=True)
        self.flow.connect("child-activated", self._on_card)

        intro = Gtk.Label(
            label="Choose where the dock, the top bar and the taskbar go. "
                  "It changes straight away, and your apps stay open.",
            wrap=True, xalign=0)
        intro.add_css_class("dim-label")

        # Shown once the host's gsettings has answered for both keys.
        self.options = Adw.PreferencesGroup(title="Floating Dock", visible=False)
        self.option_rows = {}
        self._pending = {}
        for key, low, high, step, title, subtitle in (
                ("floating-dock-gap", 0, 64, 1, "Gap to the Screen Edge",
                 "For the RedFox and Cal layouts, in pixels"),
                ("auto-dock-min-width", 0, 10000, 10, "Dock on Screens at Least",
                 "The RedFox layout uses the plain GNOME dash on smaller screens. "
                 "Logical pixels wide.")):
            row = Adw.SpinRow.new_with_range(low, high, step)
            row.set_title(title)
            row.set_subtitle(subtitle)
            row.set_sensitive(False)
            row.connect("notify::value", self._on_option, key)
            self.options.add(row)
            self.option_rows[key] = row
            host.run(["gsettings", "get", RFL, key],
                     on_done=lambda rc, out, k=key: self._on_option_read(k, rc, out))

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18,
                      margin_top=24, margin_bottom=24, margin_start=12, margin_end=12)
        box.append(intro)
        box.append(self.flow)
        box.append(self.options)
        clamp = Adw.Clamp(maximum_size=820, child=box)
        scroller = Gtk.ScrolledWindow(child=clamp, hscrollbar_policy=Gtk.PolicyType.NEVER)

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        toolbar.set_content(scroller)
        super().__init__(title="Layout", child=toolbar, tag="layout")

        # Three across, fewer on a narrow window.
        for width, per_line in ((720, 2), (520, 1)):
            breakpoint = Adw.Breakpoint.new(
                Adw.BreakpointCondition.parse(f"max-width: {width}sp"))
            breakpoint.add_setter(self.flow, "min-children-per-line", per_line)
            breakpoint.add_setter(self.flow, "max-children-per-line", per_line)
            section.window.add_breakpoint(breakpoint)
        self.reload()

    def _on_option_read(self, key, returncode, output):
        row = self.option_rows[key]
        try:
            value = int(output.split()[-1])
        except (ValueError, IndexError):
            return
        if returncode != 0:
            return
        row.set_value(value)
        row.set_sensitive(True)
        self.options.set_visible(True)

    def _on_option(self, row, _param, key):
        if not row.get_sensitive():
            return  # still the value read from the host
        # Write once the value has settled, not on every step of a drag.
        if key in self._pending:
            GLib.source_remove(self._pending[key])

        def write():
            self._pending.pop(key, None)
            host.run(["gsettings", "set", RFL, key, str(int(row.get_value()))])
            return GLib.SOURCE_REMOVE

        self._pending[key] = GLib.timeout_add(400, write)

    def reload(self):
        host.run_json(["redfox-layout", "list", "--json"], self._on_list)

    def _on_list(self, data, error):
        if self.cards:
            self._mark(data.get("current") if data else None)
            return
        if error:
            self.flow.append(Gtk.Label(label=f"Couldn't list the layouts: {error}", wrap=True))
            return
        for layout in data["layouts"]:
            card = LayoutCard(layout)
            self.cards[layout["id"]] = card
            self.flow.append(card)
        self._mark(data.get("current"))

    def _mark(self, current):
        for layout_id, card in self.cards.items():
            card.set_current(layout_id == current)

    def _on_card(self, _flow, card):
        if self.busy or card.current:
            return
        self.busy = True
        card.set_busy(True)

        def done(returncode, output):
            self.busy = False
            card.set_busy(False)
            if returncode == 0:
                self._mark(card.layout_id)
            else:
                lines = output.strip().splitlines()
                self.section.window.toast(lines[-1] if lines else "The layout didn't change")

        host.run(["redfox-layout", "set", card.layout_id], on_done=done)

