"""Updates: automatic updates, update now, the channel and going back.

A front end to redfox-updates (status, update now, automatic on/off) and
redfox-rollback-helper (channel, rollback, other builds).
"""

import time

from gi.repository import Adw, Gio, GLib, Gtk

from . import host
from .strings import ALL_HINTS, data as copy_data, s
from .window import Section

CHANNELS = [
    ("latest", s("H-175"), s("H-176")),
    ("unstable", s("H-177"), s("H-178")),
]


def when(ts, capital=True):
    """A friendly time: 'Today at 04:12', 'Yesterday at 09:30', '3 November
    2026'. With capital=False, 'today at 04:12', for the middle of a sentence."""
    text, relative = _when(ts)
    if not capital and relative and not ALL_HINTS:
        text = text[0].lower() + text[1:]
    return text


def clock():
    """strftime for a time of day, following GNOME's 12h/24h setting."""
    try:
        twelve = Gio.Settings.new("org.gnome.desktop.interface").get_string("clock-format") == "12h"
    except Exception:
        twelve = False
    return "%-I:%M %p" if twelve else "%H:%M"


def _when(ts):
    """The text, and whether it's a relative phrase (today, never, ...) that
    goes lower case in the middle of a sentence."""
    if not ts:
        return s("H-162"), True
    then = time.localtime(ts)
    now = time.localtime()
    day_diff = (time.mktime((now.tm_year, now.tm_mon, now.tm_mday, 0, 0, 0, 0, 0, -1)) -
                time.mktime((then.tm_year, then.tm_mon, then.tm_mday, 0, 0, 0, 0, 0, -1))) // 86400
    clock_text = time.strftime(clock(), then)
    if day_diff == 0:
        return s("H-158", time=clock_text), True
    if day_diff == 1:
        return s("H-159", time=clock_text), True
    if day_diff == -1:
        return s("H-160", time=clock_text), True
    if abs(day_diff) < 7:
        return s("H-161", weekday=time.strftime("%A", then), time=clock_text), False
    return time.strftime("%-d %B %Y", then), False


def cancelled(output):
    """Whether a command failed because the password dialog was cancelled."""
    return any(text in output for text in (
        "not allowed for user", "Not authorized", "Request dismissed",
        "Error executing command as another user"))


def long_date(iso):
    """2026-11-01 -> 1 November 2026"""
    try:
        return time.strftime("%-d %B %Y", time.strptime(iso, "%Y-%m-%d"))
    except (TypeError, ValueError):
        return iso or ""


def system_name(d):
    if not d:
        return s("H-195")
    version = d.get("version") or ""
    built = time.strftime("%-d %B %Y", time.localtime(d["timestamp"])) if d.get("timestamp") else ""
    channel = {"latest": s("H-197"), "unstable": s("H-198")}.get(d.get("channel"), d.get("tag") or "")
    parts = [p for p in (s("H-196", version=version).strip(), channel,
                         built and s("H-199", date=built)) if p]
    return " · ".join(parts)


