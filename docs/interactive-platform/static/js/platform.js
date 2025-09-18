// Interactive Documentation Platform - Main JavaScript

// ===== GLOBAL STATE =====
const HMSPlatform = {
  currentUser: null,
  currentRole: null,
  searchIndex: null,
  tutorials: null,
  videoData: null,
  analytics: null,
  settings: {
    theme: 'light',
    language: 'en',
    animations: true,
    keyboardNavigation: true,
    autoSave: true
  }
};

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function() {
  initializePlatform();
  initializeEventListeners();
  initializeSearch();
  initializeTutorials();
  initializeVideos();
  initializeAnalytics();
  loadUserPreferences();
});

function initializePlatform() {
  console.log('Initializing HMS Interactive Documentation Platform...');

  // Load search index
  loadSearchIndex();

  // Load tutorials
  loadTutorials();

  // Load video data
  loadVideoData();

  // Load analytics data
  loadAnalytics();

  // Check authentication
  checkAuthentication();

  // Initialize responsive design
  initializeResponsiveDesign();
}

// ===== AUTHENTICATION =====
function checkAuthentication() {
  // Check if user is authenticated with HMS
  const token = localStorage.getItem('hms_auth_token');
  const userInfo = localStorage.getItem('hms_user_info');

  if (token && userInfo) {
    try {
      HMSPlatform.currentUser = JSON.parse(userInfo);
      updateUIForAuthenticatedUser();
    } catch (error) {
      console.error('Error parsing user info:', error);
      logout();
    }
  } else {
    // Try single sign-on with HMS
    attemptSSO();
  }
}

function attemptSSO() {
  // Attempt single sign-on with HMS system
  // This would typically involve redirecting to HMS auth endpoint
  console.log('Attempting single sign-on with HMS...');
}

function updateUIForAuthenticatedUser() {
  const userMenu = document.querySelector('.hms-user-menu');
  if (userMenu) {
    userMenu.innerHTML = `
      <div class="hms-user-info">
        <img src="${HMSPlatform.currentUser.avatar || '/static/images/default-avatar.png'}"
             alt="${HMSPlatform.currentUser.name}"
             class="hms-avatar">
        <span class="hms-user-name">${HMSPlatform.currentUser.name}</span>
        <span class="hms-user-role">${HMSPlatform.currentUser.role}</span>
      </div>
      <div class="hms-user-actions">
        <button onclick="showUserProfile()" class="hms-btn hms-btn-sm hms-btn-outline">
          Profile
        </button>
        <button onclick="logout()" class="hms-btn hms-btn-sm hms-btn-outline">
          Logout
        </button>
      </div>
    `;
  }
}

function logout() {
  localStorage.removeItem('hms_auth_token');
  localStorage.removeItem('hms_user_info');
  HMSPlatform.currentUser = null;
  HMSPlatform.currentRole = null;
  window.location.reload();
}

// ===== SEARCH FUNCTIONALITY =====
function initializeSearch() {
  const searchInput = document.getElementById('hms-search-input');
  const searchSuggestions = document.getElementById('hms-search-suggestions');

  if (searchInput) {
    searchInput.addEventListener('input', debounce(handleSearchInput, 300));
    searchInput.addEventListener('keydown', handleSearchKeydown);
    searchInput.addEventListener('focus', () => {
      if (searchInput.value.length > 0) {
        showSearchSuggestions();
      }
    });
    searchInput.addEventListener('blur', () => {
      setTimeout(() => hideSearchSuggestions(), 200);
    });
  }
}

function handleSearchInput(event) {
  const query = event.target.value.trim();

  if (query.length < 2) {
    hideSearchSuggestions();
    return;
  }

  performSearch(query);
}

function handleSearchKeydown(event) {
  const suggestions = document.querySelectorAll('.hms-search-suggestion');
  const currentIndex = Array.from(suggestions).findIndex(s => s.classList.contains('selected'));

  switch (event.key) {
    case 'ArrowDown':
      event.preventDefault();
      selectSearchSuggestion(currentIndex + 1, suggestions);
      break;
    case 'ArrowUp':
      event.preventDefault();
      selectSearchSuggestion(currentIndex - 1, suggestions);
      break;
    case 'Enter':
      event.preventDefault();
      if (currentIndex >= 0 && suggestions[currentIndex]) {
        suggestions[currentIndex].click();
      }
      break;
    case 'Escape':
      hideSearchSuggestions();
      break;
  }
}

