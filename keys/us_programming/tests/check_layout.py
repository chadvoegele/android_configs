#!/usr/bin/env python3
"""Check KCM characters using explicit expectations and AOSP modifier rules.

This tests the packaged mapping and precedence, not an Android device/parser.
"""
import ast
import itertools
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
KCM_PATH = ROOT / 'app/src/main/res/raw/us_programming.kcm'

# Android KeyEvent meta masks. Actual events include normalized generic bits.
MODS = {'shift': 1, 'alt': 2, 'lalt': 16, 'ralt': 32,
        'lshift': 64, 'rshift': 128, 'ctrl': 4096, 'lctrl': 8192,
        'rctrl': 16384, 'meta': 65536, 'lmeta': 131072,
        'rmeta': 262144, 'capslock': 1048576}
EXACT = sum(MODS[m] for m in ('alt', 'lalt', 'ralt', 'ctrl', 'lctrl',
                              'rctrl', 'meta', 'lmeta', 'rmeta'))


def matches(event, behavior):
    # Transcribed from AOSP KeyCharacterMap::matchesMetaState.
    if event & behavior != behavior:
        return False
    unmatched = event & ~behavior & EXACT
    for generic, left, right in [('alt', 'lalt', 'ralt'),
                                 ('ctrl', 'lctrl', 'rctrl'),
                                 ('meta', 'lmeta', 'rmeta')]:
        if behavior & MODS[generic]:
            unmatched &= ~(MODS[left] | MODS[right])
        elif behavior & (MODS[left] | MODS[right]):
            unmatched &= ~MODS[generic]
    return not unmatched


packaged_raw = KCM_PATH.read_text()
remaps = re.findall(r'^map key (?:(usage) )?(\w+) (\w+)$', packaged_raw, re.M)
assert [(kind, int(code, 0), target) for kind, code, target in remaps] == [
    ('', 56, 'ALT_RIGHT'), ('usage', 0x000700e2, 'ALT_RIGHT')]


# Check ordinary character behavior; shortcut actions are tested
# separately by check_terminal.py.
raw = re.sub(
    r'^    ctrl: replace (?:ESCAPE|BUTTON_16)\n    ctrl\+shift: none\n',
    '', packaged_raw, flags=re.M)
raw = re.sub(r'^key BUTTON_16 \{\n.*?^\}\n?', '', raw, flags=re.M | re.S)
assert re.search(r'^type OVERLAY$', raw, re.M)
keys = {}
for name, body in re.findall(r'^key (\w+) \{\n(.*?)^\}', raw, re.M | re.S):
    assert name not in keys, f'Duplicate key {name}'
    behaviors = []
    labels = set()
    for line in body.splitlines():
        match = re.fullmatch(
            r"\s*(\w+(?:\+\w+)*):\s*(none|'(?:\\.|[^'\\])*'|fallback \w+)\s*",
            line)
        assert match, f'Invalid KCM property: {line}'
        prop, literal = match.groups()
        action = literal == 'none' or literal.startswith('fallback ')
        char = '' if action else ast.literal_eval(literal)
        assert len(char) == 1 or action
        if prop in ('label', 'number'):
            assert prop not in labels
            labels.add(prop)
            continue
        mask = 0
        if prop != 'base':
            for modifier in prop.split('+'):
                assert modifier in MODS
                assert not mask & MODS[modifier]
                mask |= MODS[modifier]
        assert all(mask != m for m, _ in behaviors), f'Duplicate mask {name}/{prop}'
        behaviors.append((mask, char))
    keys[name] = list(reversed(behaviors))  # Android parser uses push_front.


def get(name, event):
    return next((char for mask, char in keys[name] if matches(event, mask)), '')


# Explicit expected characters, independent of the KCM under test.
normal = dict(zip(
    ['GRAVE'] + list('1234567890') +
    ['MINUS', 'EQUALS'] + list('QWERTYUIOP') +
    ['LEFT_BRACKET', 'RIGHT_BRACKET'] + list('ASDFGHJKL') +
    ['SEMICOLON', 'APOSTROPHE'] + list('ZXCVBNM') +
    ['COMMA', 'PERIOD', 'SLASH', 'BACKSLASH'],
    "`1234567890-=qwertyuiop[]asdfghjkl;'zxcvbnm,./\\"))
