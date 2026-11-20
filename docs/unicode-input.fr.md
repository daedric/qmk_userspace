# Saisie Unicode sous Linux (X11 et Wayland)

[English version](unicode-input.md)

Les keymaps tapent tout caractère absent d'un clavier US (é, œ, …, —, ß, …)
sous forme de point de code Unicode. Sous Linux, le firmware ne peut pas
produire le caractère lui-même : il tape une séquence de touches qu'une
**méthode de saisie** (input method) sur l'hôte transforme en caractère. Cette
page décrit ce contrat, la mise en place sur n'importe quelle distribution, et
la configuration NixOS utilisée sur babasse.

## Le contrat entre le firmware et l'hôte

En `UNICODE_MODE_LINUX` (choisi au démarrage par la détection d'OS dans
`daedric.c`, LED 4 allumée), QMK tape, pour chaque caractère
(`quantum/unicode/unicode.c` dans qmk_firmware) :

1. `Ctrl+Shift+U` (`UNICODE_KEY_LNX`)
2. le point de code en hexadécimal, en minuscules, sans zéros de tête (`e9`
   pour é)
3. `Espace`

Verr. Maj est relâché pendant la séquence puis rétabli ; les modificateurs
tenus sont relâchés pendant la séquence puis ré-enregistrés.
`UC_NEXT` / `UC_PREV` (couche Media) font défiler les modes listés dans
`UNICODE_SELECTED_MODES` (Linux, WinCompose, macOS).

Toute méthode de saisie qui gère « Ctrl+Shift+U, hexa, Espace » convient :

| Méthode de saisie | Gestionnaire | Remarques |
|---|---|---|
| fcitx5 | addon intégré `unicode`, `DirectUnicodeMode` (par défaut `Control+Shift+U`) ; Espace ou Entrée valide | utilisée ici |
| IBus | saisie Unicode intégrée (`Ctrl+Shift+U`) | GNOME la démarre ; rien ne la démarre sous sway |

Sans méthode de saisie :

- **Wayland** : personne n'interprète la séquence ; l'application reçoit
  `Ctrl+Shift+U` (un raccourci, ou `^U` dans un terminal, qui efface la ligne)
  puis les chiffres hexa comme du texte.
- **X11** (non mesuré ici) : les applications GTK la gèrent via le contexte de
  saisie intégré de GTK (`GtkIMContextSimple`) ; les autres toolkits ont besoin
  d'une méthode de saisie.

## Grands principes (toute distribution)

1. **Une seule méthode de saisie, démarrée avec la session.** Installer
   fcitx5 et lancer `fcitx5 -d --replace` avec la session graphique : les
   environnements de bureau exécutent son entrée d'autostart XDG
   (`org.fcitx.Fcitx5.desktop`) ; les compositeurs nus comme sway ou i3 ont
   besoin d'une ligne `exec`. Ne pas en laisser une seconde configurée (GNOME
   choisit IBus par défaut).
