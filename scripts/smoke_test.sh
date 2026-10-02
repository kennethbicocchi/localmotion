#!/usr/bin/env bash
# Smoke test: proves the installation works, step by step, without waiting for a full video.
#   1. unit tests of the check rules            (no model, no GPU)
#   2. check_code on the example video          (TypeScript + ESLint + Remotion rules)
#   3. renders frames of the example            (Remotion + headless Chrome)
#   4. asks the loaded vision model about them  (skipped if LM Studio has no vision model loaded)
set -uo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
py="$here/remotion-check/.venv/bin/python"
export REMOTION_PROJECT="${REMOTION_PROJECT:-$here/remotion-template}"
pass=0; fail=0
step() { printf '\n\033[1m%s\033[0m\n' "$*"; }
ok() { echo "  ✅ $*"; pass=$((pass + 1)); }
ko() { echo "  ❌ $*"; fail=$((fail + 1)); }

step "1/4 Unit tests"
if "$py" -m pytest "$here/tests" -q; then ok "check rules"; else ko "unit tests failed"; fi

step "2/4 check_code on the example"
out=$(cd "$here/remotion-check" && "$py" -c 'import server; print(server.check_code("Example"))' 2>&1)
if grep -q "NO ERRORS" <<<"$out"; then ok "example code is clean"; else ko "check_code:"; echo "$out" | head -20; fi

step "3/4 Rendering frames of the example"
out=$(cd "$here/remotion-check" && "$py" -c '
import server
r = server.render_stills("Example", [30, 200, 400])
print(len(r["stills"]), "frames", r["errors"])' 2>&1 | tail -1)
if [[ "$out" == 3\ frames\ \[\]* ]]; then ok "3 frames rendered into $REMOTION_PROJECT/out/check/"; else ko "render: $out"; fi

step "4/4 Vision model"
out=$(cd "$here/remotion-check" && "$py" -c '
import server
if server.vision_model() is None:
    print("SKIP")
else:
    print(server.ask_vision([("", server.PUBLIC / "example" / "keeper.jpg")], "Describe this photo in one sentence.", max_tokens=600, effort="none"))' 2>&1 | tail -1)
case "$out" in
  SKIP) echo "  ⏭  no vision model loaded in LM Studio: load one to enable describe_media and review_frames" ;;
  *"UNAVAILABLE"*|"") ko "vision call failed: $out" ;;
  *) ok "vision model sees: ${out:0:100}" ;;
esac

step "Result: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
