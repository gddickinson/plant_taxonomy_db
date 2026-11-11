// Entry point: registers the page modules (loaded on first visit), sets the mode line and starts the router.
import { start, route, lazy, app, $, isStatic } from './core.js';

const PAGES = { 'home.js': ['home', 'about', 'ranks'], 'tree.js': ['tree'], 'taxon.js': ['taxon'], 'search.js': ['search'] };
lazy(Object.fromEntries(Object.entries(PAGES).flatMap(([file, names]) => names.map(n => [n, () => import('./' + file)]))));

route('notfound', () => { app().innerHTML = '<h1>Not found</h1><p><a href="#/">Back to the start</a></p>'; });

$('#mode').textContent = isStatic() ? 'static site (ITIS subset)' : 'local app';
start();
