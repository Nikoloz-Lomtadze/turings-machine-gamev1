# Turing Dungeons - all the game logic lives here.
# Runs in the browser through Brython (index.html loads it).

from browser import document, window, timer, aio
import math
import random


# --- sound -----------------------------------------------------------
# Tiny synth on top of the Web Audio API. We can't create the
# AudioContext until the user interacts with the page (browsers block
# autoplay), so we lazy-init it the first time something plays.
class Sound:
    def __init__(self):
        self.ctx = None

    def _ctx(self):
        if self.ctx is None:
            AC = getattr(window, 'AudioContext', None) or window.webkitAudioContext
            self.ctx = AC.new()
        return self.ctx

    def play(self, freq, duration=0.06, wave='square', volume=0.05):
        # Wrap everything: some browsers throw if the context is suspended.
        try:
            ctx = self._ctx()
            osc = ctx.createOscillator()
            gain = ctx.createGain()

            osc.type = wave
            osc.frequency.value = freq

            # snap up to volume, then decay exponentially to (near) silence
            gain.gain.setValueAtTime(volume, ctx.currentTime)
            gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + duration)

            osc.connect(gain)
            gain.connect(ctx.destination)
            osc.start()
            osc.stop(ctx.currentTime + duration)
        except Exception:
            pass  # if audio's broken, the game still works without it

    def play_sequence(self, notes, gap_ms=140, duration=0.18, wave='square', volume=0.09):
        # schedule a series of notes spaced gap_ms apart
        for i, freq in enumerate(notes):
            timer.set_timeout(lambda f=freq: self.play(f, duration, wave, volume), i * gap_ms)

    # named one-shots so call sites read like English
    def key_click(self):
        self.play(700 + random.random() * 300, 0.03, 'square', 0.025)

    def tm_step(self):
        self.play(520, 0.08, 'triangle', 0.06)

    def tm_write(self):
        self.play(880, 0.06, 'square', 0.05)

    def accept(self):
        self.play_sequence([523, 659, 784, 1046], gap_ms=120)

    def reject(self):
        self.play(180, 0.18, 'sawtooth', 0.1)
        timer.set_timeout(lambda: self.play(120, 0.28, 'sawtooth', 0.1), 140)

    def fanfare(self):
        self.play_sequence([523, 659, 784, 1046, 784, 1046, 1318, 1568, 1318, 1568, 2093])


sound = Sound()


# --- the three Turing machines (one per level) -----------------------
# Each level is a plain dict so it's easy to add more levels later.
# transitions map "state,read_symbol" -> [next_state, write_symbol, move_direction]
# edges are purely visual: how to draw the arrows on the canvas.

