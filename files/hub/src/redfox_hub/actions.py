"""One-off actions from `redfox-actions`, shown as rows with a button next
to the settings they're about, and the "Restart to finish" prompt."""

from gi.repository import Adw, GLib, Gtk

from . import host

# Where each action group lives in Hub, for Help's links.
GROUP_PAGES = {
    "sound": ("settings", "Settings › Sound & Music"),
    "gaming": ("apps/gaming", "Software › Gaming"),
    "updates": ("updates", "Updates"),
}


def load(on_done):
    """on_done(list of action dicts), or [] if they couldn't be read."""
    host.run_json(["redfox-actions", "list", "--json"],
                  lambda data, error: on_done([] if error else data.get("actions", [])))


class ActionRow(Adw.ActionRow):
    def __init__(self, window, action, on_finished=None):
        super().__init__(title=GLib.markup_escape_text(action["title"]),
                         subtitle=GLib.markup_escape_text(action["subtitle"]))
        self.window = window
        self.action = action
        self.on_finished = on_finished
        self.spinner = Adw.Spinner(visible=False)
        self.add_suffix(self.spinner)
        self.button = Gtk.Button(label=action["button"], valign=Gtk.Align.CENTER,
                                 visible=not action.get("done"))
        self.button.connect("clicked", self._on_clicked)
        self.add_suffix(self.button)

    def _on_clicked(self, _button):
        confirm = self.action.get("confirm")
        if not confirm:
            self._run()
            return
        dialog = Adw.AlertDialog(heading=confirm["heading"], body=confirm["body"])
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("go", confirm["button"])
        dialog.set_response_appearance("go", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_close_response("cancel")
        dialog.connect("response", lambda _d, r: r == "go" and self._run())
        dialog.present(self.window)

    def _run(self):
        self.button.set_sensitive(False)
        self.spinner.set_visible(True)

        def done(returncode, output):
            self.spinner.set_visible(False)
            self.button.set_sensitive(True)
            lines = [line for line in output.strip().splitlines() if line.strip()]
            if returncode == 0:
                self.window.toast(lines[-1] if lines else "Done")
            else:
                self.window.toast(lines[-1] if lines else "That didn't work")
            if self.on_finished:
                self.on_finished()

        host.run(["redfox-actions", "run", self.action["id"]], on_done=done)


def ask_restart(window, names):
    """After changes that only take effect after a restart."""
    dialog = Adw.AlertDialog(
        heading="Restart to Finish",
        body=f"{', '.join(names)}: these take effect when the computer restarts. "
             "Save your work before restarting.")
    dialog.add_response("later", "Later")
    dialog.add_response("restart", "Restart")
    dialog.set_response_appearance("restart", Adw.ResponseAppearance.SUGGESTED)
    dialog.set_close_response("later")
    dialog.connect("response", lambda _d, r: r == "restart" and
                   host.run(["systemctl", "reboot"]))
    dialog.present(window)
