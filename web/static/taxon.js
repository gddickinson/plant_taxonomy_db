// Taxon detail: lineage, rank and classification, common names, synonyms and children (from /api/taxon/<id>).
import { route, api, app, esc, list } from './core.js';
import { kv, sciName, taxonLink, rankCounts, or } from './ui.js';

const CLASSIFICATION = [['Kingdom', 'kingdom'], ['Division', 'division'], ['Class', 'class'], ['Order', 'order_name'],
  ['Family', 'family'], ['Genus', 'genus'], ['Species epithet', 'species'], ['Subspecies', 'subspecies'], ['Variety', 'variety']];
const itis = tsn => `https://www.itis.gov/servlet/SingleRpt/SingleRpt?search_topic=TSN&search_value=${tsn}`;

route('taxon', async ([id]) => {
  const [meta, t] = await Promise.all([api('/meta'), api('/taxon/' + encodeURIComponent(id))]);
  const byRank = {};
  t.children.forEach(c => (byRank[c.rank] = byRank[c.rank] || []).push(c));
  const cls = CLASSIFICATION.filter(([, k]) => t[k]);
  app().innerHTML = `
    <div class="lineage" role="navigation" aria-label="Lineage">${list(t.lineage, a => taxonLink(a), '<span class="sep">›</span>')}</div>
    <p class="kicker">${esc(t.rank || 'Taxon')}</p>
    <h1>${sciName(t.name, t.rank)} ${t.authorship ? `<span class="auth">${esc(t.authorship)}</span>` : ''}</h1>
    ${t.synonym_of.length ? `<p class="callout">Listed as a synonym of ${list(t.synonym_of, a => taxonLink(a), ', ')}.</p>` : ''}
    ${kv([
      ['Rank', t.rank],
      ['TSN', t.tsn ? `<a href="${itis(t.tsn)}" target="_blank" rel="noopener">${t.tsn}</a>` : '—', true],
      ['Taxonomic status', t.taxonomic_status],
      ['Source', t.source],
      ['Below it', rankCounts(t.descendants, meta.rank_order) || 'nothing in this database'],
    ])}
    <p><a href="#/tree?open=${t.id}">Show in the tree</a></p>
    ${cls.length ? `<h2>Classification</h2>${kv(cls.map(([label, k]) => [label, t[k]]))}` : ''}
    <h2>Common names</h2>
    ${t.common_names.length ? `<p>${list(t.common_names, c => `<span class="tag a">${esc(c.name)}${c.language && c.language !== 'en' ? ` · ${esc(c.language)}` : ''}</span>`)}</p>`
      : '<p class="mute">None recorded.</p>'}
    <h2>Synonyms</h2>
    ${t.synonyms.length ? `<div class="scroll"><table><thead><tr><th>Name</th><th>Author</th><th>TSN</th></tr></thead><tbody>
      ${list(t.synonyms, s => `<tr><td>${sciName(s.name, t.rank)}</td><td>${esc(or(s.author))}</td><td><a href="${itis(s.tsn)}" target="_blank" rel="noopener">${s.tsn}</a></td></tr>`)}
      </tbody></table></div>` : '<p class="mute">None recorded.</p>'}
    <h2>Children <span class="mute small">(${t.children.length})</span></h2>
    ${t.children.length ? list(Object.entries(byRank), ([rank, kids]) => `<h3>${esc(rank)} (${kids.length})</h3>
      <div class="grid">${list(kids, c => `<a class="card" href="#/taxon/${c.id}"><b>${sciName(c.name, c.rank)}</b>${c.author ? `<small>${esc(c.author)}</small>` : ''}</a>`)}</div>`)
      : '<p class="mute">No children in this database.</p>'}`;
});
