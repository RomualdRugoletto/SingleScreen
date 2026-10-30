#!/usr/bin/env bash
# Installs the applet for the current user (no sudo) by symlinking it into Cinnamon's
# applets folder, so edits in this repo are picked up after an applet reload.
set -euo pipefail

UUID="single-screen@romu"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPLETS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/cinnamon/applets"

mkdir -p "$APPLETS_DIR"
rm -rf "${APPLETS_DIR:?}/$UUID"
ln -s "$ROOT/$UUID" "$APPLETS_DIR/$UUID"

echo "Single Screen installed. Add it to a panel: System Settings > Applets > Single Screen."
echo "Default shortcut: Super+P (configurable in the applet settings)."
