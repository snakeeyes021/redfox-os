"""The main window: a sidebar of sections, the section on the right."""

from gi.repository import Adw, Gio, Gtk

SECTIONS = [
    # id, title, icon, sidebar block (blocks are drawn apart)
    ("welcome", "Welcome", "user-home-symbolic", 0),
    ("apps", "Software", "view-app-grid-symbolic", 0),
    ("updates", "Updates", "software-update-available-symbolic", 0),
    ("desktop", "Desktop", "video-display-symbolic", 1),
    ("services", "Services", "network-server-symbolic", 1),
    ("storage", "Storage", "drive-harddisk-symbolic", 1),
    ("sound", "Sound & Music", "audio-speakers-symbolic", 1),
    ("terminal", "Terminal", "utilities-terminal-symbolic", 1),
    ("setup", "Full Setup", "emblem-system-symbolic", 1),
    ("manual", "Manual", "help-browser-symbolic", 2),
]
SECTION_IDS = [s[0] for s in SECTIONS]
# Links from before the setting sections had their own place in the sidebar.
OLD_PAGES = {"settings": "desktop", "settings/layout": "desktop/layout", "settings/setup": "setup"}


def make_section(section_id, window):
    if section_id == "welcome":
        from .welcome import WelcomeSection
        return WelcomeSection(window)
    if section_id == "apps":
        from .apps import AppsSection
        return AppsSection(window)
    if section_id == "updates":
        from .updates import UpdatesSection
        return UpdatesSection(window)
    if section_id in ("desktop", "services", "storage", "sound", "terminal"):
        from .settings import SettingsSection
        return SettingsSection(window, section_id)
    if section_id == "setup":
        from .setup import SetupSection
        return SetupSection(window)
    from .manual import ManualSection
    return ManualSection(window)


def header_page(title, child, tag=None, header=None):
    """An Adw.NavigationPage with a header bar over child."""
    toolbar = Adw.ToolbarView()
    toolbar.add_top_bar(header or Adw.HeaderBar())
    toolbar.set_content(child)
    page = Adw.NavigationPage(title=title, child=toolbar)
    if tag:
        page.set_tag(tag)
    return page


class HubWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(title="RedFox Hub", default_width=1000,
                         default_height=720, **kwargs)
        self.set_size_request(360, 400)
        self.sections = {}
        self.toasts = Adw.ToastOverlay()

        # Sidebar
        self.sidebar = Adw.Sidebar()
        blocks = {}
        for _section_id, title, icon, block in SECTIONS:
            if block not in blocks:
                blocks[block] = Adw.SidebarSection()
                self.sidebar.append(blocks[block])
            blocks[block].append(Adw.SidebarItem(title=title, icon_name=icon))
        self.sidebar.connect("activated", self._on_activated)

        menu = Gio.Menu()
        menu.append("Show the welcome tour", "app.welcome")
        menu.append("About RedFox Hub", "app.about")
        sidebar_header = Adw.HeaderBar()
        sidebar_header.pack_end(Gtk.MenuButton(
            icon_name="open-menu-symbolic", menu_model=menu,
            tooltip_text="Main menu", primary=True))
        sidebar_page = header_page("RedFox Hub", self.sidebar, header=sidebar_header)

        # Content: one navigation view per section, built when first shown.
        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        self.content = Adw.NavigationPage(title="RedFox Hub", child=self.stack)

        self.split = Adw.NavigationSplitView(
            sidebar=sidebar_page, content=self.content,
            min_sidebar_width=200, max_sidebar_width=240)
        self.toasts.set_child(self.split)
        self.set_content(self.toasts)

        breakpoint = Adw.Breakpoint.new(
            Adw.BreakpointCondition.parse("max-width: 640sp"))
        breakpoint.add_setter(self.split, "collapsed", True)
        self.add_breakpoint(breakpoint)

        self.show_section("welcome", reveal=False)

    def toast(self, text):
        self.toasts.add_toast(Adw.Toast(title=text, timeout=4))

    def _on_activated(self, _sidebar, index):
        self.show_section(SECTIONS[index][0])

    def section(self, section_id):
        if section_id not in self.sections:
            section = make_section(section_id, self)
            self.sections[section_id] = section
            self.stack.add_named(section.view, section_id)
        return self.sections[section_id]

    def show_section(self, section_id, reveal=True):
        ids = SECTION_IDS
        section_id = OLD_PAGES.get(section_id, section_id)
        if section_id not in ids:
            section_id = "welcome"
        section = self.section(section_id)
        self.stack.set_visible_child_name(section_id)
        self.content.set_title(SECTIONS[ids.index(section_id)][1])
        if self.sidebar.get_selected() != ids.index(section_id):
            self.sidebar.set_selected(ids.index(section_id))
        if reveal:
            self.split.set_show_content(True)
        section.shown()
        return section

    def open_page(self, path):
        """Open a deep link: 'updates', 'desktop/layout', 'manual/apps'."""
        path = path.strip().strip("/")
        if path.startswith("hub:"):
            path = path[4:]
        path = OLD_PAGES.get(path, path)
        section_id, _, rest = path.partition("/")
        section = self.show_section(section_id or "welcome")
        if rest:
            section.open(rest)


class Section:
    """A section of the window: an Adw.NavigationView with its root page."""

    def __init__(self, window, title, root):
        self.window = window
        self.view = Adw.NavigationView()
        self.view.add(header_page(title, root, tag="root"))

    def shown(self):
        pass

    def open(self, subpath):
        pass

    def push(self, title, child, tag=None):
        page = header_page(title, child, tag=tag)
        self.view.push(page)
        return page
