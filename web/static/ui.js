// Shared building blocks: taxon names and links (italic from genus down, as botanical convention), rank labels,
// key/value panels and the site's data-subset notice.
import { esc, list } from './core.js';

const ITALIC = new Set(['Genus', 'Subgenus', 'Section', 'Subsection', 'Species', 'Subspecies', 'Variety', 'Subvariety', 'Form', 'Subform']);
export const isItalic = rank => ITALIC.has(rank);
export const or = (v, dash = '—') => (v === null || v === undefined || v === '' ? dash : v);

// Scientific name with ITIS-style connecting terms (var., ssp., subsp., f., x) kept upright.
export function sciName(name, rank) {
  if (!isItalic(rank)) return esc(name);
  return String(name).split(' ').map(w => /^(var\.|ssp\.|subsp\.|f\.|x|X|×)$/.test(w) ? esc(w) : `<i>${esc(w)}</i>`).join(' ');
}

export const taxonHref = t => `#/taxon/${t.id}`;
export const taxonLink = (t, { rank = false, author = false } = {}) =>
  `${rank ? `<span class="rank">${esc(t.rank)}</span>` : ''}<a href="${taxonHref(t)}">${sciName(t.name, t.rank)}</a>${author && t.author ? ` <span class="auth">${esc(t.author)}</span>` : ''}`;

export function kv(pairs) {
  return `<div class="kv">${list(pairs, ([label, value, raw]) =>
    `<div><b>${raw ? value : esc(or(value))}</b><span>${esc(label)}</span></div>`)}</div>`;
}

export const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;

// Counts like {Species: 12, Variety: 3} as "12 species · 3 varieties" (rank order kept from the caller).
const PLURALS = { Species: 'species', Variety: 'varieties', Subspecies: 'subspecies', Genus: 'genera', Family: 'families', Class: 'classes', Subclass: 'subclasses', Order: 'orders', Division: 'divisions', Subdivision: 'subdivisions' };
export function rankCounts(counts, rankOrder) {
  const ranks = Object.keys(counts || {}).sort((a, b) => (rankOrder.indexOf(a) + 1 || 999) - (rankOrder.indexOf(b) + 1 || 999));
  return ranks.map(r => `${counts[r]} ${counts[r] === 1 ? r.toLowerCase() : (PLURALS[r] || r.toLowerCase() + 's')}`).join(' · ');
}

// Which data the page is showing (the committed ITIS subset on the static site, or any database locally).
export function subsetNote(meta) {
  const s = meta.subset;
  if (!s) return `<div class="callout">Database <code>${esc(meta.database)}</code>: ${meta.stats.total_taxa} taxa.</div>`;
  return `<div class="callout a">Showing <b>${esc(s.root_name)}</b> (ITIS TSN ${s.root_tsn}) and its lineage:
    ${s.subtree_taxa} taxa in the subtree, downloaded from <a href="https://www.itis.gov">ITIS</a> on ${esc(s.downloaded)}
    with <code>${esc(s.builder)}</code>. This is a subset for the web site, not all plants: the local app can browse any
    database the repo builds.</div>`;
}
