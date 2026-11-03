#!/usr/bin/env bash
# Screenshot Mailspring in the test VM at a fixed window size, light and dark,
# with a given theme pair, for the comparison page. Nothing opens on the host:
# the VM is driven over SSH, GNOME Shell's Eval and virsh screenshots.
#
#   capture-mailspring.sh vanilla OUTDIR      Mailspring's own ui-light / ui-dark
#   capture-mailspring.sh redfox OUTDIR       RedFox Adwaita Light / Dark
#
# Needs the redfox-test VM from tests/vm with Mailspring set up on the fake
# test account (a GreenMail container in the VM; see README.md here), and
# GNOME Shell's unsafe mode on (Looking Glass: global.context.unsafe_mode = true),
# which Shell's Eval needs to move windows.
set -euo pipefail

MODE="$1"
OUT="$2"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
VM="${REPO}/tests/vm/vm"
export LIBVIRT_DEFAULT_URI=qemu:///session
NAME="${VM_NAME:-redfox-test}"
X=100 Y=100 W=1280 H=800
mkdir -p "${OUT}"

case "${MODE}" in
    vanilla) LIGHT=ui-light DARK=ui-dark ;;
    redfox) LIGHT=ui-redfox-adwaita-light DARK=ui-redfox-adwaita-dark ;;
    *) echo "mode is vanilla or redfox" >&2; exit 1 ;;
esac

# MAILSPRING_ARGS adds arguments to Mailspring's command line, e.g.
# --remote-debugging-port=9222 to measure the window over DevTools afterwards.
ARGS="${MAILSPRING_ARGS:-}"

# GreenMail keeps mail in memory, so refill the fake inbox after a restart.
# FRESH=1 restarts it first, to replace whatever is there.
[ "${FRESH:-0}" = 1 ] && "${VM}" ssh 'sudo podman restart greenmail >/dev/null'
"${VM}" ssh 'sudo podman start greenmail >/dev/null 2>&1 || true; sleep 8; python3 - <<PY
import email.message, imaplib, smtplib
m = imaplib.IMAP4("127.0.0.1", 143); m.login("tester@redfox.test", "secret")
n = int(m.select("INBOX")[1][0]); m.logout()
if n == 0:
    # The same mailbox as mock.py, newest first, with fixed times so the order is stable.
    mails = [("Ada Lovelace", "Notes on the Analytical Engine", "I have attached my notes, with the table for Bernoulli numbers.", 5),
             ("Linus", "Re: patch v3", "Applied, thanks. Looks good.", 4),
             ("Margaret Hamilton", "Lunar module checklist", "Final review of the priority display logic.", 3),
             ("RedFox Labs", "Welcome to RedFoxOS", "Your desktop is ready. Here are a few tips to get started.", 2),
             ("Dewy", "Weekend plans?", "Hiking on Saturday if the weather holds.", 1),
             ("Grace Hopper", "Compiler meeting moved to Thursday", "Room 4B, bring the punch cards.", 0)]
    import datetime, email.utils
    day = datetime.datetime.now().astimezone().replace(hour=11, second=0, microsecond=0)
    s = smtplib.SMTP("127.0.0.1", 587)
    for who, sub, body, minute in mails:
        msg = email.message.EmailMessage()
        msg["Date"] = email.utils.format_datetime(day.replace(minute=minute))
        msg["From"] = f"{who} <{who.split()[0].lower()}@example.org>"
        msg["To"] = "tester@redfox.test"; msg["Subject"] = sub; msg.set_content(body)
        s.send_message(msg)
    s.quit(); print("refilled the test inbox")
else:
    print(f"test inbox has {n} messages")
