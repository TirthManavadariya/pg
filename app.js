/**
 * app.js - Frontend Application for Roomee Managed Co-living & PG Discovery Platform
 */

// Application State
const state = {
  currentCity: 'Bangalore',
  currentLocality: 'all',
  gender: 'all',
  sharing: 'all',
  minPrice: 0,
  maxPrice: 30000,
  ac: false,
  wifi: false,
  food: false,
  search: '',
  sortBy: 'popular',
  currentPage: 1,
  limit: 12,
  totalPages: 1,
  totalResults: 0,
  pgs: [],
  cities: [],
  activePgDetails: null,
  activeFoodDay: 'Monday'
};

// DOM Element Selectors
const DOM = {
  // Navigation & City
  currentCityBtn: document.getElementById('currentCityBtn'),
  currentCityName: document.getElementById('currentCityName'),
  currentCityIcon: document.getElementById('currentCityIcon'),
  cityDropdownMenu: document.getElementById('cityDropdownMenu'),
  cityDropdownGrid: document.getElementById('cityDropdownGrid'),
  globalSearchInput: document.getElementById('globalSearchInput'),
  globalSearchClear: document.getElementById('globalSearchClear'),
  requestCallbackBtn: document.getElementById('requestCallbackBtn'),
  scheduleTopVisitBtn: document.getElementById('scheduleTopVisitBtn'),

  // Hero Section
  heroCityPills: document.getElementById('heroCityPills'),
  heroSelectCity: document.getElementById('heroSelectCity'),
  heroSelectLocality: document.getElementById('heroSelectLocality'),
  heroSelectGender: document.getElementById('heroSelectGender'),
  heroSelectSharing: document.getElementById('heroSelectSharing'),
  heroSearchBtn: document.getElementById('heroSearchBtn'),

  // Filter Bar
  genderFilterGroup: document.getElementById('genderFilterGroup'),
  sharingFilterGroup: document.getElementById('sharingFilterGroup'),
  sortBySelect: document.getElementById('sortBySelect'),
  filterAc: document.getElementById('filterAc'),
  filterWifi: document.getElementById('filterWifi'),
  filterFood: document.getElementById('filterFood'),
  budgetRange: document.getElementById('budgetRange'),
  budgetVal: document.getElementById('budgetVal'),
  resetFiltersBtn: document.getElementById('resetFiltersBtn'),

  // Results & Grid
  resultsCount: document.getElementById('resultsCount'),
  resultsCityName: document.getElementById('resultsCityName'),
  pgGridContainer: document.getElementById('pgGridContainer'),
  emptyState: document.getElementById('emptyState'),
  emptyResetBtn: document.getElementById('emptyResetBtn'),

  // Pagination
  paginationWrapper: document.getElementById('paginationWrapper'),
  prevPageBtn: document.getElementById('prevPageBtn'),
  nextPageBtn: document.getElementById('nextPageBtn'),
  pageNumbersContainer: document.getElementById('pageNumbersContainer'),

  // Modal & Schedule Visit
  propertyModal: document.getElementById('propertyModal'),
  closeModalBtn: document.getElementById('closeModalBtn'),
  modalMainImg: document.getElementById('modalMainImg'),
  modalImgBadge: document.getElementById('modalImgBadge'),
  modalThumbStrip: document.getElementById('modalThumbStrip'),
  modalPgName: document.getElementById('modalPgName'),
  modalRating: document.getElementById('modalRating'),
  modalLocality: document.getElementById('modalLocality'),
  modalBadges: document.getElementById('modalBadges'),
  modalSharingGrid: document.getElementById('modalSharingGrid'),
  modalAmenitiesGrid: document.getElementById('modalAmenitiesGrid'),
  menuDayTabs: document.getElementById('menuDayTabs'),
  menuContentBox: document.getElementById('menuContentBox'),
  modalRulesList: document.getElementById('modalRulesList'),
  visitBookingForm: document.getElementById('visitBookingForm'),
  formPgId: document.getElementById('formPgId'),
  visitorName: document.getElementById('visitorName'),
  visitorPhone: document.getElementById('visitorPhone'),
  visitorDate: document.getElementById('visitorDate'),
  visitorSlot: document.getElementById('visitorSlot'),
  submitVisitBtn: document.getElementById('submitVisitBtn'),
  bookingSuccessBox: document.getElementById('bookingSuccessBox'),
  bookingSuccessMsg: document.getElementById('bookingSuccessMsg'),
  bookingRefBadge: document.getElementById('bookingRefBadge'),
  bookAnotherBtn: document.getElementById('bookAnotherBtn')
};

