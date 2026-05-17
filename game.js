/* =====================================================================
 * TURING DUNGEONS - a tale of automata
 * ===================================================================== */

/* ----- AUDIO (tiny Web Audio synth) ---------------------------------- */
const audio = (() => {
  let ctx;
  const getCtx = () => (ctx = ctx || new (window.AudioContext || window.webkitAudioContext)());
  function beep(freq=440, dur=0.06, type='square', vol=0.05) {
    try {
      const c = getCtx();
      const o = c.createOscillator();
      const g = c.createGain();
      o.type = type; o.frequency.value = freq;
      g.gain.setValueAtTime(vol, c.currentTime);
      g.gain.exponentialRampToValueAtTime(0.0001, c.currentTime + dur);
      o.connect(g); g.connect(c.destination);
      o.start();
      o.stop(c.currentTime + dur);
    } catch(e) {}
  }
  return {
    beep,
    type:   () => beep(700 + Math.random()*300, 0.03, 'square',   0.025),
    step:   () => beep(520, 0.08, 'triangle', 0.06),
    write:  () => beep(880, 0.06, 'square',   0.05),
    accept: () => [523,659,784,1046].forEach((f,i)=>setTimeout(()=>beep(f,0.18,'square',0.09), i*120)),
    reject: () => { beep(180, 0.18, 'sawtooth', 0.1); setTimeout(()=>beep(120, 0.28, 'sawtooth', 0.1), 140); },
    win:    () => {
      const notes = [523,659,784,1046,784,1046,1318,1568,1318,1568,2093];
      notes.forEach((f,i)=>setTimeout(()=>beep(f,0.18,'square',0.09), i*140));
    }
  };
})();

