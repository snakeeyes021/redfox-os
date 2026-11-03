#!/usr/bin/env bash
# Install this checkout's Mailspring theme in the test VM's user account, by
# running the login hook against a copy in /tmp (the VM's /usr may be read-only).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
VM="${REPO}/tests/vm/vm"
tar -C "${REPO}/files/system" -cf - usr/share/redfox/mailspring usr/share/redfox/user-setup.hooks.d/70-mailspring-theme.sh |
    "${VM}" ssh 'rm -rf /tmp/rfms && mkdir -p /tmp/rfms && tar -C /tmp/rfms -xf -'
"${VM}" user 'sed "s|^SRC=/usr/share/redfox/mailspring|SRC=/tmp/rfms/usr/share/redfox/mailspring|" /tmp/rfms/usr/share/redfox/user-setup.hooks.d/70-mailspring-theme.sh | bash
    grep -c "column-RootSidebar" ~/.var/app/com.getmailspring.Mailspring/config/Mailspring/packages/ui-redfox-adwaita-light/styles/adwaita.less | sed "s/^/theme rules present: /"'
