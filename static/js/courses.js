// Courses Management Module

const API_BASE = '/v1';
const TOKEN_KEY = 'plansphere_token';
let branches = [];
let currentBranch = null;
let currentSemester = 1;
let branchCourses = [];

// Helper to get auth token
function getAuthToken() {
    return localStorage.getItem(TOKEN_KEY);
}

// Helper to get auth headers
function getAuthHeaders() {
    const token = getAuthToken();
    return {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
    };
}

// Initialization
window.initCourses = function() {
    console.log('Initializing Courses Module');
    fetchBranches();
    
    // Search listener
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            renderBranches(e.target.value, document.getElementById('degree-filter').value);
        });
    }

    // Filter listener
    const degreeFilter = document.getElementById('degree-filter');
    if (degreeFilter) {
        degreeFilter.addEventListener('change', (e) => {
            renderBranches(document.getElementById('search-input').value, e.target.value);
        });
    }
};

// Auto-init if DOM is already loaded (for direct page loads, though rare in this SPA setup)
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    // window.initCourses(); // Don't auto-init here to avoid double init if app.js calls it
}

// Fetch Branches
async function fetchBranches() {
    try {
        const response = await fetch(`${API_BASE}/branches`);
        if (!response.ok) throw new Error('Failed to fetch branches');
        branches = await response.json();
        renderBranches();
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('courses-container').innerHTML = 
            '<div class="text-center text-red-500 py-12">Error loading courses. Please try again.</div>';
    }
}

// Render Branches
function renderBranches(searchTerm = '', degreeFilter = '') {
    const container = document.getElementById('courses-container');
    container.innerHTML = '';

    // Filter branches
    const filtered = branches.filter(branch => {
        const matchesSearch = (branch.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                             (branch.code && branch.code.toLowerCase().includes(searchTerm.toLowerCase())));
        const matchesDegree = degreeFilter ? branch.degree === degreeFilter : true;
        return matchesSearch && matchesDegree;
    });

    if (filtered.length === 0) {
        container.innerHTML = '<div class="text-center text-gray-500 py-12">No courses found.</div>';
        return;
    }

    // Group by Degree
    const grouped = filtered.reduce((acc, branch) => {
        if (!acc[branch.degree]) acc[branch.degree] = [];
        acc[branch.degree].push(branch);
        return acc;
    }, {});

    // Render Groups
    for (const [degree, degreeBranches] of Object.entries(grouped)) {
        const section = document.createElement('div');
        section.innerHTML = `
            <h2 class="text-2xl font-bold text-gray-800 border-b pb-3 mb-6">${getDegreeFullName(degree)} (${degree})</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 branch-grid">
                <!-- Branches injected here -->
            </div>
        `;
        
        const grid = section.querySelector('.branch-grid');
        degreeBranches.forEach(branch => {
            const card = createBranchCard(branch);
            grid.appendChild(card);
        });

        container.appendChild(section);
    }
}

function getDegreeFullName(degree) {
    const map = {
        'B.Tech': 'Bachelor of Technology',
        'BCA': 'Bachelor of Computer Applications',
        'B.Sc': 'Bachelor of Science',
        'M.Tech': 'Master of Technology',
        'MBA': 'Master of Business Administration'
    };
    return map[degree] || degree;
}

function createBranchCard(branch) {
    const div = document.createElement('div');
    div.className = 'bg-white border border-secondary-200 rounded-lg shadow-sm p-6 flex flex-col gap-4 cursor-pointer hover:shadow-md transition-shadow';
    div.onclick = (e) => {
        if (!e.target.closest('button')) {
            openBranchDetail(branch);
        }
    };

    // Determine icon and color based on branch name
    let icon = 'school';
    let colorClass = 'bg-blue-100 text-blue-600';
    
    if (branch.name.toLowerCase().includes('computer') || branch.code === 'CSE' || branch.code === 'IT') {
        icon = 'computer';
        colorClass = 'bg-blue-100 text-blue-600';
    } else if (branch.name.toLowerCase().includes('mechanic')) {
        icon = 'precision_manufacturing';
        colorClass = 'bg-orange-100 text-orange-600';
    } else if (branch.name.toLowerCase().includes('civil')) {
        icon = 'architecture';
        colorClass = 'bg-yellow-100 text-yellow-600';
    } else if (branch.name.toLowerCase().includes('electr')) {
        icon = 'bolt';
        colorClass = 'bg-yellow-100 text-yellow-600';
    } else if (branch.name.toLowerCase().includes('science') || branch.degree === 'B.Sc') {
        icon = 'science';
        colorClass = 'bg-green-100 text-green-600';
    }

    div.innerHTML = `
        <div class="flex items-start justify-between">
            <div class="flex items-center gap-4">
                <div class="flex-shrink-0 w-12 h-12 flex items-center justify-center ${colorClass} rounded-lg">
                    <span class="material-symbols-outlined">${icon}</span>
                </div>
                <div>
                    <h3 class="font-semibold text-secondary-900">${branch.name} ${branch.code ? `(${branch.code})` : ''}</h3>
                    <p class="text-sm text-secondary-500">${branch.duration_years}-Year Program</p>
                </div>
            </div>
            <button class="text-secondary-400 hover:text-secondary-600" onclick="event.stopPropagation(); deleteBranch(${branch.id})">
                <span class="material-symbols-outlined">delete</span>
            </button>
        </div>
        <div class="flex-grow"></div>
        <div class="flex items-center justify-between text-sm text-secondary-500 pt-4 border-t">
            <span class="font-medium text-secondary-700">HOD: ${branch.hod_name || 'Not Assigned'}</span>
            <span class="font-medium text-secondary-700">${branch.total_semesters} Semesters</span>
        </div>
    `;
    return div;
}

