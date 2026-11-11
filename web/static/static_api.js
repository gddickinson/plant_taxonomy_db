// Static-site data layer: answers api(path) calls from the JSON files exported by scripts/build_static.py.
// Plain paths map to files (api/taxon/12.json); /search is computed here from the exported index with the same rules
// as web/search.py (search_engine.js).
import { searchTaxa } from './search_engine.js';

const files = new Map();
function file(rel) {
  if (!files.has(rel)) {
    files.set(rel, fetch('api/' + rel + '.json').then(r => { if (!r.ok) throw new Error(`${r.status} ${rel}`); return r.json(); }));
  }
  return files.get(rel);
}

export async function staticApi(path, body) {
  const [p, qs] = path.split('?');
  const q = Object.fromEntries(new URLSearchParams(qs || ''));
  const clean = p.replace(/^\/+|\/+$/g, '');
  if (body) throw new Error('This action needs the full app (Python server).');
  if (clean === 'search') {
    const [index, meta] = await Promise.all([file('taxa'), file('meta')]);
    return searchTaxa(index, meta.rank_order, q.q, q.rank);
  }
  return file(clean);
}
