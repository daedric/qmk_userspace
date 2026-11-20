from collections import defaultdict
from dataclasses import dataclass, replace
from unicodedata import name as unicode_name

from model import TRNS, Host, Key, KeyCode, Layer, parse_layout

MOONLANDER_LAYOUT = """
        {}, {}, {}, {}, {}, {}, {},           {}, {}, {}, {}, {}, {}, {},
        {}, {}, {}, {}, {}, {}, {},           {}, {}, {}, {}, {}, {}, {},
        {}, {}, {}, {}, {}, {}, {},           {}, {}, {}, {}, {}, {}, {},
        {}, {}, {}, {}, {}, {},                   {}, {}, {}, {}, {}, {},
        {}, {}, {}, {}, {},         {},     {},       {}, {}, {}, {}, {},
                            {}, {}, {},     {}, {}, {}
"""

KEYMAP_C = """
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


@dataclass
class Coord:
    row: int
    col: int


@dataclass(frozen=True)
class KeyOverride:
    layer: Layer
    keycode: KeyCode
    shifted: KeyCode


@dataclass(frozen=True)
class CustomKeycode:
    layer: Layer
    keycode: KeyCode
    shifted_name: str


class ShiftedKeycodes:
    """Gives every ergol key its shifted keycode on a layer, through an alias, a key
    override or a custom keycode, and keeps them by their C symbol."""

    def __init__(self, unicode: dict[int, str]):
        self.unicode = unicode
        self.aliases: dict[str, str] = {}
        self.key_overrides: dict[str, KeyOverride] = {}
        self.custom_keycodes: dict[str, CustomKeycode] = {}

    def realise(
        self, layer: Layer, name: str, keycode: KeyCode, shifted: KeyCode
    ) -> KeyCode:
        symbol = f"{layer.name}_{name}"
        code_point, shifted_code_point = keycode.code_point, shifted.code_point
        if code_point is not None and shifted_code_point is not None:
            unicode_pair = (
                f"{self.unicode[code_point]}, {self.unicode[shifted_code_point]}"
            )
            return self._alias(symbol, f"UP({unicode_pair})")
        if code_point is not None and shifted.is_transparent:
            return self._alias(symbol, f"UM({self.unicode[code_point]})")
        if keycode.keycode == shifted.keycode:
            return keycode
        if code_point is None and shifted_code_point is None:
            self.key_overrides[symbol] = KeyOverride(
                layer, keycode, keycode if shifted.is_transparent else shifted
            )
            return keycode
        return self._custom_keycode(symbol, layer, keycode, shifted)

    def _alias(self, symbol: str, value: str) -> KeyCode:
        if (defined := self.aliases.setdefault(symbol, value)) != value:
            raise ValueError(f"conflict for {symbol}, we have {defined} and {value}")
        return KeyCode(symbol)

    def _custom_keycode(
        self, symbol: str, layer: Layer, keycode: KeyCode, shifted: KeyCode
    ) -> KeyCode:
        if (shifted_code_point := shifted.code_point) is None:
            raise ValueError("a custom key must be mapped to an unicode keycode")
        if keycode.tap_hold or shifted.tap_hold:
            raise ValueError(
                f"custom keycode cannot be created with keycode using special function (LT/OSL/...): {keycode.c}"
            )
        self.custom_keycodes[symbol] = CustomKeycode(
            layer, keycode, self.unicode[shifted_code_point]
        )
        return KeyCode(symbol)


def unicode_names(keys: dict[str, Key]) -> dict[int, str]:
    """Name of every code point of the keys, in table then layer order."""
    names: dict[int, str] = {}
    for key in keys.values():
        for layer in Layer:
            for keycode in key.pair(layer) or ():
                code_point = keycode.code_point
                if code_point is not None and code_point not in names:
                    name = unicode_name(chr(code_point))
                    names[code_point] = name.replace(" ", "_").replace("-", "_")
    return names


def generate(layouts: dict[Layer, str], host: Host, autoshift: bool) -> str:
    if any(KeyCode(key.base).code_point is not None for key in host.keys.values()):
        raise ValueError("At the moment base keymaps need to be basic")

    unicode = unicode_names(host.keys)
    shifted = ShiftedKeycodes(unicode)
    layers = _build_layers(layouts, host.keys, shifted)
    emitted = [
        layer
        for layer, cells in layers.items()
        if any(not cell.is_transparent for row in cells for cell in row)
    ]
    layer_moves = {f"CKC_LMOVE_{layer.name}": layer for layer in emitted}

    return KEYMAP_C.format(
        extra_include="\n".join(f'#include "{include}"' for include in host.includes),
        custom_keycodes=",\n".join([*layer_moves, *shifted.custom_keycodes]),
        layers=",\n".join(layer.name for layer in emitted),
        aliases="\n".join(
            f"#define {name} {value}" for name, value in shifted.aliases.items()
        ),
        unicode_map=_render_unicode_map(unicode),
        overrides=_render_key_overrides(shifted.key_overrides),
        layouts=",\n".join(
            f"[{layer.name}] = LAYOUT({_format_layer(layers[layer])})"
            for layer in emitted
        ),
        custom_process=_render_process_record_user(
            layer_moves, shifted.custom_keycodes
        ),
        custom_autoshift=_render_autoshift(emitted, shifted) if autoshift else "",
    )


def _build_layers(
    layouts: dict[Layer, str], keys: dict[str, Key], shifted: ShiftedKeycodes
) -> dict[Layer, list[list[KeyCode]]]:
    """Every layer: its hand-written layout, or transparent keys, under the keys the
    base layout's ergol keys type on it. On Base an ergol key keeps its tap-hold and
    the other keys are copied; on the other layers the tap-hold is dropped."""
    transparent = MOONLANDER_LAYOUT.format(*[TRNS] * MOONLANDER_LAYOUT.count("{}"))
    base = parse_layout(layouts[Layer.Base])
    layers: dict[Layer, list[list[KeyCode]]] = {}
    for layer in Layer:
        cells = parse_layout(
            transparent if layer is Layer.Base else layouts.get(layer, transparent)
        )
        for row, base_row in enumerate(base):
            for col, cell in enumerate(base_row):
                name = str(cell.keycode)
                key = keys.get(name)
                if key is None:
                    if layer is Layer.Base:
                        _place(cells, Coord(row=row, col=col), cell)
                    continue
                if (pair := key.pair(layer)) is None:
                    continue
                keycode, shifted_keycode = pair
                if layer is Layer.Base:
                    keycode = replace(cell, keycode=keycode.keycode)
                realised = shifted.realise(layer, name, keycode, shifted_keycode)
                _place(cells, Coord(row=row, col=col), realised)
        layers[layer] = cells
    return layers


def _place(cells: list[list[KeyCode]], coord: Coord, keycode: KeyCode):
    if keycode.is_transparent:
        return
    previous = cells[coord.row][coord.col]
    if not previous.is_transparent and previous.c != keycode.c:
        raise ValueError(f"Key at {coord} is not transparent: {previous.c}")
    cells[coord.row][coord.col] = KeyCode(keycode.c)


def _format_layer(cells: list[list[KeyCode]]) -> str:
    width = max(len(cell.c) for row in cells for cell in row)
    # A cell that still carries its layout tap-hold (a hand-written key) is emitted
    # unpadded: the committed keymaps are aligned that way.
    keycodes = [
        cell.c if cell.tap_hold else f"{cell.c:^{width}}"
        for row in cells
        for cell in row
    ]
    layout = MOONLANDER_LAYOUT.format(*keycodes)
    return f"\n// clang-format off\n{layout}\n// clang-format on\n"


def _render_unicode_map(unicode: dict[int, str]) -> str:
    template = """
            enum unicode_names {{
                {indices},
            }};


            const uint32_t PROGMEM unicode_map[] = {{
                {unicode_map_lines},
            }};
        """
    return template.format(
        indices=",\n".join(unicode.values()),
        unicode_map_lines=",\n".join(
            f"[{name}]  = {code_point:#06x} /* {chr(code_point)} */"
            for code_point, name in unicode.items()
        ),
    )


def _render_key_overrides(key_overrides: dict[str, KeyOverride]) -> str:
    key_override_tpl = "const key_override_t {name} = ko_make_with_layers(MOD_MASK_SHIFT, {key}, {skey}, (1 << {mode}));"
    template = """
        {overrides}

        const key_override_t *key_overrides[] = (const key_override_t *[]){{
            {override_names},
            NULL,
        }};
        """
    return template.format(
        overrides="\n".join(
            key_override_tpl.format(
                name=name,
                key=override.keycode.c,
                skey=override.shifted.c,
                mode=override.layer.name,
            )
            for name, override in key_overrides.items()
        ),
        override_names=",\n".join(f"&{name}" for name in key_overrides),
    )


def _render_process_record_user(
    layer_moves: dict[str, Layer], custom_keycodes: dict[str, CustomKeycode]
) -> str:
    template = """
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
    custom_keycode_case_tpl = """
            case {name}:
                kc = {kc};
                skc_idx = {skc_name};
                break;
        """
    layer_move_case_tpl = """
            case {name}:
                layer_move({layer});
                return false;
                break;
        """
    cases = [
        layer_move_case_tpl.format(name=name, layer=layer.name)
        for name, layer in layer_moves.items()
    ] + [
        custom_keycode_case_tpl.format(
            name=name, kc=custom.keycode.c, skc_name=custom.shifted_name
        )
        for name, custom in custom_keycodes.items()
    ]
    return template.format(cases="\n".join(cases))