shifted = dict(zip(normal, '~!@#$%^&*()_+QWERTYUIOP{}ASDFGHJKL:"ZXCVBNM<>?|'))
programming = dict(zip(
    list('WERTYUIOP') + ['LEFT_BRACKET', 'RIGHT_BRACKET'] +
    list('ASDFGHJKL') + ['SEMICOLON', 'APOSTROPHE'] +
    list('ZXCVBNM') + ['COMMA', 'PERIOD', 'SLASH'],
    "~\\{}#789*/` ()=_&+456-,[]$|!0123.".replace(' ', '')))
fourth = {'K': '%', 'L': '^', 'COMMA': '@', 'PERIOD': '#'}
assert set(keys) == set(normal) | {'SPACE'}

count = 0
for alt_sides in (MODS['lalt'], MODS['ralt'], MODS['lalt'] | MODS['ralt']):
    for shift, caps, alt in itertools.product((False, True), repeat=3):
        event = (MODS['shift'] | MODS['lshift'] if shift else 0)
        event |= MODS['capslock'] if caps else 0
        if alt:
            event |= MODS['alt'] | alt_sides
        for name, base in normal.items():
            if alt and name in programming:
                expected = fourth.get(name, '') if shift else programming[name]
            elif base.isalpha():
                expected = base.upper() if shift != caps else base
            else:
                expected = shifted[name] if shift else base
            assert get(name, event) == expected, (name, event, expected, get(name, event))
            for shortcut in [MODS['ctrl'] | MODS['lctrl'],
                             MODS['meta'] | MODS['lmeta']]:
                assert get(name, event | shortcut) == ''
            count += 1

# Alt+Space must produce space with either/both Alt keys, Shift, and Caps.
for shift, caps, alt_sides in itertools.product(
        (False, True), (False, True), (0, MODS['lalt'], MODS['ralt'],
                                     MODS['lalt'] | MODS['ralt'])):
    event = (MODS['shift'] if shift else 0) | (MODS['capslock'] if caps else 0)
    assert get('SPACE', event) == ' '
    assert get('SPACE', event | MODS['alt'] | alt_sides) == ' '
assert get('SPACE', MODS['ctrl'] | MODS['lctrl']) == ''
assert get('SPACE', MODS['meta'] | MODS['lmeta']) == ''
assert "meta: fallback SEARCH" in raw
assert "ctrl: fallback LANGUAGE_SWITCH" in raw

# Verify the package's discovery metadata and APK resource when built.
ns = '{http://schemas.android.com/apk/res/android}'
manifest = ET.parse(ROOT / 'app/src/main/AndroidManifest.xml').getroot()
assert manifest.find('.//service') is None, 'This must not register an IME'
receiver = manifest.find('.//receiver')
assert receiver.get(ns + 'exported') == 'true'
assert receiver.find('intent-filter/action').get(ns + 'name') == \
    'android.hardware.input.action.QUERY_KEYBOARD_LAYOUTS'
assert receiver.find('meta-data').get(ns + 'resource') == '@xml/keyboard_layouts'
for xml_dir in ('xml', 'xml-v34'):
    layouts = ET.parse(ROOT / f'app/src/main/res/{xml_dir}/keyboard_layouts.xml').getroot()
    assert {item.get(ns + 'name'): item.get(ns + 'keyboardLayout') for item in layouts} == {
        'us_prog_terminal': '@raw/us_programming'}
    assert len(layouts) == 1
    assert layouts[0].get(ns + 'label') == '@string/layout_name'
strings = ET.parse(ROOT / 'app/src/main/res/values/strings.xml').getroot()
assert strings.find("string[@name='layout_name']").text == 'US Programming'
apk = ROOT / 'app/build/outputs/apk/debug/app-debug.apk'
if apk.exists():
    with zipfile.ZipFile(apk) as archive:
        assert archive.read('res/raw/us_programming.kcm') == KCM_PATH.read_bytes()
        assert {name for name in archive.namelist() if name.endswith('.kcm')} == {
            'res/raw/us_programming.kcm'}
print(f'PASS: {count} KCM mapping cases, Alt scan/usage remaps, Ctrl/Meta exclusion, and package metadata.')
