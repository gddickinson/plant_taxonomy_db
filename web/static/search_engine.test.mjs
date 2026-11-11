// node search_engine.test.mjs: the JS search must give the same results as web/search.py. The cases and expected ids
// in tests/fixtures/search_parity.json are computed by scripts/make_search_fixture.py running the Python search on the
// committed database (tests/test_web.py checks the fixture is current).
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { like, searchTaxa } from './search_engine.js';

const fx = JSON.parse(readFileSync(new URL('../../tests/fixtures/search_parity.json', import.meta.url)));
for (const c of fx.cases) {
  const got = searchTaxa(fx.index, fx.rank_order, c.q, c.rank);
  assert.equal(got.total, c.total, JSON.stringify(c));
  assert.deepEqual(got.results.map(t => t.id), c.ids, JSON.stringify(c));
}

// LIKE semantics (SQLite): ASCII-only case folding, % and _ wildcards, regex characters literal.
assert.ok(like('pin')('Pinus'));
assert.ok(like('P_NUS')('pinus'));
assert.ok(like('a%z')('abcz'));
assert.ok(!like('é')('É'));
assert.ok(like('(L.)')('x (L.) y'));
assert.ok(!like('.')('abc'));
console.log(`search_engine: ${fx.cases.length} parity cases ok`);
