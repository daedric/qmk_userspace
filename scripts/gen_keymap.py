from collections import defaultdict
import itertools
from dataclasses import dataclass
import copy
from enum import Enum
from typing import Generator
from unicodedata import name as unicode_name
import re
import argparse


parser = argparse.ArgumentParser(description="Process keymap options.")
parser.add_argument(
    "--keymap",
    choices=["std", "daedric", "daedric_34"],
    default="std",
    help='Specify the keymap to use. Options are "std" or "daedric".',
)
parser.add_argument(
    "--host",
    choices=["us", "fr"],
    default="us",
    help="Specify the host on which the keyboard will be plugged",
)
parser.add_argument(
    "--autoshift",
    action="store_true",
    default=False,
    help="Autoshift support",
)

args = parser.parse_args()


class Mode(Enum):
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


class ShiftMode(Enum):
    Default = 0
    Override = 1
    CustomKey = 2
    UnicodeMap = 3


def is_basic(kc) -> bool:
    return isinstance(kc, str)


def is_unicode(kc) -> bool:
    return isinstance(kc, int)


class LTFunction:
    def __init__(self, layer, kc):
        self.layer = layer
        self.kc = kc

    @staticmethod
    def parse(kc: str):
        pattern = re.compile(r"^LT\((?P<layer>\w+)\|\s*(?P<keycode>\w+)\)$")
        if match := pattern.match(kc):
            return LTFunction(match.group("layer"), match.group("keycode"))

        return None

    def __call__(self, kc):
        return f"LT({self.layer}, {kc})"


class UnaryKCFunction:
    _known_functions = {
        # incomplete
        # https://docs.qmk.fm/mod_tap
        "ALGR_T",
        "ALL_T",
        "ALT_T",
        "CMD_T",
        "CTL_T",
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
        "RSG_T",
        "RWIN_T",
        "SAGR_T",
        "SCMD_T",
        "SFT_T",
        "SFT_T",
        "SGUI_T",
        "SWIN_T",
        "WIN_T",
    }

    def __init__(self, fn, kc):
        self.fn = fn
        self.kc = kc

    @classmethod
    def parse(cls, kc: str):
        for kf in cls._known_functions:
            if kc.startswith(kf):
                break
        else:
            return None
        pattern = re.compile(r"(?P<fn>\w+)\((?P<keycode>\w+)\)")
        match = pattern.match(kc)
        return UnaryKCFunction(match.group("fn"), match.group("keycode"))

    def __call__(self, kc):
        return f"{self.fn}({kc})"


_functions = (
    LTFunction,
    UnaryKCFunction,
)


class KeyCode:
    def __init__(self, kc: str | int):
        self._kc: str | int = kc
        self._layer: str | None = None
        self._fn: LTFunction | UnaryKCFunction | None = None
        if isinstance(kc, str):
            for fn in _functions:
                self._fn = fn.parse(kc)
                if self._fn:
                    self._kc = self._fn.kc
                    break

    @property
    def has_function(self):
        return self._fn is not None

    @property
    def is_unicode(self):
        return is_unicode(self._kc)

    @property
    def is_transparent(self):
        return is_transparent(self._kc)

    @property
    def is_basic(self):
        return is_basic(self._kc)

    @property
    def layer(self):
        return self._layer

    @property
    def raw_keycode(self) -> str | int:
        return self._kc

    def replace_keycode(self, new_kc):
        self._kc = new_kc

    def remove_function(self):
        self._layer = None
        self._fn = None

    @property
    def kc(self):
        if self.has_function:
            return self._fn(self._kc)
        return self._kc

    def __str__(self):
        return f"{self.kc}"

    def __repr__(self):
        return str(self.kc)

    def __eq__(self, other: "KeyCode|str"):
        if not isinstance(other, KeyCode):
            if isinstance(other, str):
                return self == KeyCode(other)
            return False
        return self.kc == other.kc

    def __hash__(self):
        return hash(self.kc)

    def __format__(self, format_spec):
        if self.has_function:
            return self._fn(self._kc)
        return format(self._kc, format_spec)

    def __len__(self):
        return len(self.kc)


def get_shift_mod(kc: KeyCode, skc: KeyCode) -> ShiftMode:
    if kc.is_basic:
        if skc is None or kc == skc:
            return ShiftMode.Default
        if kc.has_function and kc.raw_keycode == skc.raw_keycode:
            return ShiftMode.Default
        if skc.is_basic:
            return ShiftMode.Override
    if kc.is_unicode:
        if skc.is_unicode:
            return ShiftMode.UnicodeMap
        if skc.is_transparent:
            return ShiftMode.Default
    return ShiftMode.CustomKey


TRNS = "_______"


def is_transparent(kc):
    return kc == "KC_TRNS" or kc == TRNS


@dataclass
class Override:
    m: Mode
    n: str
    kc: KeyCode
    skc: KeyCode

    @property
    def name(self):
        return f"{self.m.name}_{self.n}"


@dataclass
class Key:
    base: str
    shifted: str | int | None

    dk_base: str | int
    dk_shifted: str | int

    sym_base: str | int
    sym_shifted: str | int

    def get_kc(self, m: Mode):
        kc = None
        skc = None
        match m:
            case Mode.Base:
                kc, skc = self.base, self.shifted
            case Mode.DK:
                kc, skc = self.dk_base, self.dk_shifted
            case Mode.Sym:
                kc, skc = self.sym_base, self.sym_shifted
            case _:
                kc, skc = TRNS, TRNS
        if not skc:
            skc = kc

        return kc, skc

    def is_basic(self, m: Mode):
        kc, _ = self.get_kc(m)
        return isinstance(kc, str)


@dataclass
class Coord:
    row: int
    col: int


class Layer:
    def __init__(self, layout: "Keymaps", rows: list[list[KeyCode]]):
        self.layout: "Keymaps" = layout
        self.rows = rows
        self.max_length = 0
        self.has_keys = False
        for cols in rows:
            for c in cols:
                self.has_keys = self.has_keys or not c.is_transparent
                self.max_length = max(self.max_length, len(c))

    def set_key(self, coord: Coord, key: KeyCode):
        if key.is_transparent:
            return

        self.has_keys = True
        prev = self.rows[coord.row][coord.col]
        if not prev.is_transparent and key != prev:
            raise Exception(f"Key at {coord} is not transparent: {prev}")
        self.rows[coord.row][coord.col] = key.kc
        self.max_length = max(self.max_length, len(key))

    def format(self, FMT: str | None):
        if not FMT:
            return ",\n".join(", ".join(cols) for cols in self.rows)

        fmt = "{{:^{}}}".format(self.max_length)
        kcs = [fmt.format(kc) for kc in itertools.chain(*self.rows)]
        return f"\n// clang-format off\n{FMT.format(*kcs)}\n// clang-format on\n"


