// Taxonomy tree: the whole hierarchy from /api/tree as nested <details>, opened down to the subset's focus taxon.
// #/tree?open=<id> opens the path to that taxon, highlights it and scrolls to it.
import { route, api, app, esc, list } from './core.js';
import { sciName, subsetNote } from './ui.js';

const LEAF_RANKS = new Set(['Species', 'Subspecies', 'Variety', 'Subvariety', 'Form', 'Subform']);

// Number of species below a node (for the count shown after each name).
function speciesBelow(n) {
  return n.children.reduce((s, c) => s + (c.rank === 'Species' ? 1 : 0) + speciesBelow(c), 0);
}

// Ids on the path from a root to the node with id `target` (empty if absent).
export function pathTo(nodes, target) {
  for (const n of nodes) {
    if (n.id === target) return [n.id];
    const p = pathTo(n.children, target);
    if (p.length) return [n.id, ...p];
  }
  return [];
}

function render(n, open, hit) {
  const name = `<a href="#/taxon/${n.id}">${sciName(n.name, n.rank)}</a>`;
  const label = `<span class="rank">${esc(n.rank)}</span>${name}`;
  const cls = n.id === hit ? ' class="hit"' : '';
  if (!n.children.length) return `<li${cls} id="t${n.id}"><span class="leaf">${label}</span></li>`;
  const sp = LEAF_RANKS.has(n.rank) ? 0 : speciesBelow(n);
  const count = sp ? `<span class="n">${sp} sp.</span>` : `<span class="n">${n.children.length}</span>`;
  return `<li${cls} id="t${n.id}"><details${open.has(n.id) ? ' open' : ''}><summary>${label}${count}</summary>
    <ul>${list(n.children, c => render(c, open, hit))}</ul></details></li>`;
}

route('tree', async (_args, query) => {
  const [meta, tree] = await Promise.all([api('/meta'), api('/tree')]);
  const target = +query.open || (meta.focus ? meta.focus.id : null);
  const path = target ? pathTo(tree, target) : [];
  const open = new Set(query.open ? path.slice(0, -1) : path);  // focus taxon itself opens one level too
  app().innerHTML = `<p class="kicker">Browse</p><h1>Taxonomy tree</h1>
    <p class="lead">Every taxon in the database, nested by parent. Select a name for its details; the count after a
    name is the number of species below it.</p>
    ${subsetNote(meta)}
    <div class="row" style="flex:0"><div style="flex:0"><button class="alt" id="t-open" type="button">Expand all</button></div>
      <div style="flex:0"><button class="alt" id="t-close" type="button">Collapse all</button></div></div>
    <div class="panel"><ul class="tree">${list(tree, n => render(n, open, query.open ? target : null))}</ul></div>`;
  const all = open => document.querySelectorAll('.tree details').forEach(d => { d.open = open; });
  document.getElementById('t-open').addEventListener('click', () => all(true));
  document.getElementById('t-close').addEventListener('click', () => all(false));
  if (query.open) document.getElementById('t' + target)?.scrollIntoView({ block: 'center' });
});
