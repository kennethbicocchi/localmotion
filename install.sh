#!/usr/bin/env bash
# Installs localmotion: the check server, the Remotion project, the skill, and prints the MCP config.
#
#   ./install.sh                                   # use the Remotion template shipped in this repo
#   REMOTION_PROJECT=~/my-remotion ./install.sh    # use your own Remotion project instead
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
project="$(realpath -m "${REMOTION_PROJECT:-$here/remotion-template}")"
skills="${LMSTUDIO_SKILLS:-$HOME/.lmstudio/skills}"

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }
need() { command -v "$1" >/dev/null || { echo "Missing: $1 ($2)"; exit 1; }; }

say "1/5 Checking requirements"
need node "Node.js 20+ — https://nodejs.org"
need npm "comes with Node.js"
need uv "Python manager — https://docs.astral.sh/uv/"
node -e 'process.exit(+process.versions.node.split(".")[0] >= 20 ? 0 : 1)' || { echo "Node.js 20+ required"; exit 1; }
command -v ffprobe >/dev/null || echo "Note: ffprobe not found (optional: audio/video durations in describe_media)."

say "2/5 Python environment for the check server"
(cd "$here/remotion-check" && uv sync --quiet)

say "3/5 Remotion project: $project"
if [ "$project" = "$here/remotion-template" ]; then
  (cd "$project" && npm install --no-fund --no-audit --loglevel=error)
else
  [ -f "$project/package.json" ] || { echo "$project is not a Remotion project (no package.json)"; exit 1; }
  for dir in kit Example; do
    if [ -e "$project/src/$dir" ]; then
      echo "src/$dir already exists in your project: left untouched."
    else
      cp -r "$here/remotion-template/src/$dir" "$project/src/" && echo "Copied src/$dir"
    fi
  done
  mkdir -p "$project/public" && cp -rn "$here/remotion-template/public/example" "$project/public/"
  echo "Register the example in your src/Root.tsx:  import { Example } from \"./Example\";  …  <Example />"
fi

say "4/5 Skill for LM Studio / Bionic: $skills/remotion-video"
mkdir -p "$skills/remotion-video"
sed "s|{{REMOTION_PROJECT}}|$project|g" "$here/skills/remotion-video/SKILL.md" > "$skills/remotion-video/SKILL.md"

say "5/5 MCP servers: add these to LM Studio (~/.lmstudio/mcp.json → \"mcpServers\")"
cat <<EOF
{
  "remotion-filesystem": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "$project"]
  },
  "remotion-check": {
    "command": "$here/remotion-check/.venv/bin/python",
    "args": ["$here/remotion-check/server.py"],
    "env": { "REMOTION_PROJECT": "$project" },
    "timeout": 1800000
  }
}
EOF

say "Done."
echo "Next: run ./scripts/smoke_test.sh, then see docs/INSTALL.md for the model settings and the Telegram bot."
