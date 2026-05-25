#!/usr/bin/env bash
# Install force-pray as a launchd user agent (auto-starts at login, kept alive).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
PLIST_SRC="$HERE/com.meysam.forcepray.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.meysam.forcepray.plist"

mkdir -p "$HOME/Library/LaunchAgents" "$HOME/.force-pray"

# Unload if already loaded (ignore errors)
launchctl bootout "gui/$(id -u)/com.meysam.forcepray" 2>/dev/null || true

cp "$PLIST_SRC" "$PLIST_DST"
launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
launchctl enable "gui/$(id -u)/com.meysam.forcepray"

echo "Installed. Logs: ~/.force-pray/{daemon.log,stdout.log,stderr.log}"
echo "Status:"
launchctl print "gui/$(id -u)/com.meysam.forcepray" | head -20 || true
