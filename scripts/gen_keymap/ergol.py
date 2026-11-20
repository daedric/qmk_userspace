from model import Host, Key

HOSTS = {
    "us": Host(
        keys={
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
    ),
    "fr": Host(
        keys={
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
        includes=("keymap_french.h", "sendstring_french.h"),
    ),
}
