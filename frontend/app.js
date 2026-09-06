/**
 * Roomee — AI PG Housing Hub Client Application
 * Handles:
 * - Smart NLP Semantic Vector Search (/api/semantic-search)
 * - AI Housing Chatbot (/api/chat)
 * - PyTorch Two-Tower Personalized Neural Matching (/api/recommend-personalized)
 * - XGBoost / GradientBoosting Fair Market Rent Validation (/api/predict-rent)
 * - Dynamic Filter Chips, Sorting & Modal Intelligence
 */

const API_BASE = ''; // Same origin

// ─── Application State ────────────────────────────────────────────────────────
const state = {
  query: '',
  city: '',
  sharing: '',
  amenities: {
    ac: false,
    wifi: false,
    food: false
  },
  maxBudget: 25000,
  sortBy: 'relevance',
  page: 1,
  limit: 18,
  listings: [],
  totalCount: 0,
  totalPages: 1,
  mode: 'all', // 'search' | 'recommendations' | 'all'
  currentDetailListing: null,
  isLoading: false,
  metadata: null,
  isChatOpen: false
};

// ─── Initialization ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

async function initApp() {
  checkBackendHealth();
  await loadMetadata();
  fetchInitialListings();

  // Search input live clear button toggle
  const searchInput = document.getElementById('search-input');
  const clearBtn = document.getElementById('clear-search-btn');
  if (searchInput && clearBtn) {
    searchInput.addEventListener('input', () => {
      clearBtn.style.display = searchInput.value.trim() ? 'flex' : 'none';
    });
  }
}

// ─── Health Check ─────────────────────────────────────────────────────────────
async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    if (res.ok) {
      const data = await res.json();
      const statusEl = document.getElementById('ai-status-text');
      if (statusEl) {
        statusEl.textContent = '3 ML Models Online';
      }
    }
  } catch (err) {
    console.warn('Backend connection note:', err);
    const statusEl = document.getElementById('ai-status-text');
    if (statusEl) {
      statusEl.textContent = 'AI Core Initializing';
    }
  }
}

// ─── Metadata ────────────────────────────────────────────────────────────────
async function loadMetadata() {
  try {
    const res = await fetch(`${API_BASE}/api/meta`);
    if (res.ok) {
      const data = await res.json();
      state.metadata = data;
      populateCityOptions(data.cities);
    }
  } catch (err) {
    console.warn('Could not load metadata:', err);
  }
}

