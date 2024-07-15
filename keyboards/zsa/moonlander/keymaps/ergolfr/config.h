/* Copyright 2020 ZSA Technology Labs, Inc <@zsa>
 * Copyright 2020 Jack Humbert <jack.humb@gmail.com>
 * Copyright 2020 Christopher Courtney, aka Drashna Jael're  (@drashna) <drashna@live.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#pragma once

#define USB_SUSPEND_WAKEUP_DELAY 0

/* Set by Oryx to their default value:
 * https://github.com/qmk/qmk_firmware/blob/a4da5f219fe0f202a07afa045fc0c08f6ce1f86b/docs/features/rawhid.md#basic-configuration-basic-configuration
 */
#define RAW_USAGE_PAGE 0xFF60
#define RAW_USAGE_ID 0x61

// As long as I'm using <= 8 layers
// https://github.com/qmk/qmk_firmware/blob/a4da5f219fe0f202a07afa045fc0c08f6ce1f86b/docs/squeezing_avr.md#layers
#define LAYER_STATE_8BIT
#define RGBLIGHT_MAX_LAYERS 8

// Default animation speed
#define RGB_MATRIX_STARTUP_SPD 60

#define UNICODE_SELECTED_MODES UNICODE_MODE_LINUX, UNICODE_MODE_WINCOMPOSE, UNICODE_MODE_MACOS
