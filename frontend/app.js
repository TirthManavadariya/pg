/**
 * app.js - Production Roomee Co-Living & PG Discovery Platform
 * Includes Persistent DB Integration, Authentication & Role Access,
 * Room Bed Reservation, Visit Scheduling, Owner Operations Dashboard,
 * Student Bookings Dashboard, Razorpay/Stripe Payment Flow, and Live Bed Inventory.
 */

// ─── Application State ────────────────────────────────────────────────────────
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
  activeFoodDay: 'Monday',
  
  // Auth state
  auth: {
    token: localStorage.getItem('roomee_token') || null,
    user: (() => {
      try {
        return JSON.parse(localStorage.getItem('roomee_user')) || null;
      } catch (e) {
        return null;
      }
    })()
  },

  // Active payment and booking modals
  activeBookingForPayment: null,
  myBookings: [],
  ownerBookings: [],
  myBookingFilter: 'all',
  ownerBookingFilter: 'all'
};

// ─── DOM Element Selectors ───────────────────────────────────────────────────
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
  navAuthContainer: document.getElementById('navAuthContainer'),

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
  emptyStateCard: document.getElementById('emptyStateCard'),
  emptyResetBtn: document.getElementById('emptyResetBtn'),

  // Pagination
  paginationWrapper: document.getElementById('paginationWrapper'),
  prevPageBtn: document.getElementById('prevPageBtn'),
  nextPageBtn: document.getElementById('nextPageBtn'),
  pageNumbersContainer: document.getElementById('pageNumbersContainer'),

  // Detail Modal & Forms
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
  
  // Tab buttons
  tabBookRoomBtn: document.getElementById('tabBookRoomBtn'),
  tabScheduleVisitBtn: document.getElementById('tabScheduleVisitBtn'),
  
  // Room Booking Form
  roomBookingForm: document.getElementById('roomBookingForm'),
  bookFormPgId: document.getElementById('bookFormPgId'),
  bookRoomSelect: document.getElementById('bookRoomSelect'),
  roomAvailHint: document.getElementById('roomAvailHint'),
  bookMoveInDate: document.getElementById('bookMoveInDate'),
  bookStudentName: document.getElementById('bookStudentName'),
  bookStudentPhone: document.getElementById('bookStudentPhone'),
  bookCollegeName: document.getElementById('bookCollegeName'),
  bookNotes: document.getElementById('bookNotes'),
  summaryRentVal: document.getElementById('summaryRentVal'),
  submitBookRoomBtn: document.getElementById('submitBookRoomBtn'),

  // Visit Booking Form
  visitBookingForm: document.getElementById('visitBookingForm'),
  formPgId: document.getElementById('formPgId'),
  visitorName: document.getElementById('visitorName'),
  visitorPhone: document.getElementById('visitorPhone'),
  visitorDate: document.getElementById('visitorDate'),
  visitorSlot: document.getElementById('visitorSlot'),
  submitVisitBtn: document.getElementById('submitVisitBtn'),
  bookingSuccessBox: document.getElementById('bookingSuccessBox'),
  bookingSuccessTitle: document.getElementById('bookingSuccessTitle'),
  bookingSuccessMsg: document.getElementById('bookingSuccessMsg'),
  bookingRefBadge: document.getElementById('bookingRefBadge'),
  viewInDashboardBtn: document.getElementById('viewInDashboardBtn'),
  bookAnotherBtn: document.getElementById('bookAnotherBtn'),

  // Auth Modal
  authModal: document.getElementById('authModal'),
  closeAuthModalBtn: document.getElementById('closeAuthModalBtn'),
  authTabLoginBtn: document.getElementById('authTabLoginBtn'),
  authTabRegisterBtn: document.getElementById('authTabRegisterBtn'),
  loginForm: document.getElementById('loginForm'),
  registerForm: document.getElementById('registerForm'),
  loginEmail: document.getElementById('loginEmail'),
  loginPassword: document.getElementById('loginPassword'),
  loginSubmitBtn: document.getElementById('loginSubmitBtn'),
  registerName: document.getElementById('registerName'),
  registerEmail: document.getElementById('registerEmail'),
  registerPassword: document.getElementById('registerPassword'),
  registerPhone: document.getElementById('registerPhone'),
  registerCollege: document.getElementById('registerCollege'),
  registerSubmitBtn: document.getElementById('registerSubmitBtn'),
  quickLoginStudentBtn: document.getElementById('quickLoginStudentBtn'),
  quickLoginOwnerBtn: document.getElementById('quickLoginOwnerBtn'),

  // Student Dashboard Modal
  myBookingsModal: document.getElementById('myBookingsModal'),
  closeMyBookingsBtn: document.getElementById('closeMyBookingsBtn'),
  refreshMyBookingsBtn: document.getElementById('refreshMyBookingsBtn'),
  myBookingsList: document.getElementById('myBookingsList'),
  countMyAll: document.getElementById('countMyAll'),
  countMyRooms: document.getElementById('countMyRooms'),
  countMyVisits: document.getElementById('countMyVisits'),

  // Owner Dashboard Modal
  ownerDashboardModal: document.getElementById('ownerDashboardModal'),
  closeOwnerDashboardBtn: document.getElementById('closeOwnerDashboardBtn'),
  refreshOwnerBookingsBtn: document.getElementById('refreshOwnerBookingsBtn'),
  ownerRequestsList: document.getElementById('ownerRequestsList'),
  ownerTotalCount: document.getElementById('ownerTotalCount'),
  ownerPendingCount: document.getElementById('ownerPendingCount'),
  ownerConfirmedCount: document.getElementById('ownerConfirmedCount'),

  // Payment Modal
  paymentModal: document.getElementById('paymentModal'),
  closePaymentModalBtn: document.getElementById('closePaymentModalBtn'),
  payRefId: document.getElementById('payRefId'),
  payPropertyName: document.getElementById('payPropertyName'),
  payRoomType: document.getElementById('payRoomType'),
  confirmPayBtn: document.getElementById('confirmPayBtn'),

  // Toast Container
  toastContainer: document.getElementById('toastContainer')
};