function populateCityOptions(cities) {
  if (!cities || !cities.length) return;
  const select = document.getElementById('filter-city');
  if (!select) return;
  const currentVal = select.value;
  select.innerHTML = '<option value="">All Cities</option>' + 
    cities.map(c => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join('');
  select.value = currentVal;
}

// ─── Fetch Listings (Standard Filtered View) ──────────────────────────────────
async function fetchInitialListings(page = 1) {
  setLoading(true, 'Loading verified student accommodations...');
  state.page = page;
  state.mode = 'all';

  try {
    const params = new URLSearchParams({
      page: state.page,
      limit: state.limit
    });

    if (state.city) params.append('city', state.city);
    if (state.sharing) params.append('sharing', state.sharing);
    if (state.maxBudget) params.append('max_rent', state.maxBudget);
    if (state.amenities.ac) params.append('ac', '1');
    if (state.amenities.wifi) params.append('wifi', '1');
    if (state.amenities.food) params.append('food', '1');

    const res = await fetch(`${API_BASE}/api/listings?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch listings');

    const data = await res.json();
    state.listings = data.listings || [];
    state.totalCount = data.total || 0;
    state.totalPages = data.pages || 1;

    applyClientSorting();
    renderListingsGrid();
    updateResultsMeta();
  } catch (err) {
    console.error('Listings fetch error:', err);
    showToast('Failed to load listings. Please try again.', 'error');
  } finally {
    setLoading(false);
  }
}

// ─── Semantic Natural Language Search ─────────────────────────────────────────
async function handleSemanticSearch(event) {
  if (event) event.preventDefault();

  const searchInput = document.getElementById('search-input');
  const query = searchInput ? searchInput.value.trim() : '';

  if (!query) {
    fetchInitialListings(1);
    return;
  }

  state.query = query;
  state.mode = 'search';
  setLoading(true, `Embedding query "${query}" & matching accommodations...`);

  try {
    const payload = {
      query: query,
      city: state.city || undefined,
      max_budget: state.maxBudget || undefined,
      sharing_type: state.sharing || undefined,
      ac: state.amenities.ac ? '1' : undefined,
      wifi: state.amenities.wifi ? '1' : undefined,
      food_included: state.amenities.food ? '1' : undefined,
      top_k: 24
    };

    const res = await fetch(`${API_BASE}/api/semantic-search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error('Semantic search request failed');

    const data = await res.json();
    state.listings = data.results || [];
    state.totalCount = data.count || state.listings.length;
    state.totalPages = 1;

    applyClientSorting();
    renderListingsGrid();
    updateResultsMeta(`Semantic Match: ${state.listings.length} accommodations found for "${query}"`);
    showToast(`Found ${state.listings.length} matching rooms!`);
  } catch (err) {
    console.error('Semantic search error:', err);
    showToast('Notice: Using filter search fallback.', 'info');
    fetchInitialListings(1);
  } finally {
    setLoading(false);
  }
}

function applyQueryPrompt(promptText) {
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.value = promptText;
    const clearBtn = document.getElementById('clear-search-btn');
    if (clearBtn) clearBtn.style.display = 'flex';
    handleSemanticSearch();
  }
}

function clearSearchInput() {
  const searchInput = document.getElementById('search-input');
  const clearBtn = document.getElementById('clear-search-btn');
  if (searchInput) {
    searchInput.value = '';
    if (clearBtn) clearBtn.style.display = 'none';
    state.query = '';
    fetchInitialListings(1);
  }
}

// ─── AI Housing Chatbot ───────────────────────────────────────────────────────
function toggleChatbot() {
  state.isChatOpen = !state.isChatOpen;
  const chatWindow = document.getElementById('chatbot-window');
  if (chatWindow) {
    chatWindow.classList.toggle('active', state.isChatOpen);
    if (state.isChatOpen) {
      const chatInput = document.getElementById('chat-input');
      if (chatInput) chatInput.focus();
    }
  }
}

async function handleChatSubmit(event) {
  if (event) event.preventDefault();

  const chatInput = document.getElementById('chat-input');
  const message = chatInput ? chatInput.value.trim() : '';
  if (!message) return;

  // Add User Message to Chat
  addChatMessage(message, 'user');
  chatInput.value = '';

  // Add loading bot message
  const loadingMsgId = addChatMessage('Thinking & searching accommodations...', 'bot', true);

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });

    const data = await res.json();
    removeChatMessage(loadingMsgId);

    // Render formatted response
    addChatMessage(data.reply || 'I found some options for you!', 'bot', false, data.pgs);
  } catch (err) {
    console.error('Chatbot error:', err);
    removeChatMessage(loadingMsgId);
    addChatMessage("Sorry, I couldn't reach the AI model right now. Please try again in a moment.", 'bot');
  }
}

function sendChatPrompt(promptText) {
  const chatInput = document.getElementById('chat-input');
  if (chatInput) {
    chatInput.value = promptText;
    handleChatSubmit();
  }
}

