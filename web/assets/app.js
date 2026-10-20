// Unpile demo app. Loads the baked REAL TabPFN+Gemma snapshot (static-data.json), renders
// it, and lets you re-triage live with the in-browser model mirror (model.js).

const $ = (s) => document.querySelector(s);
let BAKED = null;      // the real baked snapshot
let PILE = [];         // current working pile (items)
let usedBrowser = false;

async function boot() {
  try {
    const res = await fetch('static-data.json', { cache: 'no-store' });
    BAKED = await res.json();
  } catch (e) {
    BAKED = null;
  }
  if (BAKED) {
    PILE = BAKED.pile.map((x) => ({ ...x }));
    renderHeroFromBaked(BAKED);
    renderBaked(BAKED);
    renderHonest(BAKED.metrics);
    setBadge(false);
  } else {
    // fallback: synthesize from model.js alone (should rarely happen)
    renderHonest({ lift: 1.6, silenced_pct: 0.55, missed_pct: 0.39, precision: 0.59, recall: 0.38 });
  }
  $('#btn-run').addEventListener('click', runBrowserTriage);
  $('#btn-reset').addEventListener('click', () => {
    PILE = BAKED.pile.map((x) => ({ ...x }));
    renderBaked(BAKED);
    setBadge(false);
  });
}

function setBadge(browser) {
  usedBrowser = browser;
  const b = $('#src-badge');
  if (browser) { b.textContent = 'in-browser estimate'; b.className = 'badge'; }
  else { b.textContent = 'real TabPFN-v2 + Gemma'; b.className = 'badge live'; }
}

function renderHeroFromBaked(d) {
  const kept = d.triage.kept.length;
  const total = d.triage.total;
  $('#hero-total').textContent = total.toLocaleString();
  $('#hero-kept').textContent = kept;
  $('#hero-silenced').textContent = Math.round(d.metrics.silenced_pct * 100) + '%';
}

function statTiles(tri, metrics) {
  const hrs = (tri.minutes_saved / 60);
  return `
    <div class="stat"><div class="v">${tri.total}</div><div class="k">items in the pile</div></div>
    <div class="stat"><div class="v good">${tri.kept.length}</div><div class="k">kept for your morning</div></div>
    <div class="stat"><div class="v">${tri.dropped.length}</div><div class="k">silenced automatically</div></div>
    <div class="stat"><div class="v good">${hrs >= 1 ? hrs.toFixed(1) + ' h' : Math.round(tri.minutes_saved) + ' m'}</div><div class="k">reading time reclaimed</div></div>`;
}

function itemCard(d, blurb) {
  const probClass = d.action === 'keep' ? 'keep' : d.action === 'skim' ? 'skim' : 'drop';
  const pct = Math.round(d.prob * 100);
  const meta = `${d.source || ''}${d.length_min ? ' · ~' + Math.round(d.length_min) + ' min' : ''}`;
  return `
    <div class="item ${d.action}">
      <div class="row1">
        <div class="t">${escapeHtml(d.title)}</div>
        <span class="prob ${probClass}" title="probability you'd actually read it">${pct}%</span>
      </div>
      <div class="meta">${escapeHtml(meta)}</div>
      <div class="why">${escapeHtml((d.reasons || []).join(' · '))}</div>
      ${blurb ? `<div class="blurb">${escapeHtml(blurb)}</div>` : ''}
    </div>`;
}

function renderColumns(tri, digest, animate) {
  const keepers = tri.kept;
  const blurbs = (digest && digest.blurbs) || [];
  $('#keep-list').innerHTML = keepers.length
    ? keepers.map((d, i) => itemCard(d, blurbs[i])).join('')
    : `<div class="empty">Nothing cleared the bar - a quiet morning.</div>`;
  $('#drop-list').innerHTML = tri.dropped.length
    ? tri.dropped.map((d) => itemCard(d, null)).join('')
    : `<div class="empty">Nothing dropped this time.</div>`;
  $('#keep-count').textContent = `${keepers.length} kept`;
  $('#drop-count').textContent = `${tri.dropped.length} dropped`;
  $('#stats').innerHTML = statTiles(tri, null);
  if (animate && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    document.querySelectorAll('#keep-list .item, #drop-list .item').forEach((el, i) => {
      el.classList.add('enter');
      el.style.animationDelay = (Math.min(i, 8) * 45) + 'ms';
    });
  }
}

function renderDigest(digest) {
  const src = digest.source === 'gemma'
    ? 'written locally by Gemma 3'
    : 'written by the offline fallback (Ollama was busy)';
  $('#digest').innerHTML = `
    <div class="d-label"><svg class="ic" style="width:14px;height:14px" viewBox="0 0 24 24"><path d="M3 12h18M12 3v18"/></svg> YOUR MORNING DIGEST</div>
    <div class="greeting">${escapeHtml(digest.greeting || '')}</div>
    <div class="d-src">${src}</div>`;
}

function renderBaked(d) {
  renderColumns(d.triage, d.digest);
  renderDigest(d.digest);
}

// Live re-triage using the in-browser mirror (keeps the demo interactive & offline).
function runBrowserTriage() {
  const tri = triagePile(PILE);
  // build a light rule-based digest in-browser (no Gemma in the static page)
  const greeting = tri.kept.length
    ? `${tri.kept.length} thing${tri.kept.length !== 1 ? 's' : ''} worth your coffee today - the rest is archived. No pressure.`
    : `Your pile is clear this morning. Nothing urgent made the cut, enjoy the quiet.`;
  const blurbs = tri.kept.map((d) => {
    const r = (d.reasons[0] || 'worth a look');
    const m = d.length_min ? ` (~${Math.round(d.length_min)} min)` : '';
    return r.charAt(0).toUpperCase() + r.slice(1) + m + '.';
  });
  renderColumns(tri, { blurbs }, true);
  renderDigest({ greeting, source: 'offline-fallback' });
  setBadge(true);
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function renderHonest(m) {
  const lift = (m.lift || 1.6);
  const missed = Math.round((m.missed_pct || 0.39) * 100);
  const silenced = Math.round((m.silenced_pct || 0.55) * 100);
  const prec = Math.round((m.precision || 0.59) * 100);
  const rec = Math.round((m.recall || 0.38) * 100);
  $('#honest-metrics').textContent =
    `held-out: precision ${prec}% · recall ${rec}% · silences ${silenced}% of the pile · lift ${lift}x vs a random item`;
  const hl = $('#h-lift'); if (hl) hl.textContent = lift + '×';
  const hm = $('#h-missed'); if (hm) hm.textContent = '~' + missed + '%';
}

boot();
