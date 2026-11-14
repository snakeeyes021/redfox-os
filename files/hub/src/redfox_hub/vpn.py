"""Hub's VPN section: the VPN servers RedFox keeps for you (redfox-nord), which one is
connected, the countries to keep, and the provider's access token.

Connecting and switching also work from GNOME's Quick Settings; the servers are ordinary
NetworkManager connections shared by every account. Adding, changing or removing them asks
for an administrator's password once (NetworkManager's own policy); connecting doesn't."""

import json

from gi.repository import Adw, GLib, Gtk

from . import host
from .window import Section

PROVIDERS = [("nordvpn", "NordVPN")]
TOKEN_HELP = "From nordaccount.com › NordVPN › Advanced settings › Access token"
BUSY_LOAD = 85  # redfox-nord refresh replaces servers at this load or more


def server_title(server):
    """"United States #13024": the country, then the server's number."""
    country = server.get("country_name") or server.get("country") or "Server"
    return f"{country} #{server['number']}" if server.get("number") else country


def server_subtitle(server):
    """P2P, the load, and whether it's busy or offline, as far as they're known."""
    parts = []
    if server.get("p2p"):
        parts.append("P2P")
    online, load = server.get("online"), server.get("load")
    if online is False:
        parts.append("Offline")
    elif load is not None:
        parts.append(f"Load {load}%" + (" · busy" if load >= BUSY_LOAD else ""))
    if server.get("active"):
        parts.append("Connected")
    return " · ".join(parts)


def rule_title(rule):
    return rule.get("country_name") or rule.get("country", "")


def rules_payload(rules):
    """What `redfox-nord rules set` reads: [{"country", "count", "p2p"}]."""
    return json.dumps([{"country": r["country"], "count": int(r["count"]), "p2p": bool(r["p2p"])}
                       for r in rules])


def last_line(output, fallback):
    lines = [line for line in output.strip().splitlines() if line.strip()]
    return lines[-1].replace("[ERROR] ", "").replace("[SUCCESS] ", "") if lines else fallback


