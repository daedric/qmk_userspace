import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]

TARGETS = {
    "daedric_34": ["--keymap", "daedric_34"],
    "daedric": ["--keymap", "daedric", "--autoshift"],
    "ergol": [],
    "ergolfr": ["--host", "fr"],
}


# Each committed keymap.c is exactly the generator output, run with the options
# gen.sh passes for that target, after clang-format.
@pytest.mark.parametrize("target", TARGETS)
def test_generated_keymap_matches_committed(target: str) -> None:
    generated = subprocess.run(
        [sys.executable, "scripts/gen_keymap", *TARGETS[target]],
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout
    formatted = subprocess.run(
        ["clang-format"], input=generated, cwd=REPO, check=True, capture_output=True
    ).stdout
    keymap = REPO / "keyboards/zsa/moonlander/keymaps" / target / "keymap.c"
    assert formatted == keymap.read_bytes()