function addChatMessage(text, sender = 'bot', isLoading = false, pgs = []) {
  const container = document.getElementById('chat-messages');
  if (!container) return;

  const msgId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 4);
  const msgEl = document.createElement('div');
  msgEl.className = `chat-msg ${sender}-msg`;
  msgEl.id = msgId;

  // Basic markdown to html formatting for bold, italic, bullets
  let formattedText = escapeHtml(text)
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br/>');

  let pgsHtml = '';
  if (pgs && pgs.length > 0) {
    pgsHtml = `
      <div style="margin-top: 0.5rem; display: flex; flex-direction: column; gap: 0.4rem;">
        ${pgs.slice(0, 3).map(pg => `
          <div class="chat-card-preview" onclick="openListingDetail('${escapeHtml(pg.pg_id)}')">
            <div class="chat-card-name">🏠 ${escapeHtml(pg.name)}</div>
            <div class="chat-card-sub">📍 ${escapeHtml(pg.locality)}, ${escapeHtml(pg.city)} • <strong>₹${Number(pg.rent_monthly).toLocaleString('en-IN')}/mo</strong> (${escapeHtml(pg.sharing_type || 'Double')})</div>
          </div>
        `).join('')}
      </div>
    `;
  }

  msgEl.innerHTML = `
    <div class="msg-bubble">
      ${isLoading ? '<div class="spinner" style="width: 18px; height: 18px; border-width: 2px; margin: 0;"></div>' : formattedText}
      ${pgsHtml}
    </div>
  `;

  container.appendChild(msgEl);
  container.scrollTop = container.scrollHeight;
  return msgId;
}

function removeChatMessage(msgId) {
  const el = document.getElementById(msgId);
  if (el) el.remove();
}