/* ----- TURING MACHINE DEFINITIONS ------------------------------------ */
const LEVELS = [
  /* Level 1: contains "ab" as a substring */
  {
    name: "THE WHISPERING TAPE",
    intro: "* You step into the first dungeon.\n* Damp stone, a chalk diagram on the wall.\n* A voice whispers:\n*   <b>\"speak a word containing 'ab'...</b>\n*   <b>or perish on the tape.\"</b>",
    prompt: "* Speak a word of <b>a</b>'s and <b>b</b>'s &mdash; it must contain <b>ab</b>.",
    hint: "* hint: try <b>ab</b>, <b>bbab</b>, or <b>babab</b>.",
    alphabet: ['a', 'b'],
    states: {
      q0: { x: 180, y: 240, label: 'q0' },
      q1: { x: 450, y: 240, label: 'q1' },
      q2: { x: 720, y: 240, label: 'q2', accept: true }
    },
    initial: 'q0',
    finalAccept: ['q2'],
    transitions: {
      'q0,a': ['q1', 'a', 'R'],
      'q0,b': ['q0', 'b', 'R'],
      'q1,a': ['q1', 'a', 'R'],
      'q1,b': ['q2', 'b', 'R'],
      'q2,a': ['q2', 'a', 'R'],
      'q2,b': ['q2', 'b', 'R'],
    },
    edges: [
      { from:'q0', to:'q0', self:'top',    symbols:[['b','b','R']] },
      { from:'q0', to:'q1',                symbols:[['a','a','R']] },
      { from:'q1', to:'q1', self:'top',    symbols:[['a','a','R']] },
      { from:'q1', to:'q2',                symbols:[['b','b','R']] },
      { from:'q2', to:'q2', self:'top',    symbols:[['a','a','R'],['b','b','R']] },
    ]
  },

  /* Level 2: a^n b^n */
  {
    name: "THE BALANCED HALL",
    intro: "* The next chamber pulses.\n* A more intricate diagram glows.\n* The voice sharpens:\n*   <b>\"a^n b^n. all a's first.</b>\n*   <b>equal b's. prove your balance.\"</b>",
    prompt: "* Speak <b>a^n b^n</b> &mdash; all a's first, then equal b's.",
    hint: "* hint: try <b>ab</b>, <b>aabb</b>, or <b>aaabbb</b>.",
    alphabet: ['a', 'b'],
    states: {
      q0: { x: 130, y: 290, label: 'q0' },
      q1: { x: 350, y: 290, label: 'q1' },
      q2: { x: 350, y: 110, label: 'q2' },
      q3: { x: 620, y: 290, label: 'q3' },
      qA: { x: 820, y: 290, label: 'qA', accept: true }
    },
    initial: 'q0',
    finalAccept: ['qA'],
    transitions: {
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
    edges: [
      { from:'q0', to:'q1',                symbols:[['a','X','R']] },
      { from:'q0', to:'q3', curve: 0.32,   symbols:[['Y','Y','R']] },
      { from:'q1', to:'q1', self:'bottom', symbols:[['a','a','R'],['Y','Y','R']] },
      { from:'q1', to:'q2',                symbols:[['b','Y','L']] },
      { from:'q2', to:'q2', self:'top',    symbols:[['a','a','L'],['Y','Y','L']] },
      { from:'q2', to:'q0',                symbols:[['X','X','R']] },
      { from:'q3', to:'q3', self:'top',    symbols:[['Y','Y','R']] },
      { from:'q3', to:'qA',                symbols:[['_','_','R']] },
    ]
  },

  /* Level 3: a^n b^n c^n */
  {
    name: "THE TRIPLE TOMB",
    intro: "* Final dungeon. the walls breathe.\n* The voice is everywhere:\n*   <b>\"a^n b^n c^n. the triple bind.</b>\n*   <b>not even a pushdown can pass.</b>\n*   <b>but the tape... the tape can.\"</b>",
    prompt: "* Speak <b>a^n b^n c^n</b> &mdash; equal counts of each.",
    hint: "* hint: try <b>abc</b>, <b>aabbcc</b>, or <b>aaabbbccc</b>.",
    alphabet: ['a', 'b', 'c'],
    states: {
      q0: { x:  90, y: 300, label: 'q0' },
      q1: { x: 240, y: 300, label: 'q1' },
      q2: { x: 400, y: 300, label: 'q2' },
      q3: { x: 240, y: 110, label: 'q3' },
      q4: { x: 570, y: 300, label: 'q4' },
      q5: { x: 710, y: 300, label: 'q5' },
      qA: { x: 850, y: 300, label: 'qA', accept: true }
    },
    initial: 'q0',
    finalAccept: ['qA'],
    transitions: {
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
    edges: [
      { from:'q0', to:'q1',                 symbols:[['a','X','R']] },
      { from:'q0', to:'q4', curve: 0.22,    symbols:[['Y','Y','R']] },
      { from:'q1', to:'q1', self:'bottom',  symbols:[['a','a','R'],['Y','Y','R']] },
      { from:'q1', to:'q2',                 symbols:[['b','Y','R']] },
      { from:'q2', to:'q2', self:'bottom',  symbols:[['b','b','R'],['Z','Z','R']] },
      { from:'q2', to:'q3', curve: 0.45,    symbols:[['c','Z','L']] },
      { from:'q3', to:'q3', self:'top',     symbols:[['a','a','L'],['b','b','L'],['Y','Y','L'],['Z','Z','L']] },
      { from:'q3', to:'q0',                 symbols:[['X','X','R']] },
      { from:'q4', to:'q4', self:'top',     symbols:[['Y','Y','R']] },
      { from:'q4', to:'q5',                 symbols:[['Z','Z','R']] },
      { from:'q5', to:'q5', self:'top',     symbols:[['Z','Z','R']] },
      { from:'q5', to:'qA',                 symbols:[['_','_','R']] },
    ]
  }
];

/* ----- SIMULATOR ----------------------------------------------------- */
function simulate(level, input, maxSteps = 800) {
  const tape = input.split('');
  let head = 0;
  let state = level.initial;
  const trace = [{ state, tape: tape.slice(), head, edge: null }];

  for (let i = 0; i < maxSteps; i++) {
    const sym = (head < 0 || head >= tape.length || tape[head] === undefined) ? '_' : tape[head];
    const key = `${state},${sym}`;
    const trans = level.transitions[key];

    if (!trans) {
      const accepted = (sym === '_' && level.finalAccept.includes(state));
      return { accepted, trace, halt: accepted ? 'accept' : 'no-transition' };
    }

    const [newState, write, move] = trans;

    while (head >= tape.length) tape.push('_');
    tape[head] = write;

    let newHead = head;
    if (move === 'R') newHead++;
    else if (move === 'L') newHead--;

    if (newHead < 0) return { accepted: false, trace, halt: 'left-off-tape' };

    trace.push({
      state: newState,
      tape: tape.slice(),
      head: newHead,
      edge: { from: state, to: newState, read: sym, write, move }
    });

    state = newState;
    head = newHead;
  }

  return { accepted: false, trace, halt: 'max-steps' };
}

/* ----- CANVAS DRAWING ------------------------------------------------ */
const STATE_RADIUS = 26;

function getCanvas() { return document.getElementById('tm'); }

function clearCanvas(ctx, W, H) {
  ctx.clearRect(0, 0, W, H);
  // faint grid
  ctx.save();
  ctx.strokeStyle = 'rgba(170, 0, 255, 0.06)';
  ctx.lineWidth = 1;
  for (let x = 0; x < W; x += 30) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
  }
  for (let y = 0; y < H; y += 30) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
  }
  ctx.restore();
}

