import re
import subprocess
import sys
from pathlib import Path

import pytest
from codegen import generate
from ergol import HOSTS
from model import Host, Key, Layer

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


def test_hand_written_key_under_an_ergol_key_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match=re.escape("Key at Coord(row=0, col=0) is not transparent: KC_A"),
    ):
        generate({Layer.Base: "EKC_Q", Layer.Sym: "KC_A"}, HOSTS["us"], False)


def test_unicode_base_keycode_is_rejected() -> None:
    host = Host(
        keys={
            "EKC_Q": Key(
                base=0x00E2,  # pyright: ignore[reportArgumentType] the input under test
                shifted=None,
                dk_base="KC_TRNS",
                dk_shifted="KC_TRNS",
                sym_base="KC_TRNS",
                sym_shifted="KC_TRNS",
            )
        }
    )
    with pytest.raises(
        ValueError, match=re.escape("At the moment base keymaps need to be basic")
    ):
        generate({Layer.Base: "EKC_Q"}, host, False)


def test_custom_keycode_needs_a_unicode_shifted_keycode() -> None:
    host = Host(
        keys={
            "EKC_X": Key(
                base="KC_X",
                shifted=None,
                dk_base=0x00E2,
                dk_shifted="KC_A",
                sym_base="KC_TRNS",
                sym_shifted="KC_TRNS",
            )
        }
    )
    with pytest.raises(
        ValueError,
        match=re.escape("a custom key must be mapped to an unicode keycode"),
    ):
        generate({Layer.Base: "EKC_X"}, host, False)


def test_custom_keycode_under_a_tap_hold_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match=re.escape(
            "custom keycode cannot be created with keycode using special function"
            " (LT/OSL/...): LSFT_T(KC_1)"
        ),
    ):
        generate({Layer.Base: "LSFT_T(EKC_1)"}, HOSTS["us"], False)


def test_ergol_key_placed_twice_shares_its_alias() -> None:
    keymap = generate({Layer.Base: "EKC_DK, EKC_DK"}, HOSTS["us"], False)
    alias = "#define DK_EKC_DK UP(COMBINING_DIAERESIS, INVERTED_EXCLAMATION_MARK)"
    assert keymap.count(alias) == 1
    dk_layer = re.search(r"\[DK\] = LAYOUT\(([^)]*)\)", keymap)
    assert dk_layer is not None
    assert dk_layer[1].count("DK_EKC_DK") == 2
