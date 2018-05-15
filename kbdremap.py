#!/usr/bin/env python3

# MIT License
#
# Copyright (c) 2018 Alexander Sosedkin
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import atexit

import evdev
import evdev.ecodes as ec


MATCH = 'AT Translated Set 2 keyboard'


SHORT = {
    'C_LOCK': 'CAPSLOCK',
    'INS': 'INSERT', 'DEL': 'DELETE',
    'LEFT': 'LEFT_ARROW', 'RIGHT': 'RIGHT_ARROW',
    'UP': 'UP_ARROW', 'DOWN': 'DOWN_ARROW',
    'LSHIFT': 'LEFTSHIFT', 'RSHIFT': 'RIGHTSHIFT',
    'LCTRL': 'LEFTCTRL', 'RCTRL': 'RIGHTCTRL',
    'LALT': 'LEFTALT', 'RALT': 'RIGHTALT',
    'LWIN': 'LEFTWINDOWS', 'RWIN': 'RIGHTWINDOWS',
    'PGUP': 'PAGEUP', 'PGDN': 'PAGEDOWN',
    'BS': 'BACKSPACE', 'RET': 'ENTER',
    '`': 'GRAVE', '\'': 'APOSTROPHE', '=': 'EQUAL',
    ',': 'COMMA', '.': 'DOT', '-': 'MINUS',
    '/': 'SLASH', '\\': 'BACKSLASH',
    ';': 'SEMICOLON',
    '[': 'LEFTBRACE', ']': 'RIGHTBRACE',
    '#': None,
    'CTRLESC': 'LEFTCTRL',
    'SPS': 'RIGHTSHIFT',
    'FN': 'WAKEUP',
    'ENT': 'ENTER',
    'WIN': 'LEFTMETA',
    'ALT': 'LEFTALT', 'RA': 'RIGHTALT', 'CP': 'COMPOSE',
    'XX1': 'MUHENKAN', 'XX2': 'HENKAN', 'XX3': 'KATAKANAHIRAGANA',
    'LANG/LEAD': 'RIGHTALT',
    'LAN': 'CAPSLOCK',
}

ex = lambda k: SHORT[k] if k in SHORT else k
expand = lambda layout: [ex(k) for k in layout]
keyify = lambda s: eval('ec.KEY_' + s) if isinstance(s, str) else s

HARDWARE = r'''
     ` 1   2   3   4   5   6   7   8   9   0   -   =  YEN BS
   TAB   Q   W   E   R   T   Y   U   I   O   P   [   ]
C_LOCK    A   S   D   F   G   H   J   K   L   ;   '   \  RET
LSHIFT      Z   X   C   V   B   N   M   ,   .   /  RO RSHIFT
LCTRL   FN WIN ALT XX1    SPACE  XX2 XX3 RA CP RCTRL BACK
'''

#QWERTY_RU = r'''
#     ` 1   2   3   4   5   #   6   7   8   9   0   -   # #
#   TAB   Q   W   E   R   T   #   Y   U   I   O   P   [
#CTRLESC   A   S   D   F   G   #   H   J   K   L   ;   '   ]
#        Z   X   C   V   B   #   #  N   M   ,   .   /  RSHIFT
##       =  WIN ALT BS     SPACE  ENT SPS LAN #   #  BACK
#'''

QWERTY_RU = r'''
     ` 1   2   3   4   5   #   #   6   7   8   9   0   - \
   TAB   Q   W   E   R   T   #   #   Y   U   I   O   P
CTRLESC   A   S   D   F   G   #   #   H   J   K   L   ;   '
        Z   X   C   V   B   #   #  #   N   M   ,   .  /
#       =  WIN ALT BS     SPACE  SPS ENT SPS LAN [  ]
'''

#COLEMAK = r'''
#     ` 1   2   3   4   5   #   6   7   8   9   0   -   #  #
#   TAB   Q   W   F   P   G   #   J   L   U   Y   ;   \
#CTRLESC   A   R   S   T   D   #   H   N   E   I   O   '   #
#        Z   X   C   V   B   #   #   K   M   ,   .   /  RSHIFT
##       =  WIN ALT BS     SPACE  ENT SPS LAN #   [   ]
#'''

COLEMAK = r'''
     ` 1   2   3   4   5   #   #   6   7   8   9   0   -  \
   TAB   Q   W   F   P   G   #   #   J   L   U   Y   ;
CTRLESC   A   R   S   T   D   #   #   H   N   E   I   O   '
        Z   X   C   V   B   #   #   #   K   M   ,   .  /
#       =  WIN ALT BS     SPACE  SPS ENT SPS LAN  [   ]
'''


MODBUTTONS = {
    'CTRLESC': 'ESC',
    'SPS': 'SPACE',
}
BACK_PAIRS = dict(zip(COLEMAK.split(), HARDWARE.split()))
MODBUTTONS = {keyify(ex(BACK_PAIRS[orig])): keyify(to)
              for orig, to in MODBUTTONS.items()}
LANGUAGE_TOGGLE_KEY = keyify(ex(BACK_PAIRS['LAN']))


def make_layout(target, hardware):
    target, hardware = target.split(), hardware.split()
    remap_pairs = dict(zip(expand(hardware), expand(target)))
    return {keyify(orig): keyify(to) for orig, to in remap_pairs.items()}


COLEMAK = make_layout(COLEMAK, HARDWARE)
QWERTY_RU = make_layout(QWERTY_RU, HARDWARE)


def is_abort(ev):
    return (ev.type == ec.EV_KEY and ev.code == ec.KEY_PAUSE and ev.value == 1)


devices = [evdev.InputDevice(fn).name for fn in evdev.list_devices()]
devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
kbd = [d for d in devices if MATCH in d.name][0]


atexit.register(kbd.ungrab)
kbd.grab()

current_layout = COLEMAK
prev_ev = None
solo = None
with evdev.UInput.from_device(kbd, name='kbdremap') as ui:
    for ev in kbd.read_loop():
        if is_abort(ev):
            break
        sec, usec = ev.sec, ev.usec
        etype, code, value = ev.type, ev.code, ev.value
        if etype == ec.EV_KEY:
            if code in current_layout:
                remap = current_layout[ev.code]
                if remap is None:
                    pass
                else:
                    if ev.code == LANGUAGE_TOGGLE_KEY and ev.value:
                        current_layout = QWERTY_RU \
                            if current_layout == COLEMAK else COLEMAK
                    if ev.code not in MODBUTTONS:
                        code = remap
                        ui.write(etype, code, value)
                        if value == 1:
                            solo = None
                    else:
                        mod_code, solo_code = remap, MODBUTTONS[ev.code]
                        if solo != solo_code and value == 1:
                            solo = solo_code
                            ui.write(etype, mod_code, value)
                        elif solo == solo_code and ev.value == 0:
                            solo = None
                            ui.write(etype, mod_code, 0)
                            ui.write(etype, solo_code, 1)
                            ui.write(etype, solo_code, 0)
                        elif solo == solo_code and value == 2:
                            ui.write(etype, mod_code, value)
                            solo = None  # abort soloing on long presses
                        else:
                            solo = None
                            ui.write(etype, mod_code, value)
            else:
                ui.write(etype, code, value)
            prev_ev = ev
        else:
            ui.write(etype, code, value)