function performSearch(query) {
  if (!HMSPlatform.searchIndex) {
    console.warn('Search index not loaded');
    return;
  }

  const results = searchInIndex(query, HMSPlatform.searchIndex);
  displaySearchResults(results, query);
  trackSearch(query, results.length);
}

function searchInIndex(query, index) {
  const lowerQuery = query.toLowerCase();
  const results = [];

  // Search in documents
  index.documents.forEach(doc => {
    let score = 0;

    // Title match (highest weight)
    if (doc.title.toLowerCase().includes(lowerQuery)) {
      score += 10;
    }

    // Content match
    if (doc.content.toLowerCase().includes(lowerQuery)) {
      score += 5;
    }

    // Tags match
    if (doc.tags.some(tag => tag.toLowerCase().includes(lowerQuery))) {
      score += 3;
    }

    // Category match
    if (doc.category.toLowerCase().includes(lowerQuery)) {
      score += 2;
    }

    if (score > 0) {
      results.push({
        ...doc,
        score,
        relevance: calculateRelevance(doc, query)
      });
    }
  });

  // Sort by score and relevance
  return results.sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score;
    return b.relevance - a.relevance;
  }).slice(0, 10);
}

function calculateRelevance(doc, query) {
  // Calculate relevance based on various factors
  let relevance = 0;

  // Freshness (recently updated content gets higher relevance)
  if (doc.lastUpdated) {
    const daysSinceUpdate = (Date.now() - new Date(doc.lastUpdated)) / (1000 * 60 * 60 * 24);
    relevance += Math.max(0, 10 - daysSinceUpdate);
  }

  // Popularity (frequently viewed content gets higher relevance)
  if (doc.viewCount) {
    relevance += Math.min(doc.viewCount / 100, 5);
  }

  // User role relevance
  if (HMSPlatform.currentRole && doc.targetRoles.includes(HMSPlatform.currentRole)) {
    relevance += 3;
  }

  return relevance;
}

function displaySearchResults(results, query) {
  const suggestionsContainer = document.getElementById('hms-search-suggestions');

  if (!suggestionsContainer) return;

  if (results.length === 0) {
    suggestionsContainer.innerHTML = `
      <div class="hms-search-suggestion">
        <div class="hms-search-no-results">
          <strong>No results found</strong>
          <p>Try different keywords or browse by category</p>
        </div>
      </div>
    `;
  } else {
    suggestionsContainer.innerHTML = results.map(result => `
      <div class="hms-search-suggestion" onclick="navigateToDocument('${result.url}')">
        <div class="hms-search-result-title">
          ${highlightSearchTerm(result.title, query)}
        </div>
        <div class="hms-search-result-description">
          ${highlightSearchTerm(result.description || result.content.substring(0, 100), query)}
        </div>
        <div class="hms-search-result-meta">
          <span class="hms-badge hms-badge-${getCategoryBadgeClass(result.category)}">${result.category}</span>
          <span class="hms-search-result-reading-time">${result.readingTime || '5 min read'}</span>
        </div>
      </div>
    `).join('');
  }

  showSearchSuggestions();
}

function highlightSearchTerm(text, term) {
  const regex = new RegExp(`(${term})`, 'gi');
  return text.replace(regex, '<mark>$1</mark>');
}

function getCategoryBadgeClass(category) {
  const categoryMap = {
    'clinical': 'secondary',
    'technical': 'primary',
    'administrative': 'success',
    'training': 'warning',
    'api': 'error'
  };
  return categoryMap[category.toLowerCase()] || 'primary';
}

function showSearchSuggestions() {
  const suggestions = document.getElementById('hms-search-suggestions');
  if (suggestions) {
    suggestions.classList.add('active');
  }
}

function hideSearchSuggestions() {
  const suggestions = document.getElementById('hms-search-suggestions');
  if (suggestions) {
    suggestions.classList.remove('active');
  }
}

function selectSearchSuggestion(index, suggestions) {
  // Remove previous selection
  suggestions.forEach(s => s.classList.remove('selected'));

  // Add selection to current item
  if (index >= 0 && index < suggestions.length) {
    suggestions[index].classList.add('selected');
    suggestions[index].scrollIntoView({ block: 'nearest' });
  }
}

function navigateToDocument(url) {
  // Track navigation
  trackDocumentView(url);

  // Navigate to document
  window.location.href = url;
}

function trackSearch(query, resultCount) {
  if (HMSPlatform.analytics) {
    HMSPlatform.analytics.searches.push({
      query,
      resultCount,
      timestamp: new Date().toISOString(),
      userRole: HMSPlatform.currentRole
    });
  }
}

