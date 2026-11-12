// Entry point: lazy page modules, the mode label, a subtle drifting-shade background, then the router.
import { $, app, isStatic, lazy, route, start } from './core.js';

const PAGES = { 'home.js': ['home'], 'workflow.js': ['workflow'], 'demo.js': ['demo'], 'results.js': ['results'],
  'about.js': ['about'] };
lazy(Object.fromEntries(Object.entries(PAGES).flatMap(([file, names]) => names.map(n => [n, () => import('./' + file)]))));
route('notfound', () => { app().innerHTML = '<h1>Not found</h1><p><a href="#/">Back to the start</a></p>'; });

$('#mode').textContent = isStatic()
  ? 'static site: the TTools maths runs in your browser; ArcGIS and Excel steps are described, not run'
  : 'local app: Python runs the original Step-script functions on this computer';

// Background: a few soft leaf-coloured shadows drifting slowly. Off under prefers-reduced-motion.
function background(canvas) {
  if (!canvas || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const g = canvas.getContext('2d');
  const fitBg = () => { canvas.width = innerWidth; canvas.height = innerHeight; };
  fitBg(); addEventListener('resize', fitBg);
  const blobs = Array.from({ length: 7 }, (_, i) => ({ x: Math.random(), y: Math.random(), r: 80 + Math.random() * 140,
    v: 0.00004 + Math.random() * 0.00006, c: i % 3 === 0 ? '255,179,71' : '89,240,160' }));
  let last = 0;
  const tick = t => {
    requestAnimationFrame(tick);
    if (document.hidden || t - last < 80) return;
    last = t;
    g.clearRect(0, 0, canvas.width, canvas.height);
    for (const b of blobs) {
      b.x = (b.x + b.v) % 1.2;
      const x = (b.x - 0.1) * canvas.width, y = b.y * canvas.height;
      const grd = g.createRadialGradient(x, y, 0, x, y, b.r);
      grd.addColorStop(0, `rgba(${b.c},.10)`); grd.addColorStop(1, `rgba(${b.c},0)`);
      g.fillStyle = grd; g.beginPath(); g.arc(x, y, b.r, 0, 7); g.fill();
    }
  };
  requestAnimationFrame(tick);
}
background($('#bg'));
start();