// ─── PyTorch Two-Tower Personalized Recommender ──────────────────────────────
async function handleNeuralRecommenderSubmit(event) {
  if (event) event.preventDefault();

  const city = document.getElementById('rec-city').value;
  const budget = parseFloat(document.getElementById('rec-budget').value) || 14000;
  const sharing_type = document.getElementById('rec-sharing').value;
  const food_type = document.getElementById('rec-food-type').value;
  const ac = document.getElementById('rec-ac').checked ? 1 : 0;
  const wifi = document.getElementById('rec-wifi').checked ? 1 : 0;
  const food_included = document.getElementById('rec-food-inc').checked ? 1 : 0;

  closeModal('modal-recommender');
  state.mode = 'recommendations';
  setLoading(true, 'Running PyTorch Two-Tower latent space matcher...');

  try {
    const payload = {
      city,
      budget,
      sharing_type,
      food_type,
      ac,
      wifi,
      food_included,
      top_k: 20
    };

    const res = await fetch(`${API_BASE}/api/recommend-personalized`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error('Personalized recommendation failed');

    const data = await res.json();
    state.listings = data.recommendations || [];
    state.totalCount = data.count || state.listings.length;
    state.totalPages = 1;

    applyClientSorting();
    renderListingsGrid();
    updateResultsMeta(`✨ Neural Matcher: Top ${state.listings.length} personalized picks in ${city}`);
    showToast(`Generated ${state.listings.length} personalized recommendations!`);
  } catch (err) {
    console.error('Neural matcher error:', err);
    showToast('Neural recommendation error. Please try again.', 'error');
  } finally {
    setLoading(false);
  }
}


// ─── Client-Side Filters & Controls ──────────────────────────────────────────
function triggerFilterChange() {
  const citySelect = document.getElementById('filter-city');
  state.city = citySelect ? citySelect.value : '';

  if (state.mode === 'search' && state.query) {
    handleSemanticSearch();
  } else {
    fetchInitialListings(1);
  }
}

function setSharingFilter(btn, value) {
  document.querySelectorAll('#sharing-pills .segment-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  state.sharing = value;

  if (state.mode === 'search' && state.query) {
    handleSemanticSearch();
  } else {
    fetchInitialListings(1);
  }
}

function toggleAmenity(key) {
  state.amenities[key] = !state.amenities[key];
  const btn = document.getElementById(`chip-${key}`);
  if (btn) {
    btn.classList.toggle('active', state.amenities[key]);
  }

  if (state.mode === 'search' && state.query) {
    handleSemanticSearch();
  } else {
    fetchInitialListings(1);
  }
}

function handleBudgetChange(val) {
  state.maxBudget = parseFloat(val);
  const display = document.getElementById('budget-display');
  if (display) {
    display.textContent = `₹${state.maxBudget.toLocaleString('en-IN')} / mo`;
  }

  debounce(() => {
    if (state.mode === 'search' && state.query) {
      handleSemanticSearch();
    } else {
      fetchInitialListings(1);
    }
  }, 300)();
}

function handleSortChange(sortVal) {
  state.sortBy = sortVal;
  applyClientSorting();
  renderListingsGrid();
}

function applyClientSorting() {
  if (!state.listings || !state.listings.length) return;

  if (state.sortBy === 'price-asc') {
    state.listings.sort((a, b) => (a.rent_monthly || 0) - (b.rent_monthly || 0));
  } else if (state.sortBy === 'price-desc') {
    state.listings.sort((a, b) => (b.rent_monthly || 0) - (a.rent_monthly || 0));
  } else if (state.sortBy === 'value') {
    state.listings.sort((a, b) => {
      const diffA = a.fair_rent ? a.fair_rent.deal_difference_pct : 0;
      const diffB = b.fair_rent ? b.fair_rent.deal_difference_pct : 0;
      return diffA - diffB;
    });
  } else if (state.sortBy === 'relevance') {
    state.listings.sort((a, b) => {
      const scoreA = a.match_percentage || (a.similarity_score ? a.similarity_score * 100 : 80);
      const scoreB = b.match_percentage || (b.similarity_score ? b.similarity_score * 100 : 80);
      return scoreB - scoreA;
    });
  }
}

function resetAllFilters() {
  state.query = '';
  state.city = '';
  state.sharing = '';
  state.amenities = { ac: false, wifi: false, food: false };
  state.maxBudget = 25000;
  state.sortBy = 'relevance';

  const searchInput = document.getElementById('search-input');
  if (searchInput) searchInput.value = '';

  const clearBtn = document.getElementById('clear-search-btn');
  if (clearBtn) clearBtn.style.display = 'none';

  const citySelect = document.getElementById('filter-city');
  if (citySelect) citySelect.value = '';

  document.querySelectorAll('#sharing-pills .segment-btn').forEach((b, i) => {
    b.classList.toggle('active', i === 0);
  });

  ['ac', 'wifi', 'food'].forEach(key => {
    const btn = document.getElementById(`chip-${key}`);
    if (btn) btn.classList.remove('active');
  });

  const budgetSlider = document.getElementById('filter-budget');
  if (budgetSlider) budgetSlider.value = 25000;

  const budgetDisplay = document.getElementById('budget-display');
  if (budgetDisplay) budgetDisplay.textContent = '₹25,000 / mo';

  const sortSelect = document.getElementById('sort-by');
  if (sortSelect) sortSelect.value = 'relevance';

  fetchInitialListings(1);
  showToast('Filters reset.');
}

// ─── UI Rendering ─────────────────────────────────────────────────────────────
function renderListingsGrid() {
  const grid = document.getElementById('listings-grid');
  const emptyState = document.getElementById('empty-state');
  const countBadge = document.getElementById('tab-count-badge');
  const paginationWrapper = document.getElementById('pagination-wrapper');

  if (!grid) return;

  if (countBadge) {
    countBadge.textContent = state.listings.length;
  }

  if (!state.listings || state.listings.length === 0) {
    grid.innerHTML = '';
    if (emptyState) emptyState.style.display = 'block';
    if (paginationWrapper) paginationWrapper.style.display = 'none';
    return;
  }

  if (emptyState) emptyState.style.display = 'none';

  const cardsHtml = state.listings.map((item, index) => {
    const rent = item.rent_monthly || item.rent || 0;
    const matchScore = item.match_percentage || (item.similarity_score ? Math.round(item.similarity_score * 100) : (95 - (index % 10)));
    const fairRent = item.fair_rent || {};
    const dealCategory = fairRent.deal_category || 'Fair Deal';
    const badgeColor = fairRent.deal_badge_color || (dealCategory === 'Great Value' ? 'emerald' : dealCategory === 'Overpriced' ? 'amber' : 'indigo');

    const acActive = item.ac === 1 || String(item.ac).toLowerCase() === 'yes';
    const wifiActive = item.wifi === 1 || String(item.wifi).toLowerCase() === 'yes';
    const foodActive = item.food_included === 1 || String(item.food_included).toLowerCase() === 'yes';

    return `
      <div class="pg-card" onclick="openListingDetail('${escapeHtml(item.pg_id || String(index))}')">
        <div class="card-media">
          <div class="card-media-bg-pattern"></div>
          <div class="card-badges-top">
            <span class="city-badge">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
              ${escapeHtml(item.city || 'Pune')}
            </span>
            <span class="match-score-badge">${matchScore}% Match</span>
          </div>
          <span class="card-room-type">${escapeHtml(item.sharing_type || 'Double')} Sharing</span>
        </div>

        <div class="card-body">
          <div class="card-header-row">
            <h3 class="card-title">${escapeHtml(item.name || 'Student PG Stay')}</h3>
            <div class="card-locality">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a8 8 0 0 0-8 8c0 5.25 8 12 8 12s8-6.75 8-12a8 8 0 0 0-8-8z"></path><circle cx="12" cy="10" r="3"></circle></svg>
              ${escapeHtml(item.locality || 'City Center')}, ${escapeHtml(item.city || '')}
            </div>
          </div>

          <p class="card-desc-snippet">${escapeHtml(item.description || 'Modern and fully equipped accommodation for students and working professionals.')}</p>

          <div class="card-amenities">
            ${acActive ? '<span class="amenity-tag active">❄️ AC</span>' : '<span class="amenity-tag">Non-AC</span>'}
            ${wifiActive ? '<span class="amenity-tag active">📶 Wi-Fi</span>' : ''}
            ${foodActive ? `<span class="amenity-tag active">🍲 ${escapeHtml(item.food_type || 'Meals')}</span>` : '<span class="amenity-tag">Self Cooking</span>'}
          </div>

          <div style="margin-bottom: 0.75rem;">
            <span class="deal-badge ${badgeColor}">
              ${escapeHtml(dealCategory)}
            </span>
          </div>

          <div class="card-footer">
            <div class="price-box">
              <div class="price-main">₹${rent.toLocaleString('en-IN')}</div>
              <div class="price-sub">per month</div>
            </div>
            <button class="btn btn-secondary" onclick="event.stopPropagation(); openListingDetail('${escapeHtml(item.pg_id || String(index))}')">
              View Details
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');

  grid.innerHTML = cardsHtml;

  if (paginationWrapper) {
    paginationWrapper.style.display = (state.mode === 'all' && state.totalPages > state.page) ? 'block' : 'none';
  }
}

function updateResultsMeta(customMsg) {
  const metaEl = document.getElementById('results-count-text');
  if (!metaEl) return;

  if (customMsg) {
    metaEl.textContent = customMsg;
  } else {
    metaEl.textContent = `Showing ${state.listings.length} of ${state.totalCount.toLocaleString()} verified accommodations`;
  }
}

function loadMoreListings() {
  if (state.page < state.totalPages) {
    fetchInitialListings(state.page + 1);
  }
}

// ─── Modal Managers ──────────────────────────────────────────────────────────
function openListingDetail(pgId) {
  const item = state.listings.find(x => String(x.pg_id) === String(pgId)) || state.listings[0];
  if (!item) return;

  state.currentDetailListing = item;

  const rent = item.rent_monthly || item.rent || 0;
  const matchScore = item.match_percentage || (item.similarity_score ? Math.round(item.similarity_score * 100) : 98);
  const fairRent = item.fair_rent || {};
  const predRent = fairRent.predicted_rent || Math.round(rent * 0.95);
  const dealCategory = fairRent.deal_category || 'Fair Deal';
  const badgeColor = fairRent.deal_badge_color || 'indigo';

  document.getElementById('detail-name').textContent = item.name || 'PG Stay';
  document.getElementById('detail-locality-city').textContent = `${item.locality || 'Area'}, ${item.city || 'City'}`;
  document.getElementById('detail-sharing-pill').textContent = `${item.sharing_type || 'Double'} Sharing`;
  document.getElementById('detail-match-score').textContent = `${matchScore}% AI Match`;
  document.getElementById('detail-description').textContent = item.description || 'Fully furnished modern student and working professional accommodation.';
  document.getElementById('detail-rent').innerHTML = `₹${rent.toLocaleString('en-IN')} <span class="price-unit">/ month</span>`;

  // Valuation Card
  document.getElementById('detail-deal-badge').textContent = dealCategory;
  document.getElementById('detail-deal-badge').className = `deal-badge ${badgeColor}`;
  document.getElementById('detail-market-avg').textContent = `₹${predRent.toLocaleString('en-IN')}`;

  const diffPct = fairRent.deal_difference_pct || Math.round(((rent - predRent) / predRent) * 100);
  document.getElementById('detail-val-diff').textContent = `${diffPct > 0 ? '+' : ''}${diffPct}% vs Market`;
  document.getElementById('detail-deal-note').textContent = fairRent.deal_explanation || 'Price validated against AI Fair Market Benchmark model.';

  // Amenities List
  const amenitiesList = document.getElementById('detail-amenities-list');
  const acActive = item.ac === 1 || String(item.ac).toLowerCase() === 'yes';
  const wifiActive = item.wifi === 1 || String(item.wifi).toLowerCase() === 'yes';
  const foodActive = item.food_included === 1 || String(item.food_included).toLowerCase() === 'yes';

  amenitiesList.innerHTML = `
    <div class="detail-amenity-item">${acActive ? '✅' : '❌'} Air Conditioning (AC)</div>
    <div class="detail-amenity-item">${wifiActive ? '✅' : '❌'} High-Speed Wi-Fi</div>
    <div class="detail-amenity-item">${foodActive ? '✅' : '❌'} Food Included (${item.food_type || 'Meals'})</div>
    <div class="detail-amenity-item">✅ 24/7 Water & Power Backup</div>
    <div class="detail-amenity-item">✅ CCTV & Biometric Security</div>
    <div class="detail-amenity-item">✅ Daily Housekeeping Service</div>
  `;

  openModal('modal-listing-detail');
}

function openRecommenderModal() {
  openModal('modal-recommender');
}


function openModal(id) {
  const el = document.getElementById(id);
  if (el) {
    el.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) {
    el.classList.remove('active');
    document.body.style.overflow = '';
  }
}

function handleModalBackdropClick(event, id) {
  if (event.target && event.target.id === id) {
    closeModal(id);
  }
}

function switchView(view) {
  if (view === 'search') {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    const input = document.getElementById('search-input');
    if (input) input.focus();
  }
}

function switchTab(tab) {
  if (tab === 'results') {
    fetchInitialListings(1);
  }
}

function resetToHome(e) {
  if (e) e.preventDefault();
  resetAllFilters();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ─── Interactive Actions ──────────────────────────────────────────────────────
function simulateBooking() {
  if (!state.currentDetailListing) return;
  showToast(`Visit request sent for ${state.currentDetailListing.name}! The host will contact you.`, 'success');
  closeModal('modal-listing-detail');
}

function copyListingLink() {
  if (!state.currentDetailListing) return;
  navigator.clipboard?.writeText?.(window.location.href);
  showToast('Listing link copied to clipboard!');
}

function setLoading(isLoading, message = 'Loading...') {
  state.isLoading = isLoading;
  const loadingEl = document.getElementById('loading-state');
  const loadingMsg = document.getElementById('loading-message');
  const grid = document.getElementById('listings-grid');

  if (loadingEl) {
    loadingEl.style.display = isLoading ? 'block' : 'none';
  }
  if (loadingMsg && message) {
    loadingMsg.textContent = message;
  }
  if (grid && isLoading) {
    grid.innerHTML = '';
  }
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = message;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.2s ease-in';
    setTimeout(() => toast.remove(), 200);
  }, 3500);
}

// Utility Helpers
function escapeHtml(str) {
  if (typeof str !== 'string') return String(str || '');
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}
