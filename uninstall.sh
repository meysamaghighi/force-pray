#!/usr/bin/env bash
set -euo pipefail
launchctl bootout "gui/$(id -u)/com.meysam.forcepray" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/com.meysam.forcepray.plist"
echo "Uninstalled. Logs still in ~/.force-pray/ (delete manually if you want)."
