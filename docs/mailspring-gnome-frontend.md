# A GNOME front end over Mailspring's sync engine: feasibility

Status: research note for Matt. Nothing is built, and nothing should be until the questions below are answered.

The idea: keep Mailspring's sync engine (`mailsync`), which is good at IMAP, and replace its Electron interface with a GTK 4 / libadwaita app. This note looks at whether that's practical, and compares it with just recommending a GNOME mail client.

## How Mailspring is put together

- **`mailsync`** ([Foundry376/Mailspring-Sync](https://github.com/Foundry376/Mailspring-Sync)) is a C++ program built on MailCore2. Mailspring starts one per account. It syncs mail, contacts and calendars into a SQLite database in the config folder.
- **The interface talks to it over stdin/stdout.** Commands go in as newline-separated JSON (`queue-task`, `cancel-task`, `wake-workers`, `need-bodies`, `sync-calendar`, `search-remote`). Every object it changes comes back out as a JSON line, so the interface can update.
- **The interface also reads the SQLite database directly** for everything it shows: threads, messages, folders, contacts. Each table keeps the full object as JSON in a `data` column, plus a few copied columns for queries.
- **The actions are "tasks"** defined by the Electron app (marking read, moving, labelling, saving and sending drafts, and so on). `mailsync` runs a local part straight away and a remote part with retries.

## The questions

### Licence

`mailsync` is **GPL-3.0**. A front end that bundles or links it must be GPL-3.0 too. That's fine for an open-source RedFox app, but the RedFox repo itself is Apache-2.0, so it would have to live in its own repo.

The README asks that forks not use the Mailspring name. The code goes further. In release builds, `mailsync` exits at startup unless its own file path contains "mailspring" (`main.cpp`, commented "prevent re-use of Mailspring-Sync in products / forks not called Mailspring"). That makes the author's wishes clear: the engine isn't meant to be reused this way, and RedFox shouldn't build on it against them. That matters for the next point too.

### Protocol stability

There is **no public API**. The stdin/stdout messages, the task formats and the database layout are internal to Mailspring and ship in lockstep with its Electron app. They change between releases without notice; both repos are very active (commits this week). A third-party front end would have to:

- pin a `mailsync` version and build it ourselves (it vendors libetpan, and builds its own OpenSSL and curl on Linux);
- follow Mailspring's changes by reading its source, every release.

### Accounts and OAuth

- **Plain IMAP/SMTP accounts with passwords** would work; `mailsync` takes the account details on stdin.
- **Gmail and Microsoft 365/Outlook** use OAuth. Mailspring's Electron app runs those sign-in flows with Mailspring's own registered OAuth client IDs, and `mailsync` only refreshes the tokens. We can't reuse Mailspring's client IDs. Registering our own works for Microsoft. For Gmail, full mailbox access is a "restricted" Google scope: past a small test-user limit, it needs Google's app verification plus a yearly third-party security assessment, which has a real cost. This alone rules out Gmail support for a hobby-scale app.
- **The Mailspring ID** (read receipts, snooze, send later) is a Mailspring cloud service. `mailsync` runs without one (`null` identity), and those features would simply be missing.

### What the Electron side does that we'd have to rebuild

Practically the whole mail client except syncing:

- account setup: autodiscovery of server settings, the OAuth sign-in windows, storing passwords in the keyring;
- the thread list, threading, search, unread counts and the folder/label sidebar, all built on the database and the change stream;
- **message display**: HTML email, rendered safely in a sandboxed web view (WebKitGTK), with remote images blocked by default and quoted text collapsed;
- **the composer**: rich-text HTML editing, replies and forwards with quoting, signatures, attachments, inline images, drafts saved through tasks, spell check;
- notifications, the tray, keyboard shortcuts, undo, translations;
- contacts and the calendar, if we want those.

### Effort

- **A usable first version** (IMAP accounts only, read, search, reply and send, plain composer): roughly **4–6 months of full-time work** for one experienced GTK developer, most of it on message display and the composer.
- **Matching Mailspring's features**: well over a year. After that, ongoing work every time Mailspring changes its internals.

## The alternative: recommend a GNOME-native client

| | Geary | Evolution | Mailspring + RedFox Adwaita theme |
| --- | --- | --- | --- |
| Toolkit | GTK 3 + libhandy (adaptive) | GTK 3 | Electron, themed to look like libadwaita |
| Accounts | GNOME Online Accounts, so Gmail and Microsoft OAuth come from GNOME's registered clients; also IMAP | GNOME Online Accounts, IMAP, Exchange (EWS), Microsoft 365 | Its own sign-in; Gmail, Microsoft, IMAP |
| Calendar and contacts | No | Yes | Contacts; the engine also syncs calendars (CalDAV, Google, Microsoft) |
| Activity | Slow: last release 46.0, November 2025; recent commits are mostly translations | Active: 3.62.1, October 2026 | Very active |
| Flathub | `org.gnome.Geary` | `org.gnome.Evolution` | `com.getmailspring.Mailspring` |

- **Geary** is the closest to "a GNOME mail app". It's simple and conversation-based. But it's on GTK 3 and moving slowly.
- **Evolution** is the most complete (mail, calendar, contacts, Exchange) and well maintained. It's heavier and looks older, though it follows the system theme.
- **Mailspring with RedFox Adwaita** keeps the client Matt already uses and makes it look at home. That's the theme on `feat/mailspring-adwaita`: light and dark, following GNOME's setting and accent colour.

## Recommendation

**Don't build the front end.** A GPL engine with no stable interface, whose author blocks reuse, plus a Gmail OAuth problem we can't solve cheaply: that's months of work to start and constant upkeep after.

Instead:

1. **Ship Mailspring with the RedFox Adwaita theme** (done on `feat/mailspring-adwaita`).
2. **Offer Geary or Evolution** in RedFox's software list for people who want a GNOME-native client. Both get Gmail and Microsoft sign-in through GNOME Online Accounts.
3. **Revisit only if Mailspring publishes a documented engine API**, or if a GTK 4 mail client that uses GNOME Online Accounts matures. Then RedFox could adopt it rather than build one.