LEVELS = [
    {
        'name': "პირველი დავალება",
        'intro': ("* თქვენ შეაბიჯეთ A212 აუდიტორიაში.\n"
                  "* დაფაზე დახაზულია ტურინგის მანქანის დიაგრამები\n"
                  "* ლექტორი გავალებთ:\n"
                  "*   <b>\"ჩაწერე სიტყვა რომელიც შეიცავს 'ab'-ს...</b>\n"
                  "*   <b>ან დარჩით აუდიტორიაში სამუდამოდ.\"</b>"),
        'prompt': "* წარმოთქვით სიტყვა რომელიც შეიცავს <b>a</b>'s და <b>b</b> &mdash; აუცილებლად უნდა შეიცავდეს <b>ab</b>.",
        'hint': "* მინიშნება: სცადეთ <b>ab</b>, <b>bbab</b>, ან <b>babab</b>.",
        'alphabet': ['a', 'b'],
        'states': {
            'q0': {'x': 180, 'y': 240, 'label': 'q0'},
            'q1': {'x': 450, 'y': 240, 'label': 'q1'},
            'q2': {'x': 720, 'y': 240, 'label': 'q2', 'accept': True},
        },
        'initial': 'q0',
        'accept_states': ['q2'],
        'transitions': {
            'q0,a': ['q1', 'a', 'R'],
            'q0,b': ['q0', 'b', 'R'],
            'q1,a': ['q1', 'a', 'R'],
            'q1,b': ['q2', 'b', 'R'],
            'q2,a': ['q2', 'a', 'R'],
            'q2,b': ['q2', 'b', 'R'],
        },
        'edges': [
            {'from': 'q0', 'to': 'q0', 'self': 'top',    'symbols': [['b', 'b', 'R']]},
            {'from': 'q0', 'to': 'q1',                    'symbols': [['a', 'a', 'R']]},
            {'from': 'q1', 'to': 'q1', 'self': 'top',    'symbols': [['a', 'a', 'R']]},
            {'from': 'q1', 'to': 'q2',                    'symbols': [['b', 'b', 'R']]},
            {'from': 'q2', 'to': 'q2', 'self': 'top',    'symbols': [['a', 'a', 'R'], ['b', 'b', 'R']]},
        ],
    },

    # a^n b^n - balance n a's against n b's by crossing them off in pairs
    {
        'name': "მეორე დავალება",
        'intro': ("* ჰმმ.. კარგია, წარმატებით შეასრულეთ პირველი დავალება\n"
                  "* ფიქრის შემდეგ შემოგხედათ.\n"
                  "* ლექტორი გავალებთ:\n"
                  "*   <b>\"a^n b^n. უნდა იწყებოდეს 'a' სიმბოლოთი.</b>\n"
                  "*   <b>იგივე რაოდენობის a და b. დაამტკიცეთ შენი ცოდნა.\"</b>"),
        'prompt': "* ჩაწერეთ <b>a^n b^n</b> &mdash; ყველა a არის დასაწყისში, შემდეგ იგივე რაოდენობის b",
        'hint': "* მინიშნება: სცადეთ <b>ab</b>, <b>aabb</b>, ან <b>aaabbb</b>.",
        'alphabet': ['a', 'b'],
        'states': {
            'q0': {'x': 130, 'y': 290, 'label': 'q0'},
            'q1': {'x': 350, 'y': 290, 'label': 'q1'},
            'q2': {'x': 350, 'y': 110, 'label': 'q2'},
            'q3': {'x': 620, 'y': 290, 'label': 'q3'},
            'qA': {'x': 820, 'y': 290, 'label': 'qA', 'accept': True},
        },
        'initial': 'q0',
        'accept_states': ['qA'],
        'transitions': {
            'q0,a': ['q1', 'X', 'R'],
            'q0,Y': ['q3', 'Y', 'R'],
            'q1,a': ['q1', 'a', 'R'],
            'q1,Y': ['q1', 'Y', 'R'],
            'q1,b': ['q2', 'Y', 'L'],
            'q2,a': ['q2', 'a', 'L'],
            'q2,Y': ['q2', 'Y', 'L'],
            'q2,X': ['q0', 'X', 'R'],
            'q3,Y': ['q3', 'Y', 'R'],
            'q3,_': ['qA', '_', 'R'],
        },
        'edges': [
            {'from': 'q0', 'to': 'q1',                    'symbols': [['a', 'X', 'R']]},
            {'from': 'q0', 'to': 'q3', 'curve': 0.32,     'symbols': [['Y', 'Y', 'R']]},
            {'from': 'q1', 'to': 'q1', 'self': 'bottom', 'symbols': [['a', 'a', 'R'], ['Y', 'Y', 'R']]},
            {'from': 'q1', 'to': 'q2',                    'symbols': [['b', 'Y', 'L']]},
            {'from': 'q2', 'to': 'q2', 'self': 'top',    'symbols': [['a', 'a', 'L'], ['Y', 'Y', 'L']]},
            {'from': 'q2', 'to': 'q0',                    'symbols': [['X', 'X', 'R']]},
            {'from': 'q3', 'to': 'q3', 'self': 'top',    'symbols': [['Y', 'Y', 'R']]},
            {'from': 'q3', 'to': 'qA',                    'symbols': [['_', '_', 'R']]},
        ],
    },

    # a^n b^n c^n - same trick but in two passes (a->b, then b->c)
    {
        'name': "მესამე დავალება",
        'intro': ("* ყოჩაღ!!\n"
                  "* ვნახოთ, თუ შეძლებთ ბოლო დავალების შესრულებას!.\n"
                  "*   <b>\"a^n b^n c^n. გამოიყენეთ სიმბოლოები a,b,c.</b>\n"
                  "*   <b>ამას ყველა ვერ ამოხსნის,</b>\n"
                  "*   <b>მაგრამ თქვენ ეს შეგიძლიათ!!\"</b>"),
        'prompt': "* ჩაწერეთ <b>a^n b^n c^n</b> &mdash; ყველა ერთი რაოდენობით.",
        'hint': "* მინიშნება: სცადეთ <b>abc</b>, <b>aabbcc</b>, ან <b>aaabbbccc</b>.",
        'alphabet': ['a', 'b', 'c'],
        'states': {
            'q0': {'x':  90, 'y': 300, 'label': 'q0'},
            'q1': {'x': 240, 'y': 300, 'label': 'q1'},
            'q2': {'x': 400, 'y': 300, 'label': 'q2'},
            'q3': {'x': 240, 'y': 110, 'label': 'q3'},
            'q4': {'x': 570, 'y': 300, 'label': 'q4'},
            'q5': {'x': 710, 'y': 300, 'label': 'q5'},
            'qA': {'x': 850, 'y': 300, 'label': 'qA', 'accept': True},
        },
        'initial': 'q0',
        'accept_states': ['qA'],
        'transitions': {
            'q0,a': ['q1', 'X', 'R'],
            'q0,Y': ['q4', 'Y', 'R'],
            'q1,a': ['q1', 'a', 'R'],
            'q1,Y': ['q1', 'Y', 'R'],
            'q1,b': ['q2', 'Y', 'R'],
            'q2,b': ['q2', 'b', 'R'],
            'q2,Z': ['q2', 'Z', 'R'],
            'q2,c': ['q3', 'Z', 'L'],
            'q3,a': ['q3', 'a', 'L'],
            'q3,b': ['q3', 'b', 'L'],
            'q3,Y': ['q3', 'Y', 'L'],
            'q3,Z': ['q3', 'Z', 'L'],
            'q3,X': ['q0', 'X', 'R'],
            'q4,Y': ['q4', 'Y', 'R'],
            'q4,Z': ['q5', 'Z', 'R'],
            'q5,Z': ['q5', 'Z', 'R'],
            'q5,_': ['qA', '_', 'R'],
        },
        'edges': [
            {'from': 'q0', 'to': 'q1',                    'symbols': [['a', 'X', 'R']]},
            {'from': 'q0', 'to': 'q4', 'curve': 0.22,     'symbols': [['Y', 'Y', 'R']]},
            {'from': 'q1', 'to': 'q1', 'self': 'bottom', 'symbols': [['a', 'a', 'R'], ['Y', 'Y', 'R']]},
            {'from': 'q1', 'to': 'q2',                    'symbols': [['b', 'Y', 'R']]},
            {'from': 'q2', 'to': 'q2', 'self': 'bottom', 'symbols': [['b', 'b', 'R'], ['Z', 'Z', 'R']]},
            {'from': 'q2', 'to': 'q3', 'curve': 0.45,     'symbols': [['c', 'Z', 'L']]},
            {'from': 'q3', 'to': 'q3', 'self': 'top',
                'symbols': [['a', 'a', 'L'], ['b', 'b', 'L'], ['Y', 'Y', 'L'], ['Z', 'Z', 'L']]},
            {'from': 'q3', 'to': 'q0',                    'symbols': [['X', 'X', 'R']]},
            {'from': 'q4', 'to': 'q4', 'self': 'top',    'symbols': [['Y', 'Y', 'R']]},
            {'from': 'q4', 'to': 'q5',                    'symbols': [['Z', 'Z', 'R']]},
            {'from': 'q5', 'to': 'q5', 'self': 'top',    'symbols': [['Z', 'Z', 'R']]},
            {'from': 'q5', 'to': 'qA',                    'symbols': [['_', '_', 'R']]},
        ],
    },
]


# --- the Turing machine simulator ------------------------------------
# Runs the TM step by step. Doesn't draw anything - it just records what
# happened. The animation function below replays the trace.

