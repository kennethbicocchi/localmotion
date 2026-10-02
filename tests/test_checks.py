"""Tests for the remotion-check rules. They need no model, no GPU and no Node: each test builds a
tiny fake Remotion project and checks that the static rules, fidelity and pacing helpers react."""
import importlib
import json
import sys
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "remotion-check"))
sys.path.insert(0, str(ROOT / "agent"))


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A fake Remotion project, with the server module pointed at it."""
    (tmp_path / "src").mkdir()
    (tmp_path / "public").mkdir()
    (tmp_path / "src" / "Root.tsx").write_text('import { Demo } from "./Demo";\n')
    monkeypatch.setenv("REMOTION_PROJECT", str(tmp_path))
    import server
    server = importlib.reload(server)
    return tmp_path, server


def write(folder: Path, files: dict[str, str]) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (folder / name).write_text(text)
    return folder


INDEX = """import { Composition } from "remotion";
import { makeTimeline } from "../kit";
import { Scene } from "./Scene";
const timeline = makeTimeline([{ len: 120, Comp: Scene }]);
export const Demo = () => <Composition id="Demo" component={() => null} durationInFrames={timeline.duration}
  fps={30} width={1080} height={1920} />;
"""


def test_classic_mistakes_are_errors(project):
    root, server = project
    demo = write(root / "src" / "Demo", {"index.tsx": INDEX, "Scene.tsx": """
import { spring, interpolate, Img } from "remotion";
export const Scene = () => {
  const x = Math.random();
  const s = spring({ frame: 10 });
  const items = [1, 2, 3].map((_, i) => interpolate(frame, [10 + i * 3, 30], [0, 1]));
  return <div style={{ fontFamily: "Arial" }}><img src="/photo.jpg" /></div>;
};
"""})
    errors, _ = server.static_checks(demo)
    text = "\n".join(errors)
    assert "Math.random" in text
    assert "spring() without fps" in text
    assert "start grows with the loop index" in text
    assert "System font" in text
    assert "<Img>" in text


def test_html_entity_in_string_is_flagged(project):
    root, server = project
    demo = write(root / "src" / "Demo", {"index.tsx": INDEX, "Scene.tsx": """
export const Scene = () => { const label = "&gt;&gt; TRANSFER BURN"; return <div>{label} &amp; more</div>; };
"""})
    _, warnings = server.static_checks(demo)
    assert sum("HTML entity" in w for w in warnings) == 1  # the string, not the JSX text


def test_clean_scene_passes(project):
    root, server = project
    demo = write(root / "src" / "Demo", {"index.tsx": INDEX, "Scene.tsx": """
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { RevealLine, stagger } from "../kit";
export const Scene = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame, fps });
  return <RevealLine delay={stagger(1, 4)}>Hello</RevealLine>;
};
"""})
    errors, warnings = server.static_checks(demo)
    assert errors == []
    assert not any("breathing room" in w for w in warnings)


def test_unregistered_composition(project):
    root, server = project
    (root / "src" / "Root.tsx").write_text("// nothing registered\n")
    demo = write(root / "src" / "Demo", {"index.tsx": INDEX, "Scene.tsx": "export const Scene = () => null;"})
    errors, _ = server.static_checks(demo)
    assert any("does not import ./Demo" in e for e in errors)


def test_late_landing_and_slow_stagger_warnings(project):
    root, server = project
    demo = write(root / "src" / "Demo", {"index.tsx": INDEX, "Scene.tsx": """
import { RevealLine } from "../kit";
export const Scene = () => [0, 1, 2].map((i) => <RevealLine delay={10 + i * 9}>x</RevealLine>)
  .concat(<RevealLine delay={110}>late</RevealLine>);
"""})
    _, warnings = server.static_checks(demo)
    text = "\n".join(warnings)
    assert "no breathing room" in text
    assert "per-item stagger" in text


def test_fidelity_uses_the_users_content(project):
    root, server = project
    demo = write(root / "src" / "Demo", {"index.tsx": INDEX, "Scene.tsx": """
export const Scene = () => <div><div>24</div><span>TRACKS</span><div>Every corner</div><div>is a decision.</div></div>;
"""})
    server.ORIGINAL_BRIEF = 'A 4-second vertical trailer. Use: 24 tracks, 12 cars. Tagline: "Every corner is a decision."'
    notes = server.fidelity(demo)
    assert any("12" in n and "not on screen" in n for n in notes)       # 12 cars is missing
    assert not any("24" in n and "not on screen" in n for n in notes)   # a giant "24" counts
    assert not any("Quoted text" in n for n in notes)                    # the tagline is split across lines: fine


def test_fidelity_flags_invented_figures(project):
    root, server = project
    demo = write(root / "src" / "Demo", {"index.tsx": INDEX, "Scene.tsx": """
export const Scene = () => <div><div>800M+ games sold</div><div>SOURCE: annual report</div></div>;
"""})
    server.ORIGINAL_BRIEF = "A 4-second vertical video about our games."
    notes = server.fidelity(demo)
    assert any("800M" in n for n in notes)
    _, warnings = server.static_checks(demo)
    assert any("source" in w.lower() for w in warnings)


def test_timeline_and_scene_lookup(project):
    root, server = project
    write(root / "src" / "Demo", {"index.tsx": """const timeline = makeTimeline([
  { len: 90, Comp: Hook },
  { len: 120, Comp: Body },
]);"""})
    timeline = server.scene_timeline("Demo")
    assert timeline == [("Hook", 0, 90), ("Body", 90, 120)]
    assert "scene Body, local frame 10 of 120" == server.scene_at(timeline, 100)


def test_empty_band_measurement(project):
    _, server = project
    img = Image.new("RGB", (540, 960), "black")
    noise = Image.effect_noise((540, 300), 80).convert("RGB")
    img.paste(noise, (0, 110))   # content only near the top of the safe area
    share, start, end = server.empty_band(img, 1920)
    assert share > 0.5 and end == 1520
    full = Image.effect_noise((540, 960), 80).convert("RGB")
    assert server.empty_band(full, 1920)[0] < 0.1


def test_compaction_keeps_recent_turns():
    import run_agent
    big = "x" * 5000
    messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]
    for i in range(10):
        messages.append({"role": "assistant", "content": "thinking out loud", "reasoning_content": big,
                         "tool_calls": [{"id": str(i), "function": {"name": "write_file",
                                         "arguments": json.dumps({"path": f"src/V/S{i}.tsx", "content": big})}}]})
        messages.append({"role": "tool", "tool_call_id": str(i), "content": big})
    before = len(json.dumps(messages))
    changed = run_agent.compact(messages)
    assert changed > 0 and len(json.dumps(messages)) < before * 0.7  # 4 old turns of 10 slimmed down
    recent = [m for m in messages if m["role"] == "assistant"][-run_agent.KEEP_RECENT:]
    assert all(m.get("reasoning_content") == big for m in recent)          # recent turns untouched
    assert "content omitted" in messages[2]["tool_calls"][0]["function"]["arguments"]


def test_format_follows_an_explicit_ratio(project):
    root, server = project
    index = INDEX.replace("width={1080} height={1920}", "width={1920} height={1080}")
    demo = write(root / "src" / "Demo", {"index.tsx": index, "Scene.tsx": "export const Scene = () => null;"})
    server.ORIGINAL_BRIEF = "A 4-second horizontal (16:9) promo. Show the vertical clips inside phone frames."
    assert not any("asks for a" in n for n in server.fidelity(demo))
    server.ORIGINAL_BRIEF = "A 4-second vertical reel."
    assert any("asks for a vertical" in n for n in server.fidelity(demo))