class UpdatesSection(Section):
    def __init__(self, window):
        self.status = None
        self.updating = False
        self.refresh_id = 0
        self._channel_guard = False
        self._auto_guard = False

        page = Adw.PreferencesPage()
        super().__init__(window, s("H-022"), page)

        # Status: icon, headline, a line of detail, the buttons.
        self.icon = Gtk.Image(pixel_size=64, icon_name="software-update-available-symbolic")
        self.icon.add_css_class("status-icon")
        self.spinner = Adw.Spinner(width_request=64, height_request=64, visible=False)
        self.headline = Gtk.Label(wrap=True, justify=Gtk.Justification.CENTER)
        self.headline.add_css_class("title-2")
        self.detail = Gtk.Label(wrap=True, justify=Gtk.Justification.CENTER)
        self.detail.add_css_class("dim-label")
        self.update_button = Gtk.Button(label=s("H-140"), halign=Gtk.Align.CENTER)
        self.update_button.add_css_class("pill")
        self.update_button.connect("clicked", self.on_update_now)
        self.restart_button = Gtk.Button(label=s("H-141"), halign=Gtk.Align.CENTER,
                                         visible=False)
        self.restart_button.add_css_class("pill")
        self.restart_button.add_css_class("suggested-action")
        self.restart_button.connect("clicked", self.on_restart)
        buttons = Gtk.Box(spacing=12, halign=Gtk.Align.CENTER, margin_top=12)
        buttons.append(self.restart_button)
        buttons.append(self.update_button)

        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6,
                             margin_top=12, margin_bottom=6)
        status_box.append(self.icon)
        status_box.append(self.spinner)
        status_box.append(self.headline)
        status_box.append(self.detail)
        status_box.append(buttons)

        # The output of "update now", folded away.
        self.log = Gtk.TextView(editable=False, cursor_visible=False,
                                monospace=True, wrap_mode=Gtk.WrapMode.WORD_CHAR,
                                top_margin=8, bottom_margin=8, left_margin=10,
                                right_margin=10)
        self.log.add_css_class("hub-log")
        scroller = Gtk.ScrolledWindow(child=self.log, min_content_height=220,
                                      max_content_height=220)
        scroller.add_css_class("card")
        self.log_scroller = scroller
        scroller.set_margin_top(6)
        self.log_expander = Gtk.Expander(label=s("H-142"), child=scroller,
                                         margin_top=12, visible=False)
        status_box.append(self.log_expander)

        status_group = Adw.PreferencesGroup()
        status_group.add(status_box)
        page.add(status_group)

        # Automatic updates
        auto = Adw.PreferencesGroup(
            title=s("H-150"),
            description=s("H-151"))
        self.auto_row = Adw.SwitchRow(
            title=s("H-152"),
            subtitle=s("H-153"))
        self.auto_row.connect("notify::active", self.on_auto_toggled)
        self.last_row = Adw.ActionRow(title=s("H-154"), subtitle="…")
        self.last_row.add_css_class("property")
        self.next_row = Adw.ActionRow(title=s("H-155"), subtitle="…")
        self.next_row.add_css_class("property")
        for row in (self.auto_row, self.last_row, self.next_row):
            auto.add(row)
        page.add(auto)

        # Image: the graphics (three images) and the channel (two tags of each).
        channel = Adw.PreferencesGroup(
            title=s("H-170"),
            description=s("H-171"))
        self.images = []
        self._graphics_guard = False
        self.graphics_row = Adw.ComboRow(title=s("H-172"), subtitle="…",
                                         model=Gtk.StringList.new([]), sensitive=False)
        self.graphics_row.add_prefix(Gtk.Image(icon_name="video-display-symbolic"))
        self.graphics_row.connect("notify::selected", self.on_graphics_changed)
        # The popover's own items, so "NVIDIA (Recommended)" isn't cut short.
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._graphics_item_setup)
        factory.connect("bind", self._graphics_item_bind)
        self.graphics_row.set_list_factory(factory)
        self._graphics_checks = set()
        self.graphics_row.connect("notify::selected", self._sync_graphics_checks)
        channel.add(self.graphics_row)
        self.channel_checks = {}
        group_check = None
        for channel_id, title, subtitle in CHANNELS:
            check = Gtk.CheckButton(valign=Gtk.Align.CENTER, group=group_check)
            group_check = group_check or check
            row = Adw.ActionRow(title=title, subtitle=subtitle, activatable_widget=check)
            row.add_prefix(check)
            check.connect("toggled", self.on_channel_toggled, channel_id)
            self.channel_checks[channel_id] = check
            channel.add(row)
        self.pinned_row = Adw.ActionRow(
            title=s("H-179"),
            subtitle=s("H-181"),
            visible=False)
        self.pinned_row.add_prefix(Gtk.Image(icon_name="changes-prevent-symbolic"))
        channel.add(self.pinned_row)
        page.add(channel)

        # Going back
        back = Adw.PreferencesGroup(
            title=s("H-190"),
            description=s("H-191"))
        self.current_row = Adw.ActionRow(title=s("H-192"), subtitle="…")
        self.current_row.add_css_class("property")
        self.previous_row = Adw.ActionRow(title=s("H-193"), subtitle="…")
        self.previous_row.add_css_class("property")
        self.rollback_button = Gtk.Button(label=s("H-200"), valign=Gtk.Align.CENTER)
        self.rollback_button.connect("clicked", self.on_rollback)
        self.previous_row.add_suffix(self.rollback_button)
        builds_row = Adw.ActionRow(
            title=s("H-201"),
            subtitle=s("H-202"),
            activatable=True)
        builds_row.add_suffix(Gtk.Image(icon_name="go-next-symbolic"))
        builds_row.connect("activated", lambda *_: self.open("builds"))
        for row in (self.current_row, self.previous_row, builds_row):
            back.add(row)
        page.add(back)

        # Advanced: feature branches' test builds, for developers.
        advanced = Adw.PreferencesGroup(title=s("H-210"))
        self.branches_row = Adw.ExpanderRow(
            title=s("H-211"),
            subtitle=s("H-212"))
        self.branches_row.add_prefix(Gtk.Image(icon_name="applications-engineering-symbolic"))
        self.branches_row.connect("notify::expanded", self._on_branches_expanded)
        self.branch_rows = []
        advanced.add(self.branches_row)
        page.add(advanced)

        self.view.connect("destroy", lambda *_: self._stop_refresh())

    # Refreshing

    def shown(self):
        self.refresh()
        if not self.images:
            host.run_json(["redfox-rollback-helper", "--json", "images"], self._on_images)

    def _stop_refresh(self):
        if self.refresh_id:
            GLib.source_remove(self.refresh_id)
            self.refresh_id = 0

    def refresh(self):
        host.run_json(["redfox-updates", "status", "--json"], self._on_status)

    def _schedule(self, seconds):
        self._stop_refresh()
        self.refresh_id = GLib.timeout_add_seconds(seconds, self._tick)

    def _tick(self):
        self.refresh_id = 0
        if self.window.get_visible():
            self.refresh()
        return GLib.SOURCE_REMOVE

    def _on_status(self, status, error):
        if error:
            self.show_state("dialog-warning-symbolic", s("H-139"), error)
            self._schedule(30)
            return
        self.status = status
        auto = status["auto"]
        booted = status.get("booted") or {}

        busy = status["busy"] or self.updating
        if self.updating:
            self.show_state(None, s("H-120"), s("H-121"))
        elif status["busy"]:
            self.show_state(None, s("H-122"), s("H-123"))
        elif status.get("restart_for") == "rollback":
            self.show_state("system-reboot-symbolic", s("H-124"), s("H-125"))
        elif status["restart_pending"]:
            staged = status.get("staged") or {}
            version = staged.get("version")
            ready = s("H-127", version=version) if version else s("H-128")
            self.show_state("system-reboot-symbolic", s("H-126"), f"{ready} {s('H-129')}")
        elif not auto["enabled"]:
            self.show_state("dialog-warning-symbolic", s("H-130"), s("H-131"), "warning")
        else:
            # The most recent update, automatic or "update now", and whether it
            # worked. The header says which it was, so it doesn't read as a
            # contradiction of "Last Automatic Update" below.
            runs = [(auto["last_run"], auto.get("last_result") in (None, "success"), s("H-137")),
                    (status["now"]["last_run"], status["now"].get("last_ok") is not False,
                     s("H-138"))]
            runs = [r for r in runs if r[0]]
            last, ok, how = max(runs) if runs else (None, True, "")
            if not ok:
                self.show_state("dialog-warning-symbolic", s("H-132"),
                                s("H-133", how=how, when=when(last, capital=False)), "warning")
            else:
                self.show_state("object-select-symbolic", s("H-134"),
                                s("H-135", how=how, when=when(last, capital=False))
                                if last else s("H-136"), "success")
        self.restart_button.set_visible(status["restart_pending"] and not busy)
        self.update_button.set_sensitive(not busy)
        self.update_button.set_label(s("H-140"))

        self._set_auto(auto["enabled"])
        result = auto.get("last_result")
        last = when(auto["last_run"])
        if auto["last_run"] and result and result != "success":
            last += s("H-156")
        self.last_row.set_subtitle(last)
        self.next_row.set_subtitle(when(auto["next"]) if auto["enabled"] else s("H-157"))

        self._channel_guard = True
        channel = booted.get("channel")
        for channel_id, check in self.channel_checks.items():
            check.set_active(channel == channel_id)
        if channel not in self.channel_checks:
            for check in self.channel_checks.values():
                check.set_active(False)
        self._channel_guard = False
        self.pinned_row.set_visible(channel == "pinned")
        if channel == "pinned":
            self.pinned_row.set_title(s("H-180", tag=booted.get("tag")))

        self.current_row.set_subtitle(system_name(booted))
        rollback = status.get("rollback")
        self.previous_row.set_subtitle(system_name(rollback) if rollback else s("H-194"))
        self.rollback_button.set_sensitive(bool(rollback) and not busy)

        self._schedule(5 if busy else 60)

    def show_state(self, icon, headline, detail, tone=None):
        spinning = icon is None
        self.spinner.set_visible(spinning)
        self.icon.set_visible(not spinning)
        if icon:
            self.icon.set_from_icon_name(icon)
        for css in ("success", "warning", "accent"):
            self.icon.remove_css_class(css)
        self.icon.add_css_class(tone or "accent")
        self.headline.set_label(headline)
        self.detail.set_label(detail)

    # Update now

    def on_update_now(self, _button):
        self.updating = True
        buffer = self.log.get_buffer()
        buffer.set_text("")
        self.log_expander.set_visible(True)
        self.update_button.set_sensitive(False)
        self.restart_button.set_visible(False)
        self.show_state(None, s("H-120"), s("H-121"))
        host.run(["redfox-updates", "now"], on_done=self._on_updated,
                 on_line=self._append_log, on_partial=self._partial_log)

    ANSI = GLib.Regex.new(r"\x1b\[[0-9;?]*[A-Za-z]", 0, 0)

    def _clean(self, text):
        return self.ANSI.replace(text, -1, 0, "", 0)  # topgrade's colours

    def _clear_partial(self):
        buffer = self.log.get_buffer()
        mark = buffer.get_mark("partial")
        if mark:
            buffer.delete(buffer.get_iter_at_mark(mark), buffer.get_end_iter())
            buffer.delete_mark(mark)

    def _append_log(self, line):
        self._clear_partial()
        buffer = self.log.get_buffer()
        buffer.insert(buffer.get_end_iter(), self._clean(line) + "\n")
        self._scroll_log()

    def _partial_log(self, text):
        """The line a progress bar is redrawing, shown as the log's last line."""
        self._clear_partial()
        if text is None:
            return
        buffer = self.log.get_buffer()
        buffer.create_mark("partial", buffer.get_end_iter(), True)
        buffer.insert(buffer.get_end_iter(), self._clean(text))
        self._scroll_log()

    def _scroll_log(self):
        adj = self.log_scroller.get_vadjustment()
        GLib.idle_add(lambda: adj.set_value(adj.get_upper()) and False)

    def _on_updated(self, returncode, _output):
        self.updating = False
        if returncode == 0:
            self.window.toast(s("H-225"))
        else:
            self.window.toast(s("H-226"))
            self.log_expander.set_expanded(True)
        self.refresh()

    # Automatic updates

    def _set_auto(self, enabled):
        self._auto_guard = True
        self.auto_row.set_active(enabled)
        self._auto_guard = False

    def on_auto_toggled(self, row, _param):
        if getattr(self, "_auto_guard", False):
            return
        state = "on" if row.get_active() else "off"

        def done(returncode, output):
            if returncode != 0:
                self.window.toast(s("H-227")
                                  if cancelled(output) or returncode in (126, 127)
                                  else s("H-228"))
            self.refresh()

        host.run(["redfox-updates", "auto", state], on_done=done)

    # Restart

    def on_restart(self, _button):
        dialog = Adw.AlertDialog(
            heading=s("H-206"),
            body=s("H-207"))
        dialog.add_response("cancel", s("H-188"))
        dialog.add_response("restart", s("H-208"))
        dialog.set_response_appearance("restart", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("restart")
        dialog.connect("response", lambda _d, r: r == "restart" and
                       host.run(["redfox-updates", "restart"]))
        dialog.present(self.window)

    # Graphics

    def _on_images(self, data, error):
        if error:
            self.graphics_row.set_subtitle(s("H-174"))
            return
        # The image names and what they're for come from redfox-rollback-helper.
        self.images = [dict(i, name=copy_data("G", f"{i['id']}-name", i["name"], "graphics variant name"),
                            description=copy_data("G", f"{i['id']}-description", i["description"],
                                                  "which graphics cards"))
                       for i in data["images"]]
        self.booted_image = data["booted"]["image"]
        self.booted_channel = data["booted"]["channel"]
        self._graphics_guard = True
        # The helper detects the graphics card; an unclear case recommends nothing.
        recommended = data.get("recommended")
        self.graphics_row.set_model(Gtk.StringList.new(
            [i["name"] + (s("H-173") if i["id"] == recommended else "")
             for i in self.images]))
        ids = [i["id"] for i in self.images]
        if self.booted_image in ids:
            self.graphics_row.set_selected(ids.index(self.booted_image))
        self._graphics_guard = False
        self._graphics_subtitle()
        self.graphics_row.set_sensitive(True)

    def _graphics_item_setup(self, _factory, item):
        box = Gtk.Box(spacing=6)
        box.append(Gtk.Label(xalign=0, hexpand=True, ellipsize=0))
        box.append(Gtk.Image(icon_name="object-select-symbolic", visible=False))
        item.set_child(box)

    def _graphics_item_bind(self, _factory, item):
        box = item.get_child()
        label, check = box.get_first_child(), box.get_last_child()
        label.set_label(item.get_item().get_string())
        check.position = item.get_position()
        self._graphics_checks.add(check)
        self._sync_graphics_checks()

    def _sync_graphics_checks(self, *_args):
        selected = self.graphics_row.get_selected()
        for check in self._graphics_checks:
            check.set_visible(getattr(check, "position", -1) == selected)

    def _graphics_subtitle(self):
        index = self.graphics_row.get_selected()
        if 0 <= index < len(self.images):
            self.graphics_row.set_subtitle(self.images[index]["description"])

    def _select_booted_graphics(self):
        ids = [i["id"] for i in self.images]
        self._graphics_guard = True
        if getattr(self, "booted_image", None) in ids:
            self.graphics_row.set_selected(ids.index(self.booted_image))
        self._graphics_guard = False
        self._graphics_subtitle()

    def on_graphics_changed(self, row, _param):
        if self._graphics_guard or not self.images:
            return
        self._graphics_subtitle()
        image = self.images[row.get_selected()]
        if image["id"] == self.booted_image:
            return
        channel = self.booted_channel if self.booted_channel in ("latest", "unstable") else "latest"
        dialog = Adw.AlertDialog(
            heading=s("H-182", name=image["name"]),
            body=s("H-183", description=image["description"]))
        dialog.add_response("cancel", s("H-188"))
        dialog.add_response("switch", s("H-187"))
        dialog.set_response_appearance("switch", Adw.ResponseAppearance.DESTRUCTIVE)

        def response(_d, r):
            if r == "switch":
                channel_name = dict((c, t) for c, t, _ in CHANNELS)[channel]
                self.rebase(f"{image['id']}:{channel}", f"{image['name']} ({channel_name})")
                self.booted_image = image["id"]  # what the next boot will be
            else:
                self._select_booted_graphics()

        dialog.connect("response", response)
        dialog.present(self.window)

    # Feature branches

    def _on_branches_expanded(self, row, _param):
        if row.get_expanded():
            self._set_branch_rows([Adw.ActionRow(title=s("H-213"))])
            host.run_json(["redfox-rollback-helper", "--json", "branches"], self._on_branches)

    def _set_branch_rows(self, rows):
        for row in self.branch_rows:
            self.branches_row.remove(row)
        self.branch_rows = rows
        for row in rows:
            self.branches_row.add_row(row)

    def _on_branches(self, data, error):
        if error:
            self._set_branch_rows([Adw.ActionRow(title=s("H-214"),
                                                 subtitle=GLib.markup_escape_text(error))])
            return
        rows = []
        for branch in data["branches"]:
            # The source decides the title: a branch's name, or "#N" and a
            # pull request's title (see feature-branches.conf).
            updated = s("H-217", date=long_date(branch["updated"]))
            where = (updated if branch["title"] == branch["branch"]
                     else f"{branch['branch']} · {updated}")
            row = Adw.ActionRow(
                title=GLib.markup_escape_text(branch["title"]),
                subtitle=GLib.markup_escape_text(
                    where + (f"\n{branch['description']}" if branch.get("description") else "")))
            row.set_subtitle_lines(3)
            button = Gtk.Button(label=s("H-218"), valign=Gtk.Align.CENTER)
            button.connect("clicked", self._on_try_branch, data["image"], branch)
            row.add_suffix(button)
            rows.append(row)
        if not rows:
            rows = [Adw.ActionRow(
                title=s("H-215"),
                subtitle=s("H-216"))]
        self._set_branch_rows(rows)

    def _on_try_branch(self, _button, image, branch):
        dialog = Adw.AlertDialog(
            heading=s("H-219"),
            body=s("H-220", title=branch["title"]))
        dialog.add_response("cancel", s("H-188"))
        dialog.add_response("try", s("H-221"))
        dialog.set_response_appearance("try", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.connect("response", lambda _d, r: r == "try" and self.rebase(
            f"{image}:{branch['tag']}", s("H-147", title=branch["title"])))
        dialog.present(self.window)

    # Channel

    def on_channel_toggled(self, check, channel_id):
        if self._channel_guard or not check.get_active():
            return
        title = dict((c, t) for c, t, _ in CHANNELS)[channel_id]
        dialog = Adw.AlertDialog(
            heading=s("H-184", name=title),
            body=s("H-185") if channel_id == "unstable" else s("H-186"))
        dialog.add_response("cancel", s("H-188"))
        dialog.add_response("switch", s("H-187"))
        dialog.set_response_appearance("switch", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", self._on_channel_response, channel_id)
        dialog.present(self.window)

    def _on_channel_response(self, _dialog, response, channel_id):
        if response != "switch":
            self.refresh()
            return
        self.rebase(channel_id)

    def rebase(self, target, label=None):
        self.updating = True
        self.update_button.set_sensitive(False)
        self.show_state(None, s("H-143"), s("H-144", label=label or s("H-145")))
        self.log.get_buffer().set_text("")
        self.log_expander.set_visible(True)

        def done(returncode, output):
            self.updating = False
            if returncode == 0:
                self.window.toast(s("H-229"))
            elif cancelled(output):
                self.window.toast(s("H-227"))
            else:
                self.window.toast(s("H-230"))
                self.log_expander.set_expanded(True)
            self.refresh()

        host.run(["redfox-rollback-helper", "--yes", "rebase", target],
                 on_done=done, on_line=self._append_log, on_partial=self._partial_log)

    # Rollback

    def on_rollback(self, _button):
        rollback = (self.status or {}).get("rollback")
        dialog = Adw.AlertDialog(
            heading=s("H-203"),
            body=s("H-204", system=system_name(rollback)))
        dialog.add_response("cancel", s("H-188"))
        dialog.add_response("back", s("H-205"))
        dialog.set_response_appearance("back", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self._on_rollback_response)
        dialog.present(self.window)

    def _on_rollback_response(self, _dialog, response):
        if response != "back":
            return

        def done(returncode, output):
            if returncode == 0:
                self.window.toast(s("H-231"))
            else:
                self.window.toast(output.strip().splitlines()[-1] if output.strip()
                                  else s("H-232"))
            self.refresh()

        host.run(["redfox-rollback-helper", "--yes", "rollback"], on_done=done)

    # Other builds

    def open(self, subpath):
        if subpath == "builds":
            self.view.pop_to_tag("root")
            self.view.push(BuildsPage(self))


class BuildsPage(Adw.NavigationPage):
    def __init__(self, section):
        self.section = section
        booted = (section.status or {}).get("booted") or {}
        self.channel = booted.get("channel") if booted.get("channel") in ("latest", "unstable") else "latest"

        self.page = Adw.PreferencesPage()
        self.group = Adw.PreferencesGroup(
            title=s("H-241"),
            description=s("H-242"))
        toggle = Adw.ToggleGroup(valign=Gtk.Align.CENTER)
        for channel_id, title, _ in CHANNELS:
            toggle.add(Adw.Toggle(name=channel_id, label=title))
        toggle.set_active_name(self.channel)
        toggle.connect("notify::active-name", self._on_channel)
        self.group.set_header_suffix(toggle)
        self.page.add(self.group)
        self.rows = []
        self.stack = Gtk.Stack()
        self.stack.add_named(Adw.Spinner(), "loading")
        self.stack.add_named(self.page, "list")
        self.error = Adw.StatusPage(icon_name="network-offline-symbolic",
                                    title=s("H-245"))
        self.stack.add_named(self.error, "error")

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        toolbar.set_content(self.stack)
        super().__init__(title=s("H-240"), child=toolbar, tag="builds")
        self.load()

    def _on_channel(self, toggle, _param):
        self.channel = toggle.get_active_name()
        self.load()

    def load(self):
        self.stack.set_visible_child_name("loading")
        host.run_json(["redfox-rollback-helper", "--json", "list", self.channel, "20"],
                      self._on_list)

    def _on_list(self, data, error):
        for row in self.rows:
            self.group.remove(row)
        self.rows = []
        if error:
            self.error.set_description(error)
            self.stack.set_visible_child_name("error")
            return
        booted_tag = ((self.section.status or {}).get("booted") or {}).get("tag")
        for build in data.get("builds", []):
            # The date is what most people go by; the change is the detail.
            row = Adw.ActionRow(title=long_date(build["date"]),
                                subtitle=GLib.markup_escape_text(
                                    f"{build['message']} · {build['commit']}"))
            row.set_subtitle_lines(2)
            if build["tag"] == booted_tag:
                row.add_suffix(Gtk.Label(label=s("H-243"), css_classes=["dim-label"]))
            else:
                button = Gtk.Button(label=s("H-244"), valign=Gtk.Align.CENTER)
                button.connect("clicked", self._on_switch, build)
                row.add_suffix(button)
            self.group.add(row)
            self.rows.append(row)
        self.stack.set_visible_child_name("list")

    def _on_switch(self, _button, build):
        dialog = Adw.AlertDialog(
            heading=s("H-246"),
            body=s("H-247", date=long_date(build["date"]), change=build["message"],
                   commit=build["commit"]))
        dialog.add_response("cancel", s("H-188"))
        dialog.add_response("switch", s("H-187"))
        dialog.set_response_appearance("switch", Adw.ResponseAppearance.SUGGESTED)

        def response(_d, r):
            if r == "switch":
                self.section.view.pop()
                self.section.rebase(build["commit"], s("H-146", date=long_date(build["date"])))

        dialog.connect("response", response)
        dialog.present(self.section.window)


