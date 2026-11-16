#!/usr/bin/env bash
# Installs the applet for the current user (no sudo) by symlinking it into Cinnamon's
# applets folder, so edits in this repo are picked up after an applet reload, and compiles
# the translations (po/*.po) where Cinnamon looks for them.
set -euo pipefail

UUID="single-screen@romu"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPLETS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/cinnamon/applets"
# Cinnamon and its settings panel always read applet translations from ~/.local/share/locale.
LOCALE_DIR="$HOME/.local/share/locale"

mkdir -p "$APPLETS_DIR"
rm -rf "${APPLETS_DIR:?}/$UUID"
ln -s "$ROOT/$UUID" "$APPLETS_DIR/$UUID"

for po in "$ROOT/$UUID"/po/*.po; do
    lang="$(basename "$po" .po)"
    mkdir -p "$LOCALE_DIR/$lang/LC_MESSAGES"
    msgfmt -o "$LOCALE_DIR/$lang/LC_MESSAGES/$UUID.mo" "$po"
done

echo "Single Screen installed. Add it to a panel: System Settings > Applets > Single Screen."
echo "Default shortcut: Super+P (configurable in the applet settings)."
