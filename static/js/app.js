// ===== PLANSPHERE MAIN APPLICATION JS =====
// Merged Authentication + Dashboard Functionality
// Single JS file handling: Login, Registration, Dashboard, Sidebar, Date Widget

document.addEventListener("DOMContentLoaded", () => {
  // ======================================
  // CONFIGURATION (Production-Ready)
  // ======================================
  const API_BASE = '/v1';
  const TEMPLATES_BASE = '/templates';
  const TOKEN_KEY = 'plansphere_token';

  // ======================================
  // HELPER FUNCTIONS
  // ======================================

  function getAuthToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  async function fetchAPI(endpoint, options = {}) {
    const token = getAuthToken();
    
    const headers = {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...(options.headers || {})
    };

    try {
      console.log(`[API] Fetching: ${API_BASE}${endpoint}`);
      const response = await fetch(API_BASE + endpoint, {
        ...options,
        headers
      });

      console.log(`[API] Response status: ${response.status} for ${endpoint}`);

      if (response.status === 401) {
        localStorage.removeItem(TOKEN_KEY);
        console.warn('[API] Authentication failed. Token may have expired.');
        return null;
      }

      if (!response.ok) {
        console.error(`[API] Error: ${response.status} ${response.statusText} for ${endpoint}`);
        return null;
      }

      const data = await response.json();
      console.log(`[API] Success: ${endpoint}`, data);
      return data;
    } catch (error) {
      console.error('[API] Fetch error:', error.message);
      return null;
    }
  }

  // ======================================
  // AUTH PAGE SETUP (index.html)
  // ======================================

  const tabLogin = document.getElementById("tab-login");
  const tabRegister = document.getElementById("tab-register");
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");
  const authMsg = document.getElementById("auth-msg");
  const loginBtn = document.getElementById("login-btn");
  const registerBtn = document.getElementById("register-btn");

  // Only initialize auth if we're on the login page
  if (tabLogin && tabRegister && loginForm && registerForm) {
    console.log("Auth page detected - initializing");

    const showMsg = (msg, isError = true) => {
      if (!authMsg) return;
      authMsg.textContent = msg;
      authMsg.classList.remove("hidden");
      authMsg.style.color = isError ? "#b91c1c" : "#059669";
      setTimeout(() => authMsg.classList.add("hidden"), 6000);
    };

    // Tab switching
    tabLogin.addEventListener("click", () => {
      loginForm.classList.remove("hidden");
      registerForm.classList.add("hidden");
      tabLogin.classList.add("bg-blue-600", "text-white");
      tabRegister.classList.remove("bg-blue-600", "text-white");
    });

    tabRegister.addEventListener("click", () => {
      registerForm.classList.remove("hidden");
      loginForm.classList.add("hidden");
      tabRegister.classList.add("bg-blue-600", "text-white");
      tabLogin.classList.remove("bg-blue-600", "text-white");
    });

    // LOGIN handler
    if (loginBtn) {
      loginBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        const email = document.getElementById("login-email")?.value.trim();
        const password = document.getElementById("login-password")?.value;
        
        if (!email || !password) {
          showMsg("Please enter email and password");
          return;
        }
        
        try {
          const body = new URLSearchParams();
          body.append("grant_type", "password");
          body.append("username", email);
          body.append("password", password);

          const res = await fetch(API_BASE + "/auth/token", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: body.toString()
          });

          if (!res.ok) {
            const errorText = await res.text();
            console.error("Login failed:", res.status, errorText);
            if (res.status === 401) showMsg("Invalid credentials");
            else showMsg("Login failed (server error)");
            return;
          }
          
          const data = await res.json();
          localStorage.setItem(TOKEN_KEY, data.access_token);
          showMsg("Login successful! Redirecting...", false);
          
          setTimeout(() => {
            window.location.href = "/common_layout.html#dashboard";
          }, 500);
        } catch (err) {
          console.error("Login error:", err);
          showMsg("Network error during login");
        }
      });
    }

    // REGISTER handler
    if (registerBtn) {
      registerBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        const full_name = document.getElementById("reg-fullname")?.value.trim();
        const email = document.getElementById("reg-email")?.value.trim();
        const password = document.getElementById("reg-password")?.value;
        const role = document.getElementById("reg-role")?.value;

        if (!email || !password || password.length < 6) {
          showMsg("Provide valid email and password (min 6 chars)");
          return;
        }

        try {
          console.log("Registering user:", { email, full_name, role });
          const res = await fetch(API_BASE + "/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, full_name, password, role })
          });

          console.log("Register response:", res.status);
          if (!res.ok) {
            const text = await res.text();
            console.error("Register failed:", res.status, text);
            showMsg("Register failed: " + (text || res.status));
            return;
          }

          // Auto-login after registration
          const loginBody = new URLSearchParams();
          loginBody.append("grant_type", "password");
          loginBody.append("username", email);
          loginBody.append("password", password);

          const tokenRes = await fetch(API_BASE + "/auth/token", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: loginBody.toString()
          });

          if (!tokenRes.ok) {
            console.error("Auto-login failed:", tokenRes.status);
            showMsg("Account created but auto-login failed. Please sign in.");
            return;
          }

          const tokenData = await tokenRes.json();
          localStorage.setItem(TOKEN_KEY, tokenData.access_token);
          showMsg("Account created! Redirecting to dashboard...", false);
          
          setTimeout(() => {
            window.location.href = "/common_layout.html#dashboard";
          }, 500);
        } catch (err) {
          console.error("Register error:", err);
          showMsg("Network error during register");
        }
      });
    }
  }

  // ======================================
  // DASHBOARD PAGE SETUP (common_layout.html)
  // ======================================

  // Initialize Date Widget
  function initializeDateWidget() {
    const dateWidgetEl = document.getElementById("current-date");
    if (!dateWidgetEl) return;

    const updateDate = () => {
      const now = new Date();
      const options = { 
        weekday: "short",
        month: "short", 
        day: "numeric", 
        year: "numeric" 
      };
      console.warn('[Dashboard] Could not fetch user name, using default');
    };

    updateDate();
    setInterval(updateDate, 60000);
  }

  // Initialize Sidebar Navigation
  function initializeSidebarNavigation() {
    const navItems = document.querySelectorAll(".sidebar-nav-item");
    const pageContentDiv = document.getElementById("page-content");
    
    if (navItems.length === 0) return;

    // helper: strip trailing -{id} suffix from page hash
    function stripIdSuffix(name) {
      return name.replace(/-\d+$/, '');
    }

    // Load page content based on hash
    async function loadPage(pageName) {
      if (!pageContentDiv) return;

      try {
        console.log(`[Nav] Loading page: ${pageName}`);
        
        const normalized = stripIdSuffix(pageName);

        const pageMap = {
          "dashboard": "dashboard.html",
          "timetables-list": "timetables-list.html",
          "courses": "courses.html",
          "instructors": "instructors.html",
          "classrooms": "classrooms.html",
          "nep-feature": "nep-feature.html",
          "settings": "settings.html",
          "timetable-setup": "timetable-setup.html",
          "timetable": "timetable.html"
        };

        let pageFile = pageMap[normalized] || "dashboard.html";

        const response = await fetch(TEMPLATES_BASE + "/" + pageFile, {
          cache: 'no-store',
          headers: { 'Cache-Control': 'no-cache, no-store, must-revalidate' }
        });
        
        if (!response.ok) {
          console.warn(`[Nav] Page not found: ${pageFile}, showing dashboard instead (status: ${response.status})`);
          pageContentDiv.innerHTML = "<div class='p-6 text-gray-500'>Page not found. Please select from the menu.</div>";
          return;
        }

        const html = await response.text();
        pageContentDiv.innerHTML = html;
        console.log(`[Nav] Page loaded successfully: ${pageName}`);

        // Initialize wizard if timetable-setup page was loaded
        if (normalized === "timetable-setup") {
            console.log('[App] Loading timetable-setup.js dynamically');
            const existingScript = document.querySelector('script[src="/static/js/timetable-setup.js"]');
            if (existingScript) {
              existingScript.remove();
              console.log('[App] Removed existing timetable-setup.js script');
            }
            const script = document.createElement('script');
            script.src = '/static/js/timetable-setup.js';
            script.onload = () => {
              console.log('[App] timetable-setup.js loaded, calling initWizard');
              if (typeof window.initWizard === 'function') {
                  window.initWizard();
              } else {
                  console.error('[App] initWizard not found after script load');
              }
            };
            script.onerror = () => {
              console.error('[App] Failed to load timetable-setup.js');
            };
            document.body.appendChild(script);
        }

        // Initialize courses module if courses page was loaded
        if (normalized === "courses") {
            console.log('[App] Loading courses.js dynamically');
            const existingScript = document.querySelector('script[src="/static/js/courses.js"]');
            if (existingScript) {
              existingScript.remove();
            }
            const script = document.createElement('script');
            script.src = '/static/js/courses.js';
            script.onload = () => {
                if (typeof window.initCourses === 'function') {
                    window.initCourses();
                } else {
                    document.dispatchEvent(new Event('DOMContentLoaded'));
                }
            };
            document.body.appendChild(script);
        }

        // Initialize instructors module if instructors page was loaded
        if (normalized === "instructors") {
            console.log('[App] Loading instructors.js dynamically');
            const existingScript = document.querySelector('script[src="/static/js/instructors.js"]');
            if (existingScript) {
              existingScript.remove();
            }
            const script = document.createElement('script');
            script.src = '/static/js/instructors.js';
            script.onload = () => {
                if (typeof window.initInstructors === 'function') {
                    window.initInstructors();
                } else {
                    document.dispatchEvent(new Event('DOMContentLoaded'));
                }
            };
            document.body.appendChild(script);
        }

        // Initialize timetable generator module if timetable-generator page was loaded
        if (normalized === "timetable-generator") {
            console.log('[App] Loading timetable-generator.js dynamically');
            const existingScript = document.querySelector('script[src="/static/js/timetable-generator.js"]');
            if (existingScript) {
              existingScript.remove();
            }
            const script = document.createElement('script');
            script.src = '/static/js/timetable-generator.js';
            script.onload = () => {
                if (typeof window.initTimetableGenerator === 'function') {
                    window.initTimetableGenerator();
                } else {
                    document.dispatchEvent(new Event('DOMContentLoaded'));
                }
            };
            document.body.appendChild(script);
        }
      } catch (error) {
        console.error(`[Nav] Error loading page:`, error);
        pageContentDiv.innerHTML = "<div class='p-6 text-red-500'>Error loading page. Please try again.</div>";
      }
    }

    // Update active nav item and load page on hash change
    function updateActiveNavItem() {
      const fullHash = window.location.hash.substring(1) || "dashboard";
      const currentHash = fullHash.split("?")[0]; // Remove query params
      const baseCurrent = stripIdSuffix(currentHash);
      
      navItems.forEach(item => {
        const itemHash = item.getAttribute("href").substring(1);
        const isMatch = baseCurrent === itemHash;
        
        if (isMatch) {
          item.classList.add("active");
        } else {
          item.classList.remove("active");
        }
      });

      loadPage(fullHash);
    }

    // Listen for hash changes
    window.addEventListener("hashchange", updateActiveNavItem);

    // Add click handlers to nav items
    navItems.forEach(item => {
      item.addEventListener("click", (e) => {
        const href = item.getAttribute("href");
        if (href && href.startsWith("#")) {
          window.location.hash = href;
        }
      });
    });

    // Initial load
    updateActiveNavItem();
  }

  // Initialize User Greeting
  async function initializeUserGreeting() {
    const welcomeNameEl = document.getElementById("welcome-name");
    if (!welcomeNameEl) return;

    console.log('[Dashboard] Fetching user info from /v1/me');
    const user = await fetchAPI("/me");
    
    if (user && user.full_name) {
      console.log('[Dashboard] User name received:', user.full_name);
      welcomeNameEl.textContent = user.full_name;
    } else {
      console.warn('[Dashboard] Could not fetch user name, using default');
      welcomeNameEl.textContent = "User";
    }
  }

  // Initialize Dashboard Cards
  async function initializeDashboardCards() {
    const upcomingCard = document.querySelector('[class*="Upcoming"]');
    const pendingCard = document.querySelector('[class*="Pending"]');
    
    if (!upcomingCard && !pendingCard) return;

    // Since /timetables/summary endpoint doesn't exist yet, just set placeholder values
    console.log('[Dashboard] Initializing cards with placeholder data');
    
    if (upcomingCard) {
      const description = upcomingCard.querySelector(".card-description");
      if (description) {
        description.textContent = "0 schedules scheduled";
      }
    }

    if (pendingCard) {
      const description = pendingCard.querySelector(".card-description");
      if (description) {
        description.textContent = "All tasks completed!";
      }
    }
  }

  // Initialize Quick Actions
  // NOTE: Quick action handlers are now in dashboard.html inline script
  // to avoid conflicts and ensure proper API calls before navigation

  // Initialize Dashboard
  function initializeDashboard() {
    console.log("[Dashboard] ========== DASHBOARD INIT START ==========");
    console.log("[Dashboard] Initializing date widget");
    initializeDateWidget();
    
    console.log("[Dashboard] Initializing sidebar navigation");
    initializeSidebarNavigation();
    
    console.log("[Dashboard] Initializing user greeting");
    initializeUserGreeting();
    
    console.log("[Dashboard] Initializing dashboard cards");
    initializeDashboardCards();
    
    console.log("[Dashboard] ========== DASHBOARD INIT END ==========");
  }

  // Event delegation for New Timetable button and structure page (handles dynamically loaded content)
  document.addEventListener('click', async (e) => {
    // Handle New Timetable button
    if (e.target && e.target.id === 'new-timetable-btn') {
      console.log('[App] New Timetable button clicked via event delegation!');
      e.preventDefault();
      
      try {
        const token = getAuthToken();
        if (!token) {
          alert('Please login first');
          return;
        }

        console.log('[App] Creating new timetable via API...');
        
        // Create new timetable
        const res = await fetch(API_BASE + "/timetables", {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ name: 'New Timetable' })
        });

        console.log('[App] API response status:', res.status);

        if (!res.ok) {
          const errorText = await res.text();
          console.error('[App] Failed to create timetable:', errorText);
          alert('Failed to create timetable: ' + errorText);
          return;
        }

        const timetable = await res.json();
        console.log('[App] Timetable created:', timetable);

        // Save current timetable id and redirect to unified wizard
        localStorage.setItem('current_timetable_id', timetable.id);
        console.log('[App] Redirecting to timetable wizard with id:', timetable.id);
        window.location.hash = `#timetable-setup-${timetable.id}`;
      } catch (err) {
        console.error('[App] Error creating timetable:', err);
        alert('Error creating timetable: ' + err.message);
      }
    }
  });

  // Run dashboard initialization if on dashboard page
  const sidebarContainer = document.querySelector(".sidebar-container");
  if (sidebarContainer) {
    console.log("Dashboard page detected - initializing");
    initializeDashboard();
  }

  // ======================================
  // EXPOSE API AND CONFIG TO WINDOW FOR PRODUCTION
  // ======================================
  window.plansphere = {
    fetchAPI,
    getAuthToken,
    API_BASE,
    TEMPLATES_BASE,
    TOKEN_KEY,
    VERSION: '1.0.0'
  };

  console.log('[App] PlanSphere initialized', window.plansphere);
});
