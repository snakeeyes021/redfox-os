"""The context the copy pass gives for each string with voice.

Written without the current wording: where the text is, when the user sees
it, what they need at that moment, and what the text has to get across.
"shots" are the hint-mode screenshots (tools/hint-shots.py, in its voice
mode) that show it, by file name.
"""

CONTEXT = {
    "H-008": {
        "where": "Not inside Hub. Software centres (Bazaar, GNOME Software) show it under Hub's name in their lists and at the top of Hub's page.",
        "when": "Someone is browsing their installed apps, or comes across Hub in a store, and wonders what it is.",
        "needs": "To tell at a glance what this app is and that it belongs to their system.",
        "across": "This is RedFoxOS's own app: the welcome, recommended apps, updates, settings and help in one place.",
        "shots": [],
    },
    "H-009": {
        "where": "Not inside Hub: the description paragraph on Hub's page in a software centre, under the summary (H-008).",
        "when": "Someone has opened Hub's page in a store to find out more.",
        "needs": "To understand what's inside before opening it, and that it comes with the system (nothing to install).",
        "across": "It comes with RedFoxOS. What's in it: a short welcome tour, RedFox's packs of recommended apps, the state of updates and going back to an earlier system, the desktop layouts, and a short manual.",
        "shots": [],
    },
    "H-041": {
        "where": "Welcome tour, page 1 of 5: the big headline under the painted fox. Shown in two places: the Welcome section of Hub's main window (it's the first section, so anyone opening Hub lands on it), and the tour's own window.",
        "when": "The tour's own window opens by itself at a person's first login on a new install, once setup is over. Later, it's what anyone sees on opening Hub. Nothing has happened yet; there's no problem to solve.",
        "needs": "A greeting. To feel welcome and oriented. Nothing to do yet; the only button below starts the tour (and, in its own window, there's a second one to skip it).",
        "across": "Welcome to this system, by name. It sets the tone for everything after it. (The tour window's title bar currently says the same; it isn't in this pass.)",
        "shots": ["001.png", "006.png"],
    },
    "H-042": {
        "where": "Welcome tour, page 1: the one line under the big headline (H-041), above the button that starts the tour. Same two places as H-041.",
        "when": "Same moment as H-041: the very first screen.",
        "needs": "A first impression of what kind of system they've got, before deciding whether to take the tour.",
        "across": "What this system is like to live with, in one line: its character, not a feature list.",
        "shots": ["001.png", "006.png"],
    },
    "H-045": {
        "where": "Welcome tour, page 2 of 5: the headline under a big updates icon. The ‹ › arrows at the sides move between pages.",
        "when": "They pressed the button on page 1 (or the › arrow). This is the first thing the tour explains.",
        "needs": "To learn that updates aren't a chore here.",
        "across": "Updates look after themselves: the person never has to manage them.",
        "shots": ["002.png"],
    },
    "H-046": {
        "where": "Welcome tour, page 2: the text under H-045.",
        "when": "Same moment as H-045.",
        "needs": "To trust the system with updates: what happens, and what if it goes wrong.",
        "across": "The facts: the whole system updates in the background every day, all in one piece, and the new version starts at the next restart. If a new one misbehaves, they can go back to the previous system, from Hub's Updates page or from the menu that shows when the computer starts.",
        "shots": ["002.png"],
    },
    "H-047": {
        "where": "Welcome tour, page 3 of 5: the headline under a big app-grid icon.",
        "when": "Next page of the tour, after updates.",
        "needs": "To know where software comes from.",
        "across": "There's an app for whatever they want to do, and getting it is easy.",
        "shots": ["003.png"],
    },
    "H-048": {
        "where": "Welcome tour, page 3: the text under H-047.",
        "when": "Same moment as H-047.",
        "needs": "Where to go to get apps.",
        "across": "The facts: the Bazaar app store has thousands of apps (from Flathub). RedFox's own packs of recommended apps are in Hub's Apps section, installed with a tick.",
        "shots": ["003.png"],
    },
    "H-049": {
        "where": "Welcome tour, page 4 of 5: the headline under three small pictures of desktop layouts.",
        "when": "Next page, after apps.",
        "needs": "To know the desktop can look the way they like.",
        "across": "The desktop is theirs to arrange.",
        "shots": ["004.png"],
    },
    "H-050": {
        "where": "Welcome tour, page 4: the text under H-049.",
        "when": "Same moment as H-049.",
        "needs": "What the choices are, and that trying one is safe.",
        "across": "The facts: there are six layouts (a dock at the side or along the bottom, or one taskbar), they can switch whenever they like, and their open apps stay open when they do.",
        "shots": ["004.png"],
    },
    "H-051": {
        "where": "Welcome tour, page 5 of 5 (the last): the headline under a big tick. Same page in the main window and in the tour's own window.",
        "when": "They've been through the whole tour.",
        "needs": "A sense of being done, and ready.",
        "across": "They're ready to go.",
        "shots": ["005.png", "007.png"],
    },
    "H-052": {
        "where": "Welcome tour, page 5: the one line under H-051, directly above three buttons (get apps, choose a layout, read the manual). In the tour's own window a plain close link sits under them too.",
        "when": "Same moment as H-051.",
        "needs": "To pick a next step, or close the tour.",
        "across": "Here are good places to go next (it introduces the three buttons below it).",
        "shots": ["005.png", "007.png"],
    },
    "H-080": {
        "where": "Apps section: the dim line at the top of the page, above the first pack of apps. Each pack is a list of apps with a tick box on the right.",
        "when": "They opened Apps from the sidebar, or from the tour's last page.",
        "needs": "To understand how the page works before ticking anything.",
        "across": "These are RedFox's packs of recommended apps. A ticked app is installed. To change things, tick or untick, then press Apply (in a bar that appears at the bottom).",
        "shots": ["008.png"],
    },
    "H-134": {
        "where": "Updates section: the big headline at the top, under a green tick, above the Update Now button. Appears in two states: the usual one (shot 009) and a brand-new install (shot 010).",
        "when": "Most of the time: automatic updates are on and the last update worked (or none has run yet on a new install). This is what people see nearly every time they open Updates.",
        "needs": "Reassurance. Nothing to do.",
        "across": "Updates are taken care of, automatically; all is well.",
        "shots": ["009.png", "010.png"],
    },
    "H-136": {
        "where": "Updates section: the line under H-134 on a brand-new install. (Normally that line says when the last update ran; that line isn't in this pass.)",
        "when": "A new install, before the first automatic update has run, so there's no \"last updated\" time yet.",
        "needs": "To know nothing is wrong, and that they don't have to do anything.",
        "across": "The first update will happen soon, by itself.",
        "shots": ["010.png"],
    },
    "H-131": {
        "where": "Updates section: the line under the orange warning headline that says automatic updates are switched off. The Update Now button is just below it; the switch is further down the page.",
        "when": "Someone turned the automatic updates switch off (it needs a password). It stays like this until it's turned back on.",
        "needs": "A gentle reminder, not a scolding: they chose this.",
        "across": "Update by hand now and then (the button is right there), to get fixes and security updates.",
        "shots": ["012.png"],
    },
    "H-133": {
        "where": "Updates section: the line under the orange warning headline that says the last update didn't finish, above the Update Now button.",
        "when": "The most recent update stopped part-way (for example the network dropped, or the computer was switched off).",
        "needs": "Reassurance that it's not serious, and a way to fix it now if they want.",
        "across": "When that update started and how; that it will try again by itself; and that they can update now instead. {how} is filled with \"automatically\" or a phrase meaning they pressed Update Now; {when} with something like \"today at 7:34 PM\" or \"yesterday at …\" (lower case, mid-sentence). Both phrases are fixed and not in this pass.",
        "shots": ["011.png"],
    },
    "H-129": {
        "where": "Updates section: the second sentence of the line under the headline that says to restart to finish updating. The first sentence (not in this pass) says the new version is ready. A Restart… button and Update Now sit below. Used only here.",
        "when": "An update has downloaded and is waiting for a restart to take effect.",
        "needs": "To decide when to restart, without worrying about it.",
        "across": "Restarting doesn't touch their files or apps.",
        "shots": ["013.png"],
    },
    "H-270": {
        "where": "Layout page (Settings › Layout): the dim line at the top, above six cards with a picture of each layout. The current one has an outline.",
        "when": "They opened it from Settings, or from the tour's choose-a-layout button.",
        "needs": "To choose, and to feel free to try.",
        "across": "This chooses where the dock, the top bar and the taskbar go. Clicking a card changes the desktop straight away, open apps stay open, and they can switch again any time.",
        "shots": ["014.png"],
    },
    "H-290": {
        "where": "Manual section: the dim line at the top, above the search box and the list of help pages.",
        "when": "They opened the Manual from the sidebar or from the tour, usually because they want to know how something works.",
        "needs": "To tell whether their question is covered here.",
        "across": "These are short help pages only about the places where RedFoxOS works differently from other Linux systems (for the rest, ordinary Linux and GNOME help applies).",
        "shots": ["015.png"],
    },
}
