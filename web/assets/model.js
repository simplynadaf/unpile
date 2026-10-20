// Unpile in-browser triage model.
//
// The real app decides with TabPFN-v2 (an open-weight tabular model) running locally in
// Python. GitHub Pages can't run Python, so this is a faithful JS APPROXIMATION of the
// same relationships TabPFN learns from the saved-items dataset (data/saved_items.csv),
// tuned to the same read/rot drivers so the demo behaves like the real thing: toggle any
// item's signals and the keep/skim/drop decision and probability update instantly.
//
// It is clearly labeled in the UI as a browser estimate. For the real TabPFN decision
// (with its measured precision/recall/lift), clone the repo and run `python run.py`.

const KEEP_T = 0.55;
const DROP_T = 0.40;

// source_id -> baseline "I come back to this source" pull (mirrors build_dataset.py).
const SOURCE_PULL = { 0: 0.02, 1: -0.05, 2: -0.12, 3: -0.10, 4: 0.18, 5: 0.22, 6: 0.08, 7: 0.0 };

function sigmoid(z) { return 1 / (1 + Math.exp(-z)); }

// Core read-probability model: mirrors the latent score in scripts/build_dataset.py so the
// JS estimate tracks what the local TabPFN model learns. Deterministic (no noise).
function readProb(f) {
  let z = 0.0;
  z += (SOURCE_PULL[f.source_id] ?? 0.0) * 3.0;
  z += (f.topic_affinity - 0.5) * 3.2;
  z += 0.9 * f.reopen_count;
  z += 0.8 * f.is_howto;
  z -= 0.015 * f.length_min;
  z -= 0.004 * f.age_days;
  z -= 0.0012 * f.backlog_size;
  z -= 0.35 * f.has_video;
  z += (f.save_hour >= 6 && f.save_hour <= 10) ? 0.25 : 0.0;
  z += (f.topic_id === 5) ? -0.2 : 0.0;
  return sigmoid(z);
}

function decide(p) {
  if (p >= KEEP_T) return 'keep';
  if (p <= DROP_T) return 'drop';
  return 'skim';
}

function reasonsFor(f) {
  const r = [];
  if (f.reopen_count >= 2) r.push(`you reopened it ${Math.round(f.reopen_count)}x (real intent)`);
  if (f.topic_affinity >= 0.7) r.push('squarely in your usual lane');
  else if (f.topic_affinity <= 0.3) r.push('far from what you usually read');
  if (f.is_howto === 1) r.push('actionable how-to');
  if (f.length_min >= 30) r.push(`${Math.round(f.length_min)}-min longread (likely tl;dr)`);
  if (f.age_days >= 120) r.push(`${Math.round(f.age_days)} days stale`);
  if (f.has_video === 1) r.push("'watch later' video");
  if (f.backlog_size >= 500) r.push('buried deep in the pile');
  if (!r.length) r.push('a borderline call either way');
  return r.slice(0, 3);
}

// Triage a whole pile in the browser, returning the same shape the API returns.
function triagePile(items) {
  const kept = [], skim = [], dropped = [];
  let minutesSaved = 0;
  for (const f of items) {
    const p = readProb(f);
    const action = decide(p);
    const d = {
      action, prob: round2(p), reasons: reasonsFor(f), title: f.title,
      source: f.source || '', topic: f.topic || '', length_min: f.length_min,
    };
    if (action === 'keep') kept.push(d);
    else if (action === 'skim') skim.push(d);
    else { dropped.push(d); minutesSaved += f.length_min || 0; }
  }
  kept.sort((a, b) => b.prob - a.prob);
  skim.sort((a, b) => b.prob - a.prob);
  dropped.sort((a, b) => a.prob - b.prob);
  return { kept, skim, dropped, total: items.length, minutes_saved: round1(minutesSaved),
           model: 'in-browser estimate (mirrors TabPFN-v2)' };
}

function round2(x) { return Math.round(x * 100) / 100; }
function round1(x) { return Math.round(x * 10) / 10; }
