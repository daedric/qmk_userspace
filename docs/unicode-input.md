# Unicode input on Linux (X11 and Wayland)

[Version française](unicode-input.fr.md)

The keymaps type every character that is not on a US keyboard (é, œ, …, —, ß, …)
as a Unicode code point. On Linux the firmware cannot produce the character
itself: it types a key sequence that an **input method** on the host turns into
the character. This page explains that contract, the setup on any distribution,
and the NixOS setup used on babasse.

## The contract between the firmware and the host

With `UNICODE_MODE_LINUX` (selected at boot from OS detection in `daedric.c`,
LED 4 lit), QMK types, for each character
(`quantum/unicode/unicode.c` in qmk_firmware):

1. `Ctrl+Shift+U` (`UNICODE_KEY_LNX`)
2. the hexadecimal code point, lowercase, without leading zeros (`e9` for é)
3. `Space`

Caps Lock is released for the sequence and restored afterwards; held
modifiers are cleared for the sequence and re-registered after it. `UC_NEXT` / `UC_PREV` (Media layer) cycle through the
modes listed in `UNICODE_SELECTED_MODES` (Linux, WinCompose, macOS).

Any input method that implements "Ctrl+Shift+U, hex, Space" works:

| Input method | Handler | Notes |
|---|---|---|
| fcitx5 | built-in `unicode` addon, `DirectUnicodeMode` (default `Control+Shift+U`); Space or Return commits | used here |
| IBus | built-in Unicode entry (`Ctrl+Shift+U`) | GNOME starts it; nothing does under sway |

Without an input method:

- **Wayland**: nothing interprets the sequence; the application receives
  `Ctrl+Shift+U` (a shortcut, or `^U` in a terminal, which erases the line) and
  then the hex digits as text.
- **X11** (not measured here): GTK applications handle it through GTK's
  built-in input context (`GtkIMContextSimple`); other toolkits need an input
  method.

## General principles (any distribution)

1. **One input method, started with the session.** Install fcitx5 and start
   `fcitx5 -d --replace` with the graphical session: desktop environments run
   its XDG autostart entry (`org.fcitx.Fcitx5.desktop`); bare compositors such
   as sway or i3 need an `exec` line. Do not leave a second one configured
   (GNOME selects IBus by default).
2. **Environment variables depend on the display server.**
   - Wayland: `XMODIFIERS=@im=fcitx` (for XWayland clients) and **no**
     `GTK_IM_MODULE` / `QT_IM_MODULE`. Native clients reach fcitx5 through the
     `text-input-v3` protocol, relayed by the compositor to fcitx5 over
     `input-method-v2`
     ([fcitx wiki: Using Fcitx 5 on Wayland](https://fcitx-im.org/wiki/Using_Fcitx_5_on_Wayland)).
   - X11: `XMODIFIERS=@im=fcitx`, `GTK_IM_MODULE=fcitx`, `QT_IM_MODULE=fcitx`,
     plus the `fcitx5-gtk` and `fcitx5-qt` modules.
3. **The compositor must relay input methods.** sway and Hyprland implement
   `input-method-v2` and `text-input-v3`. sway 1.12 has a bug: a client that
   creates its text-input object after it got keyboard focus (Alacritty, every
   winit application) never reaches the input method until focus leaves and
   comes back. The fix is
   [swaywm/sway#9255](https://github.com/swaywm/sway/pull/9255), not merged
   yet; without it, switch to another window and back once.
4. **Chromium and Electron need a flag on Wayland**: `--enable-wayland-ime`.
   Chrome 157 then speaks `text-input-v3` without
   `--wayland-text-input-version=3`. Without the flag Chrome creates no
   text-input object at all.
5. **Check**: `fcitx5-diagnose` reports the environment and the frontends; in
   a GTK entry, `Ctrl+Shift+U` must show a `U+` preedit.

What was measured, in a headless sway 1.12 with fcitx5 5.1.23, by replaying
the firmware sequence for é, œ and … with `wtype`:

| Client | No input method | fcitx5, sway 1.12 | fcitx5, sway 1.12 + #9255 |
|---|---|---|---|
| GTK3 entry | `e9 153 2026` | `éœ…` | `éœ…` |
| Firefox 160 | `e9 153 2026` | `éœ…` | not run |
| Qt6 `QLineEdit` | not run | not run | `éœ…` |
| foot, kitty | not run | `éœ…` | `éœ…` |
| Alacritty 0.17 | not run | lost (`^U` erases the line) | `éœ…` |
| Chromium/Chrome with `--enable-wayland-ime` | | `U+2026` preedit, then `…` (¹) | text-input-v3 enabled (²) |

(¹) Chromium in a headless compositor is flaky: the first two sequences of
that run were lost, cause not isolated. (²) `WAYLAND_DEBUG` shows Chrome
receiving `text_input.enter` and sending `enable`; the page text was not
captured.

## NixOS

The configuration lives in
[nixos-setup](https://code.ohmycode.dev/ts/nixos-setup) (Wayland/sway):

```nix
# modules/nixsystem/environments/gui/wm.nix
i18n.inputMethod = {
  enable = true;
  type = "fcitx5";              # overrides the ibus default of the GNOME module
  fcitx5.waylandFrontend = true; # no GTK_IM_MODULE / QT_IM_MODULE
};
# nixpkgs' Chrome, Slack and Discord wrappers then add --enable-wayland-ime
environment.sessionVariables.NIXOS_OZONE_WL = "1";
```

```nix
# home-manager, wayland.windowManager.sway.config.startup
{ command = "${osConfig.i18n.inputMethod.package}/bin/fcitx5 -d --replace"; }
```

- `signal-desktop` ignores `NIXOS_OZONE_WL` and no longer accepts
  `commandLineArgs`: it is wrapped with `--enable-wayland-ime` in
  `modules/nixsystem/environments/gui/apps.nix`.
- sway is built with the #9255 patch in
  `modules/nixsystem/packages/packages/sway-unwrapped.nix`.
- The variables only reach a new session: log out of sway and back in after
  `nixos-rebuild switch`.

For an X11 session on NixOS, use `fcitx5.waylandFrontend = false` (the module
then sets `GTK_IM_MODULE` and `QT_IM_MODULE`), add `fcitx5-gtk` to
`fcitx5.addons`, and let the session run the autostart entry
(`services.xserver.desktopManager.runXdgAutostartIfNone = true` for a bare
window manager).

## Troubleshooting

| Symptom | Cause |
|---|---|
| hex digits appear (`e9`) | no input method running, or the application does not talk to it |
| the line is erased in a terminal | `Ctrl+Shift+U` reached the terminal as `^U`: same causes |
| works after switching windows and back | sway without #9255 |
| works everywhere except Chrome / Electron | missing `--enable-wayland-ime` |
| works in GTK apps only, on X11 | GTK's built-in handler, no input method running |