class Keymaps:
    TRNS = "_______"

    def __init__(self, fmt_layer: str, nb_keys):
        self.fmt_layer = fmt_layer

        self.final_layers: dict[Mode, Layer] = {}
        self.transparent_layer = self._parse(fmt_layer.format(*([self.TRNS] * nb_keys)))

    @classmethod
    def _parse(cls, layout):
        lines: str = layout.split("\n")
        base_layer = []
        for line in lines:
            line = line.lstrip()
            if line.startswith("//"):
                continue
            keys = list(
                filter(
                    None, [KeyCode(kc.strip()) for kc in line.split(",") if kc.strip()]
                )
            )
            if keys:
                base_layer.append(keys)
        return base_layer

    def add_layer(self, m: Mode, preset: None | str = None) -> Layer:
        if l := self.final_layers.get(m):
            if preset != None:
                raise Exception(f"there is already a layer for mode: {m}")
            return l
        if preset is None:
            l = Layer(self, copy.deepcopy(self.transparent_layer))
        else:
            l = Layer(self, self._parse(preset))
        self.final_layers[m] = l
        return l

    def set_base(self, layer):
        self.base_layer = self._parse(layer)

    def base_keys(self) -> Generator[tuple[KeyCode, Coord], None, None]:
        for row, cols in enumerate(self.base_layer):
            for col, name in enumerate(cols):
                yield (name, Coord(row=row, col=col))

    def has_keys(self, m: Mode) -> bool:
        return self.final_layers[m].has_keys

    def format(self, m: Mode) -> str:
        return self.final_layers[m].format(self.fmt_layer)