class VpnSection(Section):
    def __init__(self, window):
        self.page = Adw.PreferencesPage()
        super().__init__(window, "VPN", self.page)
        self.status = None
        self.servers = []
        self.rules = []
        self.countries = []
        self.busy = False
        self.dirty = False

        # First use: choose the provider, give its token, set up the servers.
        self.setup_group = Adw.PreferencesGroup(
            title="Set Up a VPN",
            description="Servers you can switch between from Quick Settings, using your own VPN "
                        "account. Setting them up asks for an administrator's password once.",
            visible=False)
        self.setup_provider = Adw.ComboRow(title="Provider",
                                           model=Gtk.StringList.new([p[1] for p in PROVIDERS]))
        self.setup_group.add(self.setup_provider)
        self.setup_token = Adw.PasswordEntryRow(title="Access Token")
        self.setup_group.add(self.setup_token)
        hint = Adw.ActionRow(subtitle=TOKEN_HELP)
        hint.add_css_class("property")
        self.setup_group.add(hint)
        self.setup_button = Gtk.Button(label="Set Up Servers", valign=Gtk.Align.CENTER,
                                       halign=Gtk.Align.END, margin_top=12)
        self.setup_button.add_css_class("suggested-action")
        self.setup_button.add_css_class("pill")
        self.setup_button.connect("clicked", self._on_setup)
        self.setup_group.add(self.setup_button)
        self.page.add(self.setup_group)

        # Connected or not.
        self.status_group = Adw.PreferencesGroup(visible=False)
        self.status_row = Adw.ActionRow(title="Not Connected")
        self.status_icon = Gtk.Image(icon_name="network-vpn-disabled-symbolic")
        self.status_row.add_prefix(self.status_icon)
        self.disconnect = Gtk.Button(label="Disconnect", valign=Gtk.Align.CENTER, visible=False)
        self.disconnect.connect("clicked", self._on_disconnect)
        self.status_row.add_suffix(self.disconnect)
        self.status_group.add(self.status_row)
        self.page.add(self.status_group)

        # The servers.
        self.servers_group = Adw.PreferencesGroup(
            title="Servers", description="Also in Quick Settings, in the top-right corner.",
            visible=False)
        buttons = Gtk.Box(spacing=6)
        self.refresh_button = Gtk.Button(label="Replace Busy Servers",
                                         tooltip_text="Swap servers that are offline or busy for "
                                                      "the least busy ones in the same country")
        self.refresh_button.add_css_class("flat")
        self.refresh_button.connect("clicked", lambda *_: self._run_sync("refresh"))
        self.sync_button = Gtk.Button(label="Sync", tooltip_text="Add any servers the countries "
                                                                 "below are missing")
        self.sync_button.connect("clicked", lambda *_: self._run_sync("sync"))
        buttons.append(self.refresh_button)
        buttons.append(self.sync_button)
        self.servers_group.set_header_suffix(buttons)
        self.server_rows = []
        self.page.add(self.servers_group)

        # The provider and its token.
        self.provider_group = Adw.PreferencesGroup(title="Provider", visible=False)
        self.provider_row = Adw.ComboRow(title="Provider",
                                         model=Gtk.StringList.new([p[1] for p in PROVIDERS]))
        self.provider_group.add(self.provider_row)
        self.token_row = Adw.ActionRow(title="Access Token", subtitle="…")
        change = Gtk.Button(label="Change…", valign=Gtk.Align.CENTER)
        change.connect("clicked", self._on_change_token)
        self.token_row.add_suffix(change)
        self.provider_group.add(self.token_row)
        self.page.add(self.provider_group)

        # The countries Sync keeps installed.
        self.countries_group = Adw.PreferencesGroup(
            title="Countries", description="What Sync keeps installed", visible=False)
        self.save_button = Gtk.Button(label="Save and Sync", sensitive=False)
        self.save_button.add_css_class("suggested-action")
        self.save_button.connect("clicked", self._on_save_rules)
        self.countries_group.set_header_suffix(self.save_button)
        self.rule_rows = []
        self.add_row = Adw.ComboRow(title="Add a Country", enable_search=True)
        self.add_p2p = Gtk.ToggleButton(label="P2P", valign=Gtk.Align.CENTER,
                                        tooltip_text="Servers for peer-to-peer file sharing")
        add = Gtk.Button(label="Add", valign=Gtk.Align.CENTER)
        add.connect("clicked", self._on_add_rule)
        self.add_row.add_suffix(self.add_p2p)
        self.add_row.add_suffix(add)
        self.countries_group.add(self.add_row)
        self.page.add(self.countries_group)

        # While the page loads, or when a command fails to list anything.
        self.message_group = Adw.PreferencesGroup()
        self.message_row = Adw.ActionRow(title="Reading the VPN servers…")
        self.message_group.add(self.message_row)
        self.page.add(self.message_group)

    # Loading

    def shown(self):
        if not self.busy:
            host.run_json(["redfox-nord", "status", "--json", "--check"], self._on_status)

    def _on_status(self, data, error):
        if error:
            self._message("Couldn't read the VPN settings", error)
            return
        self.status = data
        if not data.get("token"):
            self._show_setup()
            return
        self.setup_group.set_visible(False)
        works = data.get("token_works")
        self.token_row.set_subtitle("Saved" if works is not False else
                                    "Not working: it may have expired. Change it to keep syncing.")
        if not self.dirty:
            self.rules = [dict(r) for r in data.get("rules", [])]
            self._show_rules()
        self.countries = data.get("countries", [])
        self.add_row.set_model(Gtk.StringList.new([c["name"] for c in self.countries]))
        host.run_json(["redfox-nord", "list", "--json", "--load"], self._on_list)

    def _on_list(self, data, error):
        if error:
            self._message("Couldn't list the VPN servers", error)
            return
        self.message_group.set_visible(False)
        self.servers = data.get("servers", [])
        for group in (self.status_group, self.servers_group, self.provider_group,
                      self.countries_group):
            group.set_visible(True)
        self._show_servers(data.get("connected"))

    def _message(self, title, subtitle):
        self.message_group.set_visible(True)
        self.message_row.set_title(GLib.markup_escape_text(title))
        self.message_row.set_subtitle(GLib.markup_escape_text(subtitle or ""))

    def _show_setup(self):
        self.message_group.set_visible(False)
        for group in (self.status_group, self.servers_group, self.provider_group,
                      self.countries_group):
            group.set_visible(False)
        self.setup_group.set_visible(True)

    # Servers

    def _show_servers(self, connected):
        for row in self.server_rows:
            self.servers_group.remove(row)
        self.server_rows = []
        active = next((s for s in self.servers if s["uuid"] == connected), None)
        self.status_row.set_title(GLib.markup_escape_text(
            f"Connected to {server_title(active)}" if active else "Not Connected"))
        self.status_icon.set_from_icon_name("network-vpn-symbolic" if active
                                            else "network-vpn-disabled-symbolic")
        self.disconnect.set_visible(active is not None)
        if not self.servers:
            row = Adw.ActionRow(title="No servers yet",
                                subtitle="Sync sets up servers in the countries below.")
            self.servers_group.add(row)
            self.server_rows.append(row)
        for server in sorted(self.servers, key=lambda s: (not s["active"], server_title(s))):
            row = Adw.ActionRow(title=GLib.markup_escape_text(server_title(server)),
                                subtitle=GLib.markup_escape_text(server_subtitle(server)))
            switch = Gtk.Switch(active=server["active"], valign=Gtk.Align.CENTER,
                                tooltip_text="Connect")
            switch.connect("notify::active", self._on_switch, server)
            remove = Gtk.Button(icon_name="user-trash-symbolic", valign=Gtk.Align.CENTER,
                                tooltip_text="Remove this server")
            remove.add_css_class("flat")
            remove.connect("clicked", self._on_remove, server)
            row.add_suffix(switch)
            row.add_suffix(remove)
            row.set_activatable_widget(switch)
            self.servers_group.add(row)
            self.server_rows.append(row)
        self._set_busy(self.busy)

    def _on_switch(self, switch, _param, server):
        if self.busy or switch.get_active() == server["active"]:
            return
        if switch.get_active():
            # One at a time: disconnect the connected one first.
            argv = ["nmcli", "connection", "up", "uuid", server["uuid"]]
            others = [s for s in self.servers if s["active"] and s["uuid"] != server["uuid"]]
            steps = [["nmcli", "connection", "down", "uuid", s["uuid"]] for s in others] + [argv]
            self._chain(steps, f"Connecting to {server_title(server)}…",
                        f"Couldn't connect to {server_title(server)}")
        else:
            self._chain([["nmcli", "connection", "down", "uuid", server["uuid"]]], None,
                        "Couldn't disconnect")

    def _on_disconnect(self, _button):
        active = [s for s in self.servers if s["active"]]
        self._chain([["nmcli", "connection", "down", "uuid", s["uuid"]] for s in active], None,
                    "Couldn't disconnect")

    def _chain(self, steps, toast, failure):
        if toast:
            self.window.toast(toast)
        self._set_busy(True)

        def step(index):
            if index == len(steps):
                self._set_busy(False)
                self.shown()
                return

            def done(returncode, output):
                if returncode != 0:
                    self.window.toast(f"{failure}: {last_line(output, 'no reason given')}")
                    self._set_busy(False)
                    self.shown()
                    return
                step(index + 1)

            host.run(steps[index], on_done=done)

        step(0)

    def _on_remove(self, _button, server):
        dialog = Adw.AlertDialog(
            heading=f"Remove {server_title(server)}?",
            body="It goes from Quick Settings too. Sync can set up another server in its country.")
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("remove", "Remove")
        dialog.set_response_appearance("remove", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_close_response("cancel")
        dialog.connect("response", lambda _d, r: r == "remove" and self._run(
            ["redfox-nord", "remove", server["name"], "-y"], f"Removed {server_title(server)}"))
        dialog.present(self.window)

    # Sync and refresh

    def _run_sync(self, command, after=None):
        self.window.toast("Replacing busy servers…" if command == "refresh"
                          else "Syncing the servers…")
        self._run(["redfox-nord", command], None, after)

    def _run(self, argv, success, after=None, input_text=None):
        self._set_busy(True)

        def done(returncode, output):
            self._set_busy(False)
            if returncode == 0:
                self.window.toast(success or last_line(output, "Done"))
                if after:
                    after()
                    return
            else:
                self.window.toast(last_line(output, "That didn't work"))
            self.shown()

        host.run(argv, on_done=done, input_text=input_text)

    def _set_busy(self, busy):
        self.busy = busy
        for widget in (self.sync_button, self.refresh_button, self.setup_button,
                       self.disconnect, self.save_button):
            widget.set_sensitive(not busy and (widget is not self.save_button or self.dirty))
        for row in self.server_rows:
            row.set_sensitive(not busy)

    # Countries

    def _show_rules(self):
        for row in self.rule_rows:
            self.countries_group.remove(row)
        self.rule_rows = []
        for rule in self.rules:
            row = Adw.SpinRow.new_with_range(1, 8, 1)
            row.set_title(GLib.markup_escape_text(rule_title(rule)))
            row.set_subtitle("P2P" if rule["p2p"] else "")
            row.set_value(rule["count"])
            row.connect("notify::value", self._on_count, rule)
            remove = Gtk.Button(icon_name="list-remove-symbolic", valign=Gtk.Align.CENTER,
                                tooltip_text="Remove this country")
            remove.add_css_class("flat")
            remove.connect("clicked", self._on_remove_rule, rule)
            row.add_suffix(remove)
            self.countries_group.remove(self.add_row)
            self.countries_group.add(row)
            self.countries_group.add(self.add_row)
            self.rule_rows.append(row)

    def _changed(self):
        self.dirty = True
        self.save_button.set_sensitive(not self.busy)

    def _on_count(self, row, _param, rule):
        rule["count"] = int(row.get_value())
        self._changed()

    def _on_remove_rule(self, _button, rule):
        self.rules.remove(rule)
        self._show_rules()
        self._changed()

    def _on_add_rule(self, _button):
        index = self.add_row.get_selected()
        if not self.countries or index >= len(self.countries):
            return
        country = self.countries[index]
        p2p = self.add_p2p.get_active()
        if any(r["country"] == country["code"] and r["p2p"] == p2p for r in self.rules):
            self.window.toast(f"{country['name']} is already in the list")
            return
        self.rules.append({"country": country["code"], "country_name": country["name"],
                           "count": 1, "p2p": p2p})
        self._show_rules()
        self._changed()

    def _on_save_rules(self, _button):
        def saved():
            self.dirty = False
            self._run_sync("sync")

        self._run(["redfox-nord", "rules", "set"], "Countries saved", after=saved,
                  input_text=rules_payload(self.rules))

    # Token

    def _on_setup(self, _button):
        token = self.setup_token.get_text().strip()
        if not token:
            self.window.toast("Paste your access token first")
            return

        def saved():
            self.setup_token.set_text("")
            self._run_sync("sync")

        self._run(["redfox-nord", "token", "set"], "Token saved", after=saved, input_text=token)

    def _on_change_token(self, _button):
        dialog = Adw.AlertDialog(heading="Change the Access Token", body=TOKEN_HELP)
        entry = Adw.PasswordEntryRow(title="Access Token")
        box = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        box.add_css_class("boxed-list")
        box.append(entry)
        dialog.set_extra_child(box)
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("save", "Save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_close_response("cancel")
        dialog.connect("response", lambda _d, r: r == "save" and entry.get_text().strip() and
                       self._run(["redfox-nord", "token", "set"], "Token saved",
                                 input_text=entry.get_text().strip()))
        dialog.present(self.window)
