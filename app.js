/* ─── app.js – PG Finder Frontend Logic ──────────────────── */

// ── Populate college dropdown on load ──────────────────────
(async function loadColleges() {
  const sel = document.getElementById('college');
  try {
    const res  = await fetch('/colleges');
    const data = await res.json();
    data.colleges.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c;
      opt.textContent = c;
      sel.appendChild(opt);
    });
  } catch (e) {
    console.error('Could not fetch colleges:', e);
  }
})();

// ── Rent slider display ─────────────────────────────────────
function updateRentDisplay(val) {
  const formatted = Number(val).toLocaleString('en-IN');
  document.getElementById('rentDisplay').textContent = `₹${formatted} / month`;

  // Update slider gradient fill
  const min = 3000, max = 15000;
  const pct = ((val - min) / (max - min)) * 100;
  const input = document.getElementById('rent');
  input.style.background = `linear-gradient(to right, #7c3aed ${pct}%, rgba(255,255,255,0.08) ${pct}%)`;
}

// Trigger once on load
window.addEventListener('DOMContentLoaded', () => {
  updateRentDisplay(document.getElementById('rent').value);
});

// ── Search PGs ─────────────────────────────────────────────
async function searchPGs(e) {
  e.preventDefault();

  const gender  = document.getElementById('gender').value;
  const college = document.getElementById('college').value;
  const rent    = parseInt(document.getElementById('rent').value, 10);

  if (!gender || !college) {
    alert('Please select both Gender and College.');
    return;
  }

  showLoading(true);
  hideResults();

  try {
    const res  = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ gender, college, max_rent: rent })
    });

    const data = await res.json();
    showLoading(false);

    if (data.error) {
      alert('Error: ' + data.error);
      return;
    }

    if (!data.pgs || data.pgs.length === 0) {
      document.getElementById('noResultsMsg').textContent =
        data.message || 'No PGs found. Try adjusting your rent or gender filter.';
      document.getElementById('noResults').style.display = 'block';
      return;
    }

    renderResults(data);

  } catch (err) {
    showLoading(false);
    console.error(err);
    alert('Could not connect to server. Make sure the Flask app is running.');
  }
}

// ── Render Results ─────────────────────────────────────────
function renderResults(data) {
  const pgs      = data.pgs;
  const topScore = pgs[0]?.rank_score?.toFixed(1) ?? '–';

  // Stats
  document.getElementById('statTotal').textContent   = data.total;
  document.getElementById('statCity').textContent     = data.city;
  document.getElementById('statTopScore').textContent = `${topScore}%`;

  // Results header — clearly show which college & city was searched
  document.getElementById('resultsTitle').textContent =
    `Top PGs in ${data.city}`;
  document.getElementById('results-sub-college').textContent =
    `🏢 ${data.college}  •  📍 City: ${data.city}  •  Ranked by AI score`;

  // Grid
  const grid = document.getElementById('pgGrid');
  grid.innerHTML = '';

  pgs.forEach((pg, idx) => {
    const card = buildCard(pg, idx + 1);
    grid.appendChild(card);
  });

  document.getElementById('resultsSection').style.display = 'block';

  // Animate score bars after DOM insertion
  requestAnimationFrame(() => {
    document.querySelectorAll('.score-bar-fill').forEach(bar => {
      const target = bar.dataset.width;
      setTimeout(() => { bar.style.width = target; }, 60);
    });
  });

  document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── Build a single PG card ─────────────────────────────────
function buildCard(pg, rank) {
  const card = document.createElement('div');
  card.className = 'pg-card';
  card.style.animationDelay = `${(rank - 1) * 0.06}s`;

  // Rank badge style
  let rankClass = 'normal';
  let rankEmoji = '';
  if (rank === 1) { rankClass = 'gold';   rankEmoji = '🥇'; }
  if (rank === 2) { rankClass = 'silver'; rankEmoji = '🥈'; }
  if (rank === 3) { rankClass = 'bronze'; rankEmoji = '🥉'; }

  // Amenities
  const amenities = [
    { label: '🍽 Food',  val: pg.food },
    { label: '📶 WiFi',  val: pg.wifi },
    { label: '❄️ AC',   val: pg.ac   },
  ];
  const chips = amenities.map(a =>
    `<span class="chip ${a.val === 'Yes' ? 'yes' : 'no'}">${a.label} ${a.val === 'Yes' ? '✓' : '✗'}</span>`
  ).join('');

  const labelClass = pg.label === 'Recommended' ? 'recommended' : 'not-recommended';
  const scoreWidth = `${pg.rank_score.toFixed(1)}%`;

  // Gender icon
  const gIcon = pg.gender === 'Boys' ? '👦' : pg.gender === 'Girls' ? '👧' : '🧑';

  card.innerHTML = `
    <div class="card-rank ${rankClass}">
      <span class="rank-num">${rankEmoji || '#' + rank}</span>
      <span class="rank-lbl">Rank</span>
    </div>

    <div class="card-top">
      <div class="pg-name">${pg.name}</div>
      <div class="pg-location">
        <span class="city-tag">${pg.city}</span>
        📍 ${pg.area}
        &nbsp;•&nbsp;
        ${gIcon} ${pg.gender}
      </div>
    </div>

    <div class="score-section">
      <div class="score-label">
        <span>AI Score</span>
        <span class="score-val">${pg.rank_score.toFixed(1)}%</span>
      </div>
      <div class="score-bar-bg">
        <div class="score-bar-fill" style="width:0" data-width="${scoreWidth}"></div>
      </div>
    </div>

    <div class="card-info">
      <div class="info-item">
        <span class="info-val">₹${pg.rent.toLocaleString('en-IN')}</span>
        <span class="info-lbl">Rent / mo</span>
      </div>
      <div class="info-item">
        <span class="info-val">${pg.distance_km} km</span>
        <span class="info-lbl">Distance</span>
      </div>
      <div class="info-item">
        <span class="info-val">${pg.transport}</span>
        <span class="info-lbl">Transport</span>
      </div>
      <div class="info-item">
        <span class="info-val">${pg.amenities}/3</span>
        <span class="info-lbl">Amenities</span>
      </div>
    </div>

    <div class="amenity-row">${chips}</div>

    <span class="label-badge ${labelClass}">${pg.label}</span>
  `;

  return card;
}

// ── Helpers ────────────────────────────────────────────────
function showLoading(show) {
  document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
}

function hideResults() {
  document.getElementById('resultsSection').style.display = 'none';
  document.getElementById('noResults').style.display = 'none';
  document.getElementById('pgGrid').innerHTML = '';
}
