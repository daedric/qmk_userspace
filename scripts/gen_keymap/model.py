import re
from dataclasses import dataclass
from enum import Enum

TRNS = "_______"

MOD_TAPS = {
    # incomplete
    # https://docs.qmk.fm/mod_tap
    "ALGR_T",
    "ALL_T",
    "ALT_T",
    "CMD_T",
    "CTL_T",
    "C_S_T",
    "GUI_T",
    "HYPR_T",
    "LAG_T",
    "LALT_T",
    "LCAG_T",
    "LCA_T",
    "LCMD_T",
    "LCTL_T",
    "LGUI_T",
    "LOPT_T",
    "LSA_T",
    "LSFT_T",
    "LSG_T",
    "LWIN_T",
    "MEH_T",
    "OPT_T",
    "RALT_T",
    "RCAG_T",
    "RCMD_T",
    "RGUI_T",
    "ROPT_T",
    "RSA_T",
    "RSFT_T",
    "RSG_T",
    "RWIN_T",
    "SAGR_T",
    "SCMD_T",
    "SFT_T",
    "SGUI_T",
    "SWIN_T",
    "WIN_T",
}

LAYER_TAP = re.compile(r"LT\((?P<layer>\w+)\|\s*(?P<keycode>\w+)\)")
MOD_TAP = re.compile(r"(?P<mod_tap>\w+)\((?P<keycode>\w+)\)")


class Layer(Enum):
    Base = 0
    Qwerty = 1
    DK = 2
    Sym = 3

    SymQwerty = 4
    Nav = 5
    Num = 6

    # perso
    Media = 11
    Fn = 12


@dataclass(frozen=True)
class KeyCode:
    keycode: str | int
    tap_hold: str | None = None
    """C expression wrapping the keycode, "{}" standing for it: "LALT_T({})"."""

    @classmethod
    def parse(cls, text: str) -> "KeyCode":
        if match := LAYER_TAP.fullmatch(text):
            return cls(match["keycode"], f"LT({match['layer']}, {{}})")
        if (match := MOD_TAP.fullmatch(text)) and match["mod_tap"] in MOD_TAPS:
            return cls(match["keycode"], f"{match['mod_tap']}({{}})")
        return cls(text)

    @property
    def c(self) -> str:
        return (self.tap_hold or "{}").format(self.keycode)

    @property
    def code_point(self) -> int | None:
        return self.keycode if isinstance(self.keycode, int) else None

    @property
    def is_transparent(self) -> bool:
        return self.keycode in ("KC_TRNS", TRNS)


@dataclass(frozen=True)
class Key:
    base: str
    shifted: str | int | None

    dk_base: str | int
    dk_shifted: str | int

    sym_base: str | int
    sym_shifted: str | int

    def pair(self, layer: Layer) -> tuple[KeyCode, KeyCode] | None:
        """The keycode and shifted keycode this key types on the layer."""
        match layer:
            case Layer.Base:
                return KeyCode(self.base), KeyCode(self.shifted or self.base)
            case Layer.DK:
                return KeyCode(self.dk_base), KeyCode(self.dk_shifted)
            case Layer.Sym:
                return KeyCode(self.sym_base), KeyCode(self.sym_shifted)
        return None


@dataclass(frozen=True)
class Host:
    keys: dict[str, Key]
    includes: tuple[str, ...] = ()


def parse_layout(layout: str) -> list[list[KeyCode]]:
    rows: list[list[KeyCode]] = []
    for line in layout.splitlines():
        if line.lstrip().startswith("//"):
            continue
        if cells := [KeyCode.parse(c.strip()) for c in line.split(",") if c.strip()]:
            rows.append(cells)
    return rows