def _snapshot(state, tape, head, edge):
    # tape[:] makes a copy so later edits to `tape` don't mutate this entry
    return {'state': state, 'tape': tape[:], 'head': head, 'edge': edge}


def simulate(level, word, max_steps=800):
    """Run `level`'s TM on `word`.

    Returns a dict with:
        accepted: True if we halted in an accept state on blank
        trace:    list of snapshots, one per step (oldest first)
        halt:     why the machine stopped:
                    'accept'         - landed on accept state, blank tape ahead
                    'no-transition'  - no rule for (state, symbol)
                    'left-off-tape'  - head moved left past cell 0
                    'max-steps'      - looped too long, gave up
    """
    tape = list(word)
    head = 0
    state = level['initial']
    trace = [_snapshot(state, tape, head, None)]

    for _ in range(max_steps):
        # symbol under the head; blanks ('_') stretch infinitely past the end
        symbol = tape[head] if 0 <= head < len(tape) else '_'
        rule = level['transitions'].get(f'{state},{symbol}')

        if rule is None:
            # no rule -> halt. Accept iff we're on a final state reading blank.
            accepted = symbol == '_' and state in level['accept_states']
            return {
                'accepted': accepted,
                'trace': trace,
                'halt': 'accept' if accepted else 'no-transition',
            }

        next_state, write, move = rule

        # grow the tape lazily if we're writing off the end
        while head >= len(tape):
            tape.append('_')
        tape[head] = write

        new_head = head + (1 if move == 'R' else -1 if move == 'L' else 0)
        if new_head < 0:
            return {'accepted': False, 'trace': trace, 'halt': 'left-off-tape'}

        edge = {'from': state, 'to': next_state,
                'read': symbol, 'write': write, 'move': move}
        trace.append(_snapshot(next_state, tape, new_head, edge))

        state, head = next_state, new_head

    return {'accepted': False, 'trace': trace, 'halt': 'max-steps'}


# --- drawing the TM diagram on the canvas ----------------------------
# Each level has a set of states (circles) and edges (arrows) we render.

STATE_RADIUS = 26


def _canvas():
    return document['tm']


def _clear_with_grid(ctx, W, H):
    ctx.clearRect(0, 0, W, H)
    # faint purple grid in the background
    ctx.save()
    ctx.strokeStyle = 'rgba(170, 0, 255, 0.06)'
    ctx.lineWidth = 1
    for x in range(0, W, 30):
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke()
    for y in range(0, H, 30):
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke()
    ctx.restore()


def _draw_arrowhead(ctx, x, y, angle, color):
    size = 9
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(angle)
    ctx.beginPath()
    ctx.moveTo(0, 0)
    ctx.lineTo(-size, -size / 2)
    ctx.lineTo(-size, size / 2)
    ctx.closePath()
    ctx.fillStyle = color
    ctx.fill()
    ctx.restore()


def _draw_label(ctx, x, y, symbols, color, highlighted_read):
    # Draw the "read/write,move" labels. Stack vertically if there are
    # multiple symbols on the same edge.
    ctx.save()
    ctx.font = '9px "Press Start 2P", monospace'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'

    line_height = 13
    start_y = y - (len(symbols) - 1) * line_height / 2

    for i, (read, write, move) in enumerate(symbols):
        text = f'{read}/{write},{move}'
        text_w = ctx.measureText(text).width
        line_y = start_y + i * line_height
        is_hot = highlighted_read is not None and read == highlighted_read

        # background pill so labels don't blur into the grid
        ctx.fillStyle = '#000'
        ctx.fillRect(x - text_w / 2 - 4, line_y - 7, text_w + 8, 13)
        ctx.strokeStyle = '#ffcc44' if is_hot else 'rgba(255,255,255,0.15)'
        ctx.lineWidth = 1
        ctx.strokeRect(x - text_w / 2 - 4, line_y - 7, text_w + 8, 13)

        ctx.fillStyle = '#ffcc44' if is_hot else color
        ctx.fillText(text, x, line_y)
    ctx.restore()


def _draw_state(ctx, st, highlighted, is_initial, is_accept):
    ctx.save()

    if highlighted:
        ctx.shadowColor = '#ffcc44'
        ctx.shadowBlur = 22

    # accept states get a double-ring
    if is_accept:
        ctx.beginPath()
        ctx.arc(st['x'], st['y'], STATE_RADIUS + 5, 0, math.pi * 2)
        ctx.strokeStyle = '#ffcc44' if highlighted else '#6f6'
        ctx.lineWidth = 2
        ctx.stroke()

    # the main circle
    ctx.beginPath()
    ctx.arc(st['x'], st['y'], STATE_RADIUS, 0, math.pi * 2)
    if highlighted:
        ctx.fillStyle = '#443300'
    elif is_accept:
        ctx.fillStyle = '#0c1a0c'
    else:
        ctx.fillStyle = '#0a0a18'
    ctx.fill()
    ctx.strokeStyle = '#ffee88' if highlighted else ('#6f6' if is_accept else '#cfd')
    ctx.lineWidth = 3 if highlighted else 2
    ctx.stroke()

    # the label inside
    ctx.shadowBlur = 0
    ctx.fillStyle = '#ffee88' if highlighted else '#fff'
    ctx.font = 'bold 13px "Press Start 2P", monospace'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(st['label'], st['x'], st['y'])

    # initial-state marker: little arrow coming in from the left
    if is_initial:
        ctx.beginPath()
        ctx.moveTo(st['x'] - STATE_RADIUS - 32, st['y'])
        ctx.lineTo(st['x'] - STATE_RADIUS - 4, st['y'])
        ctx.strokeStyle = '#aef'
        ctx.lineWidth = 2
        ctx.stroke()
        _draw_arrowhead(ctx, st['x'] - STATE_RADIUS - 4, st['y'], 0, '#aef')
        ctx.fillStyle = '#aef'
        ctx.font = '8px "Press Start 2P", monospace'
        ctx.textAlign = 'left'
        ctx.fillText('start', st['x'] - STATE_RADIUS - 32, st['y'] - 10)

    ctx.restore()


