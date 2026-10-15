# US Programming for Android

A physical keyboard layout package for Android 8.0+ and USB/Bluetooth keyboards.
Keep Gboard (or your usual IME) selected. No root, permissions, network access,
typing service, or input logging. There is no launcher activity.

Package ID: `dev.chad.usproglayout`. Layout ID: `us_prog_terminal`.
These legacy Android identifiers are retained for seamless installed updates;
all project and resource names use US Programming.
The only included KCM is `app/src/main/res/raw/us_programming.kcm`.

## Install

Install `us-programming-debug.apk` as an update to the existing package:

```sh
adb install -r us-programming-debug.apk
```

Select **US Programming** under Settings → Physical keyboard → your keyboard's
layout settings. Settings names vary by device. Reopen Settings or reconnect the
keyboard if the layout list has not refreshed. The old experimental layouts are
no longer included.

To undo, choose the ordinary English (US) physical layout, then uninstall this
package if desired.

## Mapping

Normal and Shift typing use US QWERTY. Both Alt keys select the programming layer;
physical left Alt is reported as right Alt/AltGr. Caps Lock affects normal letters,
not programming symbols.

```text
Alt:
  w ~    e \\    r {    t }    y #    u 7    i 8    o 9    p *
  [ /    ] `
  a (    s )    d =    f _    g &    h +    j 4    k 5    l 6
  ; -    ' ,
  z [    x ]    c $    v |    b !    n 0    m 1    , 2    . 3    / .

Shift+Alt:
  k %    l ^    , @    . #
```

Other three-level keys have no fourth-level character, matching the original layout. Two-level keys retain their normal/Shift
characters with Alt held. Alt+Space inserts a space.

Terminal shortcuts:

- **Ctrl+; → native Escape**.
- **Ctrl+. → U+E000**, via a spare `BUTTON_16` key that consumes Ctrl.
- Ctrl+Shift, Ctrl+Alt, and Ctrl+Meta do not select these shortcuts.

For Ctrl+. to insert the previous command's last word in zsh:

```zsh
bindkey -M viins $'\ue000' insert-last-word
```

Outside configured apps, Ctrl+. may insert a private-use glyph.

## Limitations

Android-reserved shortcuts and apps handling raw key events can take precedence.
Left Alt no longer acts as terminal Meta. Avoid holding both Alt keys at once:
they share one logical modifier, so releasing either may clear its state.
Unusual keyboards may need different scan/usage mappings.

The layout overlays the device's existing key map. Enter, Tab, Backspace,
navigation, function keys, and numpad keys are not redefined. Ctrl+Space and
Meta+Space preserve Android's language-switch/Search fallback actions.

The user verified the US Programming update on their device. Automated tests
are desktop models, not Android native-parser/runtime tests.

## Build and test

Requires JDK 17, Android SDK platform 35, and internet access for the first build.

```sh
export JAVA_HOME=/path/to/jdk-17
export ANDROID_HOME=/path/to/android-sdk
./gradlew assembleDebug lintDebug
python3 tests/check_layout.py
python3 tests/check_terminal.py
cp app/build/outputs/apk/debug/app-debug.apk us-programming-debug.apk
```

Tests require Python 3. They check ordinary character behavior against explicit
expectations, model terminal shortcut actions, and
check discovery metadata and the built APK's KCM resources.

Temporary build tools on this machine:

```sh
JAVA_HOME=/tmp/us-prog-jdk ANDROID_HOME=/tmp/us-prog-android-sdk \
  ./gradlew --no-daemon assembleDebug lintDebug
```

## Source files

- `app/src/main/res/raw/us_programming.kcm`: the active character map.
- `app/src/main/res/xml/keyboard_layouts.xml`: layout discovery.
- `app/src/main/res/xml-v34/keyboard_layouts.xml`: Android 14+ metadata.
- `app/src/main/AndroidManifest.xml`: physical-layout provider declaration.
- `tests/`: character mapping, shortcut, and package checks.
