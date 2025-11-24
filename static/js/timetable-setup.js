// ===== UNIFIED TIMETABLE SETUP WIZARD =====
// Handles all 4 steps: Structure, Timings, Core Data, Finalize

(function() {
  'use strict';

  // Configuration
  const API_BASE = '/v1';
  const TOKEN_KEY = 'plansphere_token';
  
  let currentStep = 1;
  let timetableId = null;
  
  // Data storage
  const wizardData = {
    subjects: [],
    teachers: [],
    classes: [],
    rooms: [],
    workingDays: [],
    periodsPerDay: 8,
    breaksPerDay: 2,
    startTime: '08:00',
    periodDuration: 45,
    periodDuration: 45,
    breakDuration: 15,
    breakConfigs: [] // Array of { afterPeriod: number, duration: number }
  };

  // Helper functions
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
      const response = await fetch(API_BASE + endpoint, {
        ...options,
        headers,
        cache: 'no-store'
      });

      if (response.status === 401) {
        localStorage.removeItem(TOKEN_KEY);
        window.location.href = '/';
        return null;
      }

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || `API Error: ${response.status}`);
      }

      return response.json();
    } catch (error) {
      console.error('[Wizard] API Error:', error);
      throw error;
    }
  }

  function showMessage(message, isError = false) {
    const statusEl = document.getElementById('status-message');
    if (!statusEl) return;
    
    statusEl.textContent = message;
    statusEl.className = `mt-4 p-4 rounded-lg text-sm ${isError ? 'status-message error' : 'status-message success'}`;
    statusEl.classList.remove('hidden');
    
    setTimeout(() => {
      statusEl.classList.add('hidden');
    }, 5000);
  }

  // Step navigation
  function showStep(step) {
    console.log(`[Wizard] showStep called with step: ${step}`);
    
    // Hide all steps
    const allSteps = document.querySelectorAll('.wizard-step');
    console.log(`[Wizard] Found ${allSteps.length} wizard-step elements`);
    allSteps.forEach((el, index) => {
      console.log(`[Wizard] Removing active from step ${index + 1}, id: ${el.id}`);
      el.classList.remove('active');
    });

    // Show current step
    const stepEl = document.getElementById(`step-${step}`);
    console.log(`[Wizard] Looking for step-${step}, found:`, stepEl);
    if (stepEl) {
      stepEl.classList.add('active');
      console.log(`[Wizard] Added active class to step-${step}`);
      console.log(`[Wizard] Step element classes:`, stepEl.className);
    } else {
      console.error(`[Wizard] Could not find element with id step-${step}`);
    }

    // Update step indicators
    document.querySelectorAll('.step-item').forEach((item, index) => {
      item.classList.remove('active', 'completed');
      if (index + 1 < step) {
        item.classList.add('completed');
      } else if (index + 1 === step) {
        item.classList.add('active');
      }
    });

    // Update navigation buttons
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    
    if (prevBtn) {
      prevBtn.disabled = step === 1;
    }
    
    if (nextBtn) {
      nextBtn.textContent = step === 4 ? 'Complete' : 'Next →';
    }

    currentStep = step;
    
    // Load step-specific data
    if (step === 1) {
      // Add listener for new Step 1 next button
      const step1NextBtn = document.getElementById('step-1-next-btn');
      if (step1NextBtn) {
        step1NextBtn.onclick = handleNext;
      }
    } else if (step === 2) {
      renderBreakInputs();
      updateTimingsPreview();
    } else if (step === 4) {
      updateSummary();
    }

    // Toggle global nav visibility
    const globalNav = document.querySelector('.wizard-nav');
    if (globalNav) {
      globalNav.style.display = step === 1 ? 'none' : 'flex';
    }
    
    console.log(`[Wizard] showStep complete, currentStep is now: ${currentStep}`);
  }

  // Step 1: Structure
  function saveStructureData() {
    const days = Array.from(document.querySelectorAll('input[name="working-day"]:checked')).map(i => i.value);
    const numPeriods = parseInt(document.getElementById('num-periods')?.value) || 8;
    const numBreaks = parseInt(document.getElementById('num-breaks')?.value) || 2;

    wizardData.workingDays = days;
    wizardData.periodsPerDay = numPeriods;
    wizardData.breaksPerDay = numBreaks;

    console.log('[Wizard] Structure data saved:', wizardData);
  }

  async function submitStructureData() {
    if (!timetableId) {
      showMessage('No timetable ID found', true);
      return false;
    }

    saveStructureData();

    try {
      await fetchAPI(`/timetables/${timetableId}`, {
        method: 'PUT',
        body: JSON.stringify({
          days_of_week: wizardData.workingDays,
          periods_per_day: wizardData.periodsPerDay,
          breaks_per_day: wizardData.breaksPerDay
        })
      });

      console.log('[Wizard] Structure data submitted to API');
      return true;
    } catch (error) {
      showMessage('Error saving structure: ' + error.message, true);
      return false;
    }
  }

  // Step 2: Timings
  function saveTimingsData() {
    wizardData.startTime = document.getElementById('start-time')?.value || '08:00';
    wizardData.periodDuration = parseInt(document.getElementById('period-duration')?.value) || 45;
    // wizardData.breakDuration is now handled per break in breakConfigs, 
    // but we keep a default for new breaks if needed.
    
    // Save individual break configs
    const breakRows = document.querySelectorAll('.break-config-row');
    wizardData.breakConfigs = Array.from(breakRows).map(row => {
      return {
        afterPeriod: parseInt(row.querySelector('.break-after-period').value),
        duration: parseInt(row.querySelector('.break-duration-input').value)
      };
    });

    console.log('[Wizard] Timings data saved:', wizardData);
  }

  function renderBreakInputs() {
    const container = document.getElementById('break-config-container');
    const section = document.getElementById('break-configuration-section');
    
    if (!container || !section) return;

    const numBreaks = wizardData.breaksPerDay;
    const numPeriods = wizardData.periodsPerDay;

    if (numBreaks === 0) {
      section.classList.add('hidden');
      wizardData.breakConfigs = [];
      return;
    }

    section.classList.remove('hidden');
    container.innerHTML = '';



    // section.classList.remove('hidden'); // Not needed
    // container.innerHTML = ''; // Cleared above

    // Initialize breakConfigs if empty or size mismatch
    if (wizardData.breakConfigs.length !== numBreaks) {
      wizardData.breakConfigs = [];
      // Default distribution: roughly evenly spaced
      const interval = Math.floor(numPeriods / (numBreaks + 1));
      for (let i = 0; i < numBreaks; i++) {
        wizardData.breakConfigs.push({
          afterPeriod: (i + 1) * interval + (i > 0 ? 1 : 0), // Simple distribution logic
          duration: 15
        });
      }
    }

    wizardData.breakConfigs.forEach((config, index) => {
      const row = document.createElement('div');
      row.className = 'flex items-center gap-4 break-config-row bg-gray-50 p-3 rounded-md';
      
      // Generate options for "After Period"
      let optionsHtml = '';
      for (let p = 1; p < numPeriods; p++) {
        const selected = config.afterPeriod === p ? 'selected' : '';
        optionsHtml += `<option value="${p}" ${selected}>Period ${p}</option>`;
      }

      row.innerHTML = `
        <span class="font-medium text-gray-700 w-20">Break ${index + 1}:</span>
        <div class="flex items-center gap-2">
          <label class="text-sm text-gray-600">After</label>
          <select class="break-after-period block rounded-md border-gray-300 py-1 px-2 text-sm">
            ${optionsHtml}
          </select>
        </div>
        <div class="flex items-center gap-2">
          <label class="text-sm text-gray-600">Duration (min)</label>
          <input type="number" value="${config.duration}" min="5" max="60" 
            class="break-duration-input block w-20 rounded-md border-gray-300 py-1 px-2 text-sm">
        </div>
      `;

      // Add event listeners for live preview update
      const select = row.querySelector('.break-after-period');
      const input = row.querySelector('.break-duration-input');

      const updateHandler = () => {
        saveTimingsData();
        updateTimingsPreview();
      };

      select.addEventListener('change', updateHandler);
      input.addEventListener('input', updateHandler);

      container.appendChild(row);
    });
  }

  function updateTimingsPreview() {
    const tbody = document.getElementById('layout-grid-body');
    if (!tbody) return;

    // Ensure data is up to date from inputs before rendering
    // But avoid infinite loop if called from saveTimingsData -> render -> update
    // We just read values directly here or rely on wizardData being updated by handlers
    
    const startTime = wizardData.startTime;
    const periodDuration = wizardData.periodDuration;
    const periodsPerDay = wizardData.periodsPerDay;
    const breakConfigs = wizardData.breakConfigs;

    let html = '';
    let currentTime = startTime;

    for (let i = 1; i <= periodsPerDay; i++) {
      const startMinutes = timeToMinutes(currentTime);
      const endMinutes = startMinutes + periodDuration;
      const endTime = minutesToTime(endMinutes);

      html += `
        <tr class="hover:bg-gray-50">
          <td class="px-4 py-3 border font-semibold">Period ${i}</td>
          <td class="px-4 py-3 border">${currentTime}</td>
          <td class="px-4 py-3 border">${endTime}</td>
          <td class="px-4 py-3 border">${periodDuration} min</td>
        </tr>
      `;

      currentTime = endTime;

      // Check if a break is configured after this period
      const breakConfig = breakConfigs.find(b => b.afterPeriod === i);
      if (breakConfig) {
        const breakStartMinutes = endMinutes;
        const breakEndMinutes = breakStartMinutes + breakConfig.duration;
        const breakEndTime = minutesToTime(breakEndMinutes);

        html += `
          <tr class="bg-yellow-50">
            <td class="px-4 py-3 border font-semibold text-yellow-700">Break</td>
            <td class="px-4 py-3 border">${endTime}</td>
            <td class="px-4 py-3 border">${breakEndTime}</td>
            <td class="px-4 py-3 border">${breakConfig.duration} min</td>
          </tr>
        `;

        currentTime = breakEndTime;
      }
    }

    tbody.innerHTML = html;
  }

  function timeToMinutes(time) {
    const [hours, minutes] = time.split(':').map(Number);
    return hours * 60 + minutes;
  }

  function minutesToTime(minutes) {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}`;
  }

  // Step 3: Core Data
  async function addSubject() {
    const input = document.getElementById('new-subject');
    const val = input?.value.trim();
    if (!val || !timetableId) return;

    try {
      const course = await fetchAPI(`/timetables/${timetableId}/courses`, {
        method: 'POST',
        body: JSON.stringify({
          code: val.slice(0, 6).toUpperCase(),
          title: val,
          credits: 0,
          sessions_per_week: 1
        })
      });

      wizardData.subjects.push(course);
      renderList('subject-list', wizardData.subjects, 'title');
      input.value = '';
      showMessage('Subject added successfully');
    } catch (error) {
      showMessage('Error adding subject: ' + error.message, true);
    }
  }

  async function addTeacher() {
    const input = document.getElementById('new-teacher');
    const val = input?.value.trim();
    if (!val || !timetableId) return;

    try {
      const instructor = await fetchAPI(`/timetables/${timetableId}/instructors`, {
        method: 'POST',
        body: JSON.stringify({ name: val })
      });

      wizardData.teachers.push(instructor);
      renderList('teacher-list', wizardData.teachers, 'name');
      input.value = '';
      showMessage('Teacher added successfully');
    } catch (error) {
      showMessage('Error adding teacher: ' + error.message, true);
    }
  }

  async function addClass() {
    const input = document.getElementById('new-class');
    const val = input?.value.trim();
    if (!val || !timetableId) return;

    try {
      const classroom = await fetchAPI(`/timetables/${timetableId}/classrooms`, {
        method: 'POST',
        body: JSON.stringify({
          name: val,
          capacity: 0,
          room_type: 'class',
          features: ''
        })
      });

      wizardData.classes.push(classroom);
      renderList('class-list', wizardData.classes, 'name');
      input.value = '';
      showMessage('Class added successfully');
    } catch (error) {
      showMessage('Error adding class: ' + error.message, true);
    }
  }

  async function addRoom() {
    const input = document.getElementById('new-room');
    const val = input?.value.trim();
    if (!val || !timetableId) return;

    try {
      const classroom = await fetchAPI(`/timetables/${timetableId}/classrooms`, {
        method: 'POST',
        body: JSON.stringify({
          name: val,
          capacity: 0,
          room_type: 'room',
          features: ''
        })
      });

      wizardData.rooms.push(classroom);
      renderList('room-list', wizardData.rooms, 'name');
      input.value = '';
      showMessage('Room added successfully');
    } catch (error) {
      showMessage('Error adding room: ' + error.message, true);
    }
  }

  function renderList(listId, items, nameField) {
    const list = document.getElementById(listId);
    if (!list) return;

    if (items.length === 0) {
      list.innerHTML = '<li class="text-gray-500 text-sm">No items added yet</li>';
      return;
    }

    list.innerHTML = items.map((item, index) => `
      <li class="flex justify-between items-center bg-white p-3 rounded-md border text-sm">
        <span class="font-medium">${item[nameField]}</span>
        <button class="text-red-500 hover:text-red-700 font-bold" onclick="window.removeItem('${listId}', ${index})">×</button>
      </li>
    `).join('');
  }

  // Step 4: Summary & Generate
  function updateSummary() {
    document.getElementById('summary-subjects').textContent = wizardData.subjects.length;
    document.getElementById('summary-teachers').textContent = wizardData.teachers.length;
    document.getElementById('summary-classes').textContent = wizardData.classes.length;
    document.getElementById('summary-rooms').textContent = wizardData.rooms.length;

    document.getElementById('summary-days').textContent = wizardData.workingDays.join(', ') || 'Not set';
    document.getElementById('summary-periods').textContent = wizardData.periodsPerDay;
    document.getElementById('summary-start-time').textContent = wizardData.startTime;
    document.getElementById('summary-duration').textContent = `${wizardData.periodDuration} minutes`;
  }

  async function generateTimetable() {
    if (!timetableId) {
      showMessage('No timetable ID found', true);
      return;
    }

    try {
      await fetchAPI(`/timetables/${timetableId}`, {
        method: 'PUT',
        body: JSON.stringify({ status: 'finalized' })
      });

      showMessage('Timetable generated successfully!');
      
      setTimeout(() => {
        window.location.hash = '#dashboard';
      }, 1500);
    } catch (error) {
      showMessage('Error generating timetable: ' + error.message, true);
    }
  }

  // Navigation handlers
  async function handleNext() {
    if (currentStep === 1) {
      const success = await submitStructureData();
      if (!success) return;
    } else if (currentStep === 2) {
      saveTimingsData();
    }

    if (currentStep < 4) {
      showStep(currentStep + 1);
    } else {
      // Final step - generate
      await generateTimetable();
    }
  }

  function handlePrev() {
    if (currentStep > 1) {
      showStep(currentStep - 1);
    }
  }

  // Initialize wizard - GLOBAL function so app.js can call it
  window.initWizard = function() {
    // Prevent duplicate initialization
    if (window.wizardInitialized) {
      console.log('[Wizard] Already initialized, skipping...');
      return;
    }
    
    console.log('[Wizard] Initializing timetable setup wizard');
    window.wizardInitialized = true;

    // Get timetable ID from localStorage or hash
    timetableId = localStorage.getItem('current_timetable_id');
    const hash = window.location.hash;
    const hashMatch = hash.match(/#timetable-setup-(\d+)/);
    if (hashMatch) {
      timetableId = hashMatch[1];
      localStorage.setItem('current_timetable_id', timetableId);
    }

    if (!timetableId) {
      console.error('[Wizard] No timetable ID found');
      showMessage('No timetable selected. Redirecting to dashboard...', true);
      setTimeout(() => {
        window.location.hash = '#dashboard';
      }, 2000);
      return;
    }

    console.log('[Wizard] Timetable ID:', timetableId);

    // Set up event listeners (remove old ones first to prevent duplicates)
    const nextBtn = document.getElementById('next-btn');
    const prevBtn = document.getElementById('prev-btn');
    const generateBtn = document.getElementById('generate-timetable-btn');

    if (nextBtn) {
      nextBtn.removeEventListener('click', handleNext);
      nextBtn.addEventListener('click', handleNext);
      console.log('[Wizard] Next button listener attached');
    } else {
      console.warn('[Wizard] Next button not found!');
    }

    if (prevBtn) {
      prevBtn.removeEventListener('click', handlePrev);
      prevBtn.addEventListener('click', handlePrev);
      console.log('[Wizard] Prev button listener attached');
    }

    if (generateBtn) {
      generateBtn.removeEventListener('click', generateTimetable);
      generateBtn.addEventListener('click', generateTimetable);
      console.log('[Wizard] Generate button listener attached');
    }

    // Step 1 event listeners
    const periodsInput = document.getElementById('num-periods');
    const breaksInput = document.getElementById('num-breaks');
    if (periodsInput) {
      periodsInput.removeEventListener('change', saveStructureData);
      periodsInput.addEventListener('change', saveStructureData);
    }
    if (breaksInput) {
      breaksInput.removeEventListener('change', saveStructureData);
      breaksInput.addEventListener('change', saveStructureData);
    }

    // Step 2 event listeners
    const startTimeInput = document.getElementById('start-time');
    const periodDurationInput = document.getElementById('period-duration');
    const breakDurationInput = document.getElementById('break-duration');
    
    if (startTimeInput) {
      startTimeInput.removeEventListener('change', updateTimingsPreview);
      startTimeInput.addEventListener('change', updateTimingsPreview);
    }
    if (periodDurationInput) {
      periodDurationInput.removeEventListener('change', updateTimingsPreview);
      periodDurationInput.addEventListener('change', updateTimingsPreview);
    }
    if (breakDurationInput) {
      breakDurationInput.removeEventListener('change', updateTimingsPreview);
      breakDurationInput.addEventListener('change', updateTimingsPreview);
    }

    // Step 3 event listeners
    const addSubjectBtn = document.getElementById('add-subject-btn');
    const addTeacherBtn = document.getElementById('add-teacher-btn');
    const addClassBtn = document.getElementById('add-class-btn');
    const addRoomBtn = document.getElementById('add-room-btn');

    if (addSubjectBtn) {
      addSubjectBtn.removeEventListener('click', addSubject);
      addSubjectBtn.addEventListener('click', addSubject);
    }
    if (addTeacherBtn) {
      addTeacherBtn.removeEventListener('click', addTeacher);
      addTeacherBtn.addEventListener('click', addTeacher);
    }
    if (addClassBtn) {
      addClassBtn.removeEventListener('click', addClass);
      addClassBtn.addEventListener('click', addClass);
    }
    if (addRoomBtn) {
      addRoomBtn.removeEventListener('click', addRoom);
      addRoomBtn.addEventListener('click', addRoom);
    }

    // Allow Enter key to add items
    const newSubjectInput = document.getElementById('new-subject');
    const newTeacherInput = document.getElementById('new-teacher');
    const newClassInput = document.getElementById('new-class');
    const newRoomInput = document.getElementById('new-room');

    if (newSubjectInput) newSubjectInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') addSubject(); });
    if (newTeacherInput) newTeacherInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') addTeacher(); });
    if (newClassInput) newClassInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') addClass(); });
    if (newRoomInput) newRoomInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') addRoom(); });

    // Show first step
    showStep(1);
    console.log('[Wizard] Initialization complete');
  };

  // Global function for removing items
  window.removeItem = function(listId, index) {
    const listMap = {
      'subject-list': 'subjects',
      'teacher-list': 'teachers',
      'class-list': 'classes',
      'room-list': 'rooms'
    };

    const dataKey = listMap[listId];
    if (dataKey && wizardData[dataKey]) {
      wizardData[dataKey].splice(index, 1);
      renderList(listId, wizardData[dataKey], dataKey === 'subjects' ? 'title' : 'name');
    }
  };

})();