def _draw_edge(ctx, level, edge, highlighted, hot_edge):
    src = level['states'][edge['from']]
    dst = level['states'][edge['to']]
    color = '#ffcc44' if highlighted else '#88c'

    ctx.save()
    ctx.strokeStyle = color
    ctx.fillStyle = color
    ctx.lineWidth = 3 if highlighted else 1.5
    if highlighted:
        ctx.shadowColor = '#ffcc44'
        ctx.shadowBlur = 14

    r = STATE_RADIUS
    hot_read = hot_edge['read'] if (highlighted and hot_edge) else None

    # self-loop: an arc sitting on top of (or below) the circle
    if edge['from'] == edge['to']:
        loop_r = 22
        side = edge.get('self', 'top')
        sign = -1 if side == 'top' else 1
        cx = src['x']
        cy = src['y'] + sign * (r + loop_r - 6)
        sweep = side == 'bottom'

        ctx.beginPath()
        if sweep:
            ctx.arc(cx, cy, loop_r, math.pi * 0.3, math.pi * 0.7, False)
        else:
            ctx.arc(cx, cy, loop_r, -math.pi * 0.7, -math.pi * 0.3, False)
        ctx.stroke()

        end_angle = math.pi * 0.7 if sweep else -math.pi * 0.3
        ax = cx + loop_r * math.cos(end_angle)
        ay = cy + loop_r * math.sin(end_angle)
        _draw_arrowhead(ctx, ax, ay, end_angle + math.pi / 2, color)

        label_y = cy - loop_r - 10 if side == 'top' else cy + loop_r + 12
        _draw_label(ctx, cx, label_y, edge['symbols'], color, hot_read)
        ctx.restore()
        return

    # straight or curved edge between two different states
    dx = dst['x'] - src['x']
    dy = dst['y'] - src['y']
    dist = math.sqrt(dx * dx + dy * dy)
    ux, uy = dx / dist, dy / dist

    # nudge endpoints to sit on the circle borders, not the centers
    sx = src['x'] + ux * r
    sy = src['y'] + uy * r
    ex = dst['x'] - ux * r
    ey = dst['y'] - uy * r

    curve = edge.get('curve', 0)
    if curve != 0:
        # quadratic bezier - the control point is offset perpendicular to the line
        perp_x, perp_y = -uy, ux
        mid_x = (sx + ex) / 2 + perp_x * dist * curve
        mid_y = (sy + ey) / 2 + perp_y * dist * curve

        ctx.beginPath()
        ctx.moveTo(sx, sy)
        ctx.quadraticCurveTo(mid_x, mid_y, ex, ey)
        ctx.stroke()
        _draw_arrowhead(ctx, ex, ey, math.atan2(ey - mid_y, ex - mid_x), color)

        # place the label closer to the arc's bulge
        lx = (sx + 2 * mid_x + ex) / 4
        ly = (sy + 2 * mid_y + ey) / 4
        _draw_label(ctx, lx, ly, edge['symbols'], color, hot_read)
    else:
        ctx.beginPath()
        ctx.moveTo(sx, sy)
        ctx.lineTo(ex, ey)
        ctx.stroke()
        _draw_arrowhead(ctx, ex, ey, math.atan2(dy, dx), color)

        # offset the label perpendicular so it doesn't sit on the line
        mid_x = (sx + ex) / 2
        mid_y = (sy + ey) / 2
        _draw_label(ctx, mid_x - uy * 16, mid_y + ux * 16, edge['symbols'], color, hot_read)
    ctx.restore()


def draw_tm(level, highlight_state, highlight_edge):
    """Redraw the whole TM diagram. `highlight_state` glows yellow,
    and the matching edge (if any) is brightened."""
    canvas = _canvas()
    ctx = canvas.getContext('2d')
    _clear_with_grid(ctx, canvas.width, canvas.height)

    # edges first, so the state circles draw on top of them
    for edge in level['edges']:
        is_hot = (highlight_edge is not None
                  and highlight_edge['from'] == edge['from']
                  and highlight_edge['to'] == edge['to']
                  and any(s[0] == highlight_edge['read'] for s in edge['symbols']))
        _draw_edge(ctx, level, edge, is_hot, highlight_edge)

    for sid, st in level['states'].items():
        _draw_state(ctx, st, sid == highlight_state, sid == level['initial'], bool(st.get('accept')))


# --- tape strip below the diagram ------------------------------------
def render_tape(tape, head):
    box = document['tape']
    box.innerHTML = ''

    # pad with blanks so the head + a few cells past it are always visible
    cells = list(tape)
    while len(cells) <= head + 3:
        cells.append('_')
    cells.extend(['_'] * 4)

    for i, c in enumerate(cells):
        cell = document.createElement('div')
        classes = ['tape-cell']
        if i == head:
            classes.append('head')
        if c == '_':
            classes.append('blank')
        cell.className = ' '.join(classes)
        cell.textContent = '·' if c == '_' else c
        box.appendChild(cell)

    # auto-scroll so the head stays roughly centered when the tape is long
    if 0 <= head < len(box.children):
        head_el = box.children[head]
        box.scrollLeft = max(0, head_el.offsetLeft - box.clientWidth / 2 + 20)


# --- typewriter (the "* text appears one char at a time" effect) -----
async def type_text(elem, text, speed_ms=28):
    # Tokenize first so we can render whole HTML tags atomically
    # (otherwise we'd render "<", then "<b", etc. and break the page).
    tokens = []
    i = 0
    while i < len(text):
        if text[i] == '<':
            end = text.index('>', i)
            tokens.append(('tag', text[i:end + 1]))
            i = end + 1
        elif text[i] == '\n':
            tokens.append(('tag', '<br/>'))
            i += 1
        else:
            tokens.append(('char', text[i]))
            i += 1

    # Let the player skip the animation by clicking or hitting space/enter.
    skipped = [False]

    def skip(e=None):
        skipped[0] = True

    def on_key(e):
        if e.key in (' ', 'Enter', 'z', 'x'):
            skipped[0] = True

    document.bind('click', skip)
    document.bind('keydown', on_key)

    elem.innerHTML = ''
    buffer = ''
    for kind, content in tokens:
        if skipped[0]:
            break
        buffer += content
        elem.innerHTML = buffer
        if kind == 'char' and content.strip():
            sound.key_click()
        await aio.sleep(speed_ms / 1000)

    if skipped[0]:
        # flush the rest instantly
        elem.innerHTML = ''.join(t[1] for t in tokens)

    document.unbind('click', skip)
    document.unbind('keydown', on_key)

    await aio.sleep(0.12)  # small breath before the next thing


