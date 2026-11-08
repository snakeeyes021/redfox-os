"""Welcome: a short tour of RedFoxOS, in the manner of GNOME Tour.

A few full-window pages, each with one picture, a headline and a sentence or
two, that end in links to the rest of Hub. It sets nothing up itself. The
words are placeholders.

At first login /usr/libexec/redfox-hub-first-login runs `redfox-hub
--first-login`, which shows it once per user (a marker in
~/.local/state/redfox/).
"""

from gi.repository import Adw, Gtk

from .paths import LAYOUTS, host_state_dir
from .window import Section

STATE = host_state_dir()
MARKER = STATE / "welcome-seen"
FOX = "tech.redfoxlabs.Hub"  # the fox, as Hub's own icon


def seen():
    return MARKER.exists()


def mark_seen():
    try:
        STATE.mkdir(parents=True, exist_ok=True)
        MARKER.touch()
    except OSError:
        pass


def hero_icon(icon_name):
    """A big symbolic icon on an accent-coloured disc, for pages without art yet."""
    image = Gtk.Image(icon_name=icon_name, pixel_size=96)
    disc = Gtk.Box(halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER,
                   width_request=192, height_request=192)
    disc.add_css_class("welcome-disc")
    image.set_hexpand(True)
    image.set_vexpand(True)
    disc.append(image)
    return disc


def fox():
    image = Gtk.Image(icon_name=FOX, pixel_size=256)
    image.add_css_class("welcome-fox")
    return image


def layout_strip():
    box = Gtk.Box(spacing=12, halign=Gtk.Align.CENTER)
    for name in ("redfox", "ubuntu", "wash"):
        path = LAYOUTS / f"{name}.svg"
        if path.exists():
            picture = Gtk.Picture.new_for_filename(str(path))
            picture.set_size_request(144, 90)
            picture.set_can_shrink(True)
            picture.set_hexpand(True)
            picture.add_css_class("layout-preview")
            box.append(picture)
    box.set_homogeneous(True)
    # The pictures are 240 px wide; keep the strip clear of the arrows.
    return Adw.Clamp(maximum_size=520, child=box)


class TourPage(Gtk.Box):
    def __init__(self, picture, headline, body, extra=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                         valign=Gtk.Align.CENTER, halign=Gtk.Align.CENTER,
                         hexpand=True, vexpand=True, margin_start=36, margin_end=36)
        picture.set_margin_bottom(24)
        self.append(picture)
        title = Gtk.Label(label=headline, wrap=True, justify=Gtk.Justification.CENTER)
        title.add_css_class("title-1")
        self.append(title)
        text = Gtk.Label(label=body, wrap=True, justify=Gtk.Justification.CENTER,
                         max_width_chars=50)
        text.add_css_class("body")
        text.add_css_class("welcome-body")
        self.append(text)
        if extra:
            extra.set_margin_top(18)
            self.append(extra)