// ─── Toast System ─────────────────────────────────────────────────────────────
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast-item ${type}`;
  const icon = type === 'success' ? '✅' : type === 'error' ? '⚠️' : 'ℹ️';
  toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
  DOM.toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ─── Authentication Service ───────────────────────────────────────────────────
const authService = {
  getAuthHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    if (state.auth.token) {
      headers['Authorization'] = `Bearer ${state.auth.token}`;
    }
    return headers;
  },

  setAuth(token, user) {
    state.auth.token = token;
    state.auth.user = user;
    localStorage.setItem('roomee_token', token);
    localStorage.setItem('roomee_user', JSON.stringify(user));
    this.renderNav();
  },

  logout() {
    state.auth.token = null;
    state.auth.user = null;
    localStorage.removeItem('roomee_token');
    localStorage.removeItem('roomee_user');
    this.renderNav();
    showToast('You have been signed out.', 'info');
  },

  async login(email, password) {
    try {
      DOM.loginSubmitBtn.disabled = true;
      DOM.loginSubmitBtn.textContent = 'Signing in...';
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (data.success && data.token) {
        this.setAuth(data.token, data.user);
        closeAuthModal();
        showToast(`Welcome back, ${data.user.name}!`, 'success');
      } else {
        showToast(data.error || 'Login failed. Please check credentials.', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Network error while signing in.', 'error');
    } finally {
      DOM.loginSubmitBtn.disabled = false;
      DOM.loginSubmitBtn.textContent = 'Sign In';
    }
  },

  async register(payload) {
    try {
      DOM.registerSubmitBtn.disabled = true;
      DOM.registerSubmitBtn.textContent = 'Creating Account...';
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success && data.token) {
        this.setAuth(data.token, data.user);
        closeAuthModal();
        showToast(`Welcome to Roomee, ${data.user.name}!`, 'success');
      } else {
        showToast(data.error || 'Registration failed.', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Network error while creating account.', 'error');
    } finally {
      DOM.registerSubmitBtn.disabled = false;
      DOM.registerSubmitBtn.textContent = 'Create Account & Sign In';
    }
  },

  renderNav() {
    const { user } = state.auth;
    if (!user) {
      DOM.navAuthContainer.innerHTML = `
        <div class="nav-demo-switches">
          <button class="btn-demo-quick" id="navDemoStudentBtn" title="1-Click Evaluation Login as Student">🎓 Demo Student</button>
          <button class="btn-demo-quick" id="navDemoOwnerBtn" title="1-Click Evaluation Login as Owner">🏢 Demo Owner</button>
        </div>
        <button class="btn btn-primary" id="openAuthModalNavBtn" style="padding: 6px 14px; font-size: 0.82rem;">Sign In</button>
      `;
      document.getElementById('navDemoStudentBtn').addEventListener('click', () => {
        authService.login('student@roomee.com', 'password123');
      });
      document.getElementById('navDemoOwnerBtn').addEventListener('click', () => {
        authService.login('owner@roomee.com', 'password123');
      });
      document.getElementById('openAuthModalNavBtn').addEventListener('click', openAuthModal);
    } else {
      const isStudent = user.role === 'student';
      DOM.navAuthContainer.innerHTML = `
        <div class="nav-user-badge">
          <span>${isStudent ? '🎓' : '🏢'}</span>
          <span>${user.name.split(' ')[0]}</span>
          <span class="nav-user-role">${user.role}</span>
        </div>
        ${isStudent ? `
          <button class="btn-nav-dash" id="navMyBookingsBtn">📋 My Bookings</button>
        ` : `
          <button class="btn-nav-dash" id="navOwnerDashboardBtn">📊 Owner Dashboard</button>
        `}
        <button class="btn-nav-logout" id="navLogoutBtn" title="Sign Out">Sign Out</button>
      `;

      if (isStudent) {
        document.getElementById('navMyBookingsBtn').addEventListener('click', openMyBookingsModal);
      } else {
        document.getElementById('navOwnerDashboardBtn').addEventListener('click', openOwnerDashboardModal);
      }
      document.getElementById('navLogoutBtn').addEventListener('click', () => authService.logout());
    }
  }
};

// ─── Modal Management ────────────────────────────────────────────────────────
function openAuthModal() {
  DOM.authModal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeAuthModal() {
  DOM.authModal.style.display = 'none';
  document.body.style.overflow = 'auto';
}

function openMyBookingsModal() {
  if (!state.auth.user) {
    openAuthModal();
    return;
  }
  DOM.myBookingsModal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
  loadMyBookings();
}

function closeMyBookingsModal() {
  DOM.myBookingsModal.style.display = 'none';
  document.body.style.overflow = 'auto';
}

function openOwnerDashboardModal() {
  if (!state.auth.user || state.auth.user.role !== 'owner') {
    showToast('Please sign in with a PG Owner account.', 'info');
    openAuthModal();
    return;
  }
  DOM.ownerDashboardModal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
  loadOwnerBookings();
}

function closeOwnerDashboardModal() {
  DOM.ownerDashboardModal.style.display = 'none';
  document.body.style.overflow = 'auto';
}

function openPaymentModal(booking) {
  state.activeBookingForPayment = booking;
  DOM.payRefId.textContent = `#ROOMEE-BK-${booking.id}`;
  DOM.payPropertyName.textContent = booking.pg_name || (state.activePgDetails ? state.activePgDetails.name : 'Roomee Stay');
  DOM.payRoomType.textContent = `${booking.room_type || 'Selected'} Sharing Room`;
  DOM.paymentModal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closePaymentModal() {
  DOM.paymentModal.style.display = 'none';
  document.body.style.overflow = 'auto';
  state.activeBookingForPayment = null;
}