# --- which screen is showing + a couple of flow helpers --------------
game = {'screen': 'title', 'level': 0, 'running': False}


def show_screen(screen_id):
    for s in document.select('.screen'):
        s.classList.remove('active')
    document[screen_id].classList.add('active')
    game['screen'] = screen_id


async def wait_for_keypress():
    # short delay so the click that opened the dialog doesn't immediately close it
    await aio.sleep(0.22)
    done = [False]

    def go(e=None):
        done[0] = True

    def on_key(e):
        if e.key in (' ', 'Enter', 'z', 'x'):
            done[0] = True

    document.bind('click', go)
    document.bind('keydown', on_key)
    while not done[0]:
        await aio.sleep(0.03)
    document.unbind('click', go)
    document.unbind('keydown', on_key)


# --- per-level flow: intro -> play -> result -------------------------
async def show_intro(level_idx):
    show_screen('intro')
    game['level'] = level_idx
    await type_text(document['introText'], LEVELS[level_idx]['intro'])
    await wait_for_keypress()
    start_level(level_idx)


def start_level(idx):
    game['level'] = idx
    lvl = LEVELS[idx]
    show_screen('game')

    # update the HUD + reset the input
    document['lvlNum'].textContent = str(idx + 1)
    document['lvlName'].textContent = lvl['name']
    document['promptText'].innerHTML = lvl['prompt']
    document['hint'].innerHTML = lvl['hint']
    document['strInput'].value = ''
    document['strInput'].focus()
    document['curState'].textContent = lvl['initial']

    draw_tm(lvl, lvl['initial'], None)
    render_tape([], 0)


async def run_input():
    if game['running']:
        return
    lvl = LEVELS[game['level']]
    word = document['strInput'].value.strip().lower()

    if word == '':
        show_message('* you must speak something.', 'bad')
        sound.reject()
        return

    # reject up front if any character isn't in the level's alphabet
    for c in word:
        if c not in lvl['alphabet']:
            show_message(
                f"* '{c}' is not in the alphabet {{{', '.join(lvl['alphabet'])}}}.\n* rejected!",
                'bad')
            sound.reject()
            return

    game['running'] = True
    document['strInput'].disabled = True
    document['runBtn'].disabled = True

    result = simulate(lvl, word)
    await play_trace(lvl, result['trace'])
    await aio.sleep(0.4)

    if result['accepted']:
        sound.accept()
        flash('#6f6')

        is_last = game['level'] == len(LEVELS) - 1
        msg = ('* ლექტორი თქვენით კმაყოფილია\n* თქვენ დატოვეთ აუდიტორია...'
               if is_last
               else '* ლექტორი თქვენით კმაყოფილია.\n* თქვენ ხართ მოტივირებული.')

        def then():
            if is_last:
                show_ending()
            else:
                aio.run(show_intro(game['level'] + 1))

        show_message(msg, 'good', then)
    else:
        sound.reject()
        art = document.select('.dungeon-art')[0]
        art.classList.add('shake')
        timer.set_timeout(lambda: art.classList.remove('shake'), 600)

        msg = '* ტექსტი არაა მიღებული.'
        if result['halt'] == 'left-off-tape':
            msg += '\n* კიდევ იფიქრე'
        elif result['halt'] == 'max-steps':
            msg += '\n* ნუ ჩქარობ...'
        msg += '\n* არაუშავს, სცადეთ კიდევ.'
        show_message(msg, 'bad')

    game['running'] = False
    document['strInput'].disabled = False
    document['runBtn'].disabled = False
    document['strInput'].focus()


async def play_trace(lvl, trace):
    """Animate the recorded run on the canvas + tape.

    Each step is split in two so the viewer can actually follow what's
    happening:
        A) glow the edge while still showing the old state ("about to fire")
        B) jump to the new state and update the tape ("done firing")

    Longer traces step a bit faster so we don't bore the player.
    """
    # show the initial config and let it sit for a moment
    draw_tm(lvl, trace[0]['state'], None)
    render_tape(trace[0]['tape'], trace[0]['head'])
    document['curState'].textContent = trace[0]['state']
    await aio.sleep(0.75)

    step_total = max(340, 1100 - len(trace) * 11)
    read_phase = int(step_total * 0.45)
    write_phase = step_total - read_phase

    for step in trace[1:]:
        # phase A: still on the source state, glow the chosen edge
        draw_tm(lvl, step['edge']['from'], step['edge'])
        sound.tm_step()
        await aio.sleep(read_phase / 1000)

        # phase B: cell is written, head moves, state changes
        draw_tm(lvl, step['state'], step['edge'])
        render_tape(step['tape'], step['head'])
        document['curState'].textContent = step['state']
        sound.tm_write()
        await aio.sleep(write_phase / 1000)

    await aio.sleep(0.5)  # let the player read the final config


def flash(color):
    art = document.select('.dungeon-art')[0]
    art.style.boxShadow = f'0 0 40px {color}, inset 0 0 60px {color}'
    timer.set_timeout(lambda: setattr(art.style, 'boxShadow', ''), 900)


def show_message(text, kind, on_continue=None):
    overlay = document['msgOverlay']
    body = document['msgText']
    btn = document['msgBtn']

    body.innerHTML = text.replace('\n', '<br/>')
    body.className = 'msg-good' if kind == 'good' else 'msg-bad'
    overlay.classList.add('active')

    def close(e=None):
        overlay.classList.remove('active')
        document.unbind('keydown', on_key)
        btn.unbind('click', close)
        if on_continue:
            on_continue()

    def on_key(e):
        if e.key in ('Enter', ' ', 'z', 'x'):
            close()

    btn.bind('click', close)
    document.bind('keydown', on_key)


