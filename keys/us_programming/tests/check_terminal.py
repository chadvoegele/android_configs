#!/usr/bin/env python3
"""Model AOSP KCM replacement actions for the terminal shortcut variant.

Importing check_layout also runs the character mapping and package checks.
These are desktop model tests, not Android runtime tests.
"""
import ast
import itertools
import re

from check_layout import MODS, ROOT, matches

path = ROOT / 'app/src/main/res/raw/us_programming.kcm'
raw = path.read_text()

# Verify the active layout's shortcut actions.
assert raw.count('ctrl: replace ESCAPE') == 1
assert raw.count('ctrl: replace BUTTON_16') == 1
assert raw.count('ctrl+shift: none') == 2

keys = {}
for name, body in re.findall(r'^key (\w+) \{\n(.*?)^\}', raw, re.M | re.S):
    assert name not in keys
    behaviors = []
    labels = set()
    for line in body.splitlines():
        match = re.fullmatch(
            r"\s*(\w+(?:\+\w+)*):\s*(none|'(?:\\.|[^'\\])*'|(?:fallback|replace) \w+)\s*",
            line)
        assert match, line
        prop, value = match.groups()
        replacement = value.split()[1] if value.startswith('replace ') else None
        action = value == 'none' or value.startswith(('fallback ', 'replace '))
        char = '' if action else ast.literal_eval(value)
        assert len(char) == 1 or action
        if prop in ('label', 'number'):
            assert not replacement and prop not in labels
            labels.add(prop)
            continue
        mask = 0
        if prop != 'base':
            for mod in prop.split('+'):
                assert mod in MODS and not mask & MODS[mod]
                mask |= MODS[mod]
        assert all(mask != entry[0] for entry in behaviors)
        behaviors.append((mask, char, replacement))
    keys[name] = list(reversed(behaviors))


def behavior(name, event):
    return next((entry for entry in keys.get(name, []) if matches(event, entry[0])), None)


def apply(name, event):
    entry = behavior(name, event)
    if entry is None or entry[2] is None:
        return name, event
    mask, _, target = entry
    result = event & ~mask
    # Same dependent-bit clearing as AOSP tryRemapKey/applyKeyBehavior.
    for generic, left, right in [('ctrl', 'lctrl', 'rctrl'),
                                 ('alt', 'lalt', 'ralt'),
                                 ('shift', 'lshift', 'rshift')]:
        if mask & MODS[generic]:
            result &= ~(MODS[left] | MODS[right])
        if mask & (MODS[left] | MODS[right]):
            result &= ~MODS[generic]
        if result & (MODS[left] | MODS[right]):
            result |= MODS[generic]
    return target, result


def character(name, event):
    entry = behavior(name, event)
    return entry[1] if entry else ''


count = 0
for side, caps in itertools.product(
        (MODS['lctrl'], MODS['rctrl'], MODS['lctrl'] | MODS['rctrl']), (0, MODS['capslock'])):
    event = MODS['ctrl'] | side | caps
    for name, expected in [('SEMICOLON', 'ESCAPE'), ('PERIOD', 'BUTTON_16')]:
        target, out_meta = apply(name, event)
        assert target == expected
        assert out_meta == caps, (target, out_meta)
        if target == 'BUTTON_16':
            assert character(target, out_meta) == '\ue000'
            assert character(target, out_meta).encode() == bytes.fromhex('ee8080')
        # Ctrl+Shift combinations deliberately retain their old behavior.
        shift_event = event | MODS['shift'] | MODS['lshift']
        assert apply(name, shift_event) == (name, shift_event)
        # Ctrl+Alt / Ctrl+Meta must not select either custom shortcut.
        for other in (MODS['alt'] | MODS['ralt'], MODS['meta'] | MODS['lmeta']):
            assert apply(name, event | other) == (name, event | other)
        count += 1

# Ordinary typing, Caps, and the programming layer remain unchanged.
for name, output in [('SEMICOLON', ';'), ('PERIOD', '.')]:
    assert character(name, 0) == output
assert character('SEMICOLON', MODS['alt'] | MODS['ralt']) == '-'
assert character('PERIOD', MODS['alt'] | MODS['ralt']) == '3'
assert character('PERIOD', MODS['alt'] | MODS['ralt'] | MODS['shift']) == '#'
assert character('SPACE', MODS['alt'] | MODS['ralt']) == ' '
assert character('BUTTON_16', 0) == '\ue000'
print(f'PASS: {count} terminal shortcut cases; consumed Ctrl bits, U+E000 bytes, and unaffected combinations.')