// ===== TUTORIALS =====
function initializeTutorials() {
  // Load tutorial data
  loadTutorials();

  // Initialize tutorial progress tracking
  initializeTutorialProgress();

  // Set up tutorial event listeners
  setupTutorialEventListeners();
}

function loadTutorials() {
  fetch('/static/data/tutorials.json')
    .then(response => response.json())
    .then(data => {
      HMSPlatform.tutorials = data;
      renderTutorials();
    })
    .catch(error => {
      console.error('Error loading tutorials:', error);
      loadFallbackTutorials();
    });
}

function loadFallbackTutorials() {
  // Fallback tutorials data
  HMSPlatform.tutorials = [
    {
      id: 'patient-registration',
      title: 'Patient Registration',
      description: 'Learn how to register new patients in the HMS system',
      category: 'clinical',
      difficulty: 'beginner',
      duration: '15 minutes',
      steps: [
        {
          title: 'Navigate to Patient Registration',
          description: 'Go to Patient Management > Register Patient',
          type: 'navigation'
        },
        {
          title: 'Enter Patient Information',
          description: 'Fill in the patient registration form',
          type: 'form'
        }
      ]
    }
  ];
  renderTutorials();
}

function renderTutorials() {
  const container = document.getElementById('hms-tutorials-container');
  if (!container || !HMSPlatform.tutorials) return;

  const filteredTutorials = filterTutorialsByRole(HMSPlatform.tutorials);

  container.innerHTML = filteredTutorials.map(tutorial => `
    <div class="hms-tutorial-card" data-tutorial-id="${tutorial.id}">
      <div class="hms-tutorial-header">
        <h3 class="hms-tutorial-title">${tutorial.title}</h3>
        <p class="hms-tutorial-description">${tutorial.description}</p>
        <div class="hms-tutorial-meta">
          <span class="hms-badge hms-badge-${getDifficultyBadgeClass(tutorial.difficulty)}">
            ${tutorial.difficulty}
          </span>
          <span class="hms-tutorial-duration">⏱️ ${tutorial.duration}</span>
          <span class="hms-tutorial-category">${tutorial.category}</span>
        </div>
      </div>
      <div class="hms-tutorial-content">
        <div class="hms-tutorial-progress">
          <div class="hms-progress-bar">
            <div class="hms-progress-fill" style="width: ${getTutorialProgress(tutorial.id)}%"></div>
          </div>
          <span class="hms-tutorial-progress-text">${getTutorialProgress(tutorial.id)}% Complete</span>
        </div>
      </div>
      <div class="hms-tutorial-footer">
        <button onclick="startTutorial('${tutorial.id}')" class="hms-btn hms-btn-primary">
          Start Tutorial
        </button>
        <button onclick="showTutorialDetails('${tutorial.id}')" class="hms-btn hms-btn-outline">
          Details
        </button>
      </div>
    </div>
  `).join('');
}

function getDifficultyBadgeClass(difficulty) {
  const difficultyMap = {
    'beginner': 'success',
    'intermediate': 'warning',
    'advanced': 'error'
  };
  return difficultyMap[difficulty.toLowerCase()] || 'primary';
}

function filterTutorialsByRole(tutorials) {
  if (!HMSPlatform.currentRole) return tutorials;

  return tutorials.filter(tutorial => {
    if (!tutorial.targetRoles) return true;
    return tutorial.targetRoles.includes(HMSPlatform.currentRole);
  });
}

function getTutorialProgress(tutorialId) {
  const progress = localStorage.getItem(`tutorial_${tutorialId}_progress`);
  return progress ? parseInt(progress) : 0;
}

function startTutorial(tutorialId) {
  const tutorial = HMSPlatform.tutorials.find(t => t.id === tutorialId);
  if (!tutorial) return;

  // Track tutorial start
  trackTutorialStart(tutorialId);

  // Initialize tutorial modal
  showTutorialModal(tutorial);
}

function showTutorialModal(tutorial) {
  const modal = document.getElementById('hms-tutorial-modal');
  if (!modal) return;

  // Update modal content
  const modalContent = modal.querySelector('.hms-modal-body');
  modalContent.innerHTML = generateTutorialContent(tutorial);

  // Show modal
  modal.classList.add('active');

  // Start tutorial
  currentTutorial = {
    tutorial,
    currentStep: 0,
    startTime: Date.now()
  };

  // Initialize tutorial navigation
  initializeTutorialNavigation();
}

