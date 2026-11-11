// Home (hero, counts by rank, entry cards), the Ranks overview and About.
import { route, api, app, esc, list, isStatic } from './core.js';
import { subsetNote, taxonLink, rankCounts } from './ui.js';

const TILE_RANKS = [['Family', 'families'], ['Genus', 'genera'], ['Species', 'species'], ['Subspecies', 'subspecies'], ['Variety', 'varieties']];

route('home', async () => {
  const meta = await api('/meta');
  const s = meta.stats, by = s.by_rank;
  const focus = meta.focus;
  app().innerHTML = `
  <section class="hero">
    <p class="kicker">ITIS · Kingdom → Species</p>
    <h1 class="glow">Plant Taxonomy Database</h1>
    <p class="lead">A plant taxonomy database built from ITIS (the Integrated Taxonomic Information System): browse the
    hierarchy from kingdom to species, search by scientific or common name, and see each taxon's lineage, children,
    common names and synonyms.</p>
    <form id="hsearch" role="search" class="row"><div><label for="hs-q">Search scientific or common names</label>
      <input id="hs-q" type="search" placeholder="e.g. Pinus, spruce, redwood, Taxus"></div>
      <div style="flex:0"><button type="submit">Search</button></div></form>
  </section>
  ${subsetNote(meta)}
  <div class="tiles">
    <a class="tile" href="#/tree"><b>${s.total_taxa}</b><span>taxa</span></a>
    ${list(TILE_RANKS.filter(([r]) => by[r]), ([r, label]) => `<a class="tile" href="#/search?rank=${r}"><b>${by[r]}</b><span>${label}</span></a>`)}
    <div class="tile"><b>${s.total_common_names}</b><span>common names</span></div>
    <div class="tile"><b>${s.total_synonyms}</b><span>synonyms</span></div>
  </div>
  <div class="grid wide">
    <a class="card" href="#/tree"><b>Taxonomy tree</b><span>Expand the hierarchy rank by rank, from the kingdom down to species and varieties.</span></a>
    <a class="card" href="#/search"><b>Search</b><span>Find taxa by scientific or common name (the database's own search) and filter by rank.</span></a>
    ${focus ? `<a class="card" href="#/taxon/${focus.id}"><b>${esc(focus.name)}</b><span>The ${esc(focus.rank.toLowerCase())} this subset is built from: its families, genera and counts.</span></a>` : ''}
    <a class="card" href="#/ranks"><b>Ranks</b><span>How many taxa of each rank the database holds.</span></a>
    <a class="card" href="#/about"><b>About</b><span>The desktop app, the web app, the data source and how this subset was built.</span></a>
  </div>
  <h2>Start at the top</h2>
  <p>${list(meta.roots, t => taxonLink(t, { rank: true }), ' · ')}</p>`;
  document.getElementById('hsearch').addEventListener('submit', e => {
    e.preventDefault();
    location.hash = '#/search?q=' + encodeURIComponent(document.getElementById('hs-q').value.trim());
  });
});

route('ranks', async () => {
  const meta = await api('/meta');
  const by = meta.stats.by_rank, max = Math.max(...Object.values(by));
  app().innerHTML = `<p class="kicker">Statistics</p><h1>Taxa by rank</h1>
    <p class="lead">Counts from the database's <code>get_statistics()</code>, in taxonomic rank order. Select a rank to list its taxa.</p>
    ${subsetNote(meta)}
    <div class="panel bars">${list(Object.entries(by), ([r, n]) =>
      `<a href="#/search?rank=${encodeURIComponent(r)}">${esc(r)}</a><div class="bar" style="width:${(100 * n / max).toFixed(1)}%"></div><b class="mono">${n}</b>`)}</div>
    <p class="mute small">${rankCounts(by, meta.rank_order)}</p>`;
});

route('about', async () => {
  const meta = await api('/meta');
  const s = meta.subset;
  app().innerHTML = `<p class="kicker">About</p><h1>Plant Taxonomy Database</h1>
  <p class="lead">A modular Python application for building and querying a plant taxonomy database with data from ITIS
  and other sources (GBIF as a fallback). This web interface browses a database the application built.</p>
  <h2>What is in the database</h2>
  <p>SQLite tables for <b>taxa</b> (TSN, rank, scientific name, authorship, parent TSN, classification from kingdom to
  variety, taxonomic status, source), <b>common names</b> (with language) and <b>synonyms</b> (linked to the accepted
  taxon). The tree follows each taxon's parent TSN; lineage, children and search use the database's own queries
  (<code>get_lineage_by_id</code>, <code>get_children_by_taxon_data</code>, <code>search_by_name</code>).</p>
  ${s ? `<h2>The subset shown here</h2>
  <p>${esc(s.root_name)} (TSN ${s.root_tsn}) and everything below it, plus its lineage up to the kingdom: ${meta.stats.total_taxa}
  taxa, ${meta.stats.total_common_names} common names and ${meta.stats.total_synonyms} synonyms. Downloaded from the ITIS web
  services on ${esc(s.downloaded)} by <code>${esc(s.builder)}</code>, which walks the tree with the repo's
  <code>ITISClient</code> and stores it with <code>TaxonomyDatabase</code>. ITIS data are produced by the US government and are in the
  public domain; see THIRD_PARTY.md. ITIS is updated continually, so names and counts may have changed since.</p>` : ''}
  <h2>Run the desktop app</h2>
  <pre>pip install -r requirements.txt
python launcher.py          # PyQt5 GUI (or: python taxonomy_gui.py)
python demo.py --interactive
python populate_database.py --db plants_populated.db</pre>
  <h2>Run the web app</h2>
  <pre>pip install -r requirements-web.txt
python run_web.py                      # http://127.0.0.1:8113, the committed ITIS subset
python run_web.py --db plants_populated.db   # any database the repo built</pre>
  <p>The static site (GitHub Pages) is the same front end reading JSON exported from the committed subset; search runs in
  the browser with the same rules as the server (checked by a parity test).
  ${isStatic() ? '' : `<br>This local app is reading <code>${esc(meta.database)}</code>.`}</p>
  <h2>Credits</h2>
  <p>Taxonomic data: <a href="https://www.itis.gov">ITIS</a>, Integrated Taxonomic Information System, with thanks to
  USGS for maintaining the ITIS web services. Built with AI assistance from Claude (Anthropic). MIT licence.</p>`;
});