ergol_keys = {
    "us": {
        # fmt: off
        "EKC_Q": Key(base="KC_Q", shifted=None, dk_base=0x00E2, dk_shifted=0x00C2, sym_base="KC_CIRC", sym_shifted=0x0302),
        "EKC_C": Key(base="KC_C", shifted=None, dk_base=0x00E7, dk_shifted=0x00C7, sym_base="KC_LABK", sym_shifted=0x2264),
        "EKC_O": Key(base="KC_O", shifted=None, dk_base=0x0153, dk_shifted=0x0152, sym_base="KC_RABK", sym_shifted=0x2265),
        "EKC_P": Key(base="KC_P", shifted=None, dk_base=0x00F4, dk_shifted=0x00D4, sym_base="KC_DLR", sym_shifted="KC_TRNS"),
        "EKC_W": Key(base="KC_W", shifted=None, dk_base="KC_TRNS", dk_shifted="KC_TRNS", sym_base="KC_PERC", sym_shifted=0x2030),

        "EKC_J": Key(base="KC_J", shifted=None, dk_base="KC_TRNS", dk_shifted="KC_TRNS", sym_base="KC_AT", sym_shifted=0x030A),
        "EKC_M": Key(base="KC_M", shifted=None, dk_base=0x00B5, dk_shifted="KC_TRNS", sym_base="KC_AMPR", sym_shifted="KC_TRNS"),
        "EKC_D": Key(base="KC_D", shifted=None, dk_base="KC_UNDS", dk_shifted="KC_TRNS", sym_base="KC_ASTR", sym_shifted=0x00D7),
        "EKC_DK": Key(base="OSL(DK)", shifted="KC_EXLM", dk_base=0x0308, dk_shifted=0x00A1, sym_base="KC_QUOT", sym_shifted=0x0301),
        "EKC_Y": Key(base="KC_Y", shifted=None, dk_base=0x00FB, dk_shifted=0x00DB, sym_base="KC_GRV", sym_shifted=0x0300),

        "EKC_A": Key(base="KC_A", shifted=None, dk_base=0x00E0, dk_shifted=0x00C0, sym_base="KC_LCBR", sym_shifted=0x030C),
        "EKC_S": Key(base="KC_S", shifted=None, dk_base=0x00E9, dk_shifted=0x00C9, sym_base="KC_LPRN", sym_shifted="KC_TRNS"),
        "EKC_E": Key(base="KC_E", shifted=None, dk_base=0x00E8, dk_shifted=0x00C8, sym_base="KC_RPRN", sym_shifted="KC_TRNS"),
        "EKC_N": Key(base="KC_N", shifted=None, dk_base=0x00EA, dk_shifted=0x00CA, sym_base="KC_RCBR", sym_shifted=0x0307),
        "EKC_F": Key(base="KC_F", shifted=None, dk_base=0x00F1, dk_shifted=0x00D1, sym_base="KC_EQL", sym_shifted=0x2260),

        "EKC_L": Key(base="KC_L", shifted=None, dk_base="KC_LPRN", dk_shifted="KC_TRNS", sym_base="KC_BSLS", sym_shifted=0x0338),
        "EKC_R": Key(base="KC_R", shifted=None, dk_base="KC_RPRN", dk_shifted="KC_TRNS", sym_base="KC_PLUS", sym_shifted=0x2A72),
        "EKC_T": Key(base="KC_T", shifted=None, dk_base=0x00EE, dk_shifted=0x00CE, sym_base="KC_MINS", sym_shifted=0x0304),
        "EKC_I": Key(base="KC_I", shifted=None, dk_base=0x00EF, dk_shifted=0x00CF, sym_base="KC_SLSH", sym_shifted=0x00F7),
        "EKC_U": Key(base="KC_U", shifted=None, dk_base=0x00F9, dk_shifted=0x00D9, sym_base="KC_DQUO", sym_shifted=0x030B),

        "EKC_Z": Key(base="KC_Z", shifted=None, dk_base=0x00E6, dk_shifted=0x00C6, sym_base="KC_TILD", sym_shifted=0x0303),
        "EKC_X": Key(base="KC_X", shifted=None, dk_base=0x00DF, dk_shifted=0x1E9E, sym_base="KC_LBRC", sym_shifted=0x0326),
        "EKC_MNS": Key(base="KC_MINS", shifted="KC_QUES", dk_base=0x2011, dk_shifted=0x00BF, sym_base="KC_RBRC", sym_shifted=0x0328),
        "EKC_V": Key(base="KC_V", shifted=None, dk_base=0x2013, dk_shifted="KC_TRNS", sym_base="KC_UNDS", sym_shifted=0x2013),
        "EKC_B": Key(base="KC_B", shifted=None, dk_base=0x2014, dk_shifted="KC_TRNS", sym_base="KC_HASH", sym_shifted="KC_TRNS"),

        "EKC_DOT": Key(base="KC_DOT", shifted="KC_COLN", dk_base=0x2026, dk_shifted="KC_TRNS", sym_base="KC_PIPE", sym_shifted=0x00A6),
        "EKC_H": Key(base="KC_H", shifted=None, dk_base="KC_TRNS", dk_shifted="KC_TRNS", sym_base="KC_EXLM", sym_shifted=0x00AC),
        "EKC_G": Key(base="KC_G", shifted=None, dk_base="KC_TRNS", dk_shifted="KC_TRNS", sym_base="KC_SCLN", sym_shifted=0x0312),
        "EKC_COMM": Key(base="KC_COMM", shifted="KC_SCLN", dk_base=0x00B7, dk_shifted=0x2022, sym_base="KC_COLN", sym_shifted="KC_TRNS"),
        "EKC_K": Key(base="KC_K", shifted=None, dk_base="KC_TRNS", dk_shifted="KC_TRNS", sym_base="KC_QUES", sym_shifted=0x0306),

        "EKC_1": Key(base="KC_1", shifted=0x20AC, dk_base=0x201E, dk_shifted=0x201A, sym_base=0x2081, sym_shifted=0x00B9),
        "EKC_2": Key(base="KC_2", shifted=0x00AB, dk_base=0x201C, dk_shifted=0x2018, sym_base=0x2082, sym_shifted=0x00B2),
        "EKC_3": Key(base="KC_3", shifted=0x00BB, dk_base=0x201D, dk_shifted=0x2019, sym_base=0x2083, sym_shifted=0x00B3),
        "EKC_4": Key(base="KC_4", shifted="KC_DLR", dk_base=0x00A2, dk_shifted="KC_TRNS", sym_base=0x2084, sym_shifted=0x2074),
        "EKC_5": Key(base="KC_5", shifted="KC_PERC", dk_base=0x2030, dk_shifted="KC_TRNS", sym_base=0x2085, sym_shifted=0x2075),
        "EKC_6": Key(base="KC_6", shifted="KC_CIRC", dk_base="KC_TRNS", dk_shifted="KC_TRNS", sym_base=0x2086, sym_shifted=0x2076),

        "EKC_7": Key(base="KC_7", shifted="KC_AMPR", dk_base="KC_TRNS", dk_shifted="KC_TRNS", sym_base=0x2087, sym_shifted=0x2077),
        "EKC_8": Key(base="KC_8", shifted="KC_ASTR", dk_base=0x00A7, dk_shifted="KC_TRNS", sym_base=0x2088, sym_shifted=0x2078),
        "EKC_9": Key(base="KC_9", shifted="KC_HASH", dk_base=0x00B6, dk_shifted="KC_TRNS", sym_base=0x2089, sym_shifted=0x2079),
        "EKC_0": Key(base="KC_0", shifted="KC_AT", dk_base=0x00B0, dk_shifted="KC_TRNS", sym_base=0x2080, sym_shifted=0x2070),

        "EKC_SPC": Key(base="KC_SPC", shifted=0x202F, dk_base=0x2019, dk_shifted="KC_TRNS", sym_base="KC_SPC", sym_shifted="KC_TRNS"),
        # fmt: on
    },
    "fr": {
        # fmt: off
        "EKC_Q": Key(base="FR_Q", shifted=None, dk_base=0x00E2, dk_shifted=0x00C2, sym_base=0x005E, sym_shifted=0x0302),
        "EKC_C": Key(base="FR_C", shifted=None, dk_base="FR_CCED", dk_shifted=0x00C7, sym_base="FR_LABK", sym_shifted=0x2264),
        "EKC_O": Key(base="FR_O", shifted=None, dk_base=0x0153, dk_shifted=0x0152, sym_base="FR_RABK", sym_shifted=0x2265),
        "EKC_P": Key(base="FR_P", shifted=None, dk_base=0x00F4, dk_shifted=0x00D4, sym_base="FR_DLR", sym_shifted="KC_TRNS"),
        "EKC_W": Key(base="FR_W", shifted=None, dk_base="KC_TRNS", dk_shifted="KC_TRNS", sym_base="FR_PERC", sym_shifted=0x2030),

        "EKC_J": Key(base="FR_J", shifted=None, dk_base="KC_TRNS", dk_shifted="KC_TRNS", sym_base="FR_AT", sym_shifted=0x030A),
        "EKC_M": Key(base="FR_M", shifted=None, dk_base=0x00B5, dk_shifted="KC_TRNS", sym_base="FR_AMPR", sym_shifted="KC_TRNS"),
        "EKC_D": Key(base="FR_D", shifted=None, dk_base="FR_UNDS", dk_shifted="KC_TRNS", sym_base="FR_ASTR", sym_shifted=0x00D7),
        "EKC_DK": Key(base="OSL(DK)", shifted="KC_EXLM", dk_base=0x0308, dk_shifted=0x00A1, sym_base="FR_QUOT", sym_shifted=0x0301),
        "EKC_Y": Key(base="FR_Y", shifted=None, dk_base=0x00FB, dk_shifted=0x00DB, sym_base="FR_GRV", sym_shifted=0x0300),

        "EKC_A": Key(base="FR_A", shifted=None, dk_base="FR_AGRV", dk_shifted=0x00C0, sym_base="FR_LCBR", sym_shifted=0x030C),
        "EKC_S": Key(base="FR_S", shifted=None, dk_base="FR_EACU", dk_shifted=0x00C9, sym_base="FR_LPRN", sym_shifted="KC_TRNS"),
        "EKC_E": Key(base="FR_E", shifted=None, dk_base="FR_EGRV", dk_shifted=0x00C8, sym_base="FR_RPRN", sym_shifted="KC_TRNS"),
        "EKC_N": Key(base="FR_N", shifted=None, dk_base=0x00EA, dk_shifted=0x00CA, sym_base="FR_RCBR", sym_shifted=0x0307),
        "EKC_F": Key(base="FR_F", shifted=None, dk_base=0x00F1, dk_shifted=0x00D1, sym_base="FR_EQL", sym_shifted=0x2260),

        "EKC_L": Key(base="FR_L", shifted=None, dk_base="FR_LPRN", dk_shifted="KC_TRNS", sym_base="FR_BSLS", sym_shifted=0x0338),
        "EKC_R": Key(base="FR_R", shifted=None, dk_base="FR_RPRN", dk_shifted="KC_TRNS", sym_base="FR_PLUS", sym_shifted=0x2A72),
        "EKC_T": Key(base="FR_T", shifted=None, dk_base=0x00EE, dk_shifted=0x00CE, sym_base="FR_MINS", sym_shifted=0x0304),
        "EKC_I": Key(base="FR_I", shifted=None, dk_base=0x00EF, dk_shifted=0x00CF, sym_base="FR_SLSH", sym_shifted=0x00F7),
        "EKC_U": Key(base="FR_U", shifted=None, dk_base=0x00F9, dk_shifted=0x00D9, sym_base="FR_DQUO", sym_shifted=0x030B),

        "EKC_Z": Key(base="FR_Z", shifted=None, dk_base=0x00E6, dk_shifted=0x00C6, sym_base="FR_TILD", sym_shifted=0x0303),
        "EKC_X": Key(base="FR_X", shifted=None, dk_base=0x00DF, dk_shifted=0x1E9E, sym_base="FR_LBRC", sym_shifted=0x0326),
        "EKC_MNS": Key(base="FR_MINS", shifted="FR_QUES", dk_base=0x2011, dk_shifted=0x00BF, sym_base="FR_RBRC", sym_shifted=0x0328),
        "EKC_V": Key(base="FR_V", shifted=None, dk_base=0x2013, dk_shifted="KC_TRNS", sym_base="FR_UNDS", sym_shifted=0x2013),
        "EKC_B": Key(base="FR_B", shifted=None, dk_base=0x2014, dk_shifted="KC_TRNS", sym_base="FR_HASH", sym_shifted="KC_TRNS"),

        "EKC_DOT": Key(base="FR_DOT", shifted="FR_COLN", dk_base=0x2026, dk_shifted="KC_TRNS", sym_base="FR_PIPE", sym_shifted=0x00A6),
        "EKC_H": Key(base="FR_H", shifted=None, dk_base="KC_TRNS", dk_shifted="KC_TRNS", sym_base="FR_EXLM", sym_shifted=0x00AC),
        "EKC_G": Key(base="FR_G", shifted=None, dk_base="KC_TRNS", dk_shifted="KC_TRNS", sym_base="FR_SCLN", sym_shifted=0x0312),
        "EKC_COMM": Key(base="FR_COMM", shifted="FR_SCLN", dk_base=0x00B7, dk_shifted=0x2022, sym_base="FR_COLN", sym_shifted="KC_TRNS"),
        "EKC_K": Key(base="FR_K", shifted=None, dk_base="KC_TRNS", dk_shifted="KC_TRNS", sym_base="FR_QUES", sym_shifted=0x0306),

        "EKC_1": Key(base="FR_1", shifted=0x20AC, dk_base=0x201E, dk_shifted=0x201A, sym_base=0x2081, sym_shifted=0x00B9),
        "EKC_2": Key(base="FR_2", shifted=0x00AB, dk_base=0x201C, dk_shifted=0x2018, sym_base=0x2082, sym_shifted=0x00B2),
        "EKC_3": Key(base="FR_3", shifted=0x00BB, dk_base=0x201D, dk_shifted=0x2019, sym_base=0x2083, sym_shifted=0x00B3),
        "EKC_4": Key(base="FR_4", shifted="FR_DLR", dk_base=0x00A2, dk_shifted="KC_TRNS", sym_base=0x2084, sym_shifted=0x2074),
        "EKC_5": Key(base="FR_5", shifted="FR_PERC", dk_base=0x2030, dk_shifted="KC_TRNS", sym_base=0x2085, sym_shifted=0x2075),
        "EKC_6": Key(base="FR_6", shifted=0x005E, dk_base="KC_TRNS", dk_shifted="KC_TRNS", sym_base=0x2086, sym_shifted=0x2076),

        "EKC_7": Key(base="FR_7", shifted="FR_AMPR", dk_base="KC_TRNS", dk_shifted="KC_TRNS", sym_base=0x2087, sym_shifted=0x2077),
        "EKC_8": Key(base="FR_8", shifted="FR_ASTR", dk_base="FR_SECT", dk_shifted="KC_TRNS", sym_base=0x2088, sym_shifted=0x2078),
        "EKC_9": Key(base="FR_9", shifted="FR_HASH", dk_base=0x00B6, dk_shifted="KC_TRNS", sym_base=0x2089, sym_shifted=0x2079),
        "EKC_0": Key(base="FR_0", shifted="FR_AT", dk_base="FR_DEG", dk_shifted="KC_TRNS", sym_base=0x2080, sym_shifted=0x2070),

        "EKC_SPC": Key(base="KC_SPC", shifted=0x202F, dk_base=0x2019, dk_shifted="KC_TRNS", sym_base="KC_SPC", sym_shifted="KC_TRNS"),
        # fmt: on
    },
}