PY'
"${VM}" user "flatpak kill com.getmailspring.Mailspring 2>/dev/null; sleep 2; python3 - <<'PY'
import json, os
p = os.path.expanduser('~/.var/app/com.getmailspring.Mailspring/config/Mailspring/config.json')
c = json.load(open(p))
core = c.setdefault('*', {}).setdefault('core', {})
core.setdefault('appearance', {}).update(lightThemeName='${LIGHT}', darkThemeName='${DARK}')
core.setdefault('workspace', {})['mode'] = 'split'
core.pop('theme', None)  # Automatic: follow GNOME's light/dark setting
json.dump(c, open(p, 'w'), indent=2)
PY
gsettings set org.gnome.desktop.interface color-scheme default
(nohup flatpak run com.getmailspring.Mailspring ${ARGS} >/dev/null 2>&1 &); sleep 15
(nohup flatpak run com.getmailspring.Mailspring >/dev/null 2>&1 &); sleep 4"

# Put Mailspring's window at a fixed place and size, and raise it.
"${VM}" ssh "cat > /tmp/place-ms.js" <<JS
(() => {
  for (const a of global.get_window_actors()) {
    const w = a.meta_window;
    if (!/mailspring/i.test(w.get_gtk_application_id() || w.get_wm_class() || '')) continue;
    if (w.get_maximized && w.get_maximized()) w.unmaximize(3);
    w.move_resize_frame(true, ${X}, ${Y}, ${W}, ${H});
    w.activate(global.get_current_time());
    const r = w.get_frame_rect();
    return [r.x, r.y, r.width, r.height].join(',');
  }
  return 'none';
})()
JS
place() { "${VM}" user "gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell --method org.gnome.Shell.Eval \"\$(cat /tmp/place-ms.js)\"" | grep -o "[0-9]*,[0-9]*,[0-9]*,[0-9]*" | head -1; }
# Mutter applies the move a moment later, so place it, wait, and read back.
place >/dev/null; sleep 2; place >/dev/null; sleep 2
RECT="$(place)"
echo "Mailspring frame: ${RECT}"

click() {
    local cx=$(( $1 * 32767 / 1919 )) cy=$(( $2 * 32767 / 1079 ))
    virsh qemu-monitor-command "${NAME}" "{\"execute\":\"input-send-event\",\"arguments\":{\"events\":[{\"type\":\"abs\",\"data\":{\"axis\":\"x\",\"value\":${cx}}},{\"type\":\"abs\",\"data\":{\"axis\":\"y\",\"value\":${cy}}}]}}" >/dev/null
    sleep 0.2
    virsh qemu-monitor-command "${NAME}" '{"execute":"input-send-event","arguments":{"events":[{"type":"btn","data":{"down":true,"button":"left"}}]}}' >/dev/null
    sleep 0.1
    virsh qemu-monitor-command "${NAME}" '{"execute":"input-send-event","arguments":{"events":[{"type":"btn","data":{"down":false,"button":"left"}}]}}' >/dev/null
}
# Open the first message: the thread list is the second column.
click $(( X + 420 )) $(( Y + 60 )); sleep 2
# Park the pointer away from the window so nothing is hovered.
virsh qemu-monitor-command "${NAME}" '{"execute":"input-send-event","arguments":{"events":[{"type":"abs","data":{"axis":"x","value":32000}},{"type":"abs","data":{"axis":"y","value":32000}}]}}' >/dev/null

shoot() {
    local scheme="$1" file="$2"
    "${VM}" user "gsettings set org.gnome.desktop.interface color-scheme ${scheme}"
    sleep 4
    "${VM}" shot /tmp/ms-capture-full.png >/dev/null
    python3 - "$RECT" "$file" <<'PY'
import sys
from PIL import Image
x, y, w, h = (int(v) for v in sys.argv[1].split(","))
Image.open("/tmp/ms-capture-full.png").crop((x, y, x + w, y + h)).save(sys.argv[2])
PY
    echo "saved ${file}"
}
shoot default "${OUT}/light.png"
shoot prefer-dark "${OUT}/dark.png"
"${VM}" user "gsettings set org.gnome.desktop.interface color-scheme default"