// ─── Initialization ──────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  initDateInput();
  fetchCities();
  setupEventListeners();
  fetchPgs();
});

function initDateInput() {
  // Set minimum date to tomorrow
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const yyyy = tomorrow.getFullYear();
  const mm = String(tomorrow.getMonth() + 1).padStart(2, '0');
  const dd = String(tomorrow.getDate()).padStart(2, '0');
  if (DOM.visitorDate) {
    DOM.visitorDate.min = `${yyyy}-${mm}-${dd}`;
    DOM.visitorDate.value = `${yyyy}-${mm}-${dd}`;
  }
}

// ─── API Interactions ────────────────────────────────────────────────────────

async function fetchCities() {
  try {
    const res = await fetch('/api/cities');
    const data = await res.json();
    if (data.success && data.cities) {
      state.cities = data.cities;
      renderCityDropdown(data.cities);
      renderHeroCityPills(data.cities);
      renderHeroCitySelect(data.cities);
      fetchLocalities(state.currentCity);
    }
  } catch (err) {
    console.error('Error fetching cities:', err);
  }
}

async function fetchLocalities(cityName) {
  try {
    const res = await fetch(`/api/localities?city=${encodeURIComponent(cityName)}`);
    const data = await res.json();
    if (data.success && data.localities) {
      renderHeroLocalitySelect(data.localities);
    }
  } catch (err) {
    console.error('Error fetching localities:', err);
  }
}

async function fetchPgs() {
  renderLoadingState();
  
  const params = new URLSearchParams({
    city: state.currentCity,
    locality: state.currentLocality,
    gender: state.gender,
    sharing: state.sharing,
    max_price: state.maxPrice,
    sort_by: state.sortBy,
    page: state.currentPage,
    limit: state.limit
  });

  if (state.ac) params.append('ac', 'true');
  if (state.wifi) params.append('wifi', 'true');
  if (state.food) params.append('food', 'true');
  if (state.search) params.append('search', state.search);

  try {
    const res = await fetch(`/api/pgs?${params.toString()}`);
    const data = await res.json();

    if (data.success) {
      state.pgs = data.pgs;
      state.totalResults = data.total;
      state.totalPages = data.total_pages;
      renderPgGrid(data.pgs);
      renderPagination();
      updateMetaCounters();
    }
  } catch (err) {
    console.error('Error fetching PGs:', err);
    DOM.pgGridContainer.innerHTML = `<div class="error-msg">Failed to load property listings. Please try again.</div>`;
  }
}

async function fetchPgDetails(pgId, openVisitTab = false) {
  try {
    const res = await fetch(`/api/pg/${pgId}`);
    const data = await res.json();
    if (data.success && data.pg) {
      state.activePgDetails = data.pg;
      openModal(data.pg, openVisitTab);
    }
  } catch (err) {
    console.error('Error fetching PG details:', err);
  }
}
window.fetchPgDetails = fetchPgDetails;
window.closeModal = closeModal;
window.openModal = openModal;

// ─── Rendering Helpers ───────────────────────────────────────────────────────

function renderCityDropdown(cities) {
  DOM.cityDropdownGrid.innerHTML = cities.map(c => `
    <div class="city-dropdown-item ${c.name === state.currentCity ? 'active' : ''}" onclick="selectCityAndFetch('${c.name}')">
      <span>${c.icon}</span>
      <span>${c.name}</span>
    </div>
  `).join('');
}

