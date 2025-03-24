#include "color.h"
#include "quantum.h"
#include QMK_KEYBOARD_H

#include "version.h"
#include "config.h"

static void set_led_for_input_mode(uint8_t input_mode);
static void init_led_for_input_mode(void);

void keyboard_post_init_user(void) {
    /* debug_enable = true; */
    /* debug_matrix   = true; */
    /* debug_keyboard = true; */
    // debug_mouse=true;

    init_led_for_input_mode();
}

static void init_led_for_input_mode(void) {
    uint8_t mode;
    switch (detected_host_os()) {
        case OS_UNSURE:
        case OS_LINUX:
            mode = UNICODE_MODE_LINUX;
            break;
        case OS_WINDOWS:
            mode = UNICODE_MODE_WINCOMPOSE;
            break;
        case OS_MACOS:
        case OS_IOS:
            mode = UNICODE_MODE_MACOS;
            break;
    }

    set_unicode_input_mode(mode);
    set_led_for_input_mode(mode);
}

#define HSV_C(h, s, v) ({h, s, v})
#define BLACK HSV_C(0, 0, 0)
#define GREEN HSV_C(0x55, 0xFF, 0xFF)
#define PURPL HSV_C(0xBF, 0xFF, 0xFF)
#define RED HSV_C(0x0, 0xFF, 0xFF)
#define GOLD HSV_C(0x24, 0xFF, 0xFF)
#define WHITE HSV_C(0x0, 0x0, 0xFF)
#define ORANG HSV_C(0x15, 0xFF, 0xFF)
#define BLUE HSV_C(0xAC, 0xFF, 0xFF)

enum layers {
    Base,
    Qwerty,
    DK,
    Sym,
    SymQwerty,
    Nav,
    Media,
    Fn,
};

layer_state_t layer_state_set_user(layer_state_t state) {
    if (IS_LAYER_ON_STATE(state, Base)) {
        // XXX: todo
    } else if (IS_LAYER_ON_STATE(state, Qwerty)) {
        state = update_tri_layer_state(state, SymQwerty, Nav, Fn);
    }

    return state;
}

const uint8_t PROGMEM ledmap[][RGB_MATRIX_LED_COUNT][3] = {
    [Base]      = {LED_LAYOUT(
        // clang-format off
        BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, GREEN,           GREEN, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,
        BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,           BLACK, BLACK, BLACK, BLACK, GOLD , BLACK, BLACK,
        BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,           BLACK, BLACK, BLACK, BLACK, BLACK, RED  , BLACK,
        BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,                         BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,
        BLACK, BLACK, BLACK, BLACK, BLACK,         BLACK,     BLACK,             BLACK, BLACK, BLACK, BLACK, GREEN,
                                    PURPL, BLACK, BLACK,      BLACK, BLACK, PURPL
        // clang-format on
        )},
         [Qwerty] = {LED_LAYOUT(
        // clang-format off
        BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,           BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,
        BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,           BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,
        BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,           BLACK, BLACK, BLACK, BLACK, BLACK, RED  , BLACK,
        BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,                         BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,
        BLACK, BLACK, BLACK, BLACK, BLACK,         BLACK,     BLACK,             BLACK, BLACK, BLACK, BLACK, PURPL,
                                    BLACK, BLACK, BLACK,      BLACK, BLACK, BLACK
        // clang-format on
        )},
         [SymQwerty] = {LED_LAYOUT(
        // clang-format off
        BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,           BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,
        BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,           BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,
        BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,           BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,
        BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,                         BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,
        BLACK, BLACK, BLACK, BLACK, BLACK,         BLACK,     BLACK,             BLACK, BLACK, BLACK, BLACK, BLACK,
                                    BLACK, BLACK, BLACK,      BLACK, BLACK, BLACK
        // clang-format on
        )},
         [Nav] = {LED_LAYOUT(
        // clang-format off
        BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,           BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,
        BLACK, BLACK, BLACK, GREEN, BLACK, BLACK, BLACK,           BLACK, BLACK, ORANG, ORANG, ORANG, BLACK, BLACK,
        BLACK, GOLD , GREEN, GREEN, GREEN, BLACK, BLACK,           BLACK, BLACK, ORANG, ORANG, ORANG, BLACK, BLACK,
        BLACK, BLACK, BLACK, BLUE , BLACK, RED  ,                         WHITE, ORANG, ORANG, ORANG, BLACK, BLACK,
        BLACK, BLACK, BLACK, BLACK, BLACK,         BLACK,     BLACK,             BLACK, BLACK, BLACK, BLACK, BLACK,
                                    BLACK, BLACK, BLACK,      BLACK, BLACK, BLACK
        // clang-format on
        )},
         [DK] = {LED_LAYOUT_ALL(BLACK)},
    [Sym]       = {LED_LAYOUT_ALL(BLACK)},
    [Media]     = {LED_LAYOUT(
        // clang-format off
        BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,           BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,
        BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,           BLACK, BLACK, BLACK, BLACK, BLACK, RED  , ORANG,
        BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,           BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,
        BLACK, BLACK, RED  , RED  , BLACK, BLACK,                         BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,
        BLACK, BLACK, BLACK, BLACK, BLACK,         BLACK,     BLACK,             BLACK, BLACK, BLACK, BLACK, BLACK,
                                    BLACK, BLACK, BLACK,      BLACK, BLACK, BLACK
        // clang-format on
        )},
        [Fn] = {LED_LAYOUT(
        // clang-format off
        BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,           BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,
        BLACK, RED  , BLACK, BLACK, BLACK, BLACK, BLACK,           BLACK, BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,
        BLACK, GREEN, GREEN, GREEN, GREEN, GREEN, BLACK,           BLACK, GREEN, GREEN, GREEN, GREEN, GREEN, BLACK,
        BLACK, BLACK, BLACK, BLACK, BLACK, BLACK,                         GREEN, GREEN, BLACK, BLACK, BLACK, BLACK,
        BLACK, BLACK, BLACK, BLACK, BLACK,         BLACK,     BLACK,             BLACK, BLACK, BLACK, BLACK, BLACK,
                                    BLACK, BLACK, BLACK,      BLACK, BLACK, BLACK
        // clang-format on
        )},
};

