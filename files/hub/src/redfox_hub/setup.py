"""Full Setup: set the computer up in one go from a profile (Matt, Dewy,
Normie, Fedora). A front end to redfox-bootstrap: it lists what each profile
does, step by step, and runs it in a terminal window, since some steps ask
for a password. The steps use the same tools as Hub's own switches, so Hub
shows the result afterwards."""

from gi.repository import Adw, GLib, Gtk

from . import host


def terminal(argv):
    """argv in a terminal window: the desktop's default terminal, else Ptyxis."""
    if GLib.find_program_in_path("xdg-terminal-exec"):
        return ["xdg-terminal-exec", *argv]
    return ["ptyxis", "--new-window", "--", *argv]


class SetupPage(Adw.NavigationPage):
    def __init__(self, section):
        self.section = section
        self.page = Adw.PreferencesPage(
            description="Each profile sets up apps, settings, the theme and the layout in one "
                        "go. It runs in a terminal window, which may ask for your password, and "
                        "ends with a list of what was done or skipped.")
        self.groups = []
        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        toolbar.set_content(self.page)
        super().__init__(title="Full Setup", child=toolbar, tag="setup")
        self.reload()

    def reload(self):
        host.run_json(["redfox-bootstrap", "list", "--json"], self._on_list)

    def _on_list(self, data, error):
        for group in self.groups:
            self.page.remove(group)
        self.groups = []
        if error:
            group = Adw.PreferencesGroup()
            group.add(Adw.ActionRow(title="Couldn't list the profiles",
                                    subtitle=GLib.markup_escape_text(error)))
            self.page.add(group)
            self.groups.append(group)
            return
        for profile in data.get("profiles", []):
            group = Adw.PreferencesGroup(title=GLib.markup_escape_text(profile["name"]),
                                         description=GLib.markup_escape_text(profile["summary"]))
            run = Gtk.Button(label="Run…", valign=Gtk.Align.CENTER)
            run.add_css_class("flat")
            run.connect("clicked", self._on_run, profile)
            group.set_header_suffix(run)
            for stage in profile["stages"]:
                if stage["steps"]:
                    row = Adw.ExpanderRow(title=GLib.markup_escape_text(stage["doc"]),
                                          subtitle=f"{len(stage['steps'])} steps")
                    for step in stage["steps"]:
                        row.add_row(Adw.ActionRow(title=GLib.markup_escape_text(step["doc"])))
                else:
                    row = Adw.ActionRow(title=GLib.markup_escape_text(stage["doc"]))
                group.add(row)
            self.page.add(group)
            self.groups.append(group)

    def _on_run(self, _button, profile):
        dialog = Adw.AlertDialog(
            heading=f"Set Up as {profile['name']}?",
            body="This changes this account's apps, settings, theme and layout. It runs in a "
                 "terminal window, which may ask for your password, and lists anything it "
                 "skipped at the end.")
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("run", "Run")
        dialog.set_response_appearance("run", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_close_response("cancel")
        dialog.connect("response", lambda _d, r: r == "run" and self._run(profile))
        dialog.present(self.section.window)

    def _run(self, profile):
        def done(returncode, output):
            if returncode != 0:
                lines = output.strip().splitlines()
                self.section.window.toast(lines[-1] if lines else "Couldn't open a terminal")

        host.run(terminal(["redfox-bootstrap", "run", profile["id"]]), on_done=done)
        self.section.window.toast(f"Setting up as {profile['name']} in a terminal window")
