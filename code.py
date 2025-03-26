import time
import board
import digitalio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

kbd = Keyboard(usb_hid.devices)

# Add a map from your labels to Keycode values
keycode_map = {
    'a': Keycode.A, 'b': Keycode.B, 'c': Keycode.C, 'd': Keycode.D,
    'e': Keycode.E, 'f': Keycode.F, 'g': Keycode.G, 'h': Keycode.H,
    'i': Keycode.I, 'j': Keycode.J, 'k': Keycode.K, 'l': Keycode.L,
    'm': Keycode.M, 'n': Keycode.N, 'o': Keycode.O, 'p': Keycode.P,
    'q': Keycode.Q, 'r': Keycode.R, 's': Keycode.S, 't': Keycode.T,
    'u': Keycode.U, 'v': Keycode.V, 'w': Keycode.W, 'x': Keycode.X,
    'y': Keycode.Y, 'z': Keycode.Z,
    '1': Keycode.ONE, '2': Keycode.TWO, '3': Keycode.THREE, '4': Keycode.FOUR,
    '5': Keycode.FIVE, '6': Keycode.SIX, '7': Keycode.SEVEN, '8': Keycode.EIGHT,
    '9': Keycode.NINE, '0': Keycode.ZERO,
    '↵': Keycode.ENTER,
    '⌫': Keycode.BACKSPACE,
    'spac': Keycode.SPACE,
    ',': Keycode.COMMA,
    '.': Keycode.PERIOD,
    ';': Keycode.SEMICOLON,
    ':': Keycode.SEMICOLON,
    "'": Keycode.QUOTE,
    '"': Keycode.QUOTE,
    '_': Keycode.MINUS,
    '-': Keycode.MINUS,
    '+': Keycode.EQUALS,
    '=': Keycode.EQUALS,
    '/': Keycode.FORWARD_SLASH,
    '?': Keycode.FORWARD_SLASH,
    '!': Keycode.ONE,
    '@': Keycode.TWO,
    '#': Keycode.THREE,
    '$': Keycode.FOUR,
    '%': Keycode.FIVE,
    '^': Keycode.SIX,
    '&': Keycode.SEVEN,
    '*': Keycode.EIGHT,
    '(': Keycode.NINE,
    ')': Keycode.ZERO
    # Extend this as needed
}

cols = [board.GP9, board.GP10, board.GP11, board.GP12, board.GP13]
rows = [board.GP0, board.GP1, board.GP2, board.GP3, board.GP4, board.GP5, board.GP6]

keymap = [
    ['q',   'e',   'r',   'u',  'o' ],
    ['w',   's',   'g',   'h',  'l' ],
    ['sym', 'd',   't',   'y',  'i' ],
    ['a',   'p',  'r⇧',   '↵',  '⌫' ],
    ['alt', 'x',   'v',   'b',  '$' ],
    ['spac','z',   'c',   'n',  'm' ],
    ['🎤', 'l⇧',  'f',   'j',  'k' ]
]

alt_keymap = [
    ['#',  '2', '3', '_', '+'],
    ['1',  '4', '/', ':', '"'],
    ['',   '5', '(', ')', '-'],
    ['*',  '@', '',  '',  ''],
    ['',   '8', '?', '!', '🔊'],
    ['',   '7', '9', ',', '.'],
    ['0',  '',  '6', ';', "'"]
]

col_pins = [digitalio.DigitalInOut(p) for p in cols]
row_pins = [digitalio.DigitalInOut(p) for p in rows]
DEBOUNCE_FRAMES = 3
DOUBLECLICK_DELAY = 0.5  # seconds

key_states = {}  # (col_idx, row_idx) -> debounce count
modifier_state = {
    'sym': {'held': False, 'latched': False, 'last_release': 0},
    'alt': {'held': False, 'latched': False, 'last_release': 0},
    'shift': {'held': False, 'latched': False, 'last_release': 0}
}

def current_time():
    return time.monotonic()

def set_modifier(label, pressed):
    state = modifier_state[label]
    now = current_time()
    if pressed:
        state['held'] = True
    else:
        state['held'] = False
        if state['latched']:
            # If already latched, any release clears it
            state['latched'] = False
        elif now - state['last_release'] < DOUBLECLICK_DELAY:
            state['latched'] = True
        state['last_release'] = now


def is_modifier_active(label):
    s = modifier_state[label]
    return s['held'] or s['latched']

def scan():
    global key_states
    new_states = {}
    current_pressed = set()

    for pin in col_pins + row_pins:
        pin.direction = digitalio.Direction.INPUT
        pin.pull = None

    for col_idx, col in enumerate(col_pins):
        col.direction = digitalio.Direction.OUTPUT
        col.value = False

        for row_idx, row in enumerate(row_pins):
            row.direction = digitalio.Direction.INPUT
            row.pull = digitalio.Pull.UP
            time.sleep(0.0005)

            if not row.value:
                current_pressed.add((col_idx, row_idx))

        col.direction = digitalio.Direction.INPUT
        col.pull = None

    previously_pressed = set(key_states.keys())

    # Handle releases
    for key in previously_pressed - current_pressed:
        row_idx, col_idx = key[1], key[0]
        label = keymap[row_idx][col_idx]
        if label == 'sym':
            set_modifier('sym', False)
        elif label in ('r⇧', 'l⇧'):
            set_modifier('shift', False)
        elif label == 'alt':
            set_modifier('alt', False)

    # Handle presses
    for key in current_pressed:
        prev_count = key_states.get(key, 0)
        count = prev_count + 1
        new_states[key] = min(count, DEBOUNCE_FRAMES)
        if count != DEBOUNCE_FRAMES:
            continue

        row_idx, col_idx = key[1], key[0]
        label = keymap[row_idx][col_idx]

        if label == 'sym':
            set_modifier('sym', True)
            continue
        elif label in ('r⇧', 'l⇧'):
            set_modifier('shift', True)
            continue
        elif label == 'alt':
            set_modifier('alt', True)
            continue

        use_alt = is_modifier_active('sym') or is_modifier_active('alt')
        use_shift = is_modifier_active('shift')

        alt_label = alt_keymap[row_idx][col_idx]
        if use_alt and alt_label:
            label = alt_label
        elif use_shift and label.isalpha():
            label = label.upper()

        code = keycode_map.get(label.lower())
        if code:
            if label.isupper() or label in '!@#$%^&*()_+{}|:"<>?':
                kbd.press(Keycode.SHIFT, code)
                kbd.release_all()
            else:
                if label == '⌫':
                    kbd.press(code)
                    # don't release yet — handle below
                else:
                    kbd.press(code)
                    kbd.release(code)



    key_states = new_states
    # Release backspace only if it's no longer held
    backspace_key = (cols.index(board.GP13), rows.index(board.GP3))  # ⌫ is at col5/row4
    if backspace_key not in current_pressed:
        kbd.release(keycode_map['⌫'])


while True:
    scan()
    time.sleep(0.01)
