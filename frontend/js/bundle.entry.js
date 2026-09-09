// The one bundle, for every page. app.js and temp.js import what they need from
// vendor/, so esbuild resolves the whole graph -- no globals, no load order to keep.
//
// temp.js has no side effects at module level: it exposes window.initCharts, and only
// index.html calls it. That keeps /timeseries to the page that shows a chart.
import './app.js';
import './temp.js';