# --- the ending: 4 student characters celebrate with you -------------
FW_COLORS = ['#ff2244', '#ffcc44', '#aa00ff', '#7af', '#fff', '#6f6', '#f6f']

# -----------------------------------------------------------------------
# 4 hand-drawn 12x20 pixel student sprites.
# Legend: .=transparent  s=skin  b=eye  m=mouth  p=nose
#         [hair letters]  [shirt/clothing letters]
#
# BOY  - brown hair, blue shirt
# GIRL1 - black hair with bangs, pink shirt
# GIRL2 - curly hair (brown), green shirt
# GIRL3 - light/blonde hair, purple shirt
# -----------------------------------------------------------------------

# Boy: brown hair, blue shirt
BOY_SPRITE = [
    "....hhhhhh..",
    "...hhhhhhhh.",
    "..hhhhhhhhhh",
    ".hhssssssshh",
    ".hsssssssssh",
    ".ssssssssss.",
    ".ssbsssssbss",
    ".ssssssssss.",
    ".sssppppssss",
    ".ssssssssss.",
    ".sssmmmmssss",
    ".ssssssssss.",
    "..ssssssss..",
    "...cccccccc.",
    "..cccccccccc",
    ".cccccccccc.",
    "..cccccccc..",
    "..llll.rrrr.",
]
BOY_PALETTE = {
    'h': "#421a05",  # brown hair
    's': '#f4c08a',  # skin
    'b': '#1a1a1a',  # eye
    'p': '#dba070',  # nose
    'm': '#883030',  # mouth
    'c': "#0a4291",  # blue shirt
    'l': '#2a2a2a',  # left trouser leg
    'r': '#2a2a2a',  # right trouser leg
}
BOY_NAME = "* Niko"

# Girl 1: black hair with bangs, pink shirt
GIRL1_SPRITE = [
    "..hhhhhhhh..",
    ".hhhhhhhhhh.",
    "hhhhhhhhhhhh",
    "hhhhshsshhhh",
    "hhsssssssshh",
    "hssssssssssh",
    "hsssbssssbsh",
    "hssssssssssh",
    "hssssppppssh",
    "hssssssssssh",
    "hsssmmmmmssh",
    "hssssssssssh",
    "hhssssssssh",
    "hhcccccccc..",
    ".cccccccccc.",
    "..cccccccc..",
    "..ssss.ssss.",
    "..ssss.ssss.",
]
GIRL1_PALETTE = {
    'h': "#0F0F0F",  # black hair
    's': '#f4c08a',  # skin
    'b': '#1a1a1a',  # eye
    'p': '#dba070',  # nose
    'm': '#883030',  # mouth
    'c': "#4b0b28",  # pink shirt
}
GIRL1_NAME = "* Dea"

# Girl 2: curly hair (represented with bumpy top row), brown, green shirt
GIRL2_SPRITE = [
    "h...hhhh...h....",
    "hh.hhhhhhhh.hh..",
    "hhhhhhhhhhhhhhhhh",
    "hhhhhhhhhhhhhhhh.",
    ".hhhhhhhhhhhhhh..",
    "..hhhhhhhhhhhh...",
    "..hh.hhhhhh.hh..",
    "...hh.hhhh.hh...",
    "h.hh..hh..hh.....",
    "hhhhhhhhhhhhhhh..",
    "hhhhhhhhhhhhh....",
    ".hhssssssshh.....",
    ".hsssssssssh.....",
    ".ssssssssss......",
    ".ssbsssssbss.....",
    ".ssssssssss......",
    ".sssppppssss.....",
    ".ssssssssss......",
    ".sssmmmmssss.....",
    ".ssssssssss......",
    "..ssssssss.......",
    "..cccccccc.......",
    ".cccccccccc......",
    "..cccccccc.......",
    "..ssss.ssss......",
    "..ssss.ssss......",
]
GIRL2_PALETTE = {
    'h': '#7a4a20',  # brown curly hair
    's': '#f4c08a',  # skin
    'b': "#04254b",  # eye
    'p': '#dba070',  # nose
    'm': '#883030',  # mouth
    'c': "#02421b",  # green shirt
}
GIRL2_NAME = "* Nina"

# Girl 3: light/blonde hair, purple shirt
GIRL3_SPRITE = [
    "............",
    "...hhhhhhhh.",
    "..hhhhhhhhhh",
    ".hhssssssshh",
    ".hsssssssssh",
    "hssssssssssh",
    "hssbsssssbsh",
    "hssssssssssh",
    "hsssppppsssh",
    "hssssssssssh",
    "hsssmmmmsssh",
    "hssssssssssh",
    "hhsssssssshh",
    "hhcccccccchh",
    ".cccccccccch",
    "..cccccccc..",
    "..ssss.ssss.",
    "..ssss.ssss.",
]
GIRL3_PALETTE = {
    'h': "#3F2601",  # blonde/light hair
    's': '#f4c08a',  # skin
    'b': '#1a1a1a',  # eye
    'p': '#dba070',  # nose
    'm': '#883030',  # mouth
    'c': '#8844cc',  # purple shirt
}
GIRL3_NAME = "* Maria"

STUDENTS = [
    (BOY_SPRITE,   BOY_PALETTE,   BOY_NAME),
    (GIRL1_SPRITE, GIRL1_PALETTE, GIRL1_NAME),
    (GIRL2_SPRITE, GIRL2_PALETTE, GIRL2_NAME),
    (GIRL3_SPRITE, GIRL3_PALETTE, GIRL3_NAME),
]

STUDENT_LINES = [
    "* ოთახი აივსო თბილი განათებით",
    "* ოთხი სტუდენტი შემოდის აუდიტორიაში.",
    "* ნიკო ამბობს. \"შენ ეს მართლაც შეძელით!!\"",
    "* დეას უხარია. \"წარმატებით შეასრულეთ დავალებები!!\"",
    "* ნინა ამაყობს. \"იდეალურად ჩაწერეთ სიტყვები!!\"",
    "* მარია ამბობს. \"ასე გააგრძელეთ, არ დანებდეთ!\"",
    "* მათ ხელი დაგიქნიეს და გაქრნენ ფიკსელებად.",
]