2. **Les variables d'environnement dépendent du serveur d'affichage.**
   - Wayland : `XMODIFIERS=@im=fcitx` (pour les clients XWayland) et **pas** de
     `GTK_IM_MODULE` / `QT_IM_MODULE`. Les clients natifs joignent fcitx5 via
     le protocole `text-input-v3`, que le compositeur relaie à fcitx5 via
     `input-method-v2`
     ([wiki fcitx : Using Fcitx 5 on Wayland](https://fcitx-im.org/wiki/Using_Fcitx_5_on_Wayland)).
   - X11 : `XMODIFIERS=@im=fcitx`, `GTK_IM_MODULE=fcitx`, `QT_IM_MODULE=fcitx`,
     plus les modules `fcitx5-gtk` et `fcitx5-qt`.
3. **Le compositeur doit relayer les méthodes de saisie.** sway et Hyprland
   implémentent `input-method-v2` et `text-input-v3`. sway 1.12 a un bug : un
   client qui crée son objet text-input après avoir reçu le focus clavier
   (Alacritty, toute application winit) n'atteint jamais la méthode de saisie
   tant que le focus ne part pas puis ne revient pas. Le correctif est
   [swaywm/sway#9255](https://github.com/swaywm/sway/pull/9255), pas encore
   fusionné ; sans lui, passer une fois sur une autre fenêtre puis revenir.
4. **Chromium et Electron ont besoin d'un flag sous Wayland** :
   `--enable-wayland-ime`. Chrome 157 parle alors `text-input-v3` sans
   `--wayland-text-input-version=3`. Sans le flag, Chrome ne crée aucun objet
   text-input.
5. **Vérifier** : `fcitx5-diagnose` décrit l'environnement et les frontends ;
   dans un champ GTK, `Ctrl+Shift+U` doit afficher une pré-édition `U+`.

Mesuré dans un sway 1.12 headless avec fcitx5 5.1.23, en rejouant avec
`wtype` la séquence du firmware pour é, œ et … :

| Client | Sans méthode de saisie | fcitx5, sway 1.12 | fcitx5, sway 1.12 + #9255 |
|---|---|---|---|
| Champ GTK3 | `e9 153 2026` | `éœ…` | `éœ…` |
| Firefox 160 | `e9 153 2026` | `éœ…` | non testé |
| `QLineEdit` Qt6 | non testé | non testé | `éœ…` |
| foot, kitty | non testé | `éœ…` | `éœ…` |
| Alacritty 0.17 | non testé | perdu (`^U` efface la ligne) | `éœ…` |
| Chromium/Chrome avec `--enable-wayland-ime` | | pré-édition `U+2026`, puis `…` (¹) | text-input-v3 activé (²) |

(¹) Chromium dans un compositeur headless est instable : les deux premières
séquences de ce run ont été perdues, cause non isolée. (²) `WAYLAND_DEBUG`
montre Chrome recevant `text_input.enter` et envoyant `enable` ; le texte de la
page n'a pas été capturé.

## NixOS

La configuration est dans
[nixos-setup](https://code.ohmycode.dev/ts/nixos-setup) (Wayland/sway) :

```nix
# modules/nixsystem/environments/gui/wm.nix
i18n.inputMethod = {
  enable = true;
  type = "fcitx5";              # remplace le défaut ibus du module GNOME
  fcitx5.waylandFrontend = true; # pas de GTK_IM_MODULE / QT_IM_MODULE
};
# les wrappers nixpkgs de Chrome, Slack et Discord ajoutent alors --enable-wayland-ime
environment.sessionVariables.NIXOS_OZONE_WL = "1";
```

```nix
# home-manager, wayland.windowManager.sway.config.startup
{ command = "${osConfig.i18n.inputMethod.package}/bin/fcitx5 -d --replace"; }
```

- `signal-desktop` ignore `NIXOS_OZONE_WL` et n'accepte plus
  `commandLineArgs` : il est enveloppé avec `--enable-wayland-ime` dans
  `modules/nixsystem/environments/gui/apps.nix`.
- sway est compilé avec le patch #9255 dans
  `modules/nixsystem/packages/packages/sway-unwrapped.nix`.
- Les variables n'atteignent qu'une nouvelle session : se déconnecter de sway
  puis se reconnecter après `nixos-rebuild switch`.

Pour une session X11 sous NixOS : `fcitx5.waylandFrontend = false` (le module
définit alors `GTK_IM_MODULE` et `QT_IM_MODULE`), ajouter `fcitx5-gtk` à
`fcitx5.addons`, et laisser la session exécuter l'entrée d'autostart
(`services.xserver.desktopManager.runXdgAutostartIfNone = true` pour un
gestionnaire de fenêtres nu).

## Dépannage

| Symptôme | Cause |
|---|---|
| des chiffres hexa apparaissent (`e9`) | aucune méthode de saisie active, ou l'application ne lui parle pas |
| la ligne s'efface dans un terminal | `Ctrl+Shift+U` est arrivé au terminal comme `^U` : mêmes causes |
| marche après être passé sur une autre fenêtre et revenu | sway sans #9255 |
| marche partout sauf Chrome / Electron | `--enable-wayland-ime` manquant |
| marche seulement dans les applis GTK, sous X11 | gestionnaire intégré de GTK, aucune méthode de saisie active |
