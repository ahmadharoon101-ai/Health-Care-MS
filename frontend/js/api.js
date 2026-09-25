/**
 * api.js — thin fetch wrapper shared by every page in the new system
 * modules. Attaches the JWT from localStorage, parses JSON, and throws a
 * readable Error on failure. Also centralizes the "session expired ->
 * back to login" handling used by auth.js.
 */

const AUTH_TOKEN_KEY = "vps_auth_token";
const AUTH_USER_KEY = "vps_auth_user";

const Auth = {
  getToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  },
  getUser() {
    try {
      return JSON.parse(localStorage.getItem(AUTH_USER_KEY) || "null");
    } catch {
      return null;
    }
  },
  setSession(token, user) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
  },
  clearSession() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
  },
  isLoggedIn() {
    return Boolean(this.getToken() && this.getUser());
  },
  logout() {
    this.clearSession();
    window.location.href = "/login.html";
  },
  /** Redirect target for each role, per the required auth workflow. */
  dashboardUrlFor(role) {
    return "/dashboard.html"; // dashboard.html adapts its content per role
  },
  /** Call at the top of any protected page. Redirects to login if not
   * authenticated, or shows a friendly "not permitted" state if the
   * user's role isn't allowed on this page. The backend enforces the
   * real authorization on every API call — this is just UX. */
  guard(allowedRoles) {
    if (!this.isLoggedIn()) {
      window.location.href = "/login.html";
      return null;
    }
    const user = this.getUser();
    if (allowedRoles && !allowedRoles.includes(user.role)) {
      document.body.innerHTML = `
        <div class="auth-shell">
          <div class="auth-card" style="text-align:center;">
            <p style="font-weight:700;color:var(--danger);margin-bottom:10px;">Access restricted</p>
            <p style="color:var(--ink-soft);font-size:13.5px;margin-bottom:18px;">
              Your role (${escapeHtmlSafe(user.role)}) doesn't have access to this page.
            </p>
            <a class="btn btn-primary" href="/dashboard.html">Back to dashboard</a>
          </div>
        </div>`;
      return null;
    }
    return user;
  },
};

function escapeHtmlSafe(str) {
  const div = document.createElement("div");
  div.textContent = String(str);
  return div.innerHTML;
}

/**
 * apiFetch(path, options) -> parsed JSON body.
 * Automatically attaches Authorization: Bearer <token> unless
 * options.noAuth is set. Throws Error(message) on any non-2xx response.
 */
async function apiFetch(path, options = {}) {
  const headers = Object.assign({}, options.headers || {});
  const isFormData = options.body instanceof FormData;
  if (!isFormData && options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  if (!options.noAuth) {
    const token = Auth.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let res;
  try {
    res = await fetch(path, { ...options, headers });
  } catch (networkErr) {
    throw new Error("Could not reach the server. Check your connection and try again.");
  }

  if (res.status === 401) {
    Auth.clearSession();
    window.location.href = "/login.html";
    throw new Error("Session expired. Please log in again.");
  }

  const contentType = res.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await res.json().catch(() => ({})) : null;

  if (!res.ok) {
    const message =
      (data && (data.detail || data.message)) ||
      `Request failed (${res.status}).`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return data;
}

/** Simple toast notifications, shared across every page (mirrors the
 * existing voice-prescription page's toast styling). */
function showToast(message, type = "info") {
  let stack = document.querySelector(".toast-stack");
  if (!stack) {
    stack = document.createElement("div");
    stack.className = "toast-stack";
    document.body.appendChild(stack);
  }
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  stack.appendChild(el);
  setTimeout(() => el.remove(), 3800);
}