void set_layer_color(int layer) {
    for (int i = 0; i < RGB_MATRIX_LED_COUNT; i++) {
        HSV hsv = {
            .h = pgm_read_byte(&ledmap[layer][i][0]),
            .s = pgm_read_byte(&ledmap[layer][i][1]),
            .v = pgm_read_byte(&ledmap[layer][i][2]),
        };
        if (!hsv.h && !hsv.s && !hsv.v) {
            rgb_matrix_set_color(i, 0, 0, 0);
        } else {
            RGB   rgb = hsv_to_rgb(hsv);
            float f   = (float)rgb_matrix_config.hsv.v / UINT8_MAX;
            rgb_matrix_set_color(i, f * rgb.r, f * rgb.g, f * rgb.b);
        }
    }

    // Toggle reg/green depending on whether the autocorrect is on or off
    if (IS_LAYER_ON(Fn)) {
        RGB   rgb = autocorrect_is_enabled() ? hsv_to_rgb((HSV)DEPAREN(GREEN)) : hsv_to_rgb((HSV)DEPAREN(RED));
        float f   = (float)rgb_matrix_config.hsv.v / UINT8_MAX;
        rgb_matrix_set_color(6, f * rgb.r, f * rgb.g, f * rgb.b);

        /* rgb = get_autoshift_state() ? hsv_to_rgb((HSV)DEPAREN(GREEN)) : hsv_to_rgb((HSV)DEPAREN(RED)); */
        /* f   = (float)rgb_matrix_config.hsv.v / UINT8_MAX; */
        /* rgb_matrix_set_color(12, f * rgb.r, f * rgb.g, f * rgb.b); */
    }
}

bool rgb_matrix_indicators_user(void) {
    if (keyboard_config.disable_layer_led) {
        return false;
    }

    int layer = biton32(layer_state);
    set_layer_color(layer);

    ML_LED_1(false);
    ML_LED_2(false);
    ML_LED_3(false);

    switch (layer) {
        case 0:
            ML_LED_1(true);
            break;
        case 1:
            ML_LED_2(true);
            break;
        case 2:
            ML_LED_1(true);
            ML_LED_2(true);
            break;
        case 3:
            ML_LED_3(true);
            break;
        case 4:
            ML_LED_1(true);
            ML_LED_3(true);
            break;
        case 5:
            ML_LED_2(true);
            ML_LED_3(true);
            break;
        case 6:
            ML_LED_1(true);
            ML_LED_2(true);
            ML_LED_3(true);
            break;
    }

    return true;
}

static void set_led_for_input_mode(uint8_t input_mode) {
    ML_LED_4(false);
    ML_LED_5(false);
    ML_LED_6(false);
    switch (input_mode) {
        default:
            ML_LED_4(true);
            ML_LED_5(true);
            ML_LED_6(true);
            break;
        case UNICODE_MODE_LINUX:
            ML_LED_4(true);
            break;
        case UNICODE_MODE_WINCOMPOSE:
        case UNICODE_MODE_WINDOWS:
            ML_LED_5(true);
            break;
        case UNICODE_MODE_MACOS:
            ML_LED_6(true);
            break;
    }
}

void unicode_input_mode_set_user(uint8_t input_mode) {
    set_led_for_input_mode(input_mode);
}

void housekeeping_task_user(void) {
    if (!IS_LAYER_ON(Qwerty)) {
        if (!is_transport_connected()) {
            layer_move(Qwerty);
        }
    }
}

void suspend_power_down_user(void) {
    for (int i = 0; i < 10; i++) {
        ML_LED_1(false);
        ML_LED_2(false);
        ML_LED_3(false);
        ML_LED_4(false);
        ML_LED_5(false);
        ML_LED_6(false);
        wait_ms(25);
    }
}

void suspend_wakeup_init_user(void) {
    init_led_for_input_mode();
    rgb_matrix_indicators_user();
}