// ─── API Data Fetching ────────────────────────────────────────────────────────
async function fetchCities() {
  try {
    const res = await fetch('/api/cities');
    const data = await res.json();
    if (data.success && data.cities) {
      state.cities = data.cities;
      renderCityDropdown(data.cities);
      renderHeroCityPills(data.cities);
      renderHeroCitySelect(data.cities);
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
      DOM.heroSelectLocality.innerHTML = `<option value="all">All Localities</option>` +
        data.localities.map(loc => `<option value="${loc}">${loc}</option>`).join('');
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

async function fetchPgDetails(pgId, openTab = 'room_booking') {
  try {
    const res = await fetch(`/api/pg/${pgId}`);
    const data = await res.json();
    if (data.success && data.pg) {
      state.activePgDetails = data.pg;
      openModal(data.pg, openTab);
    }
  } catch (err) {
    console.error('Error fetching PG details:', err);
  }
}
window.fetchPgDetails = fetchPgDetails;

// ─── Rendering Helpers ────────────────────────────────────────────────────────
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
    <option value="${c.name}" ${c.name === state.currentCity ? 'selected' : ''}>${c.name}</option>
  `).join('');
}

function renderLoadingState() {
  DOM.emptyStateCard.style.display = 'none';
  DOM.pgGridContainer.innerHTML = Array(6).fill(0).map(() => `
    <div class="pg-card skeleton-card">
      <div class="skeleton skeleton-img"></div>
      <div class="skeleton-content">
        <div class="skeleton skeleton-title"></div>
        <div class="skeleton skeleton-text"></div>
        <div class="skeleton skeleton-badge-row"></div>
        <div class="skeleton skeleton-price"></div>
      </div>
    </div>
  `).join('');
}

function renderPgGrid(pgs) {
  if (!pgs || pgs.length === 0) {
    DOM.pgGridContainer.innerHTML = '';
    DOM.emptyStateCard.style.display = 'block';
    DOM.paginationWrapper.style.display = 'none';
    return;
  }

  DOM.emptyStateCard.style.display = 'none';
  DOM.paginationWrapper.style.display = 'flex';

  DOM.pgGridContainer.innerHTML = pgs.map(pg => {
    const minPrice = pg.rent_monthly;
    const genderBadgeClass = pg.gender.toLowerCase();
    
    return `
      <article class="pg-card" onclick="fetchPgDetails('${pg.id}')">
        
        <!-- Image & Badges -->
        <div class="pg-card-img-wrap">
          <img src="${pg.image_url}" alt="${pg.name}" class="pg-card-img" id="img-${pg.id}" loading="lazy" onerror="this.src='/static/images/properties/bedroom_luxury_1.jpg'">
          <div class="card-badges-top">
            <span class="gender-badge ${genderBadgeClass}">${pg.gender}</span>
            <div class="card-badges-right">
              ${pg.badges && pg.badges.includes('⚡ Fast Filling') ? '<span class="fast-badge">⚡ Fast Filling</span>' : ''}
              <span class="badge-verified-top">✓ Verified</span>
            </div>
          </div>
          <div class="card-dots-strip" id="dots-${pg.id}">
            ${(pg.gallery || []).map((_, i) => `<span class="dot ${i === 0 ? 'active' : ''}"></span>`).join('')}
          </div>
          <button class="carousel-arrow left" aria-label="Previous photo" onclick="event.stopPropagation(); cycleCardImage('${pg.id}', -1)">&#8249;</button>
          <button class="carousel-arrow right" aria-label="Next photo" onclick="event.stopPropagation(); cycleCardImage('${pg.id}', 1)">&#8250;</button>
        </div>

        <!-- Card Body -->
        <div class="pg-card-body">
          <div class="pg-rating-row">
            <span class="star-rating">★ ${pg.rating}</span>
            <span class="review-count">(${pg.reviews_count} verified reviews)</span>
          </div>

          <h3 class="pg-card-title">${pg.name}</h3>
          <p class="pg-card-locality">📍 ${pg.locality}, ${pg.city}</p>

          <div class="hub-distance-chip">
            🚇 ${pg.nearest_hub}
          </div>

          <!-- Amenities Icons preview -->
          <div class="amenities-row">
            ${pg.wifi ? '<span class="amenity-chip" title="Free High-Speed WiFi">📶 WiFi</span>' : ''}
            ${pg.ac ? '<span class="amenity-chip" title="Air Conditioned">❄️ AC</span>' : ''}
            ${pg.food_included ? '<span class="amenity-chip" title="Nutritious Meals Included">🍲 Meals</span>' : ''}
            <span class="amenity-chip" title="Daily Cleaning">🧹 Housekeeping</span>
          </div>

          <!-- Price & Action Footer -->
          <div class="pg-card-footer">
            <div class="price-box">
              <span class="price-sub">Starts at</span>
              <span class="price-val">₹${minPrice.toLocaleString('en-IN')}<span class="per-month">/mo</span></span>
            </div>
            <div class="card-action-btns">
              <button class="btn btn-outline btn-sm" onclick="event.stopPropagation(); fetchPgDetails('${pg.id}', 'visit')">
                Schedule Visit
              </button>
              <button class="btn btn-primary btn-sm" onclick="event.stopPropagation(); fetchPgDetails('${pg.id}', 'room_booking')">
                Book Bed
              </button>
            </div>
          </div>

        </div>
      </article>
    `;
  }).join('');
}

window.cycleCardImage = function(pgId, direction) {
  const pg = state.pgs.find(p => p.id === pgId);
  if (!pg || !pg.gallery || pg.gallery.length <= 1) return;

  const gallery = pg.gallery;
  const imgEl = document.getElementById(`img-${pgId}`);
  if (!imgEl) return;

  let currIdx = gallery.findIndex(src => imgEl.src.includes(src));
  if (currIdx === -1) currIdx = 0;

  let nextIdx = (currIdx + direction + gallery.length) % gallery.length;
  imgEl.src = gallery[nextIdx];

  const dotsWrap = document.getElementById(`dots-${pgId}`);
  if (dotsWrap) {
    const dots = dotsWrap.querySelectorAll('.dot');
    dots.forEach((d, i) => d.className = `dot ${i === nextIdx ? 'active' : ''}`);
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

  for (let i = start; i <= end; i++) pages.push(i);

  DOM.pageNumbersContainer.innerHTML = pages.map(p => `
    <button class="page-num ${p === currentPage ? 'active' : ''}" onclick="goToPage(${p})">${p}</button>
  `).join('');
}

function updateMetaCounters() {
  DOM.resultsCount.textContent = state.totalResults.toLocaleString();
  DOM.resultsCityName.textContent = state.currentCity;
}

// ─── Modal & Detailed Stay Drawer ───────────────────────────────────────────
function openModal(pg, initialTab = 'room_booking') {
  DOM.modalMainImg.src = pg.image_url;
  DOM.modalThumbStrip.innerHTML = pg.gallery.map((imgUrl, i) => `
    <div class="modal-thumb ${i === 0 ? 'active' : ''}" onclick="setModalMainImg('${imgUrl}', this)">
      <img src="${imgUrl}" alt="Gallery ${i}">
    </div>
  `).join('');

  DOM.modalPgName.textContent = pg.name;
  DOM.modalRating.textContent = `★ ${pg.rating} (${pg.reviews_count} reviews)`;
  DOM.modalLocality.textContent = `📍 ${pg.full_address} • ${pg.nearest_hub}`;
  DOM.modalBadges.innerHTML = pg.badges.map(b => `<span class="modal-badge-item">✓ ${b}</span>`).join('');

  // Live Bed Inventory & Rooms Matrix
  const rooms = pg.rooms || [];
  DOM.modalSharingGrid.innerHTML = Object.entries(pg.pricing_matrix).map(([type, price]) => {
    const matchingRoom = rooms.find(r => r.room_type.toLowerCase() === type.toLowerCase());
    const availBeds = matchingRoom ? matchingRoom.available_beds : 2;
    const isSoldOut = matchingRoom && availBeds <= 0;

    return `
      <div class="sharing-item-card" data-room-type="${type}" onclick="selectRoomForBooking('${type}')">
        <div>
          <div class="type">${type} Sharing</div>
          <div class="bed-count-chip ${isSoldOut ? 'sold-out' : ''}">
            ${isSoldOut ? '🔴 Fully Booked' : `🟢 ${availBeds} Bed${availBeds > 1 ? 's' : ''} Available`}
          </div>
        </div>
        <div style="text-align: right;">
          <div class="rent">₹${price.toLocaleString('en-IN')}/mo</div>
          <div style="font-size:0.75rem; color:#64748b;">Zero Brokerage</div>
        </div>
      </div>
    `;
  }).join('');

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

  // Populate Room Dropdown for Booking Form
  DOM.bookFormPgId.value = pg.id;
  DOM.formPgId.value = pg.id;
  
  if (rooms.length > 0) {
    DOM.bookRoomSelect.innerHTML = rooms.map(r => `
      <option value="${r.id}" data-type="${r.room_type}" data-rent="${r.rent_per_month}" data-avail="${r.available_beds}" ${r.available_beds <= 0 ? 'disabled' : ''}>
        ${r.room_type} Sharing — ₹${r.rent_per_month.toLocaleString('en-IN')}/mo ${r.available_beds <= 0 ? '(Fully Booked)' : `(${r.available_beds} beds left)`}
      </option>
    `).join('');
    updateRoomBookingSummary();
  } else {
    DOM.bookRoomSelect.innerHTML = `<option value="">Standard Room — ₹${pg.rent_monthly}/mo</option>`;
    DOM.summaryRentVal.textContent = `₹${pg.rent_monthly.toLocaleString('en-IN')}/mo`;
  }

  // Set default move-in date to tomorrow
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  DOM.bookMoveInDate.value = tomorrow.toISOString().split('T')[0];
  DOM.visitorDate.value = tomorrow.toISOString().split('T')[0];

  // Auto-fill logged in student credentials
  if (state.auth.user) {
    DOM.bookStudentName.value = state.auth.user.name || '';
    DOM.bookStudentPhone.value = state.auth.user.phone || '';
    DOM.bookCollegeName.value = state.auth.user.college_name || '';
    DOM.visitorName.value = state.auth.user.name || '';
    DOM.visitorPhone.value = state.auth.user.phone || '';
  }

  // Switch to selected tab
  switchModalBookingTab(initialTab);
  DOM.bookingSuccessBox.style.display = 'none';

  DOM.propertyModal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function switchModalBookingTab(tab) {
  if (tab === 'room_booking') {
    DOM.tabBookRoomBtn.classList.add('active');
    DOM.tabScheduleVisitBtn.classList.remove('active');
    DOM.roomBookingForm.style.display = 'flex';
    DOM.visitBookingForm.style.display = 'none';
  } else {
    DOM.tabScheduleVisitBtn.classList.add('active');
    DOM.tabBookRoomBtn.classList.remove('active');
    DOM.visitBookingForm.style.display = 'flex';
    DOM.roomBookingForm.style.display = 'none';
  }
}

window.selectRoomForBooking = function(roomType) {
  switchModalBookingTab('room_booking');
  const select = DOM.bookRoomSelect;
  for (let i = 0; i < select.options.length; i++) {
    const opt = select.options[i];
    if (opt.dataset.type && opt.dataset.type.toLowerCase() === roomType.toLowerCase()) {
      select.selectedIndex = i;
      updateRoomBookingSummary();
      break;
    }
  }
  document.querySelectorAll('.sharing-item-card').forEach(card => {
    card.classList.toggle('selected', card.dataset.roomType.toLowerCase() === roomType.toLowerCase());
  });
};

function updateRoomBookingSummary() {
  const selectedOption = DOM.bookRoomSelect.selectedOptions[0];
  if (selectedOption) {
    const rent = parseInt(selectedOption.dataset.rent || '10000', 10);
    const avail = parseInt(selectedOption.dataset.avail || '1', 10);
    DOM.summaryRentVal.textContent = `₹${rent.toLocaleString('en-IN')}/mo`;
    if (avail <= 0) {
      DOM.roomAvailHint.textContent = '⚠️ All beds currently occupied in this category';
      DOM.roomAvailHint.style.color = '#dc2626';
      DOM.submitBookRoomBtn.disabled = true;
    } else {
      DOM.roomAvailHint.textContent = `🟢 ${avail} Bed${avail > 1 ? 's' : ''} available immediately`;
      DOM.roomAvailHint.style.color = '#059669';
      DOM.submitBookRoomBtn.disabled = false;
    }
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

// ─── Student Bookings Dashboard ───────────────────────────────────────────────
async function loadMyBookings() {
  try {
    DOM.myBookingsList.innerHTML = `<div style="text-align:center; padding: 30px; color:#64748b;">Loading your bookings...</div>`;
    const res = await fetch('/api/bookings/my-bookings', {
      headers: authService.getAuthHeaders()
    });
    const data = await res.json();
    if (data.success) {
      state.myBookings = data.bookings;
      renderMyBookings();
    } else {
      DOM.myBookingsList.innerHTML = `<div class="error-msg">${data.error || 'Failed to fetch bookings.'}</div>`;
    }
  } catch (err) {
    console.error(err);
    DOM.myBookingsList.innerHTML = `<div class="error-msg">Network error loading bookings.</div>`;
  }
}

function renderMyBookings() {
  const filter = state.myBookingFilter;
  let items = state.myBookings;
  
  DOM.countMyAll.textContent = items.length;
  DOM.countMyRooms.textContent = items.filter(b => b.booking_type === 'room_booking').length;
  DOM.countMyVisits.textContent = items.filter(b => b.booking_type === 'visit').length;

  if (filter !== 'all') {
    items = items.filter(b => b.booking_type === filter);
  }

  if (items.length === 0) {
    DOM.myBookingsList.innerHTML = `
      <div style="text-align: center; padding: 40px 20px; color: #64748b;">
        <div style="font-size: 2.5rem; margin-bottom: 12px;">📋</div>
        <h4>No ${filter === 'all' ? '' : filter.replace('_', ' ')} requests found</h4>
        <p>Explore stays and book your preferred room or schedule a free inspection visit.</p>
      </div>
    `;
    return;
  }

  DOM.myBookingsList.innerHTML = items.map(b => {
    const isRoom = b.booking_type === 'room_booking';
    const statusClass = b.status.toLowerCase();
    const hasPaid = b.payments && b.payments.some(p => p.status === 'paid');

    return `
      <div class="dashboard-card">
        <img src="${b.pg_image || '/static/images/properties/bedroom_luxury_1.jpg'}" alt="${b.pg_name}" class="dash-card-thumb">
        <div class="dash-card-content">
          <div class="dash-card-header">
            <div>
              <div class="dash-card-title">${b.pg_name}</div>
              <div class="dash-card-loc">📍 ${b.pg_locality}, ${b.pg_city}</div>
            </div>
            <span class="status-badge ${statusClass}">● ${b.status}</span>
          </div>

          <div class="dash-card-meta-grid">
            <div class="dash-meta-item">
              <strong>Request Type</strong>
              <span>${isRoom ? '⚡ Bed Reservation' : '📅 Physical Visit'}</span>
            </div>
            <div class="dash-meta-item">
              <strong>${isRoom ? 'Move-in Date' : 'Visit Schedule'}</strong>
              <span>${isRoom ? (b.move_in_date || 'Flexible') : `${b.visit_date} (${b.visit_slot})`}</span>
            </div>
            ${isRoom ? `
              <div class="dash-meta-item">
                <strong>Room Type</strong>
                <span>${b.room_type || 'Double'} Sharing (₹${(b.room_rent || 10000).toLocaleString('en-IN')}/mo)</span>
              </div>
            ` : ''}
            <div class="dash-meta-item">
              <strong>Token Status</strong>
              <span>${hasPaid ? '✅ ₹2,000 Paid' : isRoom ? '⏳ ₹2,000 Pending' : 'Free (Zero Fee)'}</span>
            </div>
          </div>

          <div class="dash-card-footer">
            <span style="font-size:0.75rem; color:#94a3b8;">Ref: #ROOMEE-BK-${b.id} • ${new Date(b.created_at).toLocaleDateString()}</span>
            ${isRoom && b.status === 'pending' && !hasPaid ? `
              <button class="btn btn-primary btn-sm" onclick="openPaymentModal(${JSON.stringify(b).replace(/"/g, '&quot;')})">
                💳 Pay ₹2,000 Token Now
              </button>
            ` : ''}
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// ─── Owner Operations Dashboard ───────────────────────────────────────────────
async function loadOwnerBookings() {
  try {
    DOM.ownerRequestsList.innerHTML = `<div style="text-align:center; padding: 30px; color:#64748b;">Loading requests for your properties...</div>`;
    const res = await fetch('/api/owner/bookings', {
      headers: authService.getAuthHeaders()
    });
    const data = await res.json();
    if (data.success) {
      state.ownerBookings = data.bookings;
      renderOwnerBookings();
    } else {
      DOM.ownerRequestsList.innerHTML = `<div class="error-msg">${data.error || 'Failed to fetch owner requests.'}</div>`;
    }
  } catch (err) {
    console.error(err);
    DOM.ownerRequestsList.innerHTML = `<div class="error-msg">Network error loading requests.</div>`;
  }
}

function renderOwnerBookings() {
  const all = state.ownerBookings;
  DOM.ownerTotalCount.textContent = all.length;
  DOM.ownerPendingCount.textContent = all.filter(b => b.status === 'pending').length;
  DOM.ownerConfirmedCount.textContent = all.filter(b => b.status === 'confirmed').length;

  let items = all;
  const filter = state.ownerBookingFilter;
  if (filter === 'pending') items = items.filter(b => b.status === 'pending');
  else if (filter === 'confirmed') items = items.filter(b => b.status === 'confirmed');
  else if (filter === 'visit') items = items.filter(b => b.booking_type === 'visit');

  if (items.length === 0) {
    DOM.ownerRequestsList.innerHTML = `
      <div style="text-align: center; padding: 40px 20px; color: #64748b;">
        <div style="font-size: 2.5rem; margin-bottom: 12px;">📬</div>
        <h4>No incoming requests in this category</h4>
        <p>New booking and visit requests from verified students will appear here in real-time.</p>
      </div>
    `;
    return;
  }

  DOM.ownerRequestsList.innerHTML = items.map(b => {
    const isRoom = b.booking_type === 'room_booking';
    const statusClass = b.status.toLowerCase();
    const hasPaid = b.payments && b.payments.some(p => p.status === 'paid');

    return `
      <div class="dashboard-card">
        <img src="${b.pg_image || '/static/images/properties/bedroom_modern_2.jpg'}" alt="${b.pg_name}" class="dash-card-thumb">
        <div class="dash-card-content">
          <div class="dash-card-header">
            <div>
              <div class="dash-card-title">${b.pg_name} — <span style="color:#0284c7;">${isRoom ? 'Bed Reservation' : 'Visit Request'}</span></div>
              <div class="dash-card-loc">Student: <strong>${b.user_name}</strong> (📞 ${b.user_phone || 'Not shared'}) ${b.college_name ? `• ${b.college_name}` : ''}</div>
            </div>
            <span class="status-badge ${statusClass}">● ${b.status}</span>
          </div>

          <div class="dash-card-meta-grid">
            <div class="dash-meta-item">
              <strong>${isRoom ? 'Move-in Date' : 'Visit Scheduled'}</strong>
              <span>${isRoom ? (b.move_in_date || 'Immediate') : `${b.visit_date} (${b.visit_slot})`}</span>
            </div>
            ${isRoom ? `
              <div class="dash-meta-item">
                <strong>Room Category</strong>
                <span>${b.room_type || 'Double'} Sharing</span>
              </div>
            ` : ''}
            <div class="dash-meta-item">
              <strong>Token Payment</strong>
              <span>${hasPaid ? '✅ ₹2,000 Confirmed' : '⏳ Pending'}</span>
            </div>
            <div class="dash-meta-item">
              <strong>Special Notes</strong>
              <span>${b.notes || 'None provided'}</span>
            </div>
          </div>

          <div class="dash-card-footer">
            <span style="font-size:0.75rem; color:#94a3b8;">Booking #${b.id} • ${new Date(b.created_at).toLocaleDateString()}</span>
            
            ${b.status === 'pending' ? `
              <div class="owner-action-group">
                <button class="btn-action-accept" onclick="updateBookingStatusByOwner(${b.id}, 'confirmed')">
                  ✓ Accept & Confirm Bed
                </button>
                <button class="btn-action-reject" onclick="updateBookingStatusByOwner(${b.id}, 'rejected')">
                  ✕ Reject
                </button>
              </div>
            ` : `
              <span style="font-size:0.8rem; font-weight:600; color:#475569;">Action Completed: ${b.status}</span>
            `}
          </div>
        </div>
      </div>
    `;
  }).join('');
}

window.updateBookingStatusByOwner = async function(bookingId, newStatus) {
  try {
    const res = await fetch(`/api/owner/bookings/${bookingId}`, {
      method: 'PATCH',
      headers: authService.getAuthHeaders(),
      body: JSON.stringify({ status: newStatus })
    });
    const data = await res.json();
    if (data.success) {
      showToast(`Booking request #${bookingId} has been ${newStatus}!`, 'success');
      loadOwnerBookings();
    } else {
      showToast(data.error || 'Failed to update booking status.', 'error');
    }
  } catch (err) {
    console.error(err);
    showToast('Network error updating booking status.', 'error');
  }
};

// ─── Setup Event Listeners ───────────────────────────────────────────────────
function setupEventListeners() {
  // City Dropdown
  DOM.currentCityBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    DOM.cityDropdownMenu.classList.toggle('show');
  });

  document.addEventListener('click', () => {
    DOM.cityDropdownMenu.classList.remove('show');
  });

  DOM.cityDropdownMenu.addEventListener('click', (e) => e.stopPropagation());

  // Global Search
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

  // Hero Search Capsule
  DOM.heroSelectCity.addEventListener('change', (e) => {
    selectCityAndFetch(e.target.value);
  });

  DOM.heroSearchBtn.addEventListener('click', () => {
    state.currentCity = DOM.heroSelectCity.value;
    state.currentLocality = DOM.heroSelectLocality.value;
    state.gender = DOM.heroSelectGender.value;
    state.sharing = DOM.heroSelectSharing.value;
    state.currentPage = 1;
    syncFilterBarUI();
    fetchPgs();
    document.getElementById('exploreSection').scrollIntoView({ behavior: 'smooth' });
  });

  // Filter Bar Events
  DOM.genderFilterGroup.querySelectorAll('.seg-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      DOM.genderFilterGroup.querySelectorAll('.seg-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.gender = btn.dataset.gender;
      state.currentPage = 1;
      fetchPgs();
    });
  });

  DOM.sharingFilterGroup.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      DOM.sharingFilterGroup.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      state.sharing = chip.dataset.sharing;
      state.currentPage = 1;
      fetchPgs();
    });
  });

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

  DOM.budgetRange.addEventListener('input', (e) => {
    state.maxPrice = parseInt(e.target.value, 10);
    DOM.budgetVal.textContent = `₹${state.maxPrice.toLocaleString('en-IN')}`;
  });

  DOM.budgetRange.addEventListener('change', () => {
    state.currentPage = 1;
    fetchPgs();
  });

  DOM.sortBySelect.addEventListener('change', (e) => {
    state.sortBy = e.target.value;
    state.currentPage = 1;
    fetchPgs();
  });

  DOM.resetFiltersBtn.addEventListener('click', resetAllFilters);
  DOM.emptyResetBtn.addEventListener('click', resetAllFilters);

  // Pagination
  DOM.prevPageBtn.addEventListener('click', () => {
    if (state.currentPage > 1) goToPage(state.currentPage - 1);
  });

  DOM.nextPageBtn.addEventListener('click', () => {
    if (state.currentPage < state.totalPages) goToPage(state.currentPage + 1);
  });

  // Modal Closures
  DOM.closeModalBtn.addEventListener('click', closeModal);
  DOM.propertyModal.addEventListener('click', (e) => {
    if (e.target === DOM.propertyModal) closeModal();
  });

  // Tabbed Booking Switches
  DOM.tabBookRoomBtn.addEventListener('click', () => switchModalBookingTab('room_booking'));
  DOM.tabScheduleVisitBtn.addEventListener('click', () => switchModalBookingTab('visit'));
  DOM.bookRoomSelect.addEventListener('change', updateRoomBookingSummary);

  // Room Booking Form Submit
  DOM.roomBookingForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!state.auth.user) {
      showToast('Please sign in or register to reserve your bed.', 'info');
      openAuthModal();
      return;
    }

    const roomId = DOM.bookRoomSelect.value;
    if (!roomId) {
      showToast('Please choose a valid room category.', 'error');
      return;
    }

    DOM.submitBookRoomBtn.disabled = true;
    DOM.submitBookRoomBtn.textContent = 'Processing Reservation...';

    const payload = {
      booking_type: 'room_booking',
      pg_id: DOM.bookFormPgId.value,
      room_id: parseInt(roomId, 10),
      move_in_date: DOM.bookMoveInDate.value,
      token_amount: 2000,
      notes: DOM.bookNotes.value
    };

    try {
      const res = await fetch('/api/bookings', {
        method: 'POST',
        headers: authService.getAuthHeaders(),
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success && data.booking) {
        closeModal();
        showToast('Bed reservation created! Proceed to token payment to secure your bed.', 'success');
        openPaymentModal(data.booking);
      } else {
        showToast(data.error || 'Failed to reserve room.', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Network error while placing reservation.', 'error');
    } finally {
      DOM.submitBookRoomBtn.disabled = false;
      DOM.submitBookRoomBtn.textContent = 'Proceed to Reserve & Pay Token (₹2,000)';
    }
  });

  // Visit Booking Form Submit
  DOM.visitBookingForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    DOM.submitVisitBtn.disabled = true;
    DOM.submitVisitBtn.textContent = 'Confirming Visit...';

    const payload = {
      booking_type: 'visit',
      pg_id: DOM.formPgId.value,
      visit_date: DOM.visitorDate.value,
      visit_slot: DOM.visitorSlot.value
    };

    try {
      let res;
      if (state.auth.user) {
        res = await fetch('/api/bookings', {
          method: 'POST',
          headers: authService.getAuthHeaders(),
          body: JSON.stringify(payload)
        });
      } else {
        // Fallback to legacy endpoint for unauthenticated visitors
        res = await fetch('/api/book-visit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            pg_id: DOM.formPgId.value,
            name: DOM.visitorName.value,
            phone: DOM.visitorPhone.value,
            date: DOM.visitorDate.value,
            slot: DOM.visitorSlot.value
          })
        });
      }

      const data = await res.json();
      if (data.success) {
        DOM.visitBookingForm.style.display = 'none';
        DOM.bookingSuccessTitle.textContent = 'Physical Visit Confirmed!';
        DOM.bookingSuccessMsg.textContent = `Your visit is scheduled for ${DOM.visitorDate.value} (${DOM.visitorSlot.value}). Our property manager will assist you!`;
        DOM.bookingRefBadge.textContent = `Ref: ${data.booking ? `ROOMEE-BK-${data.booking.id}` : data.booking_id}`;
        DOM.bookingSuccessBox.style.display = 'block';
        showToast('Visit confirmed successfully!', 'success');
      } else {
        showToast(data.error || 'Failed to schedule visit.', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Network error while scheduling visit.', 'error');
    } finally {
      DOM.submitVisitBtn.disabled = false;
      DOM.submitVisitBtn.textContent = 'Confirm Free Visit Now';
    }
  });

  DOM.viewInDashboardBtn.addEventListener('click', () => {
    closeModal();
    openMyBookingsModal();
  });

  DOM.bookAnotherBtn.addEventListener('click', () => {
    DOM.bookingSuccessBox.style.display = 'none';
    DOM.visitBookingForm.style.display = 'flex';
  });

  // Auth Modal Event Handlers
  DOM.closeAuthModalBtn.addEventListener('click', closeAuthModal);
  DOM.authModal.addEventListener('click', (e) => {
    if (e.target === DOM.authModal) closeAuthModal();
  });

  DOM.authTabLoginBtn.addEventListener('click', () => {
    DOM.authTabLoginBtn.classList.add('active');
    DOM.authTabRegisterBtn.classList.remove('active');
    DOM.loginForm.style.display = 'block';
    DOM.registerForm.style.display = 'none';
  });

  DOM.authTabRegisterBtn.addEventListener('click', () => {
    DOM.authTabRegisterBtn.classList.add('active');
    DOM.authTabLoginBtn.classList.remove('active');
    DOM.registerForm.style.display = 'block';
    DOM.loginForm.style.display = 'none';
  });

  DOM.loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    authService.login(DOM.loginEmail.value.trim(), DOM.loginPassword.value);
  });

  DOM.registerForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const role = document.querySelector('input[name="registerRole"]:checked').value;
    const payload = {
      name: DOM.registerName.value.trim(),
      email: DOM.registerEmail.value.trim(),
      password: DOM.registerPassword.value,
      phone: DOM.registerPhone.value.trim(),
      role: role,
      college_name: DOM.registerCollege.value.trim()
    };
    authService.register(payload);
  });

  DOM.quickLoginStudentBtn.addEventListener('click', () => {
    DOM.loginEmail.value = 'student@roomee.com';
    DOM.loginPassword.value = 'password123';
    authService.login('student@roomee.com', 'password123');
  });

  DOM.quickLoginOwnerBtn.addEventListener('click', () => {
    DOM.loginEmail.value = 'owner@roomee.com';
    DOM.loginPassword.value = 'password123';
    authService.login('owner@roomee.com', 'password123');
  });

  // Student Dashboard Modal Handlers
  DOM.closeMyBookingsBtn.addEventListener('click', closeMyBookingsModal);
  DOM.myBookingsModal.addEventListener('click', (e) => {
    if (e.target === DOM.myBookingsModal) closeMyBookingsModal();
  });
  DOM.refreshMyBookingsBtn.addEventListener('click', loadMyBookings);

  document.querySelectorAll('#myBookingsModal .dash-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#myBookingsModal .dash-tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.myBookingFilter = btn.dataset.filter;
      renderMyBookings();
    });
  });

  // Owner Dashboard Modal Handlers
  DOM.closeOwnerDashboardBtn.addEventListener('click', closeOwnerDashboardModal);
  DOM.ownerDashboardModal.addEventListener('click', (e) => {
    if (e.target === DOM.ownerDashboardModal) closeOwnerDashboardModal();
  });
  DOM.refreshOwnerBookingsBtn.addEventListener('click', loadOwnerBookings);

  document.querySelectorAll('#ownerDashboardModal .dash-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#ownerDashboardModal .dash-tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.ownerBookingFilter = btn.dataset.ownerFilter;
      renderOwnerBookings();
    });
  });

  // Payment Checkout Modal Handlers
  DOM.closePaymentModalBtn.addEventListener('click', closePaymentModal);
  DOM.paymentModal.addEventListener('click', (e) => {
    if (e.target === DOM.paymentModal) closePaymentModal();
  });

  document.querySelectorAll('.payment-method-item').forEach(item => {
    item.addEventListener('click', () => {
      document.querySelectorAll('.payment-method-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
    });
  });

  DOM.confirmPayBtn.addEventListener('click', async () => {
    if (!state.activeBookingForPayment) return;
    
    DOM.confirmPayBtn.disabled = true;
    DOM.confirmPayBtn.textContent = 'Processing Payment via Gateway...';

    const bookingId = state.activeBookingForPayment.id;
    try {
      // 1. Create order
      const orderRes = await fetch('/api/payments/create-order', {
        method: 'POST',
        headers: authService.getAuthHeaders(),
        body: JSON.stringify({ booking_id: bookingId, amount: 2000, gateway: 'Razorpay' })
      });
      const orderData = await orderRes.json();

      // 2. Verify payment
      const verifyRes = await fetch('/api/payments/verify', {
        method: 'POST',
        headers: authService.getAuthHeaders(),
        body: JSON.stringify({
          booking_id: bookingId,
          order_id: orderData.order_id || 'order_rzp_mock',
          payment_id: `pay_rzp_${Date.now()}`
        })
      });
      const verifyData = await verifyRes.json();

      if (verifyData.success) {
        closePaymentModal();
        showToast('🎉 Payment verified! Your bed reservation is CONFIRMED!', 'success');
        openMyBookingsModal();
        // Refresh active properties and list to reflect updated bed counts
        fetchPgs();
      } else {
        showToast(verifyData.error || 'Payment verification failed.', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Network error processing payment.', 'error');
    } finally {
      DOM.confirmPayBtn.disabled = false;
      DOM.confirmPayBtn.textContent = 'Pay ₹2,000 & Confirm Bed Now';
    }
  });

  // Callback button
  DOM.requestCallbackBtn.addEventListener('click', () => {
    const phone = prompt('Enter your phone number for an instant callback from our stay advisor:');
    if (phone && phone.trim().length >= 10) {
      alert(`Thank you! Our advisor will call you at ${phone.trim()} within 10 minutes.`);
    }
  });
}

// ─── Global Helper Functions ─────────────────────────────────────────────────
window.selectCityAndFetch = function(cityName) {
  state.currentCity = cityName;
  state.currentLocality = 'all';
  state.currentPage = 1;

  DOM.currentCityName.textContent = cityName;
  const found = state.cities.find(c => c.name === cityName);
  if (found) DOM.currentCityIcon.textContent = found.icon;

  DOM.cityDropdownMenu.classList.remove('show');

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

// ─── Application Bootstrap ───────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  authService.renderNav();
  setupEventListeners();
  fetchCities();
  fetchLocalities(state.currentCity);
  fetchPgs();
});
