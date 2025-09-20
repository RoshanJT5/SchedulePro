document.addEventListener("DOMContentLoaded", () => {
  const pageContent = document.getElementById("page-content");
  const navLinks = document.querySelectorAll(".nav-link");

  // --- Instructor Data (Our simple database) ---
  const instructorsData = {
    "eleanor-vance": {
      name: "Dr. Eleanor Vance",
      department: "Mathematics Dept.",
      email: "e.vance@example.edu",
      phone: "(555) 123-4567",
      office: "Room 301, Science Building",
      imgSrc:
        "https://lh3.googleusercontent.com/aida-public/AB6AXuCH6qJDSMphDfcZ8TdnNHuSBNn1Iyna49YKdP--kWNpPvFtcDuYzaUDbdDNx2EK3u1WM5RegF0-xmxAMS8Dlwo3p8WDINnlec1IFIqB-mLpaWtQaEzVR1XGwQYn9IiAUYsY4CvEownXW_NNFnwkSSFGd4ow0ivPi2mI0YtcRKeQHHKw56Fwdjb51m1dveSiMf9LSN6MQyvK5XFoX3hqTaB2cKtINBiKPSn-0_X06-Ok9ZlYKNB9NilnUFLMXrNjEn6ZGD9AdZYgwrg",
      courses: [
        { code: "MATH101", name: "Calculus I", credits: 4 },
        { code: "MATH201", name: "Linear Algebra", credits: 3 },
        { code: "MATH301", name: "Differential Equations", credits: 3 },
      ],
    },
    "samuel-reed": {
      name: "Dr. Samuel Reed",
      department: "Physics Dept.",
      email: "s.reed@example.edu",
      phone: "(555) 234-5678",
      office: "Room 305, Science Building",
      imgSrc:
        "https://lh3.googleusercontent.com/aida-public/AB6AXuDLUBAuh9N7keG6T6cQ1rj7NTi9QC1J-pW-zzca-yvFzqkhqkTg1_EPe1f0xnEIAFdWcBY3kSGfkL3PGrTn5B8mRYpuTMFqw9nsAszxx8eTNfnhly4x4iNmMthJb2r4m5zrO7vnUKbYuFdaKgwjjIGTgOceKSSwm6xofP6GllytqocOMeXa_aAWziA2aIGvxsmcdQi7EOP-gcVNuWwQdcjgUT_rfoZbe5q5EkDUPnW1L7vcWvqvEQuD-9qDU59IkwOn6dMClvBu68I",
      courses: [
        { code: "PHYS101", name: "General Physics I", credits: 4 },
        { code: "PHYS210", name: "Modern Physics", credits: 3 },
      ],
    },
    "olivia-bennett": {
      name: "Dr. Olivia Bennett",
      department: "Chemistry Dept.",
      email: "o.bennett@example.edu",
      phone: "(555) 345-6789",
      office: "Room 210, Chemistry Hall",
      imgSrc:
        "https://lh3.googleusercontent.com/aida-public/AB6AXuD3g89ByGvD7t5W1Jtgbg_C_tmvssc5JeXAOBO7QEQ2qp9x_0uOkSz6ViP-k-CRmFDUsknF2WrFSP14g2q-X5UWVjkr3NOoyw1BGCRanlzJOnpvR0RYUCyhmq0MSlsD64QENwDy0M5D6yUYAByJgjgtUtXgauj6LyRyLTw_jovYUvARUdmFW7EVlhUP-N97U33aYBu61I5-npfBrFJax-Ozv3ATC7YsdZftWO4zAGw2-qVv3bCYiKdTk_trET-dtRjLs7FZW8SpXI0",
      courses: [
        { code: "CHEM101", name: "Intro to Chemistry", credits: 4 },
        { code: "CHEM220", name: "Organic Chemistry I", credits: 4 },
        { code: "CHEM221", name: "Organic Chemistry Lab", credits: 1 },
        { code: "CHEM350", name: "Biochemistry", credits: 3 },
      ],
    },
    "ethan-carter": {
      name: "Dr. Ethan Carter",
      department: "Biology Dept.",
      email: "e.carter@example.edu",
      phone: "(555) 456-7890",
      office: "Room 112, Life Sciences Building",
      imgSrc:
        "https://lh3.googleusercontent.com/aida-public/AB6AXuCprC3K-q2U0Up7ijK1sNrUXT3502MZH7vIrwRxYJ3qIfmrNEmCltCR3dcjdXgWR7v2Yln7NcfazqTrWF24sC_MP-1Sx7lFiSh4QSpHVh6CsIxERu3_vNaS-7ItqtTpkdYy4Jt6U9b3zG4FPHcUtz5WeVx9vxWccqaXDpsGQ82lxtIfrZEqi5H7_d4KBIcX9GCh-hkivrqQuLmERVESjNRX6QMoJ3zXrkrxdibgDADuJvzjGxr7GhdvQ2WcZJUyvYD8-RJzfE3saXQ",
      courses: [
        { code: "BIO101", name: "General Biology", credits: 4 },
        { code: "BIO205", name: "Genetics", credits: 3 },
        { code: "BIO310", name: "Cell Biology", credits: 3 },
      ],
    },
  };

  // --- Color definitions and page mapping ---
  const colors = {
    active: { bg: "#2563eb", text: "#eff6ff" },
    hover: { bg: "#f1f5f9", text: "#2563eb" },
    default: { bg: "transparent", text: "#334155" },
  };
  const pageToSectionMap = {
    dashboard: "dashboard",
    "timetables-list": "timetables-list",
    "timetable-setup": "timetables-list",
    "timetable-input": "timetables-list",
    timetable: "timetables-list",
    courses: "courses",
    instructors: "instructors",
    classrooms: "classrooms",
    settings: "settings",
  };

  // --- Logic for Instructor Profile Modal ---
  const initializeInstructorsPage = () => {
    const modal = document.getElementById("instructor-modal");
    if (!modal) return;
    const closeBtn = document.getElementById("modal-close-btn");
    const viewProfileBtns = document.querySelectorAll(".view-profile-btn");
    viewProfileBtns.forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        const instructorId = btn.dataset.instructorId;
        const data = instructorsData[instructorId];
        if (data) {
          document.getElementById("modal-img").src = data.imgSrc;
          document.getElementById("modal-name").textContent = data.name;
          document.getElementById("modal-department").textContent =
            data.department;
          document.getElementById("modal-email").textContent = data.email;
          document.getElementById("modal-phone").textContent = data.phone;
          document.getElementById("modal-office").textContent = data.office;
          const coursesTableBody = document.getElementById(
            "modal-courses-table"
          );
          coursesTableBody.innerHTML = "";
          data.courses.forEach((course) => {
            const row = `<tr><td class="px-4 py-3 font-medium text-secondary-900">${course.code}</td><td class="px-4 py-3">${course.name}</td><td class="px-4 py-3">${course.credits}</td></tr>`;
            coursesTableBody.innerHTML += row;
          });
          modal.classList.remove("hidden");
        }
      });
    });
    closeBtn.addEventListener("click", () => modal.classList.add("hidden"));
    modal.addEventListener("click", (e) => {
      if (e.target.id === "instructor-modal") modal.classList.add("hidden");
    });
  };

  // --- Logic for Multi-Step Timetable Form ---
  const initializeTimetableSetupPage = () => {
    const step1Form = document.getElementById("step-1-form");
    if (!step1Form) return;
    const step2Form = document.getElementById("step-2-form");
    const nextBtn = document.getElementById("next-step-btn");
    const prevBtn = document.getElementById("prev-step-btn");
    const addSubjectBtn = document.getElementById("add-subject-btn");
    const subjectList = document.getElementById("subject-list");
    const step1Indicator = document.getElementById("step-1-indicator");
    const step2Indicator = document.getElementById("step-2-indicator");
    const breaksList = document.getElementById("breaks-list");
    const addBreakBtn = document.getElementById("add-break-btn");

    const updateIndicators = (step) => {
      const step1Circle = step1Indicator.querySelector("span:first-child");
      const step1Text = step1Indicator.querySelector("span:last-child");
      const step2Circle = step2Indicator.querySelector("span:first-child");
      const step2Text = step2Indicator.querySelector("span:last-child");
      if (step === 1) {
        step1Circle.classList.add("bg-blue-600", "text-white");
        step1Circle.classList.remove("bg-gray-200", "text-gray-500");
        step1Text.classList.add("text-blue-600");
        step1Text.classList.remove("text-gray-500");
        step2Circle.classList.remove("bg-blue-600", "text-white");
        step2Circle.classList.add("bg-gray-200", "text-gray-500");
        step2Text.classList.remove("text-blue-600");
        step2Text.classList.add("text-gray-500");
      } else {
        step1Circle.classList.remove("bg-blue-600", "text-white");
        step1Circle.classList.add("bg-gray-200", "text-gray-500");
        step1Text.classList.remove("text-blue-600");
        step1Text.classList.add("text-gray-500");
        step2Circle.classList.add("bg-blue-600", "text-white");
        step2Circle.classList.remove("bg-gray-200", "text-gray-500");
        step2Text.classList.add("text-blue-600");
        step2Text.classList.remove("text-gray-500");
      }
    };

    const goToStep2 = () => {
      step1Form.classList.add("hidden");
      step2Form.classList.remove("hidden");
      updateIndicators(2);
    };

    const goToStep1 = () => {
      step2Form.classList.add("hidden");
      step1Form.classList.remove("hidden");
      updateIndicators(1);
    };

    const addSubjectRow = () => {
      const newRow = document.createElement("div");
      newRow.className =
        "grid grid-cols-1 sm:grid-cols-[1fr_auto_auto] gap-4 items-center";
      newRow.innerHTML = `<input class="block w-full rounded-md border-secondary-200 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm" placeholder="e.g., Subject Name" type="text" /><div class="relative"><input class="block w-full rounded-md border-secondary-200 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm pr-16 remove-arrows" placeholder="e.g., 5" type="text" inputmode="numeric" pattern="[0-9]*" /><div class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3"><span class="text-secondary-500 sm:text-sm">hours/week</span></div></div><button class="remove-subject-btn p-2 text-secondary-400 hover:text-red-600" type="button"><span class="material-symbols-outlined text-base">delete</span></button>`;
      subjectList.appendChild(newRow);
      newRow
        .querySelector(".remove-subject-btn")
        .addEventListener("click", () => newRow.remove());
    };

    const addBreakRow = (name = "", duration = "", afterPeriod = "") => {
      const newRow = document.createElement("div");
      newRow.className =
        "grid grid-cols-1 sm:grid-cols-[1fr_120px_120px_auto] gap-3 items-center";
      newRow.innerHTML = `<input type="text" value="${name}" placeholder="Break Name (e.g., Lunch)" class="block w-full rounded-md border-secondary-200 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"><input type="text" inputmode="numeric" pattern="[0-9]*" value="${duration}" placeholder="Duration" class="block w-full rounded-md border-secondary-200 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm remove-arrows"><input type="text" inputmode="numeric" pattern="[0-9]*" value="${afterPeriod}" placeholder="After Period" class="block w-full rounded-md border-secondary-200 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm remove-arrows"><button class="remove-break-btn p-2 text-secondary-400 hover:text-red-600" type="button"><span class="material-symbols-outlined">delete</span></button>`;
      breaksList.appendChild(newRow);
      newRow
        .querySelector(".remove-break-btn")
        .addEventListener("click", () => newRow.remove());
    };

    nextBtn.addEventListener("click", goToStep2);
    prevBtn.addEventListener("click", goToStep1);
    addSubjectBtn.addEventListener("click", addSubjectRow);
    addBreakBtn.addEventListener("click", () => addBreakRow());

    if (subjectList.children.length === 0) {
      addSubjectRow();
      addSubjectRow();
      addSubjectRow();
    }
    if (breaksList.children.length === 0) {
      addBreakRow("Short Break", "15", "2");
      addBreakRow("Long Break", "30", "4");
    }
  };

  // --- Core Application Logic ---
  const loadContent = async (page) => {
    pageContent.innerHTML =
      '<p class="text-center text-secondary-500">Loading...</p>';
    try {
      const response = await fetch(`${page}.html`);
      if (!response.ok) throw new Error("Page not found.");
      const content = await response.text();
      pageContent.innerHTML = content;

      if (page === "instructors") {
        initializeInstructorsPage();
      } else if (page === "timetable-setup") {
        initializeTimetableSetupPage();
      }
    } catch (error) {
      pageContent.innerHTML = `<p class="text-center text-red-500">Error: Could not load page. ${error.message}</p>`;
    }
  };

  const updateNavStyles = () => {
    const currentPage = window.location.hash.substring(1) || "dashboard";
    const activeSection = pageToSectionMap[currentPage] || "";
    navLinks.forEach((link) => {
      const linkPage = new URL(link.href).hash.substring(1);
      if (linkPage === activeSection) {
        link.style.backgroundColor = colors.active.bg;
        link.style.color = colors.active.text;
        link.style.fontWeight = "600";
      } else {
        link.style.backgroundColor = colors.default.bg;
        link.style.color = colors.default.text;
        link.style.fontWeight = "500";
      }
    });
  };

  navLinks.forEach((link) => {
    link.addEventListener("mouseenter", () => {
      const currentPage = window.location.hash.substring(1) || "dashboard";
      const activeSection = pageToSectionMap[currentPage] || "";
      const linkPage = new URL(link.href).hash.substring(1);
      if (linkPage !== activeSection) {
        link.style.backgroundColor = colors.hover.bg;
        link.style.color = colors.hover.text;
      }
    });
    link.addEventListener("mouseleave", () => {
      const currentPage = window.location.hash.substring(1) || "dashboard";
      const activeSection = pageToSectionMap[currentPage] || "";
      const linkPage = new URL(link.href).hash.substring(1);
      if (linkPage !== activeSection) {
        link.style.backgroundColor = colors.default.bg;
        link.style.color = colors.default.text;
      }
    });
  });

  const handleRouteChange = () => {
    const page = window.location.hash.substring(1) || "dashboard";
    loadContent(page);
    updateNavStyles();
  };

  window.addEventListener("hashchange", handleRouteChange);
  handleRouteChange();
});