function generateTutorialContent(tutorial) {
  return `
    <div class="hms-tutorial-container">
      <div class="hms-tutorial-header">
        <h2>${tutorial.title}</h2>
        <p>${tutorial.description}</p>
        <div class="hms-tutorial-steps">
          ${tutorial.steps.map((step, index) => `
            <div class="hms-tutorial-step" data-step="${index}">
              <div class="hms-tutorial-step-number">${index + 1}</div>
              <div class="hms-tutorial-step-content">
                <h4>${step.title}</h4>
                <p>${step.description}</p>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
      <div class="hms-tutorial-instructions">
        <div id="hms-tutorial-step-content">
          ${generateStepContent(tutorial.steps[0], 0)}
        </div>
      </div>
      <div class="hms-tutorial-navigation">
        <button id="hms-tutorial-prev" onclick="previousStep()" class="hms-btn hms-btn-outline" disabled>
          Previous
        </button>
        <div class="hms-tutorial-progress">
          Step <span id="hms-tutorial-current-step">1</span> of <span id="hms-tutorial-total-steps">${tutorial.steps.length}</span>
        </div>
        <button id="hms-tutorial-next" onclick="nextStep()" class="hms-btn hms-btn-primary">
          Next
        </button>
      </div>
    </div>
  `;
}

function generateStepContent(step, stepIndex) {
  switch (step.type) {
    case 'navigation':
      return `
        <div class="hms-tutorial-step-navigation">
          <p>${step.description}</p>
          <div class="hms-tutorial-demo">
            <div class="hms-demo-menu">
              <div class="hms-demo-menu-item">Patient Management</div>
              <div class="hms-demo-menu-subitem">Register Patient</div>
            </div>
          </div>
        </div>
      `;
    case 'form':
      return `
        <div class="hms-tutorial-step-form">
          <p>${step.description}</p>
          <div class="hms-demo-form">
            <div class="hms-demo-form-field">
              <label>First Name</label>
              <input type="text" placeholder="Enter first name">
            </div>
            <div class="hms-demo-form-field">
              <label>Last Name</label>
              <input type="text" placeholder="Enter last name">
            </div>
            <div class="hms-demo-form-field">
              <label>Date of Birth</label>
              <input type="date">
            </div>
          </div>
        </div>
      `;
    case 'api':
      return `
        <div class="hms-tutorial-step-api">
          <p>${step.description}</p>
          <div class="hms-demo-api">
            <pre><code>${step.code || 'GET /api/patients/'}</code></pre>
            <button class="hms-btn hms-btn-sm hms-btn-primary">Try it out</button>
          </div>
        </div>
      `;
    default:
      return `<p>${step.description}</p>`;
  }
}

function initializeTutorialNavigation() {
  // Initialize step navigation
  updateTutorialStepUI();
}

function updateTutorialStepUI() {
  if (!currentTutorial) return;

  const { tutorial, currentStep } = currentTutorial;

  // Update progress
  document.getElementById('hms-tutorial-current-step').textContent = currentStep + 1;
  document.getElementById('hms-tutorial-total-steps').textContent = tutorial.steps.length;

  // Update buttons
  const prevBtn = document.getElementById('hms-tutorial-prev');
  const nextBtn = document.getElementById('hms-tutorial-next');

  prevBtn.disabled = currentStep === 0;
  nextBtn.textContent = currentStep === tutorial.steps.length - 1 ? 'Complete' : 'Next';

  // Update step content
  const stepContent = document.getElementById('hms-tutorial-step-content');
  stepContent.innerHTML = generateStepContent(tutorial.steps[currentStep], currentStep);

  // Update progress indicator
  updateTutorialProgressIndicator();
}

function nextStep() {
  if (!currentTutorial) return;

  const { tutorial, currentStep } = currentTutorial;

  if (currentStep < tutorial.steps.length - 1) {
    currentTutorial.currentStep++;
    updateTutorialStepUI();
    trackTutorialStep(currentTutorial.tutorial.id, currentStep);
  } else {
    completeTutorial();
  }
}

function previousStep() {
  if (!currentTutorial) return;

  if (currentTutorial.currentStep > 0) {
    currentTutorial.currentStep--;
    updateTutorialStepUI();
  }
}

function completeTutorial() {
  if (!currentTutorial) return;

  const { tutorial, startTime } = currentTutorial;

  // Save completion
  saveTutorialCompletion(tutorial.id);

  // Track completion
  trackTutorialComplete(tutorial.id, Date.now() - startTime);

  // Show completion message
  showTutorialCompletion(tutorial);

  // Close modal
  closeTutorialModal();
}

function saveTutorialCompletion(tutorialId) {
  localStorage.setItem(`tutorial_${tutorialId}_completed`, 'true');
  localStorage.setItem(`tutorial_${tutorialId}_progress`, '100');

  // Update tutorial list
  renderTutorials();
}

function showTutorialCompletion(tutorial) {
  showNotification('Tutorial Completed!', `You've successfully completed "${tutorial.title}"`);
}