function renderHeroCityPills(cities) {
  const topCities = cities.slice(0, 7);
  DOM.heroCityPills.innerHTML = topCities.map(c => `
    <button class="city-pill ${c.name === state.currentCity ? 'active' : ''}" onclick="selectCityAndFetch('${c.name}')">
      <span>${c.icon}</span>
      <span>${c.name}</span>
    </button>
  `).join('');
}

function renderHeroCitySelect(cities) {
  DOM.heroSelectCity.innerHTML = cities.map(c => `
    <option value="${c.name}" ${c.name === state.currentCity ? 'selected' : ''}>${c.name} (${c.count}+ stays)</option>
  `).join('');
}

function renderHeroLocalitySelect(localities) {
  DOM.heroSelectLocality.innerHTML = `<option value="all">All Localities</option>` + localities.map(l => `
    <option value="${l}">${l}</option>
  `).join('');
}

function renderLoadingState() {
  DOM.emptyState.style.display = 'none';
  DOM.pgGridContainer.innerHTML = Array(6).fill(0).map(() => `
    <div class="pg-card" style="opacity: 0.6; pointer-events: none;">
      <div class="card-media" style="background:#e2e8f0; animation: pulse 1.5s infinite;"></div>
      <div class="card-body">
        <div style="height:20px; width:70%; background:#e2e8f0; border-radius:4px; margin-bottom:12px;"></div>
        <div style="height:14px; width:40%; background:#e2e8f0; border-radius:4px; margin-bottom:20px;"></div>
        <div style="height:38px; width:100%; background:#e2e8f0; border-radius:8px;"></div>
      </div>
    </div>
  `).join('');
}

