# US Programming for Android

A physical keyboard layout package for Android 8.0+ and USB/Bluetooth keyboards.
Keep Gboard (or your usual IME) selected. No root, permissions, network access,
typing service, or input logging. There is no launcher activity.

Package ID: `me.voegele.chad.usproglayout`.

## Install

Install `us-programming-debug.apk`:

```sh
adb install -r us-programming-debug.apk
```

Select **US Programming** under Settings → Physical keyboard → your keyboard's
layout settings. Settings names vary by device. Reopen Settings or reconnect the
keyboard if the layout list has not refreshed.

To undo, choose the ordinary English (US) physical layout, then uninstall this
package if desired.

## Mapping

Each view shows the characters produced at the same physical key positions.
`·` means no character. Space inserts a space in all four views.

### No modifiers

```text
`  1  2  3  4  5  6  7  8  9  0  -  =
   q  w  e  r  t  y  u  i  o  p  [  ]  \
    a  s  d  f  g  h  j  k  l  ;  '
     z  x  c  v  b  n  m  ,  .  /
```

### Shift

```text
~  !  @  #  $  %  ^  &  *  (  )  _  +
   Q  W  E  R  T  Y  U  I  O  P  {  }  |
    A  S  D  F  G  H  J  K  L  :  "
     Z  X  C  V  B  N  M  <  >  ?
```

### Alt

```text
`  1  2  3  4  5  6  7  8  9  0  -  =
   q  ~  \  {  }  #  7  8  9  *  /  `  \
    (  )  =  _  &  +  4  5  6  -  ,
     [  ]  $  |  !  0  1  2  3  .
```

### Shift+Alt

```text
~  !  @  #  $  %  ^  &  *  (  )  _  +
   Q  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  |
    ·  ·  ·  ·  ·  ·  ·  %  ^  ·  ·
     ·  ·  ·  ·  ·  ·  ·  @  #  ·
```

Both Alt keys select the programming layer; physical left Alt is reported as
right Alt/AltGr. Caps Lock affects normal letters, not programming symbols.

### Terminal shortcuts

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
Left Alt acts as AltGr rather than terminal Meta. Avoid holding both Alt keys at
once: they share one logical modifier, so releasing either may clear its state.
Unusual keyboards may need different scan/usage mappings.

The layout overlays the device's existing key map. Enter, Tab, Backspace,
navigation, function keys, and numpad keys are not redefined. Ctrl+Space and
Meta+Space preserve Android's language-switch/Search fallback actions.

The layout has been tested on an Android device. Automated tests are desktop
models, not Android native-parser/runtime tests.

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
expectations, model terminal shortcut actions, and check discovery metadata and
the built APK's KCM resources.