function closeTutorialModal() {
  const modal = document.getElementById('hms-tutorial-modal');
  if (modal) {
    modal.classList.remove('active');
  }
  currentTutorial = null;
}

function trackTutorialStart(tutorialId) {
  if (HMSPlatform.analytics) {
    HMSPlatform.analytics.tutorialStarts.push({
      tutorialId,
      timestamp: new Date().toISOString(),
      userRole: HMSPlatform.currentRole
    });
  }
}

function trackTutorialStep(tutorialId, stepIndex) {
  if (HMSPlatform.analytics) {
    HMSPlatform.analytics.tutorialSteps.push({
      tutorialId,
      stepIndex,
      timestamp: new Date().toISOString()
    });
  }
}

function trackTutorialComplete(tutorialId, duration) {
  if (HMSPlatform.analytics) {
    HMSPlatform.analytics.tutorialCompletions.push({
      tutorialId,
      duration,
      timestamp: new Date().toISOString(),
      userRole: HMSPlatform.currentRole
    });
  }
}

// ===== VIDEO FUNCTIONALITY =====
function initializeVideos() {
  loadVideoData();
  initializeVideoPlayers();
  initializeVideoSearch();
}

function loadVideoData() {
  fetch('/static/data/videos.json')
    .then(response => response.json())
    .then(data => {
      HMSPlatform.videoData = data;
      renderVideoLibrary();
    })
    .catch(error => {
      console.error('Error loading video data:', error);
    });
}

function initializeVideoPlayers() {
  // Initialize video players with custom controls
  document.querySelectorAll('.hms-video-player').forEach(player => {
    initializeVideoPlayer(player);
  });
}

function initializeVideoPlayer(player) {
  const video = player.querySelector('video');
  const playButton = player.querySelector('.hms-play-button');
  const progressBar = player.querySelector('.hms-progress-bar');
  const currentTimeDisplay = player.querySelector('.hms-current-time');
  const durationDisplay = player.querySelector('.hms-duration');

  if (!video) return;

  // Play/Pause functionality
  if (playButton) {
    playButton.addEventListener('click', () => {
      if (video.paused) {
        video.play();
      } else {
        video.pause();
      }
    });
  }

  // Update play button
  video.addEventListener('play', () => {
    if (playButton) playButton.textContent = '⏸️';
  });

  video.addEventListener('pause', () => {
    if (playButton) playButton.textContent = '▶️';
  });

  // Update progress
  video.addEventListener('timeupdate', () => {
    if (progressBar) {
      const progress = (video.currentTime / video.duration) * 100;
      progressBar.querySelector('.hms-progress-fill').style.width = `${progress}%`;
    }

    if (currentTimeDisplay) {
      currentTimeDisplay.textContent = formatTime(video.currentTime);
    }
  });

  // Load metadata
  video.addEventListener('loadedmetadata', () => {
    if (durationDisplay) {
      durationDisplay.textContent = formatTime(video.duration);
    }
  });

  // Track video events
  video.addEventListener('play', () => trackVideoEvent('play', video.dataset.videoId));
  video.addEventListener('pause', () => trackVideoEvent('pause', video.dataset.videoId));
  video.addEventListener('ended', () => trackVideoEvent('complete', video.dataset.videoId));
}

