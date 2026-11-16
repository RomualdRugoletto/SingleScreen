#!/usr/bin/env bash
# Removes the applet. Keeps ~/.config/single-screen (saved layout) unless --purge is given.
set -euo pipefail

UUID="single-screen@romu"
APPLETS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/cinnamon/applets"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}"

rm -rf "${APPLETS_DIR:?}/$UUID"
rm -f "$HOME"/.local/share/locale/*/LC_MESSAGES/"$UUID".mo
[[ "${1:-}" == "--purge" ]] && rm -rf "$CONFIG_DIR/single-screen" "$CONFIG_DIR/cinnamon/spices/$UUID"
echo "Single Screen uninstalled (remove it from the panel if it is still shown)."