class Tour(Gtk.Box):
    """The pages, the arrows and the dots. on_finish(page) is called with
    'apps', 'settings/layout', 'manual' or None."""

    def __init__(self, on_finish, embedded=False):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.on_finish = on_finish
        self.carousel = Adw.Carousel(hexpand=True, vexpand=True,
                                     allow_scroll_wheel=True, allow_long_swipes=False)

        start = Gtk.Box(spacing=12, halign=Gtk.Align.CENTER)
        go = Gtk.Button(label="Take the Tour")
        go.add_css_class("pill")
        go.add_css_class("suggested-action")
        go.connect("clicked", lambda *_: self.next())
        start.append(go)
        if not embedded:
            later = Gtk.Button(label="Not Now")
            later.add_css_class("pill")
            later.connect("clicked", lambda *_: self.on_finish(None))
            start.append(later)

        links = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                        halign=Gtk.Align.CENTER)
        for label, icon, page in (("Get Apps", "view-app-grid-symbolic", "apps"),
                                  ("Choose a Layout", "view-dual-symbolic", "settings/layout"),
                                  ("Read the Manual", "help-browser-symbolic", "manual")):
            button = Gtk.Button(child=Adw.ButtonContent(label=label, icon_name=icon))
            button.add_css_class("pill")
            button.add_css_class("welcome-link")
            button.connect("clicked", lambda _b, p=page: self.on_finish(p))
            links.append(button)
        if not embedded:
            done = Gtk.Button(label="Close", halign=Gtk.Align.CENTER, margin_top=6)
            done.add_css_class("flat")
            done.connect("clicked", lambda *_: self.on_finish(None))
            links.append(done)

        pages = [
            TourPage(fox(), "Welcome to RedFoxOS",
                     "A fast, friendly desktop that looks after itself.", start),
            TourPage(hero_icon("software-update-available-symbolic"),
                     "Updates You Never Have to Think About",
                     "RedFoxOS updates itself in the background, all in one piece. "
                     "If an update ever misbehaves, go back to the one before, "
                     "in Hub or from the boot menu."),
            TourPage(hero_icon("view-app-grid-symbolic"), "Apps for Everything",
                     "Bazaar has thousands of apps from Flathub. RedFox's packs of "
                     "favourites are in Hub, a tick away."),
            TourPage(layout_strip(), "Make It Yours",
                     "Six layouts: a dock on the side or at the bottom, or one "
                     "taskbar. Switch any time; your apps stay open."),
            TourPage(hero_icon("object-select-symbolic"), "You're All Set",
                     "Here's where to go next.", links),
        ]
        for page in pages:
            self.carousel.append(page)

        self.back = Gtk.Button(icon_name="go-previous-symbolic", valign=Gtk.Align.CENTER,
                               halign=Gtk.Align.START, margin_start=18,
                               tooltip_text="Previous")
        self.forward = Gtk.Button(icon_name="go-next-symbolic", valign=Gtk.Align.CENTER,
                                  halign=Gtk.Align.END, margin_end=18,
                                  tooltip_text="Next")
        for button in (self.back, self.forward):
            button.add_css_class("circular")
            button.add_css_class("welcome-arrow")
        self.back.connect("clicked", lambda *_: self.previous())
        self.forward.connect("clicked", lambda *_: self.next())

        overlay = Gtk.Overlay(child=self.carousel, vexpand=True)
        overlay.add_overlay(self.back)
        overlay.add_overlay(self.forward)
        self.append(overlay)
        dots = Adw.CarouselIndicatorDots(carousel=self.carousel, margin_bottom=18,
                                         margin_top=6)
        self.append(dots)
        self.carousel.connect("page-changed", lambda *_: self._sync())
        self._sync()

    def _index(self):
        return round(self.carousel.get_position())

    def _sync(self):
        index = self._index()
        last = self.carousel.get_n_pages() - 1
        self.back.set_visible(index > 0)
        self.forward.set_visible(0 < index < last)
        if index == last:
            mark_seen()

    def next(self):
        index = self._index()
        if index < self.carousel.get_n_pages() - 1:
            self.carousel.scroll_to(self.carousel.get_nth_page(index + 1), True)

    def previous(self):
        index = self._index()
        if index > 0:
            self.carousel.scroll_to(self.carousel.get_nth_page(index - 1), True)


class WelcomeWindow(Adw.ApplicationWindow):
    """The tour on its own, as GNOME Tour shows it: at first login, or from
    the menu."""

    def __init__(self, first_login=False, **kwargs):
        super().__init__(title="Welcome to RedFoxOS", default_width=820,
                         default_height=640, **kwargs)
        self.set_size_request(360, 480)
        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar(show_title=False)
        toolbar.add_top_bar(header)
        toolbar.set_content(Tour(self._finish))
        self.set_content(toolbar)
        self.connect("close-request", lambda *_: (mark_seen(), False)[1])

    def _finish(self, page):
        mark_seen()
        app = self.get_application()
        if page:
            app.show_page(page)
        self.close()


class WelcomeSection(Section):
    def __init__(self, window):
        self.tour = Tour(self._finish, embedded=True)
        super().__init__(window, "Welcome", self.tour)

    def _finish(self, page):
        if page:
            self.window.open_page(page)
