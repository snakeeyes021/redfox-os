#!/bin/bash
set -ouex pipefail

# Set permissions for First Boot Dispatcher
chmod +x /usr/bin/firstboot-dispatcher.sh
chmod +x /usr/share/firstboot/scripts/*

# Enable the First Boot Service
systemctl enable firstboot-setup.service
