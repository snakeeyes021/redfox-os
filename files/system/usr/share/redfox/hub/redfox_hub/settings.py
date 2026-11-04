"""Settings: the layout picker, desktop options, and apps at login."""

from gi.repository import Adw, Gio, Gtk

from . import host
from .window import Section

RFL = "org.gnome.shell.extensions.redfox-layouts"


def settings_for(schema_id):
    source = Gio.SettingsSchemaSource.get_default()
    if source and source.lookup(schema_id, True):
        return Gio.Settings.new(schema_id)
    return None


class SettingsSection(Section):
    def __init__(self, window):
        page = Adw.PreferencesPage()
        super().__init__(window, "Settings", page)

        desktop = Adw.PreferencesGroup(title="Desktop")
        layout_row = Adw.ActionRow(title="Layout",
                                   subtitle="Where the dock, the top bar and the taskbar go",
                                   activatable=True)
        layout_row.add_prefix(Gtk.Image(icon_name="view-dual-symbolic"))
        layout_row.add_suffix(Gtk.Image(icon_name="go-next-symbolic"))
        layout_row.connect("activated", lambda *_: self.open("layout"))
        desktop.add(layout_row)

        page.add(desktop)

        self.login_group = Adw.PreferencesGroup(
            title="Start at Login",
            description="Start these apps in the background when you log in, "
                        "ready in the top bar. Opened any other way, they open normally.")
        self.login_rows = []
        page.add(self.login_group)

    def shown(self):
        host.run_json(["redfox-autostart", "list", "--json"], self._on_autostart)

    def open(self, subpath):
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


class LayoutCard(Gtk.FlowBoxChild):
    def __init__(self, layout):
        super().__init__()
        self.layout_id = layout["id"]
        self.add_css_class("layout-card")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        picture = Gtk.Picture.new_for_filename(layout["preview"])
        picture.set_can_shrink(True)
        picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        picture.set_size_request(200, 125)
        picture.add_css_class("layout-preview")
        overlay = Gtk.Overlay(child=picture)
        self.check = Gtk.Image(icon_name="object-select-symbolic", halign=Gtk.Align.END,
                               valign=Gtk.Align.END, margin_end=8, margin_bottom=8,
                               visible=False)
        self.check.add_css_class("layout-check")
        overlay.add_overlay(self.check)
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
        self.check.set_visible(current)
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

        self.rfl = settings_for(RFL)
        options = Adw.PreferencesGroup(title="Floating Dock")
        self.options = options
        if self.rfl:
            gap = Adw.SpinRow.new_with_range(0, 64, 1)
            gap.set_title("Gap to the Screen Edge")
            gap.set_subtitle("For the RedFox and Cal layouts, in pixels")
            self.rfl.bind("floating-dock-gap", gap, "value", Gio.SettingsBindFlags.DEFAULT)
            options.add(gap)
            width = Adw.SpinRow.new_with_range(0, 10000, 10)
            width.set_title("Dock on Screens at Least")
            width.set_subtitle("The RedFox layout uses the plain GNOME dash on smaller "
                               "screens. Logical pixels wide.")
            self.rfl.bind("auto-dock-min-width", width, "value", Gio.SettingsBindFlags.DEFAULT)
            options.add(width)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18,
                      margin_top=24, margin_bottom=24, margin_start=12, margin_end=12)
        box.append(intro)
        box.append(self.flow)
        if self.rfl:
            box.append(options)
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
        if self.busy or card.check.get_visible():
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