# Small object so coroutines can check whether to bail out (e.g. if the
# player smashed Restart in the middle of the ending).
class Task:
    def __init__(self):
        self.cancelled = False


ending_task = Task()


def _spawn_particle(canvas, scattered):
    return {
        'x': random.random() * canvas.width if scattered else canvas.width / 2,
        'y': random.random() * -canvas.height if scattered else canvas.height / 2,
        'vx': (random.random() - 0.5) * 4,
        'vy': 1 + random.random() * 3 if scattered else (random.random() - 0.5) * 6,
        'size': 3 + math.floor(random.random() * 4),
        'color': FW_COLORS[math.floor(random.random() * len(FW_COLORS))],
        'gravity': 0.03 + random.random() * 0.05,
        'life': 1.5 + random.random() * 1.5,
    }


def _draw_heart(ctx, cx, cy, size, color):
    # classic Undertale 7x6 pixel heart
    shape = [
        [0, 1, 1, 0, 1, 1, 0],
        [1, 1, 1, 1, 1, 1, 1],
        [1, 1, 1, 1, 1, 1, 1],
        [0, 1, 1, 1, 1, 1, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
    ]
    px = size / 7
    ctx.save()
    ctx.shadowColor = color
    ctx.shadowBlur = size
    ctx.fillStyle = color
    for r, row in enumerate(shape):
        for c, lit in enumerate(row):
            if lit:
                ctx.fillRect(cx - size / 2 + c * px, cy - size / 2 + r * px, px + 1, px + 1)
    ctx.restore()


def _draw_student(ctx, sprite, palette, cx, cy, pixel, alpha):
    """Draw a single pixel student sprite centred at (cx, cy)."""
    if alpha <= 0:
        return
    cols = len(sprite[0])
    rows = len(sprite)
    start_x = math.floor(cx - (cols * pixel) / 2)
    start_y = math.floor(cy - (rows * pixel) / 2)
    ctx.save()
    ctx.globalAlpha = max(0, min(1, alpha))
    for r, line in enumerate(sprite):
        for c, ch in enumerate(line):
            if ch == '.':
                continue
            ctx.fillStyle = palette.get(ch, '#fff')
            ctx.fillRect(start_x + c * pixel, start_y + r * pixel, pixel + 1, pixel + 1)
    ctx.restore()


def _draw_stars(ctx, W, H, frame, seed):
    ctx.save()
    for i in range(70):
        x = (i * 53.7 + seed) % W
        y = (i * 91.3 + seed * 0.3) % H
        twinkle = (math.sin(frame * 0.02 + i * 0.7) + 1) * 0.5
        ctx.globalAlpha = 0.15 + twinkle * 0.45
        if i % 7 == 0:
            ctx.fillStyle = '#aef'
        elif i % 11 == 0:
            ctx.fillStyle = '#ffd'
        else:
            ctx.fillStyle = '#fff'
        ctx.fillRect(x, y, 1.5, 1.5)
    ctx.restore()


def _draw_glow(ctx, cx, cy, radius, alpha):
    if alpha <= 0:
        return
    grad = ctx.createRadialGradient(cx, cy, 10, cx, cy, radius)
    grad.addColorStop(0, f'rgba(120, 80, 200, {0.28 * alpha})')
    grad.addColorStop(0.4, f'rgba(60, 30, 120, {0.14 * alpha})')
    grad.addColorStop(1, 'rgba(0, 0, 0, 0)')
    ctx.save()
    ctx.fillStyle = grad
    ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height)
    ctx.restore()


async def _tween(start_val, end_val, duration_ms, apply, task):
    """Animate a value from start_val to end_val over duration_ms,
    calling apply(current_value) on each frame. Eases in/out."""
    started = window.performance.now()
    while True:
        if task.cancelled:
            return
        t = min(1, (window.performance.now() - started) / duration_ms)
        eased = 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2
        apply(start_val + (end_val - start_val) * eased)
        if t >= 1:
            return
        await aio.sleep(0.016)


async def _wait_or_skip(ms, task):
    """Wait up to ms milliseconds, but bail early if the player advances."""
    done = [False]

    def finish(e=None):
        done[0] = True

    def on_key(e):
        if e.key in (' ', 'Enter', 'z', 'x'):
            done[0] = True

    document.bind('click', finish)
    document.bind('keydown', on_key)

    elapsed = 0.0
    while not done[0] and elapsed * 1000 < ms:
        if task.cancelled:
            break
        await aio.sleep(0.03)
        elapsed += 0.03

    document.unbind('click', finish)
    document.unbind('keydown', on_key)


def show_ending():
    show_screen('ending')
    document.select('.end-overlay')[0].classList.add('hidden')
    document['endDialog'].classList.remove('active')
    document['endDialogText'].innerHTML = ''
    aio.run(_run_students_scene())


