// Звуковой движок на Web Audio API — процедурный синтез, без ассетов и зависимостей.
// Контекст создаётся лениво: autoplay-политика браузера требует пользовательский жест.
// Копируй как есть, меняй набор SoundName и рецепты SYNTH под свой проект.

export type SoundName = 'dice' | 'spin' | 'wheelLand' | 'cardFlip' | 'reveal' | 'tick';

const MUTE_KEY = 'app.muted'; // поменяй на ключ своего проекта (напр. 'ao.muted')

let ctx: AudioContext | null = null;
let master: GainNode | null = null;
let muted = typeof localStorage !== 'undefined' && localStorage.getItem(MUTE_KEY) === '1';
const listeners = new Set<() => void>();

export function isMuted(): boolean {
  return muted;
}

export function setMuted(value: boolean): void {
  muted = value;
  try {
    localStorage.setItem(MUTE_KEY, value ? '1' : '0');
  } catch {
    /* ignore */
  }
  listeners.forEach((fn) => fn());
}

export function toggleMuted(): void {
  setMuted(!muted);
}

export function subscribe(fn: () => void): () => void {
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
}

function ensureCtx(): AudioContext | null {
  if (ctx) return ctx;
  const AC = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AC) return null;
  ctx = new AC();
  master = ctx.createGain();
  master.gain.value = 0.9;
  master.connect(ctx.destination);
  return ctx;
}

// Разблокировать аудио на первом жесте пользователя (autoplay-политика).
export function unlock(): void {
  const c = ensureCtx();
  if (c && c.state === 'suspended') c.resume().catch(() => {});
}

// Примитивы синтеза.
function tone(freq: number, start: number, dur: number, opts: { type?: OscillatorType; gain?: number; sweepTo?: number } = {}) {
  const c = ensureCtx();
  if (!c || !master) return;
  const { type = 'sine', gain = 0.3, sweepTo } = opts;
  const osc = c.createOscillator();
  const g = c.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(freq, start);
  if (sweepTo) osc.frequency.exponentialRampToValueAtTime(sweepTo, start + dur);
  g.gain.setValueAtTime(0.0001, start);
  g.gain.exponentialRampToValueAtTime(gain, start + 0.01);
  g.gain.exponentialRampToValueAtTime(0.0001, start + dur);
  osc.connect(g);
  g.connect(master);
  osc.start(start);
  osc.stop(start + dur + 0.05);
}

function noise(start: number, dur: number, opts: { freq?: number; q?: number; gain?: number } = {}) {
  const c = ensureCtx();
  if (!c || !master) return;
  const { freq = 2000, q = 1, gain = 0.4 } = opts;
  const len = Math.max(1, Math.floor(c.sampleRate * dur));
  const buffer = c.createBuffer(1, len, c.sampleRate);
  const data = buffer.getChannelData(0);
  for (let i = 0; i < len; i++) data[i] = Math.random() * 2 - 1;
  const src = c.createBufferSource();
  src.buffer = buffer;
  const filter = c.createBiquadFilter();
  filter.type = 'bandpass';
  filter.frequency.value = freq;
  filter.Q.value = q;
  const g = c.createGain();
  g.gain.setValueAtTime(gain, start);
  g.gain.exponentialRampToValueAtTime(0.0001, start + dur);
  src.connect(filter);
  filter.connect(g);
  g.connect(master);
  src.start(start);
}

// Конкретные звуки.
const SYNTH: Record<SoundName, () => void> = {
  // бросок костей — шумовой всплеск + несколько «клацающих» щелчков
  dice() {
    const c = ensureCtx();
    if (!c) return;
    const t = c.currentTime;
    noise(t, 0.2, { freq: 3000, q: 1, gain: 0.35 });
    [0.04, 0.08, 0.12].forEach((dt, i) => {
      tone(2200 + i * 300, t + dt, 0.03, { type: 'square', gain: 0.15 });
    });
  },
  // старт вращения колеса — «вух»
  spin() {
    const c = ensureCtx();
    if (!c) return;
    noise(c.currentTime, 0.35, { freq: 800, q: 2, gain: 0.25 });
  },
  // выпало — «мистический» колокольчик (обертоны)
  wheelLand() {
    const c = ensureCtx();
    if (!c) return;
    const t = c.currentTime;
    tone(880, t, 0.9, { gain: 0.25 });
    tone(1320, t, 0.7, { gain: 0.12 });
    tone(1760, t + 0.02, 0.5, { gain: 0.06 });
  },
  // флип карты — короткий «свист» (сдвиг частоты вверх)
  cardFlip() {
    const c = ensureCtx();
    if (!c) return;
    const t = c.currentTime;
    noise(t, 0.12, { freq: 1200, q: 2, gain: 0.3 });
    tone(400, t, 0.12, { type: 'triangle', gain: 0.15, sweepTo: 900 });
  },
  // раскрытие / успех — восходящий двухнотный перезвон
  reveal() {
    const c = ensureCtx();
    if (!c) return;
    const t = c.currentTime;
    tone(659.25, t, 0.25, { gain: 0.22 }); // E5
    tone(880, t + 0.08, 0.5, { gain: 0.2 }); // A5
  },
  // тихий тик — обновление матрицы / UI
  tick() {
    const c = ensureCtx();
    if (!c) return;
    tone(1200, c.currentTime, 0.03, { type: 'square', gain: 0.06 });
  },
};

// Точка входа: проиграть звук по имени (молча, если muted или аудио недоступно).
export function play(name: SoundName): void {
  if (muted) return;
  const c = ensureCtx();
  if (!c) return;
  if (c.state === 'suspended') {
    c.resume().then(() => SYNTH[name]()).catch(() => {});
  } else {
    SYNTH[name]();
  }
}
