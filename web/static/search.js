// Search: scientific or common name (the database's search_by_name) with a rank filter; URL keeps the query.
import { route, api, app, esc, list } from './core.js';
import { taxonLink } from './ui.js';

route('search', async (_args, query) => {
  const meta = await api('/meta');
  const ranks = Object.keys(meta.stats.by_rank);
  app().innerHTML = `<p class="kicker">Search</p><h1>Search taxa</h1>
    <p class="lead">Matches any part of a scientific name or a common name (case-insensitive; <code>_</code> and
    <code>%</code> work as wildcards, as in the database's SQL search). Choose a rank alone to list every taxon of that rank.</p>
    <div class="filters panel">
      <div><label for="s-q">Scientific or common name</label><input id="s-q" type="search" value="${esc(query.q || '')}" placeholder="e.g. Abies, fir, var."></div>
      <div><label for="s-rank">Rank</label><select id="s-rank"><option value="">Any rank</option>
        ${list(ranks, r => `<option ${r === query.rank ? 'selected' : ''}>${esc(r)}</option>`)}</select></div>
    </div>
    <p id="s-count" class="mute small" aria-live="polite"></p><div id="s-out"></div>`;
  const q = document.getElementById('s-q'), rank = document.getElementById('s-rank');
  let seq = 0;
  async function run() {
    const n = ++seq;
    const params = new URLSearchParams(Object.entries({ q: q.value.trim(), rank: rank.value }).filter(([, v]) => v)).toString();
    history.replaceState(null, '', '#/search' + (params ? '?' + params : ''));
    const r = await api('/search' + (params ? '?' + params : ''));
    if (n !== seq) return;
    document.getElementById('s-count').textContent = !r.q && !r.rank ? 'Type a name or choose a rank.'
      : `${r.total} match${r.total === 1 ? '' : 'es'}${r.total > r.results.length ? `, showing the first ${r.results.length}` : ''}`;
    document.getElementById('s-out').innerHTML = !r.results.length ? '' : `<div class="scroll"><table>
      <thead><tr><th>Taxon</th><th>Rank</th><th>Common names</th></tr></thead><tbody>
      ${list(r.results, t => `<tr><td>${taxonLink(t, { author: true })}</td><td>${esc(t.rank)}</td><td class="common">${esc(t.common.slice(0, 4).join(', '))}${t.common.length > 4 ? ' …' : ''}</td></tr>`)}
      </tbody></table></div>`;
  }
  q.addEventListener('input', run);
  rank.addEventListener('change', run);
  await run();
});
