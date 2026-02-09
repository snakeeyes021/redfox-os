#!/usr/bin/env bash
set -oue pipefail

echo "Installing pixi..."
export PIXI_HOME=/usr
export PIXI_NO_PATH_UPDATE=1
curl -fsSL https://pixi.sh/install.sh | sh
