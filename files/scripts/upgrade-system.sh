#!/bin/bash

# Standard error handling to fail the build if this script fails
set -ouex pipefail

echo "Force-upgrading system to align with current Rawhide repos..."
rpm-ostree upgrade