// Branch Detail Logic
async function openBranchDetail(branch) {
    currentBranch = branch;
    currentSemester = 1;
    
    document.getElementById('detail-branch-name').textContent = `${branch.name} (${branch.degree})`;
    document.getElementById('detail-branch-info').textContent = `${branch.duration_years} Years • ${branch.total_semesters} Semesters`;
    
    // Render Tabs
    const tabsContainer = document.getElementById('semester-tabs');
    tabsContainer.innerHTML = '';
    for (let i = 1; i <= branch.total_semesters; i++) {
        const tab = document.createElement('a');
        tab.href = '#';
        tab.className = `group flex items-center px-2 py-2 text-sm font-medium rounded-md ${i === 1 ? 'bg-gray-200 text-gray-900' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'}`;
        tab.textContent = `Semester ${i}`;
        tab.onclick = (e) => {
            e.preventDefault();
            switchSemester(i);
        };
        tabsContainer.appendChild(tab);
    }

    // Fetch Courses
    await fetchBranchCourses(branch.id);
    
    // Show Modal
    document.getElementById('branch-detail-modal').classList.remove('hidden');
    switchSemester(1);
}

function closeBranchDetail() {
    document.getElementById('branch-detail-modal').classList.add('hidden');
    currentBranch = null;
}

function switchSemester(sem) {
    currentSemester = sem;
    document.getElementById('current-semester-title').textContent = `Semester ${sem}`;
    
    // Update tabs styling
    const tabs = document.getElementById('semester-tabs').children;
    Array.from(tabs).forEach((tab, index) => {
        if (index + 1 === sem) {
            tab.className = 'group flex items-center px-2 py-2 text-sm font-medium rounded-md bg-gray-200 text-gray-900';
        } else {
            tab.className = 'group flex items-center px-2 py-2 text-sm font-medium rounded-md text-gray-600 hover:bg-gray-50 hover:text-gray-900';
        }
    });

    renderSubjects();
}

async function fetchBranchCourses(branchId) {
    try {
        const response = await fetch(`${API_BASE}/branches/${branchId}/courses`);
        if (response.ok) {
            branchCourses = await response.json();
        }
    } catch (error) {
        console.error('Error fetching courses:', error);
    }
}

function renderSubjects() {
    const tbody = document.getElementById('subjects-table-body');
    tbody.innerHTML = '';
    
    const semCourses = branchCourses.filter(c => c.semester === currentSemester);
    
    if (semCourses.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="px-3 py-8 text-center text-gray-500">No subjects added for this semester yet.</td></tr>';
        return;
    }

    semCourses.forEach(course => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-6">${course.code}</td>
            <td class="whitespace-nowrap px-3 py-4 text-sm text-gray-500">${course.name || course.title}</td>
            <td class="whitespace-nowrap px-3 py-4 text-sm text-gray-500">${course.subject_type || 'Theory'}</td>
            <td class="whitespace-nowrap px-3 py-4 text-sm text-gray-500">${course.credits || '-'}</td>
            <td class="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                <button onclick="deleteSubject(${course.id})" class="text-red-600 hover:text-red-900">Delete</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Add Branch Modal
function openAddBranchModal() {
    document.getElementById('add-branch-modal').classList.remove('hidden');
}

function closeAddBranchModal() {
    document.getElementById('add-branch-modal').classList.add('hidden');
    document.getElementById('add-branch-form').reset();
}

async function handleCreateBranch(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    
    // Check if user is logged in
    const token = getAuthToken();
    if (!token) {
        alert('You need to be logged in to create a branch. Please login first.');
        window.location.href = '/';
        return;
    }
    
    console.log('Creating branch with data:', data);
    console.log('Auth token exists:', !!token);
    
    try {
        const response = await fetch(`${API_BASE}/branches`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(data)
        });

        console.log('Response status:', response.status);
        
        if (response.ok) {
            closeAddBranchModal();
            fetchBranches();
        } else {
            const errorText = await response.text();
            console.error('Error response:', errorText);
            if (response.status === 401) {
                alert('Authentication failed. Please login again.');
                window.location.href = '/';
            } else {
                alert('Failed to create branch: ' + errorText);
            }
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error creating branch: ' + error.message);
    }
}

async function deleteBranch(id) {
    if (!confirm('Are you sure you want to delete this branch?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/branches/${id}`, { 
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        if (response.ok) {
            fetchBranches();
        } else {
            alert('Failed to delete branch');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error deleting branch');
    }
}

// Add Subject Modal
function openAddSubjectModal() {
    document.getElementById('add-subject-modal').classList.remove('hidden');
}

function closeAddSubjectModal() {
    document.getElementById('add-subject-modal').classList.add('hidden');
    document.getElementById('add-subject-form').reset();
}

async function handleCreateSubject(e) {
    e.preventDefault();
    if (!currentBranch) return;

    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    
    // Add context
    data.branch_id = currentBranch.id;
    data.semester = currentSemester;

    try {
        const response = await fetch(`${API_BASE}/courses`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(data)
        });

        if (response.ok) {
            closeAddSubjectModal();
            await fetchBranchCourses(currentBranch.id);
            renderSubjects();
        } else {
            const errorText = await response.text();
            alert('Failed to add subject: ' + errorText);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error adding subject: ' + error.message);
    }
}

async function deleteSubject(id) {
    if (!confirm('Are you sure?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/courses/${id}`, { 
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        if (response.ok) {
            await fetchBranchCourses(currentBranch.id);
            renderSubjects();
        } else {
            alert('Failed to delete subject');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error deleting subject');
    }
}
