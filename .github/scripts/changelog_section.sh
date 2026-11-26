#!/usr/bin/env bash
# Print the CHANGELOG.md section for one version (without its "## [x.y.z]" heading).
# Usage: changelog_section.sh 0.4.0 [CHANGELOG.md]
set -euo pipefail
version="$1"
file="${2:-CHANGELOG.md}"
awk -v head="## [${version}]" '
  index($0, head) == 1 { found = 1; next }
  found && /^## \[/    { exit }
  found                { print }
' "$file" | sed -e '/./,$!d'   # drop leading blank lines