function renderPgGrid(pgs) {
  if (!pgs || pgs.length === 0) {
    DOM.pgGridContainer.innerHTML = '';
    DOM.emptyState.style.display = 'block';
    return;
  }

  DOM.emptyState.style.display = 'none';
  DOM.pgGridContainer.innerHTML = pgs.map((pg, cardIdx) => {
    const galleryJson = JSON.stringify(pg.gallery).replace(/"/g, '&quot;');
    const genderBadge = pg.gender === 'Women' ? '👩 Girls Only' : pg.gender === 'Men' ? '👨 Boys Only' : '👥 Unisex Co-living';
    const sharingLabel = pg.sharing_type === 'Single' ? 'Private Single' : `${pg.sharing_type} Sharing`;
    
    return `
      <div class="pg-card" id="card-${pg.id}">
        <!-- Media Carousel -->
        <div class="card-media">
          <img class="card-carousel-img" id="img-${pg.id}" src="${pg.image_url}" alt="${pg.name}" loading="lazy" onerror="this.src='/static/images/properties/bedroom_luxury_1.jpg'">
          
          <div class="card-badges-top">
            ${pg.badges.slice(0, 2).map(b => `<span class="badge-pill ${b.includes('Fast') ? 'badge-fast' : 'badge-verified'}">${b}</span>`).join('')}
          </div>

          <div class="badge-gender">${genderBadge}</div>

          <!-- Carousel Controls -->
          <button class="carousel-btn prev" onclick="navigateCardImage('${pg.id}', -1, ${galleryJson})" title="Previous Photo">&lsaquo;</button>
          <button class="carousel-btn next" onclick="navigateCardImage('${pg.id}', 1, ${galleryJson})" title="Next Photo">&rsaquo;</button>

          <!-- Dots Indicator -->
          <div class="carousel-dots" id="dots-${pg.id}">
            ${pg.gallery.map((_, i) => `<span class="dot ${i === 0 ? 'active' : ''}"></span>`).join('')}
          </div>
        </div>

        <!-- Card Body -->
        <div class="card-body">
          <div class="card-title-row">
            <h3 class="card-title">${pg.name}</h3>
            <div class="card-rating-badge">★ ${pg.rating}</div>
          </div>

          <div class="card-location">
            <span>📍 ${pg.locality}, ${pg.city}</span>
          </div>

          <div class="card-distance">
            ⚡ ${pg.nearest_hub}
          </div>

          <!-- Amenities Strip -->
          <div class="card-amenities-strip">
            <span class="amenity-pill">📶 High-Speed WiFi</span>
            ${pg.ac ? '<span class="amenity-pill">❄️ AC Room</span>' : ''}
            ${pg.food_included ? '<span class="amenity-pill">🍲 Food Included</span>' : '<span class="amenity-pill">🧹 Daily Cleaning</span>'}
          </div>

          <!-- Pricing Row -->
          <div class="card-pricing-row">
            <div>
              <span class="price-main">₹${pg.rent_monthly.toLocaleString('en-IN')}</span>
              <span class="price-unit">/ month</span>
            </div>
            <span class="price-sharing-tag">${sharingLabel}</span>
          </div>

          <!-- Action Buttons -->
          <div class="card-actions">
            <button class="btn btn-card-details" onclick="fetchPgDetails('${pg.id}', false)">
              View Details
            </button>
            <button class="btn btn-card-visit" onclick="fetchPgDetails('${pg.id}', true)">
              Schedule Visit
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// In-memory carousel state map: { pgId: currentIndex }
const cardCarouselState = {};

window.navigateCardImage = function(pgId, direction, gallery) {
  if (!gallery || gallery.length === 0) return;
  if (cardCarouselState[pgId] === undefined) cardCarouselState[pgId] = 0;

  let nextIdx = cardCarouselState[pgId] + direction;
  if (nextIdx < 0) nextIdx = gallery.length - 1;
  if (nextIdx >= gallery.length) nextIdx = 0;

  cardCarouselState[pgId] = nextIdx;

  const imgEl = document.getElementById(`img-${pgId}`);
  if (imgEl) {
    imgEl.style.opacity = '0.7';
    imgEl.src = gallery[nextIdx];
    setTimeout(() => { imgEl.style.opacity = '1'; }, 100);
  }

  const dotsWrap = document.getElementById(`dots-${pgId}`);
  if (dotsWrap) {
    const dots = dotsWrap.querySelectorAll('.dot');
    dots.forEach((d, i) => {
      d.className = `dot ${i === nextIdx ? 'active' : ''}`;
    });
  }
};

function renderPagination() {
  const { currentPage, totalPages } = state;
  DOM.prevPageBtn.disabled = currentPage <= 1;
  DOM.nextPageBtn.disabled = currentPage >= totalPages;

  let pages = [];
  const maxButtons = 5;
  let start = Math.max(1, currentPage - 2);
  let end = Math.min(totalPages, start + maxButtons - 1);
  if (end - start < maxButtons - 1) {
    start = Math.max(1, end - maxButtons + 1);
  }

  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  DOM.pageNumbersContainer.innerHTML = pages.map(p => `
    <button class="page-num ${p === currentPage ? 'active' : ''}" onclick="goToPage(${p})">${p}</button>
  `).join('');
}

function updateMetaCounters() {
  DOM.resultsCount.textContent = state.totalResults.toLocaleString();
  DOM.resultsCityName.textContent = state.currentCity;
}

// ─── Modal & Detailed Stay Drawer ───────────────────────────────────────────

function openModal(pg, focusBooking = false) {
  // Populate Gallery
  DOM.modalMainImg.src = pg.image_url;
  DOM.modalThumbStrip.innerHTML = pg.gallery.map((imgUrl, i) => `
    <div class="modal-thumb ${i === 0 ? 'active' : ''}" onclick="setModalMainImg('${imgUrl}', this)">
      <img src="${imgUrl}" alt="Gallery ${i}">
    </div>
  `).join('');

  // Info
  DOM.modalPgName.textContent = pg.name;
  DOM.modalRating.textContent = `★ ${pg.rating} (${pg.reviews_count} reviews)`;
  DOM.modalLocality.textContent = `📍 ${pg.full_address} • ${pg.nearest_hub}`;
  
  DOM.modalBadges.innerHTML = pg.badges.map(b => `<span class="modal-badge-item">✓ ${b}</span>`).join('');

  // Pricing Sharing Matrix
  DOM.modalSharingGrid.innerHTML = Object.entries(pg.pricing_matrix).map(([type, price]) => `
    <div class="sharing-item-card">
      <div>
        <div class="type">${type} Sharing</div>
        <div style="font-size:0.75rem; color:#64748b;">Zero Brokerage</div>
      </div>
      <div class="rent">₹${price.toLocaleString('en-IN')}/mo</div>
    </div>
  `).join('');

  // Amenities
  DOM.modalAmenitiesGrid.innerHTML = pg.amenities.map(a => `
    <div class="amenity-grid-item" style="${a.available ? '' : 'opacity:0.4;'}">
      <span>${a.available ? '✅' : '❌'}</span>
      <span>${a.name}</span>
    </div>
  `).join('');

  // Weekly Food Menu
  renderFoodMenu(pg.food_menu);

  // House Rules
  DOM.modalRulesList.innerHTML = Object.entries(pg.house_rules).map(([key, val]) => `
    <div class="rule-item">
      <span>📌</span>
      <div>
        <strong style="text-transform: capitalize;">${key.replace('_', ' ')}:</strong> ${val}
      </div>
    </div>
  `).join('');

  // Setup Form
  DOM.formPgId.value = pg.id;
  DOM.bookingSuccessBox.style.display = 'none';
  DOM.visitBookingForm.style.display = 'flex';

  DOM.propertyModal.style.display = 'flex';
  document.body.style.overflow = 'hidden';

  if (focusBooking) {
    DOM.visitorName.focus();
  }
}

window.setModalMainImg = function(url, thumbEl) {
  DOM.modalMainImg.src = url;
  document.querySelectorAll('.modal-thumb').forEach(t => t.classList.remove('active'));
  if (thumbEl) thumbEl.classList.add('active');
};

function renderFoodMenu(menu) {
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  
  DOM.menuDayTabs.innerHTML = days.map(d => `
    <button class="menu-day-tab ${d === state.activeFoodDay ? 'active' : ''}" onclick="switchFoodDay('${d}')">${d}</button>
  `).join('');

  const dayMenu = menu[state.activeFoodDay] || menu['Monday'];
  DOM.menuContentBox.innerHTML = `
    <div class="meal-row">
      <div class="meal-label">🍳 Breakfast (7:30 AM - 10:00 AM)</div>
      <div class="meal-desc">${dayMenu.breakfast}</div>
    </div>
    <div class="meal-row">
      <div class="meal-label">🍱 Lunch (12:30 PM - 2:30 PM)</div>
      <div class="meal-desc">${dayMenu.lunch}</div>
    </div>
    <div class="meal-row">
      <div class="meal-label">🍲 Dinner (7:30 PM - 10:00 PM)</div>
      <div class="meal-desc">${dayMenu.dinner}</div>
    </div>
  `;
}

window.switchFoodDay = function(day) {
  state.activeFoodDay = day;
  if (state.activePgDetails && state.activePgDetails.food_menu) {
    renderFoodMenu(state.activePgDetails.food_menu);
  }
};

function closeModal() {
  DOM.propertyModal.style.display = 'none';
  document.body.style.overflow = 'auto';
}

// ─── Event Handlers ─────────────────────────────────────────────────────────

function setupEventListeners() {
  // City Dropdown Toggle
  DOM.currentCityBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    DOM.cityDropdownMenu.classList.toggle('show');
  });

  document.addEventListener('click', () => {
    DOM.cityDropdownMenu.classList.remove('show');
  });

  DOM.cityDropdownMenu.addEventListener('click', (e) => e.stopPropagation());

  // Global Search Input
  let debounceTimeout;
  DOM.globalSearchInput.addEventListener('input', (e) => {
    clearTimeout(debounceTimeout);
    state.search = e.target.value.trim();
    DOM.globalSearchClear.style.display = state.search ? 'block' : 'none';
    debounceTimeout = setTimeout(() => {
      state.currentPage = 1;
      fetchPgs();
    }, 300);
  });

  DOM.globalSearchClear.addEventListener('click', () => {
    DOM.globalSearchInput.value = '';
    state.search = '';
    DOM.globalSearchClear.style.display = 'none';
    state.currentPage = 1;
    fetchPgs();
  });

  // Hero Search Capsule Events
  DOM.heroSelectCity.addEventListener('change', (e) => {
    selectCityAndFetch(e.target.value);
  });

  DOM.heroSearchBtn.addEventListener('click', () => {
    state.currentCity = DOM.heroSelectCity.value;
    state.currentLocality = DOM.heroSelectLocality.value;
    state.gender = DOM.heroSelectGender.value;
    state.sharing = DOM.heroSelectSharing.value;
    state.currentPage = 1;
    
    // Sync filters in filter bar
    syncFilterBarUI();
    fetchPgs();
    
    document.getElementById('exploreSection').scrollIntoView({ behavior: 'smooth' });
  });

  // Gender Filter Buttons
  DOM.genderFilterGroup.querySelectorAll('.seg-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      DOM.genderFilterGroup.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.gender = btn.dataset.gender;
      state.currentPage = 1;
      fetchPgs();
    });
  });

  // Sharing Chips
  DOM.sharingFilterGroup.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      DOM.sharingFilterGroup.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      state.sharing = chip.dataset.sharing;
      state.currentPage = 1;
      fetchPgs();
    });
  });

  // Amenities Checkboxes
  DOM.filterAc.addEventListener('change', (e) => {
    state.ac = e.target.checked;
    state.currentPage = 1;
    fetchPgs();
  });

  DOM.filterWifi.addEventListener('change', (e) => {
    state.wifi = e.target.checked;
    state.currentPage = 1;
    fetchPgs();
  });

  DOM.filterFood.addEventListener('change', (e) => {
    state.food = e.target.checked;
    state.currentPage = 1;
    fetchPgs();
  });

  // Budget Range Slider
  DOM.budgetRange.addEventListener('input', (e) => {
    state.maxPrice = parseInt(e.target.value, 10);
    DOM.budgetVal.textContent = `₹${state.maxPrice.toLocaleString('en-IN')}`;
  });

  DOM.budgetRange.addEventListener('change', () => {
    state.currentPage = 1;
    fetchPgs();
  });

  // Sort By
  DOM.sortBySelect.addEventListener('change', (e) => {
    state.sortBy = e.target.value;
    state.currentPage = 1;
    fetchPgs();
  });

  // Reset Filters
  DOM.resetFiltersBtn.addEventListener('click', resetAllFilters);
  DOM.emptyResetBtn.addEventListener('click', resetAllFilters);

  // Pagination
  DOM.prevPageBtn.addEventListener('click', () => {
    if (state.currentPage > 1) {
      goToPage(state.currentPage - 1);
    }
  });

  DOM.nextPageBtn.addEventListener('click', () => {
    if (state.currentPage < state.totalPages) {
      goToPage(state.currentPage + 1);
    }
  });

  // Modal Close
  DOM.closeModalBtn.addEventListener('click', closeModal);
  DOM.propertyModal.addEventListener('click', (e) => {
    if (e.target === DOM.propertyModal) closeModal();
  });

  // Form Submission
  DOM.visitBookingForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    DOM.submitVisitBtn.disabled = true;
    DOM.submitVisitBtn.textContent = 'Scheduling Visit...';

    const payload = {
      pg_id: DOM.formPgId.value,
      name: DOM.visitorName.value,
      phone: DOM.visitorPhone.value,
      date: DOM.visitorDate.value,
      slot: DOM.visitorSlot.value
    };

    try {
      const res = await fetch('/api/book-visit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (data.success) {
        DOM.visitBookingForm.style.display = 'none';
        DOM.bookingSuccessMsg.textContent = data.message;
        DOM.bookingRefBadge.textContent = `Booking ID: ${data.booking_id}`;
        DOM.bookingSuccessBox.style.display = 'block';
      } else {
        alert(data.error || 'Failed to schedule visit. Please try again.');
      }
    } catch (err) {
      console.error('Error submitting visit:', err);
      alert('Network error while scheduling visit.');
    } finally {
      DOM.submitVisitBtn.disabled = false;
      DOM.submitVisitBtn.textContent = 'Confirm Free Visit Now';
    }
  });

  DOM.bookAnotherBtn.addEventListener('click', () => {
    DOM.bookingSuccessBox.style.display = 'none';
    DOM.visitBookingForm.style.display = 'flex';
  });

  // Top Nav quick buttons
  DOM.scheduleTopVisitBtn.addEventListener('click', () => {
    if (state.pgs && state.pgs.length > 0) {
      fetchPgDetails(state.pgs[0].id, true);
    } else {
      document.getElementById('exploreSection').scrollIntoView({ behavior: 'smooth' });
    }
  });

  DOM.requestCallbackBtn.addEventListener('click', () => {
    const phone = prompt('Please enter your 10-digit phone number for an instant callback from our Co-Living advisor:');
    if (phone && phone.trim().length >= 10) {
      alert(`Thank you! Our Roomee stay advisor will call you at ${phone.trim()} within 10 minutes.`);
    }
  });
}

window.selectCityAndFetch = function(cityName) {
  state.currentCity = cityName;
  state.currentLocality = 'all';
  state.currentPage = 1;

  DOM.currentCityName.textContent = cityName;
  const found = state.cities.find(c => c.name === cityName);
  if (found) DOM.currentCityIcon.textContent = found.icon;

  DOM.cityDropdownMenu.classList.remove('show');

  // Update pills & dropdowns
  renderHeroCityPills(state.cities);
  renderCityDropdown(state.cities);
  DOM.heroSelectCity.value = cityName;
  fetchLocalities(cityName);

  fetchPgs();
};

window.setGenderFilter = function(gender) {
  state.gender = gender;
  state.currentPage = 1;
  syncFilterBarUI();
  fetchPgs();
  document.getElementById('exploreSection').scrollIntoView({ behavior: 'smooth' });
};

window.setSharingFilter = function(sharing) {
  state.sharing = sharing;
  state.currentPage = 1;
  syncFilterBarUI();
  fetchPgs();
  document.getElementById('exploreSection').scrollIntoView({ behavior: 'smooth' });
};

window.goToPage = function(pageNum) {
  state.currentPage = pageNum;
  fetchPgs();
  document.getElementById('exploreSection').scrollIntoView({ behavior: 'smooth' });
};

function resetAllFilters() {
  state.currentLocality = 'all';
  state.gender = 'all';
  state.sharing = 'all';
  state.minPrice = 0;
  state.maxPrice = 30000;
  state.ac = false;
  state.wifi = false;
  state.food = false;
  state.search = '';
  state.sortBy = 'popular';
  state.currentPage = 1;

  DOM.globalSearchInput.value = '';
  DOM.globalSearchClear.style.display = 'none';
  DOM.filterAc.checked = false;
  DOM.filterWifi.checked = false;
  DOM.filterFood.checked = false;
  DOM.budgetRange.value = 30000;
  DOM.budgetVal.textContent = '₹30,000';
  DOM.sortBySelect.value = 'popular';

  syncFilterBarUI();
  fetchPgs();
}

function syncFilterBarUI() {
  DOM.genderFilterGroup.querySelectorAll('.seg-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.gender === state.gender);
  });

  DOM.sharingFilterGroup.querySelectorAll('.chip').forEach(c => {
    c.classList.toggle('active', c.dataset.sharing === state.sharing);
  });
}
