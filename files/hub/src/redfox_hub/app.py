"""RedFox Hub: the application."""

import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from .paths import STYLE, VERSION  # noqa: E402

APP_ID = "tech.redfoxlabs.Hub"


class HubApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID,
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        GLib.set_application_name("RedFox Hub")
        self.add_main_option("welcome", 0, GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE, "Show the welcome tour", None)
        self.add_main_option("first-login", 0, GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE,
                             "Show the welcome tour once, at first login", None)
        self.add_main_option("page", 0, GLib.OptionFlags.NONE,
                             GLib.OptionArg.STRING,
                             "Open a page, e.g. updates or settings/layout", "PAGE")
        self.add_main_option("version", 0, GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE, "Print the version", None)
        self.window = None
        self.welcome = None

    def do_handle_local_options(self, options):
        # Before startup, so --version works without a display (in a script
        # or over SSH).
        if options.contains("version"):
            print(f"redfox-hub {VERSION}")
            return 0
        return -1

    def do_startup(self):
        Adw.Application.do_startup(self)
        css = Gtk.CssProvider()
        css.load_from_path(str(STYLE))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        for name, callback, accels in (
                ("about", self.on_about, []),
                ("quit", lambda *_: self.quit(), ["<Control>q"]),
                ("open-page", self.on_open_page, []),
                ("welcome", lambda *_: self.show_welcome(), [])):
            param = GLib.VariantType.new("s") if name == "open-page" else None
            action = Gio.SimpleAction.new(name, param)
            action.connect("activate", callback)
            self.add_action(action)
            if accels:
                self.set_accels_for_action(f"app.{name}", accels)
        self.set_accels_for_action("window.close", ["<Control>w"])

    def do_command_line(self, command_line):
        options = command_line.get_options_dict().end().unpack()
        if options.get("version"):
            command_line.print_literal(f"redfox-hub {VERSION}\n")
            return 0
        if options.get("first-login"):
            from . import welcome
            if welcome.seen():
                return 0
            self.show_welcome(first_login=True)
            return 0
        if options.get("welcome"):
            self.show_welcome()
            return 0
        self.show_page(options.get("page") or "")
        return 0

    def do_activate(self):
        self.show_page("")

    def main_window(self):
        if self.window is None:
            from .window import HubWindow
            self.window = HubWindow(application=self)
            self.window.connect("close-request", self._on_main_closed)
        return self.window

    def _on_main_closed(self, *_):
        self.window = None
        return False

    def show_page(self, page):
        window = self.main_window()
        if page:
            window.open_page(page)
        window.present()

    def show_welcome(self, first_login=False):
        from .welcome import WelcomeWindow
        if self.welcome is None:
            self.welcome = WelcomeWindow(application=self, first_login=first_login)
            self.welcome.connect("close-request", self._on_welcome_closed)
        self.welcome.present()

    def _on_welcome_closed(self, *_):
        self.welcome = None
        return False

    def on_open_page(self, _action, param):
        self.show_page(param.get_string())

    def on_about(self, *_):
        about = Adw.AboutDialog(
            application_name="RedFox Hub",
            application_icon=APP_ID,
            developer_name="RedFox Labs",
            version=VERSION,
            website="https://github.com/snakeeyes021/redfox-os",
            issue_url="https://github.com/snakeeyes021/redfox-os/issues",
            license_type=Gtk.License.APACHE_2_0,
        )
        about.present(self.get_active_window())


def main():
    return HubApplication().run(sys.argv)
