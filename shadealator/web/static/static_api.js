// Static-site data layer: answers api() calls from the JSON exported by scripts/build_static.py. The demo reach runs
// in the browser (pipeline.js) on both the static site and the local app, so the only POST, /run (the same pipeline
// in Python, used to cross-check the browser), needs the local server.
const files = new Map();
async function file(rel) {
  if (!files.has(rel)) files.set(rel, fetch('api/' + rel + '.json').then(r => { if (!r.ok) throw new Error(`${r.status} ${rel}`); return r.json(); }));
  return files.get(rel);
}

export const NEEDS_SERVER = 'needs the full app running locally (Python server): see the README, "Run the web app"';

export async function staticApi(path, body) {
  const clean = path.split('?')[0].replace(/^\/+/, '');
  if (clean === 'run') throw new Error('Running the Python pipeline ' + NEEDS_SERVER + '.');
  return file(clean);
}
