#!/usr/bin/env bash
set -oue pipefail

echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/bin" sh