function formatTime(seconds) {
  const minutes = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

function renderVideoLibrary() {
  const container = document.getElementById('hms-video-library');
  if (!container || !HMSPlatform.videoData) return;

  container.innerHTML = HMSPlatform.videoData.videos.map(video => `
    <div class="hms-video-card" data-video-id="${video.id}">
      <div class="hms-video-thumbnail">
        <img src="${video.thumbnail || '/static/images/default-video-thumbnail.png'}"
             alt="${video.title}">
        <div class="hms-video-duration">${formatTime(video.duration)}</div>
        <button onclick="playVideo('${video.id}')" class="hms-play-button">▶️</button>
      </div>
      <div class="hms-video-info">
        <h3>${video.title}</h3>
        <p>${video.description}</p>
        <div class="hms-video-meta">
          <span class="hms-video-views">${video.viewCount || 0} views</span>
          <span class="hms-video-date">${formatDate(video.uploadDate)}</span>
        </div>
        <div class="hms-video-tags">
          ${video.tags.map(tag => `<span class="hms-badge hms-badge-primary">${tag}</span>`).join('')}
        </div>
      </div>
    </div>
  `).join('');
}

function playVideo(videoId) {
  const video = HMSPlatform.videoData.videos.find(v => v.id === videoId);
  if (!video) return;

  // Show video player modal
  showVideoPlayerModal(video);

  // Track video play
  trackVideoEvent('play', videoId);
}

function showVideoPlayerModal(video) {
  const modal = document.getElementById('hms-video-modal');
  if (!modal) return;

  const modalContent = modal.querySelector('.hms-modal-body');
  modalContent.innerHTML = `
    <div class="hms-video-player-container">
      <div class="hms-video-player" data-video-id="${video.id}">
        <video src="${video.url}" controls></video>
        <div class="hms-video-controls">
          <div class="hms-progress-bar">
            <div class="hms-progress-fill"></div>
          </div>
          <div class="hms-video-info">
            <span class="hms-current-time">0:00</span>
            <span class="hms-duration">${formatTime(video.duration)}</span>
          </div>
        </div>
      </div>
      <div class="hms-video-details">
        <h2>${video.title}</h2>
        <p>${video.description}</p>
        <div class="hms-video-chapters">
          ${video.chapters ? video.chapters.map(chapter => `
            <div class="hms-video-chapter" onclick="seekToTime(${chapter.timestamp})">
              <span class="hms-chapter-timestamp">${formatTime(chapter.timestamp)}</span>
              <span class="hms-chapter-title">${chapter.title}</span>
            </div>
          `).join('') : ''}
        </div>
      </div>
    </div>
  `;

  modal.classList.add('active');

  // Initialize video player
  const player = modal.querySelector('.hms-video-player');
  initializeVideoPlayer(player);
}

function seekToTime(timestamp) {
  const video = document.querySelector('.hms-video-player video');
  if (video) {
    video.currentTime = timestamp;
  }
}

function trackVideoEvent(event, videoId) {
  if (HMSPlatform.analytics) {
    HMSPlatform.analytics.videoEvents.push({
      event,
      videoId,
      timestamp: new Date().toISOString(),
      userRole: HMSPlatform.currentRole
    });
  }
}

// ===== ANALYTICS =====
function initializeAnalytics() {
  loadAnalytics();
  initializeEventTracking();
  initializePerformanceMonitoring();
}

function loadAnalytics() {
  // Load analytics data
  HMSPlatform.analytics = {
    searches: [],
    tutorialStarts: [],
    tutorialSteps: [],
    tutorialCompletions: [],
    videoEvents: [],
    documentViews: [],
    userEvents: []
  };
}

function initializeEventTracking() {
  // Track page views
  trackPageView();

  // Track user interactions
  trackUserInteractions();

  // Track time on page
  trackTimeOnPage();
}

function trackPageView() {
  if (HMSPlatform.analytics) {
    HMSPlatform.analytics.pageViews.push({
      url: window.location.pathname,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      userRole: HMSPlatform.currentRole
    });
  }
}

function trackUserInteractions() {
  // Track button clicks
  document.addEventListener('click', (event) => {
    if (event.target.matches('.hms-btn')) {
      trackUserEvent('button_click', {
        buttonText: event.target.textContent,
        buttonClass: event.target.className
      });
    }
  });

  // Track link clicks
  document.addEventListener('click', (event) => {
    if (event.target.matches('a')) {
      trackUserEvent('link_click', {
        linkText: event.target.textContent,
        linkUrl: event.target.href
      });
    }
  });
}

function trackUserEvent(eventType, eventData) {
  if (HMSPlatform.analytics) {
    HMSPlatform.analytics.userEvents.push({
      eventType,
      eventData,
      timestamp: new Date().toISOString(),
      userRole: HMSPlatform.currentRole
    });
  }
}

function trackTimeOnPage() {
  let startTime = Date.now();

  // Track time on page
  window.addEventListener('beforeunload', () => {
    const timeOnPage = Date.now() - startTime;
    trackUserEvent('time_on_page', { duration: timeOnPage });
  });
}

function trackDocumentView(documentUrl) {
  if (HMSPlatform.analytics) {
    HMSPlatform.analytics.documentViews.push({
      documentUrl,
      timestamp: new Date().toISOString(),
      userRole: HMSPlatform.currentRole
    });
  }
}

// ===== RESPONSIVE DESIGN =====
function initializeResponsiveDesign() {
  // Handle mobile menu
  initializeMobileMenu();

  // Handle responsive layout
  handleResponsiveLayout();

  // Listen for resize events
  window.addEventListener('resize', debounce(handleResponsiveLayout, 250));
}

function initializeMobileMenu() {
  const mobileMenuButton = document.querySelector('.hms-mobile-menu-button');
  const mobileMenu = document.querySelector('.hms-mobile-menu');

  if (mobileMenuButton && mobileMenu) {
    mobileMenuButton.addEventListener('click', () => {
      mobileMenu.classList.toggle('active');
    });
  }
}

function handleResponsiveLayout() {
  const width = window.innerWidth;

  // Apply responsive classes
  if (width < 768) {
    document.body.classList.add('hms-mobile');
    document.body.classList.remove('hms-tablet', 'hms-desktop');
  } else if (width < 1024) {
    document.body.classList.add('hms-tablet');
    document.body.classList.remove('hms-mobile', 'hms-desktop');
  } else {
    document.body.classList.add('hms-desktop');
    document.body.classList.remove('hms-mobile', 'hms-tablet');
  }
}

// ===== USER PREFERENCES =====
function loadUserPreferences() {
  const preferences = localStorage.getItem('hms_preferences');

  if (preferences) {
    try {
      HMSPlatform.settings = { ...HMSPlatform.settings, ...JSON.parse(preferences) };
    } catch (error) {
      console.error('Error loading user preferences:', error);
    }
  }

  applyUserPreferences();
}

function applyUserPreferences() {
  // Apply theme
  if (HMSPlatform.settings.theme === 'dark') {
    document.body.classList.add('hms-dark-mode');
  }

  // Apply animations preference
  if (!HMSPlatform.settings.animations) {
    document.body.classList.add('hms-no-animations');
  }

  // Apply language preference
  if (HMSPlatform.settings.language) {
    // This would typically load translations
    console.log(`Language set to: ${HMSPlatform.settings.language}`);
  }
}

function saveUserPreferences() {
  localStorage.setItem('hms_preferences', JSON.stringify(HMSPlatform.settings));
}

// ===== UTILITY FUNCTIONS =====
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

function throttle(func, limit) {
  let inThrottle;
  return function() {
    const args = arguments;
    const context = this;
    if (!inThrottle) {
      func.apply(context, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

function showNotification(title, message, type = 'info') {
  // Create notification element
  const notification = document.createElement('div');
  notification.className = `hms-notification hms-notification-${type}`;
  notification.innerHTML = `
    <div class="hms-notification-content">
      <h4>${title}</h4>
      <p>${message}</p>
    </div>
    <button onclick="this.parentElement.remove()" class="hms-notification-close">×</button>
  `;

  // Add to page
  document.body.appendChild(notification);

  // Auto-remove after 5 seconds
  setTimeout(() => {
    if (notification.parentElement) {
      notification.remove();
    }
  }, 5000);
}

function initializeEventListeners() {
  // Initialize global event listeners
  document.addEventListener('keydown', handleGlobalKeydown);

  // Initialize click handlers
  document.addEventListener('click', handleGlobalClick);

  // Initialize scroll handlers
  window.addEventListener('scroll', throttle(handleScroll, 100));
}

function handleGlobalKeydown(event) {
  // Handle global keyboard shortcuts
  if (event.ctrlKey || event.metaKey) {
    switch (event.key) {
      case 'k':
        event.preventDefault();
        focusSearch();
        break;
      case '/':
        event.preventDefault();
        focusSearch();
        break;
    }
  }

  // Handle escape key
  if (event.key === 'Escape') {
    closeAllModals();
  }
}

function handleGlobalClick(event) {
  // Handle clicks outside modals
  if (event.target.matches('.hms-modal')) {
    closeAllModals();
  }
}

function handleScroll() {
  // Handle scroll events
  const scrolled = window.pageYOffset;
  const header = document.querySelector('.hms-nav');

  if (header) {
    if (scrolled > 50) {
      header.classList.add('hms-nav-scrolled');
    } else {
      header.classList.remove('hms-nav-scrolled');
    }
  }
}

function focusSearch() {
  const searchInput = document.getElementById('hms-search-input');
  if (searchInput) {
    searchInput.focus();
    searchInput.select();
  }
}

function closeAllModals() {
  document.querySelectorAll('.hms-modal').forEach(modal => {
    modal.classList.remove('active');
  });
}

function loadSearchIndex() {
  // Load search index from JSON file or API
  fetch('/static/data/search-index.json')
    .then(response => response.json())
    .then(data => {
      HMSPlatform.searchIndex = data;
    })
    .catch(error => {
      console.error('Error loading search index:', error);
      HMSPlatform.searchIndex = generateFallbackSearchIndex();
    });
}

function generateFallbackSearchIndex() {
  // Generate basic search index from existing content
  return {
    documents: [
      {
        id: 'user-guide',
        title: 'User Guide',
        url: '/USER_GUIDE.md',
        content: 'Comprehensive user guide for HMS Enterprise-Grade system',
        category: 'user',
        tags: ['user', 'guide', 'manual'],
        targetRoles: ['doctor', 'nurse', 'administrator']
      },
      {
        id: 'api-documentation',
        title: 'API Documentation',
        url: '/API_DOCUMENTATION.md',
        content: 'Complete API reference for HMS Enterprise-Grade',
        category: 'technical',
        tags: ['api', 'technical', 'developer'],
        targetRoles: ['developer', 'administrator']
      }
    ]
  };
}

function initializeTutorialProgress() {
  // Load tutorial progress from localStorage
  const tutorialProgress = {};

  Object.keys(localStorage).forEach(key => {
    if (key.startsWith('tutorial_')) {
      const tutorialId = key.replace('tutorial_', '').replace('_progress', '');
      const progress = localStorage.getItem(key);
      if (progress) {
        tutorialProgress[tutorialId] = parseInt(progress);
      }
    }
  });

  HMSPlatform.tutorialProgress = tutorialProgress;
}

function setupTutorialEventListeners() {
  // Set up tutorial event listeners
  document.addEventListener('tutorial-start', (event) => {
    trackTutorialStart(event.detail.tutorialId);
  });

  document.addEventListener('tutorial-complete', (event) => {
    trackTutorialComplete(event.detail.tutorialId, event.detail.duration);
  });
}

function initializeVideoSearch() {
  // Initialize video search functionality
  const videoSearchInput = document.getElementById('hms-video-search');

  if (videoSearchInput) {
    videoSearchInput.addEventListener('input', debounce(handleVideoSearch, 300));
  }
}

function handleVideoSearch(event) {
  const query = event.target.value.trim();

  if (!HMSPlatform.videoData) return;

  const filteredVideos = HMSPlatform.videoData.videos.filter(video => {
    const searchTerms = query.toLowerCase();
    return video.title.toLowerCase().includes(searchTerms) ||
           video.description.toLowerCase().includes(searchTerms) ||
           video.tags.some(tag => tag.toLowerCase().includes(searchTerms));
  });

  renderFilteredVideos(filteredVideos);
}

function renderFilteredVideos(videos) {
  const container = document.getElementById('hms-video-library');
  if (!container) return;

  if (videos.length === 0) {
    container.innerHTML = '<p class="hms-no-results">No videos found matching your search.</p>';
    return;
  }

  container.innerHTML = videos.map(video => `
    <div class="hms-video-card" data-video-id="${video.id}">
      <div class="hms-video-thumbnail">
        <img src="${video.thumbnail || '/static/images/default-video-thumbnail.png'}"
             alt="${video.title}">
        <div class="hms-video-duration">${formatTime(video.duration)}</div>
        <button onclick="playVideo('${video.id}')" class="hms-play-button">▶️</button>
      </div>
      <div class="hms-video-info">
        <h3>${video.title}</h3>
        <p>${video.description}</p>
        <div class="hms-video-meta">
          <span class="hms-video-views">${video.viewCount || 0} views</span>
          <span class="hms-video-date">${formatDate(video.uploadDate)}</span>
        </div>
        <div class="hms-video-tags">
          ${video.tags.map(tag => `<span class="hms-badge hms-badge-primary">${tag}</span>`).join('')}
        </div>
      </div>
    </div>
  `).join('');
}

function initializePerformanceMonitoring() {
  // Initialize performance monitoring
  if ('performance' in window) {
    // Track page load performance
    window.addEventListener('load', () => {
      const perfData = performance.getEntriesByType('navigation')[0];
      trackPerformanceMetrics({
        loadTime: perfData.loadEventEnd - perfData.loadEventStart,
        domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
        firstPaint: perfData.responseEnd - perfData.fetchStart
      });
    });
  }
}

function trackPerformanceMetrics(metrics) {
  if (HMSPlatform.analytics) {
    HMSPlatform.analytics.performanceMetrics.push({
      metrics,
      timestamp: new Date().toISOString(),
      url: window.location.pathname
    });
  }
}

// Export for use in other modules
window.HMSPlatform = HMSPlatform;
window.showNotification = showNotification;
window.closeAllModals = closeAllModals;
window.focusSearch = focusSearch;