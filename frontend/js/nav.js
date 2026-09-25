/**
 * nav.js — builds the role-appropriate sidebar (per the required
 * "Navigation must change according to the logged-in role" spec) and the
 * topbar user chip. Include after api.js on every shell page, then call
 * renderShellNav('current-page-key').
 */

const NAV_ICONS = {
  dashboard:
    '<svg viewBox="0 0 24 24" fill="none"><path d="M4 13h6V4H4v9Zm10 7h6v-9h-6v9ZM4 20h6v-5H4v5Zm10-11h6V4h-6v5Z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/></svg>',
  patients:
    '<svg viewBox="0 0 24 24" fill="none"><path d="M9 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm7-1a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM2 21c.7-3.6 3.5-6 7-6s6.3 2.4 7 6M15 21c.4-2 1.6-4.7 5-4.7 1 0 1.8.2 2.5.6" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  register:
    '<svg viewBox="0 0 24 24" fill="none"><path d="M9 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM2 21c.7-3.6 3.5-6 7-6s6.3 2.4 7 6M18 9v6M15 12h6" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  lab:
    '<svg viewBox="0 0 24 24" fill="none"><path d="M9 3v6.5L4.5 18a2 2 0 0 0 1.8 3h11.4a2 2 0 0 0 1.8-3L15 9.5V3M9 3h6M8 15h8" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  upload:
    '<svg viewBox="0 0 24 24" fill="none"><path d="M12 16V4m0 0 4 4m-4-4-4 4M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  voice:
    '<svg viewBox="0 0 24 24" fill="none"><path d="M12 15a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3Zm-7-3a7 7 0 0 0 14 0M12 19v3" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  prescriptions:
    '<svg viewBox="0 0 24 24" fill="none"><path d="M6 3h9l5 5v13H6V3Zm9 0v5h5M9 12h6M9 16h6M9 8h2" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  users:
    '<svg viewBox="0 0 24 24" fill="none"><path d="M17 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm8 10v-2a4 4 0 0 0-3-3.87M15 3.13a4 4 0 0 1 0 7.75" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  activity:
    '<svg viewBox="0 0 24 24" fill="none"><path d="M22 12h-4l-3 9L9 3l-3 9H2" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  profile:
    '<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="8" r="3.6" stroke="currentColor" stroke-width="1.7"/><path d="M4.5 20c1-3.8 4-5.8 7.5-5.8s6.5 2 7.5 5.8" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>',
  logout:
    '<svg viewBox="0 0 24 24" fill="none"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>',
};

const BRAND_MARK_SVG = `
<svg viewBox="0 0 40 40" fill="none">
  <rect x="5" y="5" width="30" height="30" rx="4" stroke="currentColor" stroke-width="1.6"/>
  <path d="M13 20h5.5M20.5 20H27M20 13v5.5M20 21.5V27" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
  <path d="M13 27.5h4M23 27.5h4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" opacity="0.55"/>
</svg>`;

const BELL_SVG =
  '<svg viewBox="0 0 24 24" fill="none"><path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9Z" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/><path d="M13.7 21a2 2 0 0 1-3.4 0" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>';

const MENU_SVG =
  '<svg viewBox="0 0 24 24" fill="none"><path d="M4 6h16M4 12h16M4 18h16" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';

const CHEVRON_SVG =
  '<svg viewBox="0 0 24 24" fill="none"><path d="m6 9 6 6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';

// Nav items per role — matches the "NAVIGATION" section of the spec.
const NAV_BY_ROLE = {
  admin: [
    { key: "dashboard", label: "Dashboard", href: "/dashboard.html", icon: "dashboard" },
    { key: "users", label: "Users", href: "/users.html", icon: "users" },
    { key: "patients", label: "Patients", href: "/patients.html", icon: "patients" },
    { key: "lab-reports", label: "Laboratory Reports", href: "/lab-reports.html", icon: "lab" },
    { key: "prescriptions-list", label: "Prescriptions", href: "/prescriptions-list.html", icon: "prescriptions" },
    { key: "activity", label: "System Activity", href: "/activity.html", icon: "activity" },
    { key: "profile", label: "Profile", href: "/profile.html", icon: "profile" },
  ],
  doctor: [
    { key: "dashboard", label: "Dashboard", href: "/dashboard.html", icon: "dashboard" },
    { key: "patients", label: "Patients", href: "/patients.html", icon: "patients" },
    { key: "lab-reports", label: "Laboratory Reports", href: "/lab-reports.html", icon: "lab" },
    { key: "voice", label: "Voice Prescription", href: "/index.html", icon: "voice" },
    { key: "prescriptions-list", label: "Prescriptions", href: "/prescriptions-list.html", icon: "prescriptions" },
    { key: "profile", label: "Profile", href: "/profile.html", icon: "profile" },
  ],
  lab_staff: [
    { key: "dashboard", label: "Dashboard", href: "/dashboard.html", icon: "dashboard" },
    { key: "patients", label: "Patients", href: "/patients.html", icon: "patients" },
    { key: "upload", label: "Upload Laboratory Report", href: "/lab-upload.html", icon: "upload" },
    { key: "lab-reports", label: "Laboratory Reports", href: "/lab-reports.html", icon: "lab" },
    { key: "profile", label: "Profile", href: "/profile.html", icon: "profile" },
  ],
  receptionist: [
    { key: "dashboard", label: "Dashboard", href: "/dashboard.html", icon: "dashboard" },
    { key: "register", label: "Register Patient", href: "/patients.html?new=1", icon: "register" },
    { key: "patients", label: "Patients", href: "/patients.html", icon: "patients" },
    { key: "profile", label: "Profile", href: "/profile.html", icon: "profile" },
  ],
};

const ROLE_LABEL = {
  admin: "Admin",
  doctor: "Doctor",
  lab_staff: "Lab Staff",
  receptionist: "Receptionist",
};

function renderShellNav(activeKey) {
  const user = Auth.getUser();
  if (!user) return;

  const items = NAV_BY_ROLE[user.role] || [];
  const sidebar = document.getElementById("appSidebar");
  if (sidebar) {
    sidebar.innerHTML = `
      <div class="sidebar-brand">
        <div class="sidebar-brand-mark">${BRAND_MARK_SVG}</div>
        <div class="sidebar-brand-text">
          <div class="sidebar-brand-title">Healthcare System</div>
          <div class="sidebar-brand-role">${ROLE_LABEL[user.role] || user.role}</div>
        </div>
      </div>
      ${items
        .map(
          (item) => `
        <a class="nav-link ${item.key === activeKey ? "active" : ""}" href="${item.href}">
          ${NAV_ICONS[item.icon] || ""}<span>${item.label}</span>
        </a>`
        )
        .join("")}
      <div class="nav-spacer"></div>
      <a class="nav-link logout-link" href="#" id="logoutLink">${NAV_ICONS.logout}<span>Logout</span></a>
    `;
    document.getElementById("logoutLink").addEventListener("click", (e) => {
      e.preventDefault();
      Auth.logout();
    });
  }

  const userChip = document.getElementById("shellUserChip");
  if (userChip) {
    const initials = (user.full_name || "?")
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((s) => s[0].toUpperCase())
      .join("");
    userChip.innerHTML = `
      <div class="shell-bell">
        ${BELL_SVG}
        <span class="shell-bell-badge">3</span>
      </div>
      <a class="shell-user-chip" href="/profile.html">
        <div class="shell-user-avatar">${initials}</div>
        <div class="shell-user-name">
          <strong>${escapeHtmlSafe(user.full_name)}</strong>
          <span>${ROLE_LABEL[user.role] || user.role}</span>
        </div>
        <div class="shell-user-chevron">${CHEVRON_SVG}</div>
      </a>`;
  }

  const menuBtn = document.getElementById("shellMenuBtn");
  if (menuBtn) {
    menuBtn.innerHTML = MENU_SVG;
    menuBtn.addEventListener("click", () => {
      document.getElementById("appSidebar")?.classList.toggle("sidebar-open");
    });
  }
}
