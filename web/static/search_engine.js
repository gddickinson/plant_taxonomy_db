// Taxon search: an exact mirror of web/search.py (the repo's TaxonomyDatabase.search_by_name plus a rank filter),
// used by static_api.js to answer /api/search on the static site from the exported /api/taxa index.
// SQL LIKE '%q%': ASCII-only case folding, '%' matches any run of characters and '_' any single character.

const asciiLower = s => String(s).replace(/[A-Z]/g, c => c.toLowerCase());

// A predicate equivalent to SQLite `value LIKE '%term%'`.
export function like(term) {
  const body = [...asciiLower(term)].map(c => c === '%' ? '[\\s\\S]*' : c === '_' ? '[\\s\\S]'
    : c.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('');
  const re = new RegExp(body, 'u');
  return v => v !== null && v !== undefined && re.test(asciiLower(v));
}

// index: [{id, tsn, name, rank, author, common: [names]}]; rankOrder: models.taxonomy.RANK_ORDER (from /api/meta).
export function searchTaxa(index, rankOrder, q = '', rank = '', limit = 500) {
  q = String(q || '').trim(); rank = String(rank || '').trim();
  if (!q && !rank) return { q, rank, total: 0, results: [] };
  const m = like(q);
  let rows = index.filter(t => m(t.name) || (t.tsn !== null && t.tsn !== undefined && (t.common || []).some(m)));
  if (rank) rows = rows.filter(t => t.rank === rank);
  const level = r => { const i = rankOrder.indexOf(r); return i < 0 ? 999 : i; };
  const cmp = (a, b) => a < b ? -1 : a > b ? 1 : 0;
  rows.sort((a, b) => level(a.rank) - level(b.rank) || cmp(a.name, b.name) || a.id - b.id);
  return { q, rank, total: rows.length, results: rows.slice(0, limit) };
}