def _render_autoshift(emitted: list[Layer], shifted: ShiftedKeycodes) -> str:
    guard_tpl = """
            if (IS_LAYER_ON({layer})) return false;
        """
    press_user_tpl = """
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
    switch_tpl = """
            if (IS_LAYER_ON({layer})) {{
                switch(keycode) {{
                    default:
                        return false;
                    {cases}
                }}
            }}
        """
    case_tpl = """
        case {kc}:
            kc = {kc};
            skc_or_skc_idx = {skc};
            break;
        """
    unicode_case_tpl = """
        case {ckc}:
            kc = {kc};
            skc_or_skc_idx = {skc};
            tap_unicode = true;
            break;
        """
    release_user_tpl = """
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
    template = """
        {press}
        {relea}
        """

    cases: dict[Layer, list[str]] = defaultdict(list)
    for override in shifted.key_overrides.values():
        cases[override.layer].append(
            case_tpl.format(kc=override.keycode.c, skc=override.shifted.c)
        )

    # Does not work, probably because those keys are handled by the
    # process_record_user and we return false within it.
    # It is likely that the fact that we do a register_unicode there
    # make it impossible to have autoshift working.
    # I wonder whether we could re-emit the custom keycode
    # and handle it in the function
    # Maybe autoshift + override could be replaced with: https://getreuer.info/posts/keyboards/custom-shift-keys/index.html
    for name, custom in shifted.custom_keycodes.items():
        cases[custom.layer].append(
            unicode_case_tpl.format(
                ckc=name, kc=custom.keycode.c, skc=custom.shifted_name
            )
        )

    switches = "\n".join(
        switch_tpl.format(layer=layer.name, cases="\n".join(layer_cases))
        for layer, layer_cases in cases.items()
    )
    guard = "\n".join(
        guard_tpl.format(layer=layer.name) for layer in emitted if layer not in cases
    )
    return template.format(
        press=press_user_tpl.format(guard=guard, switch=switches),
        relea=release_user_tpl.format(guard=guard, switch=switches),
    )
