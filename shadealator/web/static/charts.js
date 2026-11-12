// Small canvas charts shared by the pages: a line/dot chart with axes and a hover crosshair + tooltip, and the
// sequential shade ramp (one hue, dim -> bright on the dark surface). One y axis per chart, never two.
import { esc } from './core.js';

export const COLORS = { a: '#59f0a0', b: '#ffb347', c: '#4fc3ff', ink: '#e8f1ff', mute: '#94a3c6', grid: '#1a2340' };

// Sequential ramp for a 0-1 magnitude (shade fraction): dark teal -> bright green.
export function ramp(t) {
  t = Math.min(Math.max(t, 0), 1);
  const a = [22, 52, 58], b = [89, 240, 160];
  const c = a.map((v, i) => Math.round(v + (b[i] - v) * Math.sqrt(t)));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}

export function fit(canvas, h) {
  const dpr = window.devicePixelRatio || 1, w = canvas.clientWidth || canvas.parentElement.clientWidth || 600;
  canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr); canvas.style.height = h + 'px';
  const g = canvas.getContext('2d'); g.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { g, w, h };
}

const nice = (lo, hi, n = 5) => {
  if (!(hi > lo)) { hi = lo + 1; }
  const step0 = (hi - lo) / n, mag = 10 ** Math.floor(Math.log10(step0));
  const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= step0);
  const ticks = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) ticks.push(+v.toFixed(10));
  return ticks;
};
const fmtTick = v => (Math.abs(v) >= 1000 ? v.toFixed(0) : +v.toPrecision(4)).toString();

// series: [{ label, color, xs, ys, dots?:bool }]. opts: { height, xlabel, ylabel, ylim, tip(i, s) -> html, onPick(i) }
export function lineChart(host, series, opts = {}) {
  host.classList.add('plot');
  host.innerHTML = `<canvas role="img" aria-label="${esc(opts.aria || opts.ylabel || 'chart')}"></canvas><div class="tip"></div>`;
  const canvas = host.querySelector('canvas'), tip = host.querySelector('.tip');
  const all = series.flatMap(s => s.xs.map((x, i) => [x, s.ys[i]])).filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y));
  let [x0, x1] = [Math.min(...all.map(p => p[0])), Math.max(...all.map(p => p[0]))];
  let [y0, y1] = opts.ylim || [Math.min(...all.map(p => p[1])), Math.max(...all.map(p => p[1]))];
  if (y1 - y0 < 1e-9) { y0 -= 1; y1 += 1; }
  const pad = (y1 - y0) * 0.06; if (!opts.ylim) { y0 -= pad; y1 += pad; }
  const M = { l: 58, r: 14, t: 12, b: 38 };
  let hover = null;
  const draw = () => {
    const { g, w, h } = fit(canvas, opts.height || 240);
    const X = x => M.l + (x - x0) / ((x1 - x0) || 1) * (w - M.l - M.r);
    const Y = y => h - M.b - (y - y0) / (y1 - y0) * (h - M.t - M.b);
    g.font = '11px ui-monospace, Menlo, monospace'; g.fillStyle = COLORS.mute; g.strokeStyle = COLORS.grid; g.lineWidth = 1;
    for (const t of nice(y0, y1)) { g.beginPath(); g.moveTo(M.l, Y(t)); g.lineTo(w - M.r, Y(t)); g.stroke(); g.textAlign = 'right'; g.fillText(fmtTick(t), M.l - 6, Y(t) + 4); }
    for (const t of nice(x0, x1, Math.max(2, Math.floor((w - 80) / 90)))) { g.textAlign = 'center'; g.fillText(fmtTick(t), X(t), h - M.b + 15); }
    g.textAlign = 'center'; if (opts.xlabel) g.fillText(opts.xlabel, (M.l + w - M.r) / 2, h - 6);
    if (opts.ylabel) { g.save(); g.translate(12, (M.t + h - M.b) / 2); g.rotate(-Math.PI / 2); g.fillText(opts.ylabel, 0, 0); g.restore(); }
    for (const s of series) {
      g.strokeStyle = s.color; g.fillStyle = s.color; g.lineWidth = 2; g.beginPath();
      let pen = false;
      s.xs.forEach((x, i) => { const y = s.ys[i]; if (!Number.isFinite(y)) { pen = false; return; } pen ? g.lineTo(X(x), Y(y)) : g.moveTo(X(x), Y(y)); pen = true; });
      if (!s.dotsOnly) g.stroke();
      if (s.dots) s.xs.forEach((x, i) => { if (Number.isFinite(s.ys[i])) { g.beginPath(); g.arc(X(x), Y(s.ys[i]), s.r || 3.5, 0, 7); g.fill(); } });
    }
    if (opts.mark != null && series[0].xs[opts.mark] != null) {
      const mx = X(series[0].xs[opts.mark]); g.strokeStyle = COLORS.b; g.setLineDash([4, 4]); g.beginPath(); g.moveTo(mx, M.t); g.lineTo(mx, h - M.b); g.stroke(); g.setLineDash([]);
    }
    if (hover != null) {
      const s0 = series[0], hx = X(s0.xs[hover]);
      g.strokeStyle = COLORS.mute; g.beginPath(); g.moveTo(hx, M.t); g.lineTo(hx, h - M.b); g.stroke();
      for (const s of series) if (Number.isFinite(s.ys[hover])) { g.fillStyle = s.color; g.strokeStyle = '#05060c'; g.lineWidth = 2; g.beginPath(); g.arc(hx, Y(s.ys[hover]), 5, 0, 7); g.fill(); g.stroke(); }
    }
    return { X, w };
  };
  let geo = draw();
  const nearest = ev => {
    const rect = canvas.getBoundingClientRect(), px = ev.clientX - rect.left, xs = series[0].xs;
    let best = 0; xs.forEach((x, i) => { if (Math.abs(geo.X(x) - px) < Math.abs(geo.X(xs[best]) - px)) best = i; });
    return { i: best, px, py: ev.clientY - rect.top, w: rect.width };
  };
  canvas.addEventListener('pointermove', ev => {
    const n = nearest(ev); hover = n.i; geo = draw();
    tip.innerHTML = opts.tip ? opts.tip(n.i) : series.map(s => `${esc(s.label)}: ${fmtTick(s.ys[n.i])}`).join('<br>');
    tip.style.display = 'block';
    tip.style.left = Math.min(n.px + 14, n.w - tip.offsetWidth - 4) + 'px'; tip.style.top = Math.max(0, n.py - 10) + 'px';
  });
  canvas.addEventListener('pointerleave', () => { hover = null; tip.style.display = 'none'; geo = draw(); });
  if (opts.onPick) canvas.addEventListener('click', ev => opts.onPick(nearest(ev).i));
  return { redraw: () => { geo = draw(); } };
}

export function legend(items) {
  return `<div class="legend">${items.map(([c, l, sq]) => `<span><i class="${sq ? 'sq' : ''}" style="background:${c}"></i>${esc(l)}</span>`).join('')}</div>`;
}