class Gen:
    file_tpl = """
        #include QMK_KEYBOARD_H

        #include <stdint.h>

        #include "keycodes.h"
        #include "version.h"

        {extra_include}

    enum layers {{
        {layers},
    }};

    enum custom_keycodes {{
        _FIRST = SAFE_RANGE,
        {custom_keycodes},
    }};

    {aliases}

    {unicode_map}

    {overrides}


    const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {{
        {layouts},
    }};

    {custom_process}
    {custom_autoshift}
    """

    def __init__(self, host, kms: "Keymaps", autoshift=False):
        self.host = host
        self.keymaps = kms
        self.autoshift = autoshift
        self.keys = ergol_keys[self.host]
        self.unicode_to_idx: dict[KeyCode, str] = {}
        self.unicode_map: str | None = None
        self.override: dict[Mode, dict[str, Override]] = defaultdict(dict)
        self.aliases: dict[str, KeyCode] = {}
        self.custom_keys: dict[Mode, dict[str, tuple[KeyCode, KeyCode]]] = defaultdict(
            dict
        )

        self._check()

    def _check(self):
        for _, k in self.keys.items():
            if not k.is_basic(Mode.Base):
                raise Exception("At the moment base keymaps need to be basic")

    def _gen_unicode_map(self):
        indices_line = "{idx}"
        unicode_map_line = "[{idx}]  = {cp:#06x} /* {dsp} */"
        tpl = """
            enum unicode_names {{
                {indices},
            }};


            const uint32_t PROGMEM unicode_map[] = {{
                {unicode_map_lines},
            }};
        """
        indices = []
        unicode_map_lines = []
        already_gen = set()
        for _, key in self.keys.items():
            for m in Mode:
                kc, skc = key.get_kc(m)
                kc = KeyCode(kc)
                skc = KeyCode(skc)
                for k in (kc, skc):
                    if k.is_unicode:
                        if k in already_gen:
                            continue
                        already_gen.add(k)

                        ch = chr(k.raw_keycode)
                        name = unicode_name(ch)
                        name = name.replace(" ", "_").replace("-", "_")

                        idx = indices_line.format(idx=name)
                        self.unicode_to_idx[k] = idx
                        ln = unicode_map_line.format(idx=idx, cp=k, dsp=ch)
                        indices.append(idx)
                        unicode_map_lines.append(ln)
        self.unicode_map = tpl.format(
            indices=",\n".join(indices),
            unicode_map_lines=",\n".join(unicode_map_lines),
        )

    def _create_override(self, m: Mode, name, kc: KeyCode, skc: KeyCode):
        if skc.is_unicode:
            skc = KeyCode(f"UM({self.unicode_to_idx[skc]})")
        if skc.is_transparent:
            skc = kc
        ovr = Override(m=m, n=name, kc=kc, skc=skc)
        self.override[m][name] = ovr
        return ovr

    def _gen_override(self):
        override_line = "const key_override_t {name} = ko_make_with_layers(MOD_MASK_SHIFT, {key}, {skey}, (1 << {mode}));"
        tpl = """
        {overrides}

        const key_override_t *key_overrides[] = (const key_override_t *[]){{
            {override_names},
            NULL,
        }};
        """
        overrides = []
        override_names = []
        for m, override_per_kc in self.override.items():
            for _, override in override_per_kc.items():
                overrides.append(
                    override_line.format(
                        name=override.name,
                        key=override.kc,
                        skey=override.skc,
                        mode=m.name,
                    )
                )
                override_names.append(f"&{override.name}")
        self.override_code = tpl.format(
            overrides="\n".join(overrides),
            override_names=",\n".join(override_names),
        )

    def _create_custom_key(self, m: Mode, name, kc: KeyCode, skc: KeyCode):
        if not skc.is_unicode:
            raise Exception("a custom key must be mapped to an unicode keycode")

        if kc.has_function or skc.has_function:
            raise Exception(
                f"custom keycode cannot be created with keycode using special function (LT/OSL/...): {kc}"
            )
        custom_key_name = f"{m.name}_{name}"
        self.custom_keys[m][custom_key_name] = (kc, skc)
        return KeyCode(custom_key_name)

    def _gen_custom_keys(self):
        custom_process_tpl = """
bool process_record_user(uint16_t keycode, keyrecord_t *record) {{
        const bool key_pressed = record->event.pressed;
        const bool shifted = (get_mods() & MOD_MASK_SHIFT) != 0;
        uint16_t kc;
        uint8_t skc_idx;
        switch (keycode) {{
        default:
            return true;
        {cases}
        }}

        if (shifted) {{
            if (key_pressed) {{
                uint8_t temp_mod = get_mods();
                clear_mods();
                uint32_t skc = unicodemap_get_code_point(skc_idx);
                register_unicode(skc);
                set_mods(temp_mod);
                return false;
            }}
        }} else {{
            if (key_pressed) {{
                register_code16(kc);
            }} else {{
                unregister_code16(kc);
            }}
        }}

    return true;
}}
        """
        custom_keycode_process_tpl = """
            case {name}:
                kc = {kc};
                skc_idx = {skc_name};
                break;
        """
        custom_keycode_layer_move_tpl = """
            case {name}:
                layer_move({layer});
                return false;
                break;
        """

        self.custom_keycodes = []
        self.cases = []

        for m in Mode:
            if not self.keymaps.has_keys(m):
                continue
            ckc_name = f"CKC_LMOVE_{m.name}"
            self.custom_keycodes.append(ckc_name)
            self.cases.append(
                custom_keycode_layer_move_tpl.format(name=ckc_name, layer=m.name)
            )

        for _, ckcs in self.custom_keys.items():
            for name, (kc, skc) in ckcs.items():
                self.custom_keycodes.append(name)
                self.cases.append(
                    custom_keycode_process_tpl.format(
                        name=name, kc=kc, skc_name=self.unicode_to_idx[skc]
                    )
                )

        self.custom_process = custom_process_tpl.format(cases="\n".join(self.cases))

    def _gen_custom_autoshift(self):
        autoshift_guard = """
            if (IS_LAYER_ON({layer})) return false;
        """
        autoshift_press_user_tpl = """
        static bool _autoshift_press_user(uint16_t keycode, bool shifted, keyrecord_t *record) {{
            {guard}

            bool tap_unicode = false;
            uint16_t kc;
            uint32_t skc_or_skc_idx;

            {switch}

            if (shifted && tap_unicode) {{
                uint8_t temp_mod = get_mods();
                clear_mods();
                uint32_t skc = unicodemap_get_code_point(skc_or_skc_idx);
                register_unicode(skc);
                set_mods(temp_mod);
                return false;
            }}

            register_code16(!shifted ? kc : skc_or_skc_idx);
            return true;
        }}
        void autoshift_press_user(uint16_t keycode, bool shifted, keyrecord_t *record) {{
            if (_autoshift_press_user(keycode, shifted, record)) return;
            if (shifted) {{
                add_weak_mods(MOD_BIT(KC_LSFT));
            }}
            // & 0xFF gets the Tap key for Tap Holds, required when using Retro Shift
            register_code16((IS_RETRO(keycode)) ? keycode & 0xFF : keycode);
        }}
        """
        autoshift_press_user_switch_tpl = """
            if (IS_LAYER_ON({layer})) {{
                switch(keycode) {{
                    default:
                        return false;
                    {cases}
                }}
            }}
        """
        autoshift_user_case_tpl = """
        case {kc}:
            kc = {kc};
            skc_or_skc_idx = {skc};
            break;
        """
        autoshift_user_case_unicode_tpl = """
        case {ckc}:
            kc = {kc};
            skc_or_skc_idx = {skc};
            tap_unicode = true;
            break;
        """

        autoshift_release_user_tpl = """
        static bool _autoshift_release_user(uint16_t keycode, bool shifted, keyrecord_t *record) {{
            {guard}

            bool tap_unicode = false;
            uint16_t kc;
            uint32_t skc_or_skc_idx;

            {switch}

            if (shifted && tap_unicode) {{
                    return false;
            }}

            unregister_code16(!shifted ? kc : skc_or_skc_idx);
            return true;
        }}
        void autoshift_release_user(uint16_t keycode, bool shifted, keyrecord_t *record) {{
            if (_autoshift_release_user(keycode, shifted, record)) return;
            unregister_code16((IS_RETRO(keycode)) ? keycode & 0xFF : keycode);
        }}
        """

        cases_per_mode = defaultdict(list)
        switches_press = []
        switches_relea = []
        for m, ovrs in self.override.items():
            for _, ovr in ovrs.items():
                cases_per_mode[m].append(
                    autoshift_user_case_tpl.format(
                        kc=ovr.kc,
                        skc=ovr.skc,
                    )
                )

        # Does not work, probably because those keys are handled by the
        # process_record_user and we return false within it.
        # It is likely that the fact that we do a register_unicode there
        # make it impossible to have autoshift working.
        # I wonder whether we could re-emit the custom keycode
        # and handle it in the function
        # Maybe autoshift + override could be replaced with: https://getreuer.info/posts/keyboards/custom-shift-keys/index.html
        for m, ckcs in self.custom_keys.items():
            for name, (kc, skc) in ckcs.items():
                cases_per_mode[m].append(
                    autoshift_user_case_unicode_tpl.format(
                        ckc=name, kc=kc, skc=self.unicode_to_idx[skc]
                    )
                )

        mode_without_autoshift = [m for m in Mode if self.keymaps.has_keys(m)]
        for m, cases in cases_per_mode.items():
            mode_without_autoshift.remove(m)
            switches_press.append(
                autoshift_press_user_switch_tpl.format(
                    layer=m.name, cases="\n".join(cases)
                )
            )
            switches_relea.append(
                autoshift_press_user_switch_tpl.format(
                    layer=m.name, cases="\n".join(cases)
                )
            )

        guard = "\n".join(
            autoshift_guard.format(layer=l.name) for l in mode_without_autoshift
        )
        self.custom_autoshift = """
        {press}
        {relea}
        """.format(
            press=autoshift_press_user_tpl.format(
                guard=guard, switch="\n".join(switches_press)
            ),
            relea=autoshift_release_user_tpl.format(
                guard=guard, switch="\n".join(switches_relea)
            ),
        )

    def _alias(self, name, value: KeyCode):
        if not isinstance(value, KeyCode):
            raise Exception("alias keycode")
        if v := self.aliases.get(name):
            if v != value:
                raise Exception(f"conflict for {name}, we have {v} and {value}")
            return name
        self.aliases[name] = value
        return KeyCode(name)

    def _gen_kc(self, m: Mode, name, kc: KeyCode, skc: KeyCode):
        alias_name = f"{m.name}_{name}"
        match get_shift_mod(kc, skc):
            case ShiftMode.Default:
                if kc.is_unicode:
                    return self._alias(
                        alias_name, KeyCode(f"UM({self.unicode_to_idx[kc]})")
                    )
                return kc
            case ShiftMode.CustomKey:
                return self._create_custom_key(m, name, kc, skc)
            case ShiftMode.Override:
                self._create_override(m, name, kc, skc)
                return kc
            case ShiftMode.UnicodeMap:
                a = self._alias(
                    alias_name,
                    KeyCode(
                        "UP({}, {})".format(
                            self.unicode_to_idx[kc],
                            self.unicode_to_idx[skc],
                        ),
                    ),
                )
                return a

    def _gen(self, m: Mode):
        l = self.keymaps.add_layer(m)
        for n, coord in self.keymaps.base_keys():
            key = self.keys.get(n.raw_keycode)
            if not key:
                if m == Mode.Base:
                    l.set_key(coord, n)
                continue

            kc = copy.deepcopy(n)

            if m != Mode.Base and kc.has_function:
                kc.remove_function()

            rkc, rskc = key.get_kc(m)
            kc.replace_keycode(rkc)
            skc = KeyCode(rskc)
            final_kc = self._gen_kc(m, n.raw_keycode, kc, skc)
            l.set_key(coord, final_kc)

    def gen(self):
        extra_includes = []
        if self.host == "fr":
            extra_includes = ["keymap_french.h", "sendstring_french.h"]

        self._gen_unicode_map()
        for m in Mode:
            self._gen(m)
        self._gen_override()
        self._gen_custom_keys()
        if self.autoshift:
            self._gen_custom_autoshift()

        return self.file_tpl.format(
            extra_include="\n".join(map(lambda f: f'#include "{f}"', extra_includes)),
            custom_keycodes=",\n".join(self.custom_keycodes),
            layers=",\n".join(m.name for m in Mode if self.keymaps.has_keys(m)),
            aliases="\n".join(
                f"#define {name} {value}" for name, value in self.aliases.items()
            ),
            unicode_map=self.unicode_map,
            overrides=self.override_code,
            layouts=",\n".join(
                f"[{m.name}] = LAYOUT({self.keymaps.format(m)})"
                for m in Mode
                if self.keymaps.has_keys(m)
            ),
            custom_process=self.custom_process,
            custom_autoshift=self.autoshift and self.custom_autoshift or "",
        )