async def _run_students_scene():
    # cancel any previous ending that's still running (e.g. mid-restart)
    global ending_task
    ending_task.cancelled = True
    task = Task()
    ending_task = task

    canvas = document['endCanvas']
    ctx = canvas.getContext('2d')

    def fit(_e=None):
        canvas.width = canvas.clientWidth
        canvas.height = canvas.clientHeight

    fit()
    window.addEventListener('resize', fit)

    # shared state for the render loop and the sequence below
    scene = {
        'phase': 'students',   # 'students' or 'fireworks'
        'alpha': 0.0,          # how visible the students are
        'frame': 0,
        'particles': [],
        'highlight': -1,       # which student (0-3) to subtly highlight, -1=all
    }
    star_seed = random.random() * 1000

    def render(_ts=None):
        if task.cancelled:
            return
        scene['frame'] += 1
        W, H = canvas.width, canvas.height

        if scene['phase'] == 'students':
            _render_students_phase(ctx, W, H, scene, star_seed)
        else:
            _render_fireworks_phase(ctx, W, H, scene, canvas)

        timer.request_animation_frame(render)

    timer.request_animation_frame(render)

    # ---- scripted sequence ----
    await aio.sleep(0.7)
    if task.cancelled: return

    sound.play(523, 0.5, 'sine', 0.05)  # soft "they appear" tone
    await _tween(0, 1, 900, lambda v: scene.__setitem__('alpha', v), task)
    if task.cancelled: return
    await aio.sleep(0.5)
    if task.cancelled: return

    # dialog — highlight each student in turn on lines 2-5
    document['endDialog'].classList.add('active')
    dialog = document['endDialogText']
    highlight_map = {2: 0, 3: 1, 4: 2, 5: 3}  # line index -> student index
    for i, line in enumerate(STUDENT_LINES):
        if task.cancelled: return
        scene['highlight'] = highlight_map.get(i, -1)
        await type_text(dialog, line, speed_ms=42)
        if task.cancelled: return
        await _wait_or_skip(1400, task)
    scene['highlight'] = -1
    document['endDialog'].classList.remove('active')
    if task.cancelled: return

    # students dissolve
    sound.play(330, 0.4, 'triangle', 0.04)
    await _tween(1, 0, 900, lambda v: scene.__setitem__('alpha', v), task)
    if task.cancelled: return
    await aio.sleep(0.3)

    # switch to fireworks/heart + reveal the credit overlay
    sound.fanfare()
    scene['phase'] = 'fireworks'
    scene['particles'].extend(_spawn_particle(canvas, True) for _ in range(140))
    for _ in range(60):
        p = _spawn_particle(canvas, False)
        p['x'] = canvas.width / 2
        p['y'] = canvas.height / 2
        angle = random.random() * math.pi * 2
        speed = 2 + random.random() * 7
        p['vx'] = math.cos(angle) * speed
        p['vy'] = math.sin(angle) * speed
        scene['particles'].append(p)

    await aio.sleep(0.45)
    document.select('.end-overlay')[0].classList.remove('hidden')


def _render_students_phase(ctx, W, H, scene, star_seed):
    ctx.fillStyle = '#000'
    ctx.fillRect(0, 0, W, H)
    _draw_stars(ctx, W, H, scene['frame'], star_seed)

    # 4 students side by side, centred vertically
    count = len(STUDENTS)
    # Fit all 4 sprites (12px wide each) + gaps within 92% of canvas width.
    # Available width per slot = W*0.92 / count; pixel = slot / (12 + gap_ratio).
    pixel = max(4, min(math.floor(W * 0.92 / (count * 18)), math.floor(H / 30)))
    sprite_w = 12 * pixel
    gap = max(4, math.floor(pixel * 6))
    total_w = count * sprite_w + (count - 1) * gap
    start_cx = W / 2 - total_w / 2 + sprite_w / 2

    cy = H / 2 - H * 0.06

    for i, (sprite, palette, _name) in enumerate(STUDENTS):
        cx = start_cx + i * (sprite_w + gap)
        # gentle independent bounce so they feel alive
        bounce = math.sin(scene['frame'] * 0.05 + i * 1.1) * 2.5

        # if one is highlighted, dim the others slightly
        if scene['highlight'] == -1:
            a = scene['alpha']
        elif scene['highlight'] == i:
            a = scene['alpha']
        else:
            a = scene['alpha'] * 0.45

        flicker = a * (0.92
                       + math.sin(scene['frame'] * 0.5 + i * 0.8) * 0.04
                       + random.random() * 0.04)

        _draw_glow(ctx, cx, cy + bounce, max(W, H) * 0.22, a * 0.7)
        _draw_student(ctx, sprite, palette, cx, cy + bounce, pixel, flicker)


def _render_fireworks_phase(ctx, W, H, scene, canvas):
    # the rgba fillRect leaves a trail behind the particles - cheap motion blur
    ctx.fillStyle = 'rgba(0,0,0,0.12)'
    ctx.fillRect(0, 0, W, H)

    # keep adding sparks from the center
    if scene['frame'] % 4 == 0:
        for _ in range(3):
            p = _spawn_particle(canvas, False)
            p['x'] = W / 2
            p['y'] = H / 2
            angle = random.random() * math.pi * 2
            speed = 1 + random.random() * 4
            p['vx'] = math.cos(angle) * speed
            p['vy'] = math.sin(angle) * speed
            scene['particles'].append(p)

    # update and draw, keeping only the live ones
    alive = []
    for p in scene['particles']:
        p['x'] += p['vx']
        p['y'] += p['vy']
        p['vy'] += p['gravity']
        p['life'] -= 0.008

        ctx.fillStyle = p['color']
        ctx.globalAlpha = max(0, min(1, p['life']))
        ctx.fillRect(p['x'], p['y'], p['size'], p['size'])

        if p['life'] > 0 and p['y'] <= H + 20:
            alive.append(p)
    ctx.globalAlpha = 1
    scene['particles'] = alive

    # top up so the screen never empties
    while len(scene['particles']) < 140:
        scene['particles'].append(_spawn_particle(canvas, True))

    pulse = 30 + math.sin(scene['frame'] * 0.08) * 8
    _draw_heart(ctx, W / 2, H / 2, pulse, '#ff2244')


# --- wiring up the buttons -------------------------------------------
def on_start(_e=None):
    if game['screen'] != 'title':
        return
    sound.play(660, 0.08, 'square', 0.07)
    aio.run(show_intro(0))


def on_title_keydown(e):
    if game['screen'] == 'title' and e.key in ('Enter', ' ', 'z', 'x'):
        on_start()


def on_run_click(_e=None):
    aio.run(run_input())


def on_input_keydown(e):
    if e.key == 'Enter':
        e.preventDefault()
        aio.run(run_input())


def on_restart(_e=None):
    ending_task.cancelled = True
    game['level'] = 0
    aio.run(show_intro(0))


document['startBtn'].bind('click', on_start)
document.bind('keydown', on_title_keydown)
document['runBtn'].bind('click', on_run_click)
document['strInput'].bind('keydown', on_input_keydown)
document['restartBtn'].bind('click', on_restart)