function drawTM(canvas, level, highlightState, highlightEdge) {
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  clearCanvas(ctx, W, H);

  for (const edge of level.edges) {
    const isHi = highlightEdge &&
                 highlightEdge.from === edge.from &&
                 highlightEdge.to === edge.to &&
                 edge.symbols.some(s => s[0] === highlightEdge.read);
    drawEdge(ctx, level, edge, isHi, highlightEdge);
  }

  for (const [id, st] of Object.entries(level.states)) {
    drawState(ctx, st, id === highlightState, id === level.initial, !!st.accept);
  }
}

function drawState(ctx, st, highlighted, isInitial, isAccept) {
  ctx.save();

  if (highlighted) {
    ctx.shadowColor = '#ffcc44';
    ctx.shadowBlur = 22;
  }

  if (isAccept) {
    ctx.beginPath();
    ctx.arc(st.x, st.y, STATE_RADIUS + 5, 0, Math.PI*2);
    ctx.strokeStyle = highlighted ? '#ffcc44' : '#6f6';
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  ctx.beginPath();
  ctx.arc(st.x, st.y, STATE_RADIUS, 0, Math.PI*2);
  ctx.fillStyle = highlighted ? '#443300' : (isAccept ? '#0c1a0c' : '#0a0a18');
  ctx.fill();
  ctx.strokeStyle = highlighted ? '#ffee88' : (isAccept ? '#6f6' : '#cfd');
  ctx.lineWidth = highlighted ? 3 : 2;
  ctx.stroke();

  ctx.shadowBlur = 0;
  ctx.fillStyle = highlighted ? '#ffee88' : '#fff';
  ctx.font = 'bold 13px "Press Start 2P", monospace';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(st.label, st.x, st.y);

  if (isInitial) {
    ctx.beginPath();
    ctx.moveTo(st.x - STATE_RADIUS - 32, st.y);
    ctx.lineTo(st.x - STATE_RADIUS - 4, st.y);
    ctx.strokeStyle = '#aef';
    ctx.lineWidth = 2;
    ctx.stroke();
    drawArrowHead(ctx, st.x - STATE_RADIUS - 4, st.y, 0, '#aef');
    ctx.fillStyle = '#aef';
    ctx.font = '8px "Press Start 2P", monospace';
    ctx.textAlign = 'left';
    ctx.fillText('start', st.x - STATE_RADIUS - 32, st.y - 10);
  }

  ctx.restore();
}

function drawArrowHead(ctx, x, y, angle, color) {
  const size = 9;
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(angle);
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(-size, -size/2);
  ctx.lineTo(-size, size/2);
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
  ctx.restore();
}

function drawTransitionLabel(ctx, x, y, symbols, color, highlightedRead) {
  ctx.save();
  ctx.font = '9px "Press Start 2P", monospace';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  const lineH = 13;
  const startY = y - (symbols.length - 1) * lineH / 2;

  symbols.forEach(([read, write, move], i) => {
    const text = `${read}/${write},${move}`;
    const tw = ctx.measureText(text).width;
    const ty = startY + i * lineH;
    const isHi = highlightedRead && read === highlightedRead;

    ctx.fillStyle = '#000';
    ctx.fillRect(x - tw/2 - 4, ty - 7, tw + 8, 13);
    ctx.strokeStyle = isHi ? '#ffcc44' : 'rgba(255,255,255,0.15)';
    ctx.lineWidth = 1;
    ctx.strokeRect(x - tw/2 - 4, ty - 7, tw + 8, 13);

    ctx.fillStyle = isHi ? '#ffcc44' : color;
    ctx.fillText(text, x, ty);
  });
  ctx.restore();
}

function drawEdge(ctx, level, edge, highlighted, hiEdge) {
  const from = level.states[edge.from];
  const to = level.states[edge.to];
  const color = highlighted ? '#ffcc44' : '#88c';
  const lw = highlighted ? 3 : 1.5;

  ctx.save();
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = lw;
  if (highlighted) { ctx.shadowColor = '#ffcc44'; ctx.shadowBlur = 14; }

  const r = STATE_RADIUS;

  if (edge.from === edge.to) {
    const loopRadius = 22;
    const side = edge.self || 'top';
    const sign = side === 'top' ? -1 : 1;
    const cx = from.x;
    const cy = from.y + sign * (r + loopRadius - 6);

    const sweep = side === 'bottom';
    ctx.beginPath();
    ctx.arc(cx, cy, loopRadius, sweep ? Math.PI*0.3 : -Math.PI*0.7,
                                sweep ? Math.PI*0.7 : -Math.PI*0.3, false);
    ctx.stroke();

    // arrow end at right side of loop
    const endAngle = sweep ? Math.PI*0.7 : -Math.PI*0.3;
    const ax = cx + loopRadius * Math.cos(endAngle);
    const ay = cy + loopRadius * Math.sin(endAngle);
    const tangentAngle = endAngle + Math.PI/2;
    drawArrowHead(ctx, ax, ay, tangentAngle, color);

    const labelY = side === 'top' ? cy - loopRadius - 10 : cy + loopRadius + 12;
    drawTransitionLabel(ctx, cx, labelY, edge.symbols, color, highlighted ? hiEdge.read : null);
  } else {
    const dx = to.x - from.x, dy = to.y - from.y;
    const dist = Math.sqrt(dx*dx + dy*dy);
    const ux = dx/dist, uy = dy/dist;
    const sx = from.x + ux*r, sy = from.y + uy*r;
    const ex = to.x - ux*r,   ey = to.y - uy*r;

    const curve = edge.curve || 0;

    if (curve !== 0) {
      const px = -uy, py = ux;
      const mx = (sx + ex)/2 + px * dist * curve;
      const my = (sy + ey)/2 + py * dist * curve;
      ctx.beginPath();
      ctx.moveTo(sx, sy);
      ctx.quadraticCurveTo(mx, my, ex, ey);
      ctx.stroke();
      const aAngle = Math.atan2(ey - my, ex - mx);
      drawArrowHead(ctx, ex, ey, aAngle, color);
      // label at curve apex
      const lx = (sx + 2*mx + ex)/4;
      const ly = (sy + 2*my + ey)/4;
      drawTransitionLabel(ctx, lx, ly, edge.symbols, color, highlighted ? hiEdge.read : null);
    } else {
      ctx.beginPath();
      ctx.moveTo(sx, sy);
      ctx.lineTo(ex, ey);
      ctx.stroke();
      const aAngle = Math.atan2(dy, dx);
      drawArrowHead(ctx, ex, ey, aAngle, color);
      const mx = (sx + ex)/2;
      const my = (sy + ey)/2;
      const ox = -uy * 16, oy = ux * 16;
      drawTransitionLabel(ctx, mx + ox, my + oy, edge.symbols, color, highlighted ? hiEdge.read : null);
    }
  }
  ctx.restore();
}

/* ----- TAPE RENDERING ------------------------------------------------ */
function renderTape(tape, head) {
  const tapeDiv = document.getElementById('tape');
  tapeDiv.innerHTML = '';
  const cells = tape.slice();
  while (cells.length <= head + 3) cells.push('_');
  for (let i = 0; i < 4; i++) cells.push('_');

  cells.forEach((c, i) => {
    const div = document.createElement('div');
    div.className = 'tape-cell' +
                    (i === head ? ' head' : '') +
                    (c === '_' ? ' blank' : '');
    div.textContent = c === '_' ? '·' : c;
    tapeDiv.appendChild(div);
  });

  const headEl = tapeDiv.children[head];
  if (headEl) {
    const target = headEl.offsetLeft - tapeDiv.clientWidth/2 + 20;
    tapeDiv.scrollLeft = Math.max(0, target);
  }
}

/* ----- TYPEWRITER ---------------------------------------------------- */
function typeText(elem, text, speed = 28) {
  return new Promise(resolve => {
    const tokens = [];
    let i = 0;
    while (i < text.length) {
      if (text[i] === '<') {
        const end = text.indexOf('>', i);
        tokens.push({ type: 'tag', content: text.slice(i, end+1) });
        i = end + 1;
      } else if (text[i] === '\n') {
        tokens.push({ type: 'tag', content: '<br/>' });
        i++;
      } else {
        tokens.push({ type: 'char', content: text[i] });
        i++;
      }
    }

    elem.innerHTML = '';
    let html = '';
    let idx = 0;
    let skipped = false;

    function complete() {
      elem.innerHTML = tokens.map(t => t.content).join('');
      cleanup();
      setTimeout(resolve, 120);
    }
    function skip() { if (!skipped) { skipped = true; complete(); } }
    function cleanup() {
      document.removeEventListener('click', skip);
      document.removeEventListener('keydown', onKey);
    }
    function onKey(e) { if (e.key === ' ' || e.key === 'Enter' || e.key === 'z' || e.key === 'x') skip(); }
    document.addEventListener('click', skip);
    document.addEventListener('keydown', onKey);

    function tick() {
      if (skipped) return;
      if (idx >= tokens.length) { cleanup(); setTimeout(resolve, 120); return; }
      const t = tokens[idx];
      html += t.content;
      elem.innerHTML = html;
      if (t.type === 'char' && t.content.trim() !== '') audio.type();
      idx++;
      setTimeout(tick, speed);
    }
    tick();
  });
}

/* ----- SCREEN / FLOW ------------------------------------------------- */
const State = { screen: 'title', level: 0, hp: 20, running: false };

function show(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  const el = document.getElementById(id);
  el.classList.add('active');
  State.screen = id;
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function waitForContinue() {
  return new Promise(resolve => {
    setTimeout(() => {
      function go() { cleanup(); resolve(); }
      function cleanup() {
        document.removeEventListener('click', go);
        document.removeEventListener('keydown', onKey);
      }
      function onKey(e) { if (e.key === ' ' || e.key === 'Enter' || e.key === 'z' || e.key === 'x') go(); }
      document.addEventListener('click', go);
      document.addEventListener('keydown', onKey);
    }, 220);
  });
}

async function showIntro(levelIdx) {
  show('intro');
  State.level = levelIdx;
  await typeText(document.getElementById('introText'), LEVELS[levelIdx].intro);
  await waitForContinue();
  startLevel(levelIdx);
}

function startLevel(idx) {
  State.level = idx;
  const lvl = LEVELS[idx];
  show('game');
  document.getElementById('lvlNum').textContent = idx + 1;
  document.getElementById('lvlName').textContent = lvl.name;
  document.getElementById('promptText').innerHTML = lvl.prompt;
  document.getElementById('hint').innerHTML = lvl.hint;
  document.getElementById('strInput').value = '';
  document.getElementById('strInput').focus();
  document.getElementById('curState').textContent = lvl.initial;

  drawTM(getCanvas(), lvl, lvl.initial, null);
  renderTape([], 0);
}

async function runInput() {
  if (State.running) return;
  const lvl = LEVELS[State.level];
  const raw = document.getElementById('strInput').value.trim().toLowerCase();

  if (raw === '') {
    showMsg('* you must speak something.', 'bad');
    audio.reject();
    return;
  }
  for (const c of raw) {
    if (!lvl.alphabet.includes(c)) {
      showMsg(`* '${c}' is not in the alphabet {${lvl.alphabet.join(', ')}}.\n* rejected!`, 'bad');
      audio.reject();
      return;
    }
  }

  State.running = true;
  document.getElementById('strInput').disabled = true;
  document.getElementById('runBtn').disabled = true;

  const result = simulate(lvl, raw);
  await animateRun(lvl, result.trace);
  await sleep(400);

  if (result.accepted) {
    audio.accept();
    flashCanvas('#6f6');
    showMsg(
      State.level === LEVELS.length - 1
        ? '* THE FINAL TAPE ACCEPTS YOU.\n* the dungeon dissolves...'
        : '* THE TAPE ACCEPTS YOU.\n* you feel determined.',
      'good',
      () => {
        if (State.level >= LEVELS.length - 1) showEnding();
        else showIntro(State.level + 1);
      });
  } else {
    audio.reject();
    document.querySelector('.dungeon-art').classList.add('shake');
    setTimeout(() => document.querySelector('.dungeon-art').classList.remove('shake'), 600);
    let msg = '* the string is REJECTED.';
    if (result.halt === 'left-off-tape') msg += '\n* the head fell off the tape...';
    if (result.halt === 'max-steps')     msg += '\n* the head wandered forever...';
    msg += '\n* try again, brave one.';
    showMsg(msg, 'bad');
  }

  State.running = false;
  document.getElementById('strInput').disabled = false;
  document.getElementById('runBtn').disabled = false;
  document.getElementById('strInput').focus();
}

async function animateRun(lvl, trace) {
  // show starting configuration first
  drawTM(getCanvas(), lvl, trace[0].state, null);
  renderTape(trace[0].tape, trace[0].head);
  document.getElementById('curState').textContent = trace[0].state;
  await sleep(750);

  // two-phase per step: highlight transition on old state, then move to new state
  // slower than before so the head/state changes are easy to follow
  const stepTotal = Math.max(340, 1100 - trace.length * 11);
  const readPhase = Math.floor(stepTotal * 0.45);
  const writePhase = stepTotal - readPhase;

  for (let i = 1; i < trace.length; i++) {
    const step = trace[i];

    // phase A: still on the source state, but glow the chosen edge
    drawTM(getCanvas(), lvl, step.edge.from, step.edge);
    audio.step();
    await sleep(readPhase);

    // phase B: cell is written, head moves, state changes
    drawTM(getCanvas(), lvl, step.state, step.edge);
    renderTape(step.tape, step.head);
    document.getElementById('curState').textContent = step.state;
    audio.write();
    await sleep(writePhase);
  }

  // brief pause on the final configuration so the player can read it
  await sleep(500);
}

function flashCanvas(color) {
  const el = document.querySelector('.dungeon-art');
  el.style.boxShadow = `0 0 40px ${color}, inset 0 0 60px ${color}`;
  setTimeout(() => { el.style.boxShadow = ''; }, 900);
}

function showMsg(text, type, onContinue) {
  const overlay = document.getElementById('msgOverlay');
  const msgText = document.getElementById('msgText');
  const msgBtn  = document.getElementById('msgBtn');
  msgText.innerHTML = text.replace(/\n/g, '<br/>');
  msgText.className = type === 'good' ? 'msg-good' : 'msg-bad';
  overlay.classList.add('active');
  function close() {
    overlay.classList.remove('active');
    document.removeEventListener('keydown', onKey);
    if (onContinue) onContinue();
  }
  function onKey(e) { if (e.key === 'Enter' || e.key === ' ' || e.key === 'z' || e.key === 'x') close(); }
  msgBtn.onclick = close;
  document.addEventListener('keydown', onKey);
}

/* ----- ENDING -------------------------------------------------------- */
const FW_COLORS = ['#ff2244','#ffcc44','#aa00ff','#7af','#fff','#6f6','#f6f'];

/* Pixel-art Alan Turing portrait (14w x 18h)
   . = transparent  h = hair  s = skin  b = eye  p = nose
   m = mouth  w = shirt  j = jacket  t = tie */
const TURING_SPRITE = [
  "....hhhhhh....",
  "...hhhhhhhh...",
  "..hhhhhhhhhh..",
  ".hhhhhhhhhhhh.",
  ".hssssssssshh.",
  ".ssssssssssss.",
  ".ssbssssssbss.",
  ".ssssssssssss.",
  ".ssssppppssss.",
  ".ssssssssssss.",
  ".sssmmmmmmsss.",
  ".ssssssssssss.",
  "..ssssssssss..",
  "...wwwwwwww...",
  "..jjwwwwwwjj..",
  ".jjjwttttwjjj.",
  "jjjjwttttwjjjj",
  "jjjjwttttwjjjj",
];
const TURING_COLORS = {
  h: '#4a3020',
  s: '#f0c8a0',
  b: '#1a1a1a',
  p: '#d8a880',
  m: '#8a3030',
  w: '#e8e8e0',
  j: '#1c2030',
  t: '#aa2030',
};

const TURING_LINES = [
  "* The void hums softly.",
  "* A figure steps out of the static.",
  "* It is ALAN TURING.",
  "* ...",
  '* "so. you walked the dungeons."',
  '* "you balanced the a\'s and the b\'s."',
  '* "you tamed the triple bind."',
  '* "the tape will remember you."',
  '* "stay determined, dear computer."',
  "* TURING smiles, and fades into pixels.",
];

function showEnding() {
  show('ending');
  document.querySelector('.end-overlay').classList.add('hidden');
  document.getElementById('endDialog').classList.remove('active');
  document.getElementById('endDialogText').innerHTML = '';
  runTuringEnding();
}

let endingTask = null;

async function runTuringEnding() {
  if (endingTask) endingTask.cancelled = true;
  const task = { cancelled: false };
  endingTask = task;

  const canvas = document.getElementById('endCanvas');
  const ctx = canvas.getContext('2d');
  function resize() {
    canvas.width  = canvas.clientWidth;
    canvas.height = canvas.clientHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  const starSeed = Math.random() * 1000;
  const state = {
    phase: 'turing',
    turingAlpha: 0,
    flicker: 0,
    particles: [],
    frame: 0,
  };

  function loop() {
    if (task.cancelled) return;
    state.frame++;
    const W = canvas.width, H = canvas.height;

    if (state.phase !== 'fireworks') {
      // dark void with subtle starfield and soft purple glow behind Turing
      ctx.fillStyle = '#000';
      ctx.fillRect(0, 0, W, H);
      drawStarfield(ctx, W, H, state.frame, starSeed);

      const cx = W / 2;
      const cy = H / 2 - H * 0.08;
      drawCharGlow(ctx, cx, cy, Math.max(W, H) * 0.45, state.turingAlpha);

      const pixelSize = Math.max(8, Math.floor(Math.min(W, H) / 28));
      // tiny flicker / sway for life
      const sway = Math.sin(state.frame * 0.04) * 1.5;
      const flickerAlpha = state.turingAlpha * (0.92 + Math.sin(state.frame * 0.6) * 0.04 + Math.random() * 0.04);
      drawTuringSprite(ctx, cx + sway, cy, pixelSize, flickerAlpha);
    } else {
      ctx.fillStyle = 'rgba(0,0,0,0.12)';
      ctx.fillRect(0, 0, W, H);

      if (state.frame % 4 === 0) {
        for (let i = 0; i < 3; i++) {
          const p = makeParticle(canvas, FW_COLORS, false);
          p.x = W / 2; p.y = H / 2;
          const a = Math.random() * Math.PI * 2;
          const s = 1 + Math.random() * 4;
          p.vx = Math.cos(a) * s; p.vy = Math.sin(a) * s;
          state.particles.push(p);
        }
      }

      for (let i = state.particles.length - 1; i >= 0; i--) {
        const p = state.particles[i];
        p.x += p.vx; p.y += p.vy;
        p.vy += p.gravity;
        p.life -= 0.008;
        ctx.fillStyle = p.color;
        ctx.globalAlpha = Math.max(0, Math.min(1, p.life));
        ctx.fillRect(p.x, p.y, p.size, p.size);
        ctx.globalAlpha = 1;
        if (p.life <= 0 || p.y > H + 20) state.particles.splice(i, 1);
      }
      while (state.particles.length < 140) state.particles.push(makeParticle(canvas, FW_COLORS, true));

      const pulse = 30 + Math.sin(state.frame * 0.08) * 8;
      drawPixelHeart(ctx, W / 2, H / 2, pulse, '#ff2244');
    }

    requestAnimationFrame(loop);
  }
  loop();

  // -- sequence --
  await sleep(700);
  if (task.cancelled) return;

  // fade Turing in
  audio.beep(523, 0.5, 'sine', 0.05);
  await tween(0, 1, 900, v => { state.turingAlpha = v; }, task);
  if (task.cancelled) return;
  await sleep(500);
  if (task.cancelled) return;

  // play dialog
  document.getElementById('endDialog').classList.add('active');
  const dialogText = document.getElementById('endDialogText');
  for (const line of TURING_LINES) {
    if (task.cancelled) return;
    await typeText(dialogText, line, 42);
    if (task.cancelled) return;
    await waitOrAdvance(1400, task);
  }
  document.getElementById('endDialog').classList.remove('active');
  if (task.cancelled) return;

  // dissolve Turing into pixels
  audio.beep(330, 0.4, 'triangle', 0.04);
  await tween(1, 0, 900, v => { state.turingAlpha = v; }, task);
  if (task.cancelled) return;
  await sleep(300);

  // burst into the celebratory fireworks ending
  audio.win();
  state.phase = 'fireworks';
  for (let i = 0; i < 140; i++) state.particles.push(makeParticle(canvas, FW_COLORS, true));
  for (let i = 0; i < 60; i++) {
    const p = makeParticle(canvas, FW_COLORS, false);
    p.x = canvas.width / 2; p.y = canvas.height / 2;
    const a = Math.random() * Math.PI * 2;
    const s = 2 + Math.random() * 7;
    p.vx = Math.cos(a) * s; p.vy = Math.sin(a) * s;
    state.particles.push(p);
  }

  await sleep(450);
  document.querySelector('.end-overlay').classList.remove('hidden');
}

function waitOrAdvance(ms, task) {
  return new Promise(resolve => {
    let done = false;
    function finish() {
      if (done) return;
      done = true;
      clearTimeout(timer);
      document.removeEventListener('click', finish);
      document.removeEventListener('keydown', onKey);
      resolve();
    }
    function onKey(e) {
      if (e.key === ' ' || e.key === 'Enter' || e.key === 'z' || e.key === 'x') finish();
    }
    const timer = setTimeout(finish, ms);
    document.addEventListener('click', finish);
    document.addEventListener('keydown', onKey);
    if (task) {
      const iv = setInterval(() => {
        if (task.cancelled) { clearInterval(iv); finish(); }
      }, 80);
    }
  });
}

function tween(from, to, duration, onUpdate, task) {
  return new Promise(resolve => {
    const start = performance.now();
    function frame() {
      if (task && task.cancelled) { resolve(); return; }
      const t = Math.min(1, (performance.now() - start) / duration);
      const eased = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
      onUpdate(from + (to - from) * eased);
      if (t < 1) requestAnimationFrame(frame);
      else resolve();
    }
    requestAnimationFrame(frame);
  });
}

function drawTuringSprite(ctx, cx, cy, px, alpha) {
  if (alpha <= 0) return;
  const w = TURING_SPRITE[0].length;
  const h = TURING_SPRITE.length;
  const startX = Math.floor(cx - (w * px) / 2);
  const startY = Math.floor(cy - (h * px) / 2);
  ctx.save();
  ctx.globalAlpha = Math.max(0, Math.min(1, alpha));
  for (let r = 0; r < h; r++) {
    for (let c = 0; c < w; c++) {
      const ch = TURING_SPRITE[r][c];
      if (ch === '.') continue;
      ctx.fillStyle = TURING_COLORS[ch] || '#fff';
      ctx.fillRect(startX + c * px, startY + r * px, px + 1, px + 1);
    }
  }
  ctx.restore();
}

function drawStarfield(ctx, W, H, frame, seed) {
  ctx.save();
  for (let i = 0; i < 70; i++) {
    const x = (i * 53.7 + seed) % W;
    const y = (i * 91.3 + seed * 0.3) % H;
    const tw = (Math.sin(frame * 0.02 + i * 0.7) + 1) * 0.5;
    ctx.globalAlpha = 0.15 + tw * 0.45;
    ctx.fillStyle = i % 7 === 0 ? '#aef' : (i % 11 === 0 ? '#ffd' : '#fff');
    ctx.fillRect(x, y, 1.5, 1.5);
  }
  ctx.restore();
}

function drawCharGlow(ctx, cx, cy, radius, alpha) {
  if (alpha <= 0) return;
  const grad = ctx.createRadialGradient(cx, cy, 10, cx, cy, radius);
  grad.addColorStop(0, `rgba(120, 80, 200, ${0.28 * alpha})`);
  grad.addColorStop(0.4, `rgba(60, 30, 120, ${0.14 * alpha})`);
  grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
  ctx.save();
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height);
  ctx.restore();
}

function makeParticle(canvas, colors, scattered) {
  return {
    x: scattered ? Math.random()*canvas.width : canvas.width/2,
    y: scattered ? Math.random()*-canvas.height : canvas.height/2,
    vx: (Math.random()-0.5)*4,
    vy: scattered ? 1 + Math.random()*3 : (Math.random()-0.5)*6,
    size: 3 + Math.floor(Math.random()*4),
    color: colors[Math.floor(Math.random()*colors.length)],
    gravity: 0.03 + Math.random()*0.05,
    life: 1.5 + Math.random()*1.5,
  };
}

function drawPixelHeart(ctx, cx, cy, size, color) {
  // 7x6 pixel heart
  const shape = [
    [0,1,1,0,1,1,0],
    [1,1,1,1,1,1,1],
    [1,1,1,1,1,1,1],
    [0,1,1,1,1,1,0],
    [0,0,1,1,1,0,0],
    [0,0,0,1,0,0,0],
  ];
  const px = size / 7;
  ctx.save();
  ctx.shadowColor = color;
  ctx.shadowBlur = size;
  for (let r = 0; r < shape.length; r++) {
    for (let c = 0; c < shape[r].length; c++) {
      if (shape[r][c]) {
        ctx.fillStyle = color;
        ctx.fillRect(cx - size/2 + c*px, cy - size/2 + r*px, px+1, px+1);
      }
    }
  }
  ctx.restore();
}

/* ----- BOOT ---------------------------------------------------------- */
document.addEventListener('DOMContentLoaded', () => {
  const start = () => {
    if (State.screen !== 'title') return;
    audio.beep(660, 0.08, 'square', 0.07);
    showIntro(0);
  };
  document.getElementById('startBtn').addEventListener('click', start);
  document.addEventListener('keydown', (e) => {
    if (State.screen === 'title' && (e.key === 'Enter' || e.key === ' ' || e.key === 'z' || e.key === 'x')) start();
  });
  document.getElementById('runBtn').addEventListener('click', runInput);
  document.getElementById('strInput').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); runInput(); }
  });
  document.getElementById('restartBtn').addEventListener('click', () => {
    if (endingTask) endingTask.cancelled = true;
    State.level = 0;
    showIntro(0);
  });
});