fmt_layer = """
        {}, {}, {}, {}, {}, {}, {},           {}, {}, {}, {}, {}, {}, {},
        {}, {}, {}, {}, {}, {}, {},           {}, {}, {}, {}, {}, {}, {},
        {}, {}, {}, {}, {}, {}, {},           {}, {}, {}, {}, {}, {}, {},
        {}, {}, {}, {}, {}, {},                   {}, {}, {}, {}, {}, {},
        {}, {}, {}, {}, {},         {},     {},       {}, {}, {}, {}, {},
                            {}, {}, {},     {}, {}, {}
"""


keymaps = {
    "std": {
        Mode.Base: """
        KC_ESC ,  EKC_1 ,  EKC_2 ,  EKC_3 ,  EKC_4 ,  EKC_5 , LT(Fn|KC_ESC),                               LT(Fn|KC_ESC),  EKC_6 ,  EKC_7,   EKC_8 ,  EKC_9 ,  EKC_0 , KC_INS,
        KC_TAB ,  EKC_Q ,  EKC_C ,  EKC_O ,  EKC_P ,  EKC_W , KC_DEL ,                                     KC_BSPC,  EKC_J ,  EKC_M ,  EKC_D , EKC_DK ,  EKC_Y , _______,
        KC_GRV ,  EKC_A ,  EKC_S ,  EKC_E ,  EKC_N ,  EKC_F , _______,                                     _______,  EKC_L ,  EKC_R ,  EKC_T ,  EKC_I , _______, _______,
        KC_LSFT,  EKC_Z ,  EKC_X , EKC_MNS,  EKC_V ,  EKC_B ,                                                             EKC_DOT,  EKC_H ,  EKC_G ,EKC_COMM,  EKC_K , KC_RSFT,
        KC_LCTL, _______, KC_LEFT,KC_RIGHT, KC_LGUI,          _______,                            _______,                          KC_UP , KC_DOWN, _______, _______, _______,
                                            MO(Sym), _______, _______,                            KC_LALT, KC_ENTER, EKC_SPC
        """,
        Mode.Fn: """
        KC_F1 ,  KC_F2 ,  KC_F3 ,  KC_F4 ,  KC_F5 ,  KC_F6 ,  _______,           _______,  KC_F7 ,  KC_F8 ,  KC_F9 ,  KC_F10, KC_F11 , KC_F12 ,
        _______, _______, _______, _______, _______, _______, _______,           _______, _______, _______, _______, _______, _______, _______,
        _______, _______, _______, _______, _______, _______, _______,           _______, _______, _______, _______, _______, _______, _______,
        _______, _______, _______, _______, _______, _______,                    _______, _______, _______, _______, _______, _______,
        _______, _______, UC_PREV, UC_NEXT, QK_BOOT,         _______,     _______,       _______, _______, _______, _______, _______,
                                           _______, _______, _______,     _______, _______, _______
        """,
    },
    "daedric": {
        Mode.Base: """
        KC_ESC ,  EKC_1 ,  EKC_2 ,  EKC_3 ,  EKC_4 ,  EKC_5 , LT(Fn|KC_ESC),                               LT(Fn|KC_ESC),  EKC_6 ,  EKC_7,   EKC_8 ,  EKC_9 ,  EKC_0 , KC_INS,
        KC_TAB ,  EKC_Q ,  EKC_C ,  EKC_O ,  EKC_P ,  EKC_W , KC_DEL ,                                     KC_BSPC,  EKC_J ,  EKC_M ,  EKC_D , EKC_DK ,  EKC_Y , _______,
        KC_GRV ,  EKC_A ,  EKC_S ,  EKC_E ,  EKC_N ,  EKC_F , _______,                                     _______,  EKC_L ,  EKC_R ,  EKC_T ,  EKC_I ,  LT(Media|EKC_U), _______,
        KC_LSFT,  EKC_Z ,  EKC_X , EKC_MNS,  EKC_V ,  EKC_B ,                                                             EKC_DOT,  EKC_H ,  EKC_G ,EKC_COMM,  EKC_K , KC_RSFT,
        KC_LCTL, _______, KC_LEFT,KC_RIGHT, KC_LGUI,          LGUI(KC_P),            LGUI(LSFT(KC_SPACE)),                          KC_UP , KC_DOWN, _______, _______, CKC_LMOVE_Qwerty,
                                            MO(Sym), _______, LGUI(KC_R),            KC_LALT, KC_ENTER, EKC_SPC
        """,
        Mode.Qwerty: """
        KC_ESC ,   KC_1 ,   KC_2 ,   KC_3 ,   KC_4 ,   KC_5 ,   LT(Fn|KC_ESC),     LT(Fn|KC_ESC),  KC_6 ,  KC_7 ,  KC_8 ,  KC_9, KC_0 , KC_INS,
        KC_TAB ,   KC_Q,    KC_W,    KC_E,    KC_R,    KC_T,    KC_DEL,           KC_BSPC,         KC_Y,   KC_U,   KC_I,   KC_O, KC_P, KC_BSLS,
        KC_GRV,    KC_A,    KC_S,    KC_D,    KC_F,    KC_G,    KC_EQL,           KC_MINS,         KC_H,   KC_J,   KC_K,   KC_L, LT(Media|KC_SCLN), KC_QUOT,
        KC_LSFT,   KC_Z,    KC_X,    KC_C,    KC_V,    KC_B,                                       KC_N,   KC_M,   KC_COMM,KC_DOT, KC_SLSH, KC_RSFT,
        KC_LCTL, _______,   KC_LEFT, KC_RIGHT, KC_LGUI,         LGUI(KC_P),     LGUI(LSFT(KC_SPC)),KC_UP,  KC_DOWN, KC_LBRC, KC_RBRC, CKC_LMOVE_Base,
                                               KC_SPC , KC_LCTL,LGUI(KC_R),     KC_LALT, KC_ENTER, KC_SPC
        """,
        Mode.Media: """
        _______, _______, _______, _______, _______, _______, _______,           _______, _______, _______, _______, _______, KC_PWR, QK_BOOT,
        _______, _______, _______, _______, _______, _______, _______,           _______, _______, _______, _______, _______, _______, _______,
        _______, _______, _______, _______, _______, _______, _______,           _______, _______, _______, KC_MPRV, KC_MNXT, _______, KC_MPLY,
        _______, _______, _______, _______, _______, _______,                             _______, _______, _______, _______, _______, _______,
        _______, _______, UC_PREV, UC_NEXT, _______,          _______,           _______,          KC_PGUP, KC_PGDN , _______, _______, _______,
                                            _______, _______, _______,           _______, _______, _______
        """,
        Mode.Fn: """
        KC_F1 ,  KC_F2 ,  KC_F3 ,  KC_F4 ,  KC_F5 ,  KC_F6 ,  _______,           _______,  KC_F7 ,  KC_F8 ,  KC_F9 ,  KC_F10, KC_F11 , KC_F12 ,
        _______, _______, _______, _______, _______, _______, RGB_VAI,           _______, _______, _______, _______, _______, _______, _______,
        _______, AC_TOGG, AS_TOGG, _______, _______, _______, RGB_VAD,           _______, _______, _______, _______, _______, _______, _______,
        _______, _______, _______, _______, _______, _______,                             _______, _______, _______, _______, _______, _______,
        _______, _______, _______, _______, _______,         _______,            _______,          _______, _______, _______, _______, _______,
                                           _______, _______, _______,            _______, _______, _______
        """,
    },
    "daedric_34": {
        Mode.Base: """
        _______, _______, _______, _______, _______, _______, _______,            _______, _______, _______, _______, _______, _______, _______,
        _______,  EKC_Q ,  EKC_C ,  EKC_O ,  EKC_P ,  EKC_W , _______,            _______,  EKC_J ,  EKC_M ,  EKC_D , EKC_DK ,  EKC_Y , _______,
        _______,  EKC_A ,  EKC_S ,  EKC_E ,  EKC_N ,  EKC_F , _______,            _______,  EKC_L ,  EKC_R ,  EKC_T ,  EKC_I ,  LT(Media|EKC_U), _______,
        _______,  EKC_Z ,  EKC_X , EKC_MNS,  EKC_V ,  EKC_B ,                              EKC_DOT,  EKC_H ,  EKC_G ,EKC_COMM,  EKC_K , _______,
        _______, _______, _______, _______, KC_LGUI,          _______,            _______,          _______, _______, _______, _______, CKC_LMOVE_Qwerty,
                              LT(Nav|KC_BSPC),LSFT_T(KC_ESC), _______,                    _______, LT(Nav|KC_ENTER), LT(Sym|KC_SPC)
        """,
        Mode.Qwerty: """
        _______, _______, _______, _______, _______, _______, _______,                    _______, _______, _______, _______, _______, _______, _______,
        _______,   KC_Q,    KC_W,    KC_E,    KC_R,    KC_T,  _______,                    _______, KC_Y,   KC_U,   KC_I,   KC_O, KC_P, _______,
        _______,   KC_A,LALT_T(KC_S),LCTL_T(KC_D),LSFT_T(KC_F),LGUI_T(KC_G), _______,     _______, KC_H,LSFT_T(KC_J),LCTL_T(KC_K),LALT_T(KC_L), LT(Media|KC_SCLN), _______,
        _______,   KC_Z,    KC_X,    KC_C,    KC_V,    KC_B,                                       KC_N,   KC_M,   KC_COMM,KC_DOT, KC_SLSH, _______,
        _______, _______,  _______, _______, KC_LGUI,         _______,                    _______,          _______, _______, _______, _______, CKC_LMOVE_Base,
                              LT(Nav|KC_BSPC),LSFT_T(KC_ESC), _______,                    _______, LT(Nav|KC_ENTER) , LT(SymQwerty|KC_SPC)
        """,
        Mode.SymQwerty: """
        _______, _______, _______, _______, _______, _______, _______,            _______, _______, _______, _______, _______, _______, _______,
        _______, KC_CIRC,  KC_LT ,  KC_GT , KC_DLR , KC_PERC, _______,            _______,  KC_AT , KC_AMPR, KC_ASTR, KC_QUOT, KC_GRV , _______,
        _______, KC_LCBR, KC_LPRN, KC_RPRN, KC_RCBR, KC_EQL , _______,            _______, KC_BSLS, KC_PLUS, KC_MINS, KC_SLSH, KC_DQT , _______,
        _______, KC_TILD, KC_LBRC, KC_RBRC, KC_UNDS, KC_HASH,                              KC_PIPE, KC_EXLM, KC_SCLN, KC_COLN, KC_QUES, _______,
        _______, _______, _______, _______, _______,          _______,            _______,          _______, _______, _______, _______, _______,
                                            _______, _______, _______,            _______, _______, _______
        """,
        #  Mode.Num: """
        #  _______, _______, _______, _______, _______, _______, _______,            _______, _______, _______, _______, _______, _______, _______,
        #  _______, _______, _______, _______, _______, _______, _______,            _______, _______, _______, _______, _______, _______, _______,
        #  _______, _______, _______, _______, _______, _______, _______,            _______, _______, _______, _______, _______, _______, _______,
        #  _______, _______, _______, _______, _______, _______,                              _______, _______, _______, _______, _______, _______,
        #  _______, _______, _______, _______, _______,          _______,            _______,          _______, _______, _______, _______, _______,
        #                                      _______, _______, _______,            _______, _______, _______
        #  """,
        Mode.Nav: """
        _______, _______, _______, _______, _______, _______, _______,            _______, _______, _______, _______, _______, _______, _______,
        _______, KC_TAB , KC_HOME,  KC_UP ,  KC_END, KC_PGUP,  _______,           _______, KC_PPLS,   KC_7 ,   KC_8 ,   KC_9 , _______, _______,
        _______, KC_LCAP, KC_LEFT, KC_DOWN, KC_RGHT, KC_PGDN,  _______,           _______, KC_PMNS,   KC_4 ,   KC_5 ,   KC_6 , _______, _______,
        _______, _______, _______, _______, _______, KC_DEL ,                                KC_0 ,   KC_1 ,   KC_2,    KC_3 , _______, _______,
        _______, _______,  _______, _______, KC_LGUI,         _______,            _______,          _______, _______, _______, _______, _______,
                                            _______, _______, _______,            _______, _______, _______
        """,
        Mode.Media: """
        _______, _______, _______, _______, _______, _______, _______,           _______, _______, _______, _______, _______, _______, _______,
        _______, _______, _______, _______, _______, _______, _______,           _______, _______, _______, _______, _______, KC_PWR , QK_BOOT,
        _______, _______, _______, _______, _______, _______, _______,           _______, _______, _______, KC_MPRV, KC_MNXT, _______, KC_MPLY,
        _______, _______, UC_PREV, UC_NEXT, _______, _______,                             _______, _______, _______, _______, _______, _______,
        _______, _______, _______, _______, _______,          _______,           _______,          _______, _______, _______, _______, _______,
                                            _______, _______, _______,           _______, _______, _______
        """,
        Mode.Fn: """
        _______, _______, _______, _______, _______, _______, _______,            _______, _______, _______, _______, _______, _______, _______,
        _______, AC_TOGG, _______, _______, _______, _______, _______,            _______, _______, _______, _______, _______, _______, _______,
        _______,  KC_F1 ,  KC_F2 ,  KC_F3 ,  KC_F4 ,  KC_F5 , _______,            _______,  KC_F6 ,  KC_F7 ,  KC_F8 ,  KC_F9 ,  KC_F10, _______,
        _______, _______, _______, _______, _______, _______,                               KC_F11,  KC_F12, _______, _______, _______, _______,
        _______, _______, _______, _______, _______,          _______,            _______,          _______, _______, _______, _______, _______,
                                            _______, _______, _______,            _______, _______, _______
        """,
    },
}


km = Keymaps(fmt_layer=fmt_layer, nb_keys=72)

for mode, k in keymaps[args.keymap].items():
    if mode == Mode.Base:
        km.set_base(k)
    else:
        km.add_layer(mode, k)

g = Gen(args.host, km, autoshift=args.autoshift)
r = g.gen()
print(r)
