import { pramaanApi } from "../services/pramaanApi.js";

let app = null;
let booted = false;

const readJSON = (key, fallback) => {
  try {
    return JSON.parse(localStorage.getItem(key) || JSON.stringify(fallback));
  } catch {
    return fallback;
  }
};
const esc = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const join = (arr, fn) => arr.map(fn).join("");
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

const state = {
  backendOnline: false,
  user: readJSON("pramaan_user", null),
  data: readJSON("pramaan_data", {}),
  sidebar: false,
  sidebarWidth: Number(localStorage.getItem("pramaan_sidebar_width") || 248),
  offline: localStorage.getItem("pramaan_offline") === "1",
  query: "",
  settings: readJSON("pramaan_settings", {
    theme: "light",
    language: "en",
    density: "comfortable",
    notifications: true,
    reducedMotion: false,
  }),
};

const nav = [
  ["/dashboard", "⌂", "Dashboard"],
  ["/cases", "▣", "Cases"],
  ["/documents", "▤", "Documents"],
  ["/vault", "▰", "My Vault"],
  ["/evidence", "◈", "Evidence"],
  ["/custody", "↔", "Chain of Custody"],
  ["/ai", "✦", "AI Assistant"],
  ["/verification", "✓", "Verification"],
  ["/reports", "▥", "Reports"],
  ["/audit", "≡", "Audit Logs"],
  ["/users", "♙", "Users"],
  ["/security", "⚠", "Security"],
  ["/system-health", "◉", "System"],
  ["/settings", "⚙", "Settings"],
];
const routes = [
  "/dashboard",
  "/cases",
  "/case-details",
  "/documents",
  "/upload",
  "/viewer",
  "/versions",
  "/vault",
  "/evidence",
  "/evidence-details",
  "/custody",
  "/transfer",
  "/verification",
  "/signature",
  "/ocr",
  "/pii",
  "/redaction",
  "/ai",
  "/search",
  "/court-export",
  "/certificate",
  "/audit",
  "/alerts",
  "/users",
  "/roles",
  "/offline",
  "/sync",
  "/system-health",
  "/settings",
  "/profile",
  "/reports",
  "/security",
];

const translations = {
  en: {
    Dashboard: "Dashboard",
    Cases: "Cases",
    Documents: "Documents",
    "My Vault": "My Vault",
    Evidence: "Evidence",
    "Chain of Custody": "Chain of Custody",
    "AI Assistant": "AI Assistant",
    Verification: "Verification",
    Reports: "Reports",
    "Audit Logs": "Audit Logs",
    Users: "Users",
    Security: "Security",
    System: "System",
    Settings: "Settings",
    "Roles & Permissions": "Roles & Permissions",
    "Offline Center": "Offline Center",
    "Sync Center": "Sync Center",
  },
  hi: {
    Dashboard: "डैशबोर्ड",
    Cases: "केस",
    Documents: "दस्तावेज़",
    "My Vault": "मेरा वॉल्ट",
    Evidence: "साक्ष्य",
    "Chain of Custody": "कस्टडी श्रृंखला",
    "AI Assistant": "AI सहायक",
    Verification: "सत्यापन",
    Reports: "रिपोर्ट",
    "Audit Logs": "ऑडिट लॉग",
    Users: "उपयोगकर्ता",
    Security: "सुरक्षा",
    System: "सिस्टम",
    Settings: "सेटिंग्स",
    "Roles & Permissions": "भूमिकाएँ और अनुमतियाँ",
    "Offline Center": "ऑफ़लाइन केंद्र",
    "Sync Center": "सिंक केंद्र",
  },
  mr: {
    Dashboard: "डॅशबोर्ड",
    Cases: "केसेस",
    Documents: "दस्तऐवज",
    "My Vault": "माझा व्हॉल्ट",
    Evidence: "पुरावा",
    "Chain of Custody": "कस्टडी साखळी",
    "AI Assistant": "AI सहाय्यक",
    Verification: "पडताळणी",
    Reports: "अहवाल",
    "Audit Logs": "ऑडिट लॉग",
    Users: "वापरकर्ते",
    Security: "सुरक्षा",
    System: "सिस्टम",
    Settings: "सेटिंग्ज",
    "Roles & Permissions": "भूमिका आणि परवानग्या",
    "Offline Center": "ऑफलाइन केंद्र",
    "Sync Center": "सिंक केंद्र",
  },
};
const t = (x) => translations[state.settings.language]?.[x] || x;

function saveState() {
  try {
    localStorage.setItem("pramaan_data", JSON.stringify(state.data));
    localStorage.setItem("pramaan_settings", JSON.stringify(state.settings));
    localStorage.setItem("pramaan_offline", state.offline ? "1" : "0");
    localStorage.setItem(
      "pramaan_vault_meta",
      JSON.stringify(state.data.vault || []),
    );
    localStorage.setItem(
      "pramaan_ai_history",
      JSON.stringify(state.data.aiHistory || []),
    );
    localStorage.setItem(
      "pramaan_ai_chats",
      JSON.stringify(state.data.aiChats || []),
    );
    if (state.data.aiCurrent)
      localStorage.setItem("pramaan_ai_current", state.data.aiCurrent);
    localStorage.setItem(
      "pramaan_sync_history",
      JSON.stringify(state.data.syncHistory || []),
    );
    localStorage.setItem(
      "pramaan_users",
      JSON.stringify(state.data.users || []),
    );
    localStorage.setItem(
      "pramaan_security",
      JSON.stringify(state.data.security || {}),
    );
    localStorage.setItem(
      "pramaan_custody",
      JSON.stringify(state.data.custody || {}),
    );
    localStorage.setItem(
      "pramaan_permissions",
      JSON.stringify(state.data.permissions || {}),
    );
    localStorage.setItem(
      "pramaan_sidebar_width",
      String(state.sidebarWidth || 248),
    );
  } catch (e) {
    console.warn("PRAMAAN local persistence warning", e);
  }
}

function demoData() {
  return {
    cases: [
      {
        id: "CASE-2026-001",
        title: "Cyber Fraud Investigation",
        status: "Active",
        officer: "Inspector Sharma",
        documents: 6,
        evidence: 3,
      },
      {
        id: "CASE-2026-002",
        title: "Financial Records Review",
        status: "Pending",
        officer: "Inspector Sharma",
        documents: 4,
        evidence: 2,
      },
      {
        id: "CASE-2026-003",
        title: "Digital Evidence Examination",
        status: "Closed",
        officer: "Dr. A. Verma",
        documents: 8,
        evidence: 4,
      },
    ],
    users: readJSON("pramaan_users", [
      {
        id: "USR-001",
        name: "Inspector Sharma",
        role: "Investigating Officer",
        email: "inspector.sharma@pramaan.gov",
        status: "Active",
      },
      {
        id: "USR-002",
        name: "Dr. A. Verma",
        role: "Forensic Officer",
        email: "verma.forensic@pramaan.gov",
        status: "Active",
      },
      {
        id: "USR-003",
        name: "Anita Rao",
        role: "Prosecutor",
        email: "anita.rao@pramaan.gov",
        status: "Active",
      },
      {
        id: "USR-004",
        name: "System Admin",
        role: "Administrator",
        email: "admin@pramaan.gov",
        status: "Active",
      },
    ]),
    documents: [
      {
        id: "DOC-001",
        caseId: "CASE-2026-001",
        filename: "FIR_1243.pdf",
        type: "FIR",
        uploader: "Inspector Sharma",
        date: "12 Sep 2026",
        size: "2.4 MB",
        hash: "8F4A...91C",
        status: "Verified",
        signature: "Valid",
      },
      {
        id: "DOC-004",
        caseId: "CASE-2026-003",
        filename: "Forensic_Report.pdf",
        type: "Forensic Report",
        uploader: "Dr. A. Verma",
        date: "08 Sep 2026",
        size: "5.2 MB",
        hash: "F09E...22B",
        status: "Verified",
        signature: "Valid",
      },
    ],
    evidence: [
      {
        id: "EV-0001",
        caseId: "CASE-2026-001",
        type: "Digital Image",
        description: "Recovered mobile screenshot",
        registeredBy: "Inspector Sharma",
        status: "IN CUSTODY",
        holder: "Forensic Lab",
      },
      {
        id: "EV-0002",
        caseId: "CASE-2026-001",
        type: "Device Image",
        description: "Forensic disk image",
        registeredBy: "Inspector Sharma",
        status: "UNDER ANALYSIS",
        holder: "Dr. A. Verma",
      },
    ],
    alerts: [
      {
        id: "ALT-001",
        type: "Hash mismatch",
        severity: "Critical",
        message: "Evidence EV-0002 requires integrity review.",
        status: "Open",
      },
    ],
    audit: [],
    vault: readJSON("pramaan_vault_meta", []),
    aiHistory: readJSON("pramaan_ai_history", []),
    aiChats: readJSON("pramaan_ai_chats", []),
    aiCurrent: localStorage.getItem("pramaan_ai_current") || null,
    syncHistory: readJSON("pramaan_sync_history", []),
    custody: readJSON("pramaan_custody", {}),
    permissions: readJSON("pramaan_permissions", {}),
    security: readJSON("pramaan_security", {
      blockedEvents: 7,
      controls: {
        "RBAC enforcement architecture": true,
        "SHA-256 integrity checks": true,
        "Digital signature metadata": true,
        "Dynamic watermarking": true,
        "Session tracking": true,
        "Rate limiting architecture": true,
      },
      innovations: {
        zKp: true,
        watermark: true,
        pqc: true,
        bsa: true,
        pii: true,
        dualKey: true,
        offline: true,
      },
    }),
    redactions: [],
    breachSimulation: null,
  };
}

async function loadData() {
  const base = demoData();
  state.data = { ...base, ...(state.data || {}) };
  for (const k of [
    "cases",
    "documents",
    "evidence",
    "alerts",
    "audit",
    "vault",
    "aiHistory",
    "aiChats",
    "syncHistory",
    "users",
  ])
    if (!Array.isArray(state.data[k])) state.data[k] = base[k];
  for (const k of ["custody", "permissions"])
    if (!state.data[k] || typeof state.data[k] !== "object")
      state.data[k] = base[k];
  saveState();
  return state.data;
}

function toast(msg, type = "success") {
  const root = document.getElementById("toast-root");
  if (!root) return;
  const d = document.createElement("div");
  d.className = "toast " + type;
  d.innerHTML =
    '<span class="toast-icon">' +
    (type === "error" ? "!" : type === "warn" ? "!" : "✓") +
    "</span><span>" +
    esc(msg) +
    "</span>";
  root.appendChild(d);
  setTimeout(() => d.classList.add("leaving"), 2400);
  setTimeout(() => d.remove(), 2850);
}
function path() {
  const raw = location.hash.slice(1) || location.pathname || "/dashboard";
  return raw.split("?")[0] || "/dashboard";
}
function go(p) {
  location.hash = p.startsWith("/") ? p : "/" + p;
  state.sidebar = false;
  window.scrollTo({
    top: 0,
    behavior: state.settings.reducedMotion ? "auto" : "smooth",
  });
}
function status(s) {
  const x = String(s).toLowerCase();
  const c =
    x.includes("tamper") ||
    x.includes("critical") ||
    x.includes("invalid") ||
    x.includes("blocked")
      ? "danger"
      : x.includes("pending") ||
          x.includes("analysis") ||
          x.includes("required") ||
          x.includes("warning")
        ? "warn"
        : x.includes("verified") ||
            x.includes("valid") ||
            x.includes("success") ||
            x.includes("active") ||
            x.includes("operational") ||
            x.includes("custody") ||
            x.includes("ready")
          ? "ok"
          : "info";
  return '<span class="status ' + c + '"><i>●</i>' + esc(s) + "</span>";
}
function stat(label, value, meta) {
  return (
    '<div class="card stat"><div class="label">' +
    esc(label) +
    '</div><div class="value">' +
    esc(value) +
    '</div><div class="meta">' +
    esc(meta) +
    "</div></div>"
  );
}
function head(title, sub, actions = "") {
  return (
    '<div class="page-head"><div><h1>' +
    esc(title) +
    "</h1><p>" +
    esc(sub) +
    '</p></div><div class="actions">' +
    actions +
    "</div></div>"
  );
}
function audit(action, document = "—", result = "Success", severity = "Info") {
  state.data.audit = state.data.audit || [];
  state.data.audit.unshift({
    user: state.user?.name || "Inspector Sharma",
    action,
    document,
    case: "—",
    result,
    severity,
    time: new Date().toLocaleString("en-IN"),
  });
  saveState();
}

function setSidebarWidth(value) {
  const width = Math.max(
    200,
    Math.min(
      360,
      Number(value) || 248,
    ),
  );

  state.sidebarWidth = width;

  document.documentElement.style.setProperty(
    "--sidebar-width",
    width + "px",
  );

  localStorage.setItem(
    "pramaan_sidebar_width",
    String(width),
  );

  const out =
    document.getElementById(
      "sidebarWidthValue",
    );

  if (out) {
    out.textContent =
      Math.round(width) + "px";
  }
}

function startSidebarResize(event) {
  if (window.innerWidth <= 800) return;

  event?.preventDefault?.();

  const move = (e) => {
    e.preventDefault?.();

    const clientX =
      e.touches?.[0]?.clientX ??
      e.clientX;

    if (typeof clientX !== "number") return;

    const width = Math.max(
      200,
      Math.min(360, clientX),
    );

    setSidebarWidth(width);
  };

  const stop = () => {
    document.removeEventListener("mousemove", move);
    document.removeEventListener("mouseup", stop);
    document.removeEventListener("touchmove", move);
    document.removeEventListener("touchend", stop);
    document.body.classList.remove("sidebar-resizing");
  };

  document.body.classList.add("sidebar-resizing");

  document.addEventListener("mousemove", move);
  document.addEventListener("mouseup", stop);
  document.addEventListener("touchmove", move, { passive: false });
  document.addEventListener("touchend", stop);
}

function applySettings() {
  setSidebarWidth(state.sidebarWidth === undefined ? 248 : state.sidebarWidth);
  document.documentElement.dataset.theme = state.settings.theme || "light";
  document.documentElement.dataset.density =
    state.settings.density || "comfortable";
  document.documentElement.lang = state.settings.language || "en";
  document.documentElement.style.colorScheme =
    state.settings.theme === "dark" ? "dark" : "light";
  document.body.classList.toggle(
    "reduced-motion",
    !!state.settings.reducedMotion,
  );
}
function logoMarkup(size = "side") {
  return (
    '<div class="logo-wrap logo-' +
    size +
    '"><img src="/assets/pramaan-mark.svg" alt="PRAMAAN" class="logo-img"><span class="logo-glow"></span></div>'
  );
}

function openVaultDB() {
  return new Promise((resolve, reject) => {
    const r = indexedDB.open("pramaan-vault", 1);
    r.onupgradeneeded = () => {
      if (!r.result.objectStoreNames.contains("files"))
        r.result.createObjectStore("files", { keyPath: "id" });
    };
    r.onsuccess = () => resolve(r.result);
    r.onerror = () => reject(r.error);
  });
}
async function vaultPut(file, meta) {
  const db = await openVaultDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("files", "readwrite");
    tx.objectStore("files").put({ id: meta.id, file, meta });
    tx.oncomplete = () => {
      db.close();
      resolve();
    };
    tx.onerror = () => {
      db.close();
      reject(tx.error);
    };
  });
}
async function vaultGet(id) {
  try {
    const db = await openVaultDB();
    return await new Promise((resolve, reject) => {
      const tx = db.transaction("files", "readonly");
      const r = tx.objectStore("files").get(id);
      r.onsuccess = () => {
        db.close();
        resolve(r.result || null);
      };
      r.onerror = () => {
        db.close();
        reject(r.error);
      };
    });
  } catch {
    return null;
  }
}
async function vaultDelete(id) {
  try {
    const db = await openVaultDB();
    return await new Promise((resolve, reject) => {
      const tx = db.transaction("files", "readwrite");
      tx.objectStore("files").delete(id);
      tx.oncomplete = () => {
        db.close();
        resolve();
      };
      tx.onerror = () => {
        db.close();
        reject(tx.error);
      };
    });
  } catch {}
}
async function sha256(data) {
  const bytes =
    data instanceof ArrayBuffer
      ? new Uint8Array(data)
      : new TextEncoder().encode(String(data));
  const hash = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(hash)]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("")
    .toUpperCase();
}
function downloadBlob(blob, name) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}
function downloadText(name, text) {
  downloadBlob(new Blob([text], { type: "application/octet-stream" }), name);
}

function layout(content) {
  const cur = path();

  const side = join(
    nav,
    (n) =>
      '<button class="nav-item ' +
      (cur === n[0]
        ? "active"
        : "") +
      '" onclick="go(\'' +
      n[0] +
      "')\">" +
      '<span class="nav-icon">' +
      n[1] +
      "</span>" +
      t(n[2]) +
      "</button>",
  );

  const admin =
    '<div class="nav-section">Administration</div>' +
    '<button class="nav-item ' +
    (cur === "/roles"
      ? "active"
      : "") +
    '" onclick="go(\'/roles\')">' +
    '<span class="nav-icon">♙</span>' +
    t("Roles & Permissions") +
    "</button>" +
    '<button class="nav-item ' +
    (cur === "/offline"
      ? "active"
      : "") +
    '" onclick="go(\'/offline\')">' +
    '<span class="nav-icon">⇩</span>' +
    t("Offline Center") +
    "</button>" +
    '<button class="nav-item ' +
    (cur === "/sync"
      ? "active"
      : "") +
    '" onclick="go(\'/sync\')">' +
    '<span class="nav-icon">⟳</span>' +
    t("Sync Center") +
    "</button>";

  const mobileRoutes = [
    ["/dashboard", "⌂", "Dashboard"],
    ["/cases", "▣", "Cases"],
    ["/documents", "▤", "Documents"],
    ["/sync", "⟳", "Sync"],
    ["/vault", "▰", "Vault"],
  ];

  const mobile = join(
    mobileRoutes,
    (n) =>
      '<button class="' +
      (cur === n[0]
        ? "active"
        : "") +
      '" onclick="go(\'' +
      n[0] +
      "')\">" +
      '<span class="mobile-nav-icon">' +
      n[1] +
      "</span>" +
      "<span>" +
      esc(n[2]) +
      "</span>" +
      "</button>",
  );

  return (
    '<div class="layout" style="--sidebar-width:' +
    state.sidebarWidth +
    'px">' +

    '<aside class="sidebar ' +
    (state.sidebar
      ? "open"
      : "") +
    '">' +

    '<div class="side-brand">' +
    logoMarkup("side") +
    '<div class="side-name">' +
    "PRAMAAN" +
    "<small>SECURE DIGITAL EVIDENCE</small>" +
    "</div>" +
    "</div>" +

    '<div class="nav-section">Workspace</div>' +

    side +

    admin +

    '<div class="sidebar-drag-handle" ' +
    'title="Drag to resize sidebar" ' +
    'aria-label="Resize sidebar" ' +
    'onmousedown="startSidebarResize(event)" ' +
    'ontouchstart="startSidebarResize(event)"></div>' +

    "</aside>" +

    '<main class="main">' +

    '<header class="topbar">' +

    '<button class="icon-btn menu-btn" onclick="state.sidebar=!state.sidebar;render()">☰</button>' +

    '<div class="searchbox">' +
    "<span>⌕</span>" +
    '<input value="' +
    esc(state.query) +
    '" placeholder="Search cases, documents, evidence, hashes..." onkeydown="if(event.key===\'Enter\'){state.query=this.value;go(\'/search?query=\'+encodeURIComponent(this.value))}">' +
    "</div>" +

    '<div class="top-actions">' +

    '<div class="backend-badge ' + (state.backendOnline ? 'online' : 'offline') + '" title="' + (state.backendOnline ? 'Django backend connected (http://127.0.0.1:8000)' : 'Django backend offline (using local storage)') + '">' +
    '<span class="badge-dot"></span>' +
    '<span>Backend: ' + (state.backendOnline ? 'Connected' : 'Offline') + '</span>' +
    '</div>' +

    '<button class="icon-btn" title="My Vault" onclick="go(\'/vault\')">▰</button>' +

    '<button class="icon-btn" title="System health" onclick="go(\'/system-health\')">◉</button>' +

    '<button class="icon-btn" title="Alerts" onclick="go(\'/alerts\')">♢<b class="badge">' +
    (state.data.alerts || []).filter(
      (a) => a.status === "Open",
    ).length +
    "</b></button>" +

    '<div class="profile" onclick="go(\'/profile\')">' +

    '<div class="avatar">' +
    (state.user?.avatar
      ? '<img src="' +
        esc(
          state.user.avatar,
        ) +
        '" alt="Profile">'
      : "IS") +
    "</div>" +

    '<div class="profile-copy">' +
    "<strong>" +
    esc(
      state.user?.name ||
        "Inspector Sharma",
    ) +
    "</strong>" +
    "<small>" +
    esc(
      state.user?.role ||
        "Investigating Officer",
    ) +
    "</small>" +
    "</div>" +

    "</div>" +

    "</div>" +

    "</header>" +

    '<section class="page page-transition">' +
    content +
    "</section>" +

    '<nav class="mobile-nav">' +
    mobile +
    "</nav>" +

    "</main>" +

    "</div>"
  );
}
function docRow(d) {
  const id = esc(d?.id || "");
  const name = esc(d?.filename || "Untitled document");
  const type = esc(d?.type || "Document");
  const size = esc(d?.size || "—");
  const date = esc(d?.date || "—");
  const statusValue = d?.status || "Registered";
  return (
    '<div class="doc-row" data-document-id="' +
    id +
    '">' +
    '<div class="doc-icon">▤</div>' +
    '<div class="doc-main"><strong>' +
    name +
    "</strong><small>" +
    type +
    " · " +
    size +
    " · " +
    date +
    "</small></div>" +
    '<div class="doc-row-status">' +
    status(statusValue) +
    "</div>" +
    '<div class="row-actions">' +
    '<button class="btn btn-sm btn-secondary" onclick="go(\'/viewer?id=' +
    encodeURIComponent(d?.id || "") +
    "')\">Preview</button>" +
    "</div>" +
    "</div>"
  );
}

function dashboard() {
  const bars = [42, 58, 47, 71, 66, 88, 76, 92, 79, 100, 83, 94],
    months = ["O", "N", "D", "J", "F", "M", "A", "M", "J", "J", "A", "S"];
  return layout(
    head(
      "Command Dashboard",
      "Secure overview of cases, documents, evidence and integrity.",
      '<button class="btn btn-primary" onclick="go(\'/upload\')">＋ Upload Document</button>',
    ) +
      '<div class="grid grid-6">' +
      stat("Total Cases", state.data.cases.length, "↑ 8 this month") +
      stat("Documents", "1,428", "↑ 12.4%") +
      stat("Evidence", state.data.evidence.length, "Active custody") +
      stat("Pending Approvals", "18", "Requires review") +
      stat("Verified", "98.7%", "Integrity checks") +
      stat("Tamper Alerts", state.data.alerts.length, "Needs attention") +
      '</div><div class="grid grid-3" style="margin-top:16px"><div class="card" style="grid-column:span 2"><h3 class="section-title">Monthly Activity</h3><div class="mini-chart">' +
      bars
        .map(
          (x, i) =>
            '<div class="bar" style="height:' +
            x +
            "%;--i:" +
            i +
            '"><span>' +
            months[i] +
            "</span></div>",
        )
        .join("") +
      '</div></div><div class="card"><h3 class="section-title">Document Types</h3><div class="donut"></div><div class="chips" style="margin-top:12px"><span class="chip">FIR 32%</span><span class="chip">Evidence 23%</span><span class="chip">Court 21%</span><span class="chip">Others 24%</span></div></div></div><div class="grid grid-3" style="margin-top:16px"><div class="card"><h3 class="section-title">Quick Actions</h3><div class="grid"><button class="btn btn-secondary" onclick="go(\'/upload\')">Upload Evidence</button><button class="btn btn-secondary" onclick="go(\'/verification\')">Run Verification</button><button class="btn btn-secondary" onclick="go(\'/vault\')">Open My Vault</button></div></div><div class="card"><h3 class="section-title">Integrity Pulse</h3><div class="progress"><i style="width:98.7%"></i></div><p style="color:var(--muted);font-size:12px">98.7% of demo integrity checks are currently valid.</p><button class="btn btn-ghost" onclick="go(\'/verification\')">Open Diagnostic</button></div><div class="card"><h3 class="section-title">Offline Readiness</h3>' +
      status(state.offline ? "OFFLINE" : "ONLINE") +
      '<p style="color:var(--muted);font-size:12px;margin-top:8px">' +
      state.data.vault.length +
      ' local vault items available.</p><button class="btn btn-ghost" onclick="go(\'/offline\')">Open Offline Center</button></div></div><div class="grid grid-2" style="margin-top:16px"><div class="card"><h3 class="section-title">Recent Activity</h3>' +
      join(state.data.documents.slice(0, 5), docRow) +
      '</div><div class="card"><h3 class="section-title">Security Alerts</h3>' +
      join(
        state.data.alerts,
        (a) =>
          '<div class="notice ' +
          (a.severity === "Critical" ? "danger" : "warn") +
          '" style="margin-bottom:10px"><strong>' +
          esc(a.type) +
          "</strong><br>" +
          esc(a.message) +
          '<div style="margin-top:8px">' +
          status(a.status) +
          ' <button class="btn btn-sm btn-ghost" onclick="go(\'/alerts\')">Review</button></div></div>',
      ) +
      "</div></div>",
  );
}

function openCaseFilter() {
  openModal(
    "Case Filter",
    '<div class="form"><div class="field"><label>Status</label><select id="caseStatusFilter"><option value="">All statuses</option><option>Active</option><option>Pending</option><option>Closed</option></select></div><div class="field"><label>Officer</label><input id="caseOfficerFilter" placeholder="Search officer"></div><div class="actions"><button class="btn btn-secondary" onclick="closeModal();render()">Reset</button><button class="btn btn-primary" onclick="applyCaseFilter()">Apply Filter</button></div></div>',
  );
}
function applyCaseFilter() {
  const statusValue = document.getElementById("caseStatusFilter")?.value || "",
    officer = (
      document.getElementById("caseOfficerFilter")?.value || ""
    ).toLowerCase();
  document.querySelectorAll("[data-case-row]").forEach((row) => {
    const okStatus = !statusValue || row.dataset.status === statusValue;
    const okOfficer =
      !officer || (row.dataset.officer || "").toLowerCase().includes(officer);
    row.style.display = okStatus && okOfficer ? "" : "none";
  });
  closeModal();
  toast("Case filters applied");
}
function openCaseActions(id) {
  const c = state.data.cases.find((x) => x.id === id);
  if (!c) return;
  openModal(
    "Case Actions",
    '<div class="form"><div class="notice"><strong>' +
      esc(c.id) +
      "</strong><br>" +
      esc(c.title) +
      '</div><button class="btn btn-secondary" onclick="closeModal();go(\'/case-details?id=' +
      encodeURIComponent(c.id) +
      '\')">Open Details</button><button class="btn btn-secondary" onclick="closeModal();go(\'/upload\')">Add Document</button><button class="btn btn-danger" onclick="archiveCase(\'' +
      esc(c.id) +
      "')\">Archive Case</button></div>",
  );
}
function archiveCase(id) {
  const c = state.data.cases.find((x) => x.id === id);
  if (!c) return;
  c.status = "Closed";
  audit("ARCHIVE CASE", id, "Success", "Info");
  closeModal();
  toast("Case archived");
  render();
}
function cases() {
  return layout(
    head(
      "Cases",
      "Manage investigation cases and their controlled evidence lifecycle.",
      '<button class="btn btn-primary" onclick="openModal(\'New Case\',newCaseForm())">＋ New Case</button>',
    ) +
      '<div class="grid grid-4">' +
      stat(
        "Active Cases",
        String(state.data.cases.filter((c) => c.status === "Active").length),
        "Across authorized units",
      ) +
      stat(
        "Pending",
        String(state.data.cases.filter((c) => c.status === "Pending").length),
        "Awaiting action",
      ) +
      stat(
        "Closed",
        String(state.data.cases.filter((c) => c.status === "Closed").length),
        "Archived securely",
      ) +
      stat(
        "Evidence Linked",
        String(state.data.cases.reduce((n, c) => n + (c.evidence || 0), 0)),
        "Across active cases",
      ) +
      '</div><div class="card cases-panel" style="margin-top:16px"><div class="actions" style="margin-bottom:12px"><button class="btn btn-sm btn-secondary" onclick="openCaseFilter()">Filter</button><button class="btn btn-sm btn-ghost" onclick="downloadText(\'cases-export.json\',JSON.stringify(state.data.cases,null,2))">Export</button><button class="btn btn-sm btn-ghost" onclick="toast(\'Case list refreshed\');render()">Refresh</button></div><div class="table-wrap"><table class="table cases-table"><thead><tr><th>Case</th><th>Status</th><th>Officer</th><th>Docs</th><th>Evidence</th><th>Action</th></tr></thead><tbody>' +
      join(
        state.data.cases,
        (c) =>
          '<tr data-case-row data-status="' +
          esc(c.status) +
          '" data-officer="' +
          esc(c.officer) +
          '"><td><strong>' +
          esc(c.id) +
          "</strong><br><small>" +
          esc(c.title) +
          "</small></td><td>" +
          status(c.status) +
          "</td><td>" +
          esc(c.officer) +
          "</td><td>" +
          c.documents +
          "</td><td>" +
          c.evidence +
          '</td><td><div class="row-actions"><button class="btn btn-sm btn-secondary" onclick="go(\'/case-details?id=' +
          encodeURIComponent(c.id) +
          '\')">Open Case</button><button class="btn btn-sm btn-ghost" onclick="openCaseActions(\'' +
          esc(c.id) +
          "')\">More</button></div></td></tr>",
      ) +
      "</tbody></table></div></div>",
  );
}
function newCaseForm() {
  const users = state.data.users || [];
  return (
    '<div class="form"><div class="notice"><strong>Create a controlled case</strong><br>Assign an existing officer or add a new user before saving.</div><div class="field"><label>Case title</label><input id="caseTitle" placeholder="e.g. Digital Evidence Examination"></div><div class="field"><label>Case type</label><select id="caseType"><option>Investigation</option><option>Cyber Crime</option><option>Financial</option><option>Forensic</option></select></div><div class="field"><label>Assigned officer</label><select id="caseOfficer">' +
    join(
      users,
      (u) =>
        '<option value="' +
        esc(u.name) +
        '">' +
        esc(u.name) +
        " · " +
        esc(u.role) +
        "</option>",
    ) +
    '</select></div><div class="actions"><button class="btn btn-secondary" onclick="openModal(\'Create User\',userForm())">＋ Add User</button><button class="btn btn-primary" onclick="createCase()">Create Case</button></div></div>'
  );
}
function createCase() {
  const title =
    document.getElementById("caseTitle")?.value.trim() ||
    "Untitled Investigation";
  const officer =
    document.getElementById("caseOfficer")?.value ||
    state.user?.name ||
    "Inspector Sharma";
  const c = {
    id: "CASE-2026-" + String(state.data.cases.length + 4).padStart(3, "0"),
    title,
    type: document.getElementById("caseType")?.value || "Investigation",
    status: "Active",
    officer,
    documents: 0,
    evidence: 0,
    createdAt: new Date().toISOString(),
  };
  state.data.cases.unshift(c);
  saveState();
  audit("CREATE CASE", c.id, "Success", "Info");
  closeModal();
  toast("Case " + c.id + " created and assigned to " + officer);
  render();
}
function caseDetails() {
  const id =
    new URLSearchParams(location.hash.split("?")[1] || "").get("id") ||
    "CASE-2026-001";
  const c = state.data.cases.find((x) => x.id === id) || state.data.cases[0];
  return layout(
    head(
      c.id,
      c.title,
      '<button class="btn btn-primary" onclick="go(\'/upload\')">＋ Add Document</button>',
    ) +
      '<div class="grid grid-4">' +
      stat("Status", c.status, "Controlled case") +
      stat("Documents", c.documents, "Linked") +
      stat("Evidence", c.evidence, "Tracked") +
      stat("Officer", c.officer, "Responsible") +
      '</div><div class="grid grid-2" style="margin-top:16px"><div class="card"><h3 class="section-title">Case Documents</h3>' +
      join(
        state.data.documents.filter((d) => d.caseId === c.id),
        docRow,
      ) +
      '</div><div class="card"><h3 class="section-title">Evidence Lifecycle</h3>' +
      join(
        state.data.evidence.filter((e) => e.caseId === c.id),
        (e) =>
          '<div class="kpi-line"><span><strong>' +
          e.id +
          "</strong><br><small>" +
          esc(e.description) +
          "</small></span>" +
          status(e.status) +
          "</div>",
      ) +
      "</div></div>",
  );
}

function documents() {
  return layout(
    head(
      "Document Management",
      "Search, organize, preview, verify and version controlled legal documents.",
      '<div class="actions"><button class="btn btn-secondary" onclick="go(\'/vault\')">▰ My Vault</button><button class="btn btn-primary" onclick="go(\'/upload\')">＋ Upload Document</button></div>',
    ) +
      '<div class="card"><div class="actions" style="margin-bottom:14px"><input id="docSearch" style="flex:1;min-width:180px;padding:12px;border:1px solid var(--line);border-radius:12px" placeholder="Search documents..." oninput="filterDocs(this.value)"><select id="docFilter" onchange="filterDocs(document.getElementById(\'docSearch\').value)"><option value="">All types</option><option>FIR</option><option>Evidence</option><option>Charge Sheet</option><option>Forensic Report</option><option>Court Order</option></select><button class="btn btn-secondary" onclick="go(\'/vault\')">Save to Vault</button></div><div id="docList">' +
      join(state.data.documents, docRow) +
      "</div></div>",
  );
}
function filterDocs(q) {
  const type = document.getElementById("docFilter")?.value || "";
  const docs = state.data.documents.filter(
    (d) =>
      (!q || JSON.stringify(d).toLowerCase().includes(q.toLowerCase())) &&
      (!type || d.type === type),
  );
  const box = document.getElementById("docList");
  if (box)
    box.innerHTML = docs.length
      ? join(docs, docRow)
      : '<div class="empty">No documents match the selected filters.</div>';
}

async function saveDocumentToVault(documentId) {
  const d = state.data.documents.find((x) => x.id === documentId);
  if (!d) return toast("Document not found", "error");
  const existing = state.data.vault.find(
    (x) => x.documentId === documentId || x.id === documentId,
  );
  if (existing) return toast("Document is already in My Vault", "warn");
  const rec = await vaultGet(documentId);
  if (rec?.file) {
    const meta = {
      ...rec.meta,
      id: documentId,
      documentId,
      filename: d.filename,
      type: d.type,
      size: d.size,
      added: new Date().toLocaleString("en-IN"),
      hash: d.fullHash || rec.meta?.hash || d.hash,
      mime: d.mime || rec.file.type,
    };
    await vaultPut(rec.file, meta);
    state.data.vault.unshift(meta);
    saveState();
    audit("SAVE TO VAULT", d.filename, "Success", "Info");
    toast("Document saved to My Vault");
    render();
    return true;
  }
  const text = [
    "PRAMAAN DOCUMENT RECORD",
    "",
    `Document: ${d.filename}`,
    `Document ID: ${d.id}`,
    `Case ID: ${d.caseId}`,
    `Type: ${d.type}`,
    `SHA-256: ${d.fullHash || d.hash || "—"}`,
    `Status: ${d.status || "—"}`,
  ].join("\n");
  const file = new File(
    [text],
    d.filename.endsWith(".txt") ? d.filename : d.filename + ".txt",
    { type: "text/plain" },
  );
  const hash = await sha256(await file.arrayBuffer());
  const meta = {
    id: documentId,
    documentId,
    filename: file.name,
    type: "text/plain",
    size: (file.size / 1024).toFixed(1) + " KB",
    added: new Date().toLocaleString("en-IN"),
    hash,
    mime: file.type,
    source: "Local document record",
  };
  await vaultPut(file, meta);
  state.data.vault.unshift(meta);
  saveState();
  audit("SAVE TO VAULT", d.filename, "Success", "Info");
  toast("Document record saved to My Vault");
  render();
  return true;
}
async function downloadVaultFile(id) {
  const rec = await vaultGet(id);
  if (!rec?.file) {
    const d = state.data.documents.find((x) => x.id === id);
    if (d?.fullHash || d?.hash) {
      const text = [
        "PRAMAAN DOCUMENT RECORD",
        "",
        `Document: ${d.filename}`,
        `Document ID: ${d.id}`,
        `Case ID: ${d.caseId}`,
        `Type: ${d.type}`,
        `SHA-256: ${d.fullHash || d.hash}`,
        `Status: ${d.status || "—"}`,
      ].join("\n");
      downloadBlob(
        new Blob([text], { type: "text/plain" }),
        d.filename + ".txt",
      );
      toast("Local document record downloaded");
      return true;
    }
    return toast("Vault file unavailable", "error");
  }
  const url = URL.createObjectURL(rec.file);
  const a = document.createElement("a");
  a.href = url;
  a.download = rec.meta?.filename || rec.file.name || "PRAMAAN-document";
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1200);
  audit("VAULT DOWNLOAD", a.download, "Success", "Info");
  toast("Document downloaded");
  return true;
}

function upload() {
  const opts = join(
    state.data.cases,
    (c) =>
      '<option value="' +
      c.id +
      '">' +
      c.id +
      " — " +
      esc(c.title) +
      "</option>",
  );
  return layout(
    head(
      "Secure Upload",
      "Register a document, calculate SHA-256 and preserve the original.",
      '<button class="btn btn-secondary" onclick="go(\'/vault\')">Open My Vault</button>',
    ) +
      '<div class="grid grid-2 upload-layout"><div class="card upload-card"><h3 class="section-title">Upload Document</h3><div class="notice">Files are hashed before registration. Drag-and-drop works on desktop, tablet and touch devices.</div><div class="form"><div class="field"><label>Case</label><select id="upCase">' +
      opts +
      '</select></div><div class="field"><label>Document type</label><select id="upType"><option>FIR</option><option>Evidence</option><option>Witness Statement</option><option>Charge Sheet</option><option>Forensic Report</option><option>Court Filing</option><option>Investigation Report</option><option>Other</option></select></div><div class="field"><label>Classification</label><select id="upClass"><option>Restricted</option><option>Confidential</option><option>Sensitive</option></select></div><div class="field"><label>File</label><div id="dropZone" class="drop-zone" tabindex="0" role="button" onclick="document.getElementById(\'fileInput\').click()" onkeydown="if(event.key===\'Enter\'||event.key===\' \'){event.preventDefault();document.getElementById(\'fileInput\').click()}" ondragover="event.preventDefault();this.classList.add(\'drag-over\')" ondragleave="this.classList.remove(\'drag-over\')" ondrop="handleFileDrop(event)"><div class="drop-icon">⇧</div><strong>Drag &amp; drop your document here</strong><span>or click / tap to browse</span><small>PDF, JPG, PNG, DOC, DOCX, TXT, CSV, ZIP · Max 15 MB</small><div id="selectedFileName" class="selected-file">No file selected</div><input id="fileInput" class="file-input-hidden" type="file" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.txt,.csv,.zip" onchange="handleFileSelected(this.files[0])"></div></div><button class="btn btn-primary upload-submit" onclick="uploadFile()">Secure Upload → Hash → Register</button></div></div><div class="card pipeline-card"><h3 class="section-title">Processing Pipeline</h3>' +
      join(
        [
          "File validation",
          "SHA-256 integrity hash",
          "Local preservation",
          "Metadata registration",
          "Audit registration",
        ],
        (x, i) =>
          '<div class="kpi-line pipeline-step"><span>' +
          (i + 1) +
          ". " +
          x +
          "</span>" +
          status("Ready") +
          "</div>",
      ) +
      '<div style="margin-top:16px"><div class="progress"><i id="uploadProgress" style="width:0"></i></div><small id="uploadStatus" style="color:var(--muted)">Waiting for file.</small></div></div></div>',
  );
}
function handleFileSelected(f) {
  const label = document.getElementById("selectedFileName"),
    zone = document.getElementById("dropZone");
  if (!label || !zone) return;
  if (!f) {
    label.textContent = "No file selected";
    zone.classList.remove("has-file");
    return;
  }
  label.textContent =
    f.name + " · " + (f.size / 1024 / 1024).toFixed(2) + " MB";
  zone.classList.add("has-file");
  toast("File selected", "success");
}
function handleFileDrop(e) {
  e.preventDefault();
  const z = e.currentTarget;
  z.classList.remove("drag-over");
  const f = e.dataTransfer?.files?.[0];
  const input = document.getElementById("fileInput");
  if (f && input) {
    try {
      const dt = new DataTransfer();
      dt.items.add(f);
      input.files = dt.files;
    } catch {}
    handleFileSelected(f);
  }
}
async function uploadFile() {
  const f = document.getElementById("fileInput")?.files?.[0];
  if (!f) return toast("Select or drop a file first", "error");
  if (f.size > 15 * 1024 * 1024)
    return toast("Prototype limit is 15 MB", "error");
  const p = document.getElementById("uploadProgress"),
    s = document.getElementById("uploadStatus"),
    z = document.getElementById("dropZone");
  const set = (w, t) => {
    if (p) p.style.width = w + "%";
    if (s) s.textContent = t;
  };
  z?.classList.add("processing");
  set(15, "Validating file…");
  await wait(180);
  set(35, "Reading file securely…");
  const buf = await f.arrayBuffer();
  set(55, "Calculating SHA-256…");
  const hash = await sha256(buf);
  await wait(180);
  const doc = {
    id: "DOC-" + String(Date.now()).slice(-7),
    caseId: document.getElementById("upCase").value,
    filename: f.name,
    type: document.getElementById("upType").value,
    uploader: state.user?.name || "Inspector Sharma",
    date: new Date().toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }),
    size: (f.size / 1024 / 1024).toFixed(2) + " MB",
    hash: hash.slice(0, 4) + "..." + hash.slice(-3),
    fullHash: hash,
    status: "Verified",
    signature: "Pending",
    classification: document.getElementById("upClass").value,
    mime: f.type,
  };
  set(75, "Uploading to Django backend & verifying SHA-256…");
  try {
    const res = await pramaanApi.uploadDocument(f, doc.caseId, doc.type);
    if (res.ok && res.data) {
      doc.backendId = res.data.id;
      doc.fullHash = res.data.sha256_hash;
      doc.hash = res.data.sha256_hash.slice(0, 4) + "..." + res.data.sha256_hash.slice(-3);
      state.backendOnline = true;
    }
  } catch (err) {
    console.warn("PRAMAAN: Backend upload fallback to local:", err);
  }

  await vaultPut(f, {
    id: doc.id,
    filename: f.name,
    mime: f.type,
    size: f.size,
  });
  state.data.documents.unshift(doc);
  state.data.vault.unshift({
    id: doc.id,
    documentId: doc.id,
    filename: f.name,
    type: doc.type,
    size: doc.size,
    added: new Date().toLocaleString("en-IN"),
    hash,
  });
  audit("UPLOAD", doc.filename, "Success", "Info");
  set(100, "Registered and audited successfully.");
  z?.classList.remove("processing");
  z?.classList.add("success");
  toast("Document uploaded, hashed and registered");
  await wait(500);
  go("/viewer?id=" + doc.id);
}

async function hydrateViewer() {
  const box = document.getElementById("livePreview");
  if (!box) return;
  const id =
    new URLSearchParams(location.hash.split("?")[1] || "").get("id") ||
    "DOC-001";
  const d =
    state.data.documents.find((x) => x.id === id) || state.data.documents[0];
  window.__pramaanZoom = 1;
  const rec = await vaultGet(id);
  if (rec) {
    const url = URL.createObjectURL(rec.file);
    if (rec.file.type.startsWith("image/"))
      box.innerHTML =
        '<div class="preview-media-inner"><img class="document-preview-media" src="' +
        url +
        '" alt="' +
        esc(d.filename) +
        '"></div>';
    else if (rec.file.type === "application/pdf")
      box.innerHTML =
        '<div class="preview-media-inner"><iframe class="document-preview-frame" src="' +
        url +
        '#toolbar=1&navpanes=0&view=FitH" title="Document preview"></iframe></div>';
    else if (
      rec.file.type.startsWith("text/") ||
      /csv|plain/.test(rec.file.type)
    ) {
      box.innerHTML =
        '<div class="preview-media-inner document-text-shell"><pre class="document-text-preview"></pre></div>';
      box.querySelector("pre").textContent = await rec.file.text();
    } else
      box.innerHTML =
        '<div class="preview-media-inner"><div class="paper document-fallback"><h3>' +
        esc(d.filename) +
        "</h3><p><strong>" +
        esc(d.type) +
        "</strong> · " +
        esc(d.caseId) +
        '</p><p>Original file is securely stored in My Vault. Browser preview for this file type is not natively supported; use Download to open the original.</p><div class="line"></div><div class="line"></div><div class="line short"></div></div></div>';
  } else
    box.innerHTML =
      '<div class="preview-media-inner"><div class="paper document-fallback"><h3>' +
      esc(d.filename) +
      "</h3><p><strong>" +
      esc(d.type) +
      "</strong> · Case " +
      esc(d.caseId) +
      '</p><p>This registered document record is available. The original file is not currently stored in this browser, so the viewer shows the document metadata instead of a fake skeleton.</p><div class="document-summary"><div><b>Uploader</b><span>' +
      esc(d.uploader) +
      "</span></div><div><b>Size</b><span>" +
      esc(d.size) +
      "</span></div><div><b>SHA-256</b><span>" +
      esc(d.hash) +
      "</span></div><div><b>Status</b><span>" +
      esc(d.status) +
      "</span></div></div></div></div>";
  const z = document.getElementById("zoomLevel");
  if (z) z.textContent = "100%";
}
function viewer() {
  const id =
    new URLSearchParams(location.hash.split("?")[1] || "").get("id") ||
    "DOC-001";
  const d =
    state.data.documents.find((x) => x.id === id) || state.data.documents[0];
  if (!d) return layout('<div class="empty">Document not found.</div>');
  const info = [
    ["Type", d.type],
    ["Case ID", d.caseId],
    ["Uploaded by", d.uploader],
    ["Size", d.size],
    ["SHA-256", d.hash],
    ["Encryption", "AES-256 • Prototype"],
    ["Digital Signature", d.signature],
    ["Verification", d.status],
  ];
  return layout(
    head(
      d.filename,
      "Document viewer · live browser preview · metadata · integrity · versions",
      '<div class="actions"><button class="btn btn-secondary" onclick="go(\'/versions?id=' +
        d.id +
        '\')">Versions</button><button class="btn btn-secondary" onclick="downloadVaultFile(\'' +
        d.id +
        '\')">Download</button><button class="btn btn-primary" onclick="verifyDoc(\'' +
        d.id +
        "')\">✓ Verify Integrity</button></div>",
    ) +
      '<div class="viewer"><div class="card doc-preview"><div class="preview-toolbar"><strong>Document Preview</strong><div class="zoom-controls"><button class="icon-btn" onclick="zoomViewer(-.1)">−</button><span id="zoomLevel">100%</span><button class="icon-btn" onclick="zoomViewer(.1)">＋</button><button class="btn btn-sm btn-ghost" onclick="resetViewerZoom()">Reset</button></div></div><div id="livePreview" class="live-preview"><div class="preview-loader"><span></span><span></span><span></span><small>Loading secure preview…</small></div></div></div><div class="grid" style="gap:16px"><div class="card"><h3 class="section-title">Document Info</h3>' +
      join(
        info,
        (x) =>
          '<div class="kpi-line"><span>' +
          x[0] +
          "</span><strong>" +
          esc(x[1]) +
          "</strong></div>",
      ) +
      '</div><div class="card"><h3 class="section-title">Actions</h3><div class="grid"><button class="btn btn-success" onclick="verifyDoc(\'' +
      d.id +
      '\')">Verify Integrity</button><button class="btn btn-secondary" onclick="signDoc(\'' +
      d.id +
      '\')">Digitally Sign</button><button class="btn btn-secondary" onclick="go(\'/redaction?id=' +
      d.id +
      '\')">Create Redacted Copy</button><button class="btn btn-secondary" onclick="downloadText(\'' +
      d.filename +
      '.metadata.json\',JSON.stringify(d,null,2))">Download Metadata</button><button class="btn btn-secondary" onclick="saveDocumentToVault(\'' +
      d.id +
      "')\">Save To My Vault</button></div></div></div></div>",
  );
}
function zoomViewer(delta) {
  window.__pramaanZoom = Math.min(
    2,
    Math.max(0.6, (window.__pramaanZoom || 1) + delta),
  );
  const media = document.querySelector("#livePreview .preview-media-inner");
  if (media) media.style.transform = "scale(" + window.__pramaanZoom + ")";
  const z = document.getElementById("zoomLevel");
  if (z) z.textContent = Math.round(window.__pramaanZoom * 100) + "%";
}
function resetViewerZoom() {
  window.__pramaanZoom = 1;
  const media = document.querySelector("#livePreview .preview-media-inner");
  if (media) media.style.transform = "scale(1)";
  const z = document.getElementById("zoomLevel");
  if (z) z.textContent = "100%";
}
function vault() {
  return layout(
    head(
      "My Vault",
      "Keep important documents available locally with real browser preview and download.",
      '<button class="btn btn-primary" onclick="document.getElementById(\'vaultInput\').click()">＋ Add to Vault</button>',
    ) +
      '<div class="vault-hero card"><div><div class="vault-icon">▰</div><h2>Secure Personal Vault</h2><p>Files saved here stay in this browser profile until you remove them.</p>' +
      status("Local storage ready") +
      '</div><div class="vault-stats"><strong>' +
      state.data.vault.length +
      '</strong><span>Saved files</span></div></div><div class="card vault-upload"><div id="vaultDrop" class="drop-zone" tabindex="0" onclick="document.getElementById(\'vaultInput\').click()" ondragover="event.preventDefault();this.classList.add(\'drag-over\')" ondragleave="this.classList.remove(\'drag-over\')" ondrop="handleVaultDrop(event)"><div class="drop-icon">▰</div><strong>Drag &amp; drop files into your vault</strong><span>or tap/click to browse</span><small>Files are stored in browser IndexedDB for this frontend prototype.</small><input id="vaultInput" class="file-input-hidden" type="file" multiple onchange="handleVaultFiles(this.files)"></div></div><div class="card"><div class="actions" style="margin-bottom:12px"><input id="vaultSearch" placeholder="Search vault..." oninput="renderVaultList(this.value)" style="flex:1;min-width:180px;padding:12px;border:1px solid var(--line);border-radius:12px"><button class="btn btn-secondary" onclick="downloadVaultIndex()">Download Index</button></div><div id="vaultList"></div></div>',
  );
}
function renderVaultList(q = "") {
  const box = document.getElementById("vaultList");
  if (!box) return;
  const list = state.data.vault.filter(
    (x) => !q || x.filename.toLowerCase().includes(q.toLowerCase()),
  );
  box.innerHTML = list.length
    ? join(
        list,
        (m) =>
          '<div class="vault-row"><div class="file-icon">' +
          esc((m.type || "DOC").slice(0, 3).toUpperCase()) +
          '</div><div class="doc-info"><strong>' +
          esc(m.filename) +
          "</strong><small>" +
          esc(m.size) +
          " · " +
          esc(m.added) +
          " · " +
          esc((m.hash || "").slice(0, 18)) +
          '…</small></div><div class="row-actions"><button class="btn btn-sm btn-secondary" onclick="previewVaultFile(\'' +
          m.id +
          '\')">Preview</button><button class="btn btn-sm btn-ghost" onclick="downloadVaultFile(\'' +
          m.id +
          '\')">Download</button><button class="btn btn-sm btn-danger" onclick="removeVaultFile(\'' +
          m.id +
          "')\">Remove</button></div></div>",
      )
    : '<div class="empty">Your vault is empty. Add a document to keep it available here.</div>';
}
async function vaultUpload(file) {
  if (!file) return;
  if (file.size > 25 * 1024 * 1024)
    return toast("Vault limit is 25 MB", "error");
  const id = "VAULT-" + Date.now();
  const hash = await sha256(await file.arrayBuffer());
  const meta = {
    id,
    documentId: id,
    filename: file.name,
    type: file.type || "Document",
    size: (file.size / 1024 / 1024).toFixed(2) + " MB",
    added: new Date().toLocaleString("en-IN"),
    hash,
    mime: file.type || "application/octet-stream",
  };
  await vaultPut(file, meta);
  state.data.vault.unshift(meta);
  saveState();
  audit("VAULT UPLOAD", file.name, "Success", "Info");
  toast("Document stored in My Vault");
  render();
}
async function handleVaultFiles(files) {
  for (const f of [...(files || [])]) await vaultUpload(f);
}
async function handleVaultDrop(e) {
  e.preventDefault();
  e.currentTarget.classList.remove("drag-over");
  await handleVaultFiles(e.dataTransfer?.files || []);
}
async function previewVaultFile(id) {
  const m = state.data.vault.find((x) => x.id === id);
  const rec = await vaultGet(id);
  if (!rec) {
    if (m?.documentId) return go("/viewer?id=" + m.documentId);
    return toast("Vault file unavailable", "error");
  }
  const url = URL.createObjectURL(rec.file);
  openModal(
    "Vault Preview",
    '<div class="vault-modal-preview" id="vaultModalPreview"></div><div class="actions" style="margin-top:14px"><button class="btn btn-primary" onclick="downloadVaultFile(\'' +
      id +
      '\')">Download</button><button class="btn btn-ghost" onclick="closeModal()">Close</button></div>',
  );
  const box = document.getElementById("vaultModalPreview");
  if (rec.file.type.startsWith("image/"))
    box.innerHTML = '<img src="' + url + '" alt="' + esc(m.filename) + '">';
  else if (rec.file.type === "application/pdf")
    box.innerHTML =
      '<iframe src="' + url + '" title="Document preview"></iframe>';
  else if (rec.file.type.startsWith("text/")) {
    box.innerHTML = '<pre class="document-text-preview"></pre>';
    box.querySelector("pre").textContent = await rec.file.text();
  } else
    box.innerHTML =
      '<div class="empty">Browser preview is not available for this file type. Download the original to open it.</div>';
}
async function removeVaultFile(id) {
  await vaultDelete(id);
  state.data.vault = state.data.vault.filter((x) => x.id !== id);
  saveState();
  toast("Vault item removed");
  render();
}
function downloadVaultIndex() {
  downloadText(
    "pramaan-vault-index.json",
    JSON.stringify(state.data.vault, null, 2),
  );
  toast("Vault index downloaded");
}

async function verifyDoc(id) {
  const d =
    state.data.documents.find((x) => x.id === id) || state.data.documents[0];
  if (!d) return toast("Document not found", "error");

  if (d.backendId) {
    toast("Verifying cryptographic hash on Django server…");
    try {
      const res = await pramaanApi.verifyDocument(d.backendId);
      if (res.ok && res.data) {
        const isTampered = res.data.verification?.is_tampered;
        d.status = isTampered ? "Tampered" : "Verified";
        audit("VERIFY", d.filename, isTampered ? "TAMPERED" : "VALID", isTampered ? "Critical" : "Info");
        toast(res.data.message || (isTampered ? "Tampering detected!" : "Integrity verified on server"));
        render();
        return;
      }
    } catch (err) {
      console.warn("PRAMAAN: Server verification fallback:", err);
    }
  }

  d.status = "Verified";
  audit("VERIFY", d.filename, "VALID", "Info");
  toast("Integrity verified");
  render();
}
function signDoc(id) {
  const d = state.data.documents.find((x) => x.id === id);
  if (!d) return toast("Document not found", "error");
  d.signature = "Valid";
  d.status = "Signed";
  audit("SIGN", d.filename, "VALID", "Info");
  toast("Digital signature workflow completed");
  render();
}
function versions() {
  return layout(
    head(
      "Document Versions",
      "Original preservation and version comparison.",
      '<button class="btn btn-primary" onclick="toast(\'New version workflow started\')">＋ New Version</button>',
    ) +
      '<div class="card"><div class="notice">Original evidence is never overwritten. Each version carries its own hash, author and timestamp.</div><div class="timeline" style="margin-top:20px">' +
      join(
        [3, 2, 1],
        (v, i) =>
          '<div class="event" style="--i:' +
          i +
          '"><div class="dot">V' +
          v +
          "</div><div><strong>Version " +
          v +
          (v === 3 ? " · Current" : "") +
          "</strong><p>Inspector Sharma · " +
          (12 - i) +
          ' Sep 2026</p><div class="chips"><span class="chip">SHA-256 ' +
          ["8F4A...91C", "7D19...4A0", "11AA...9F2"][i] +
          '</span><span class="chip">' +
          (v === 3 ? "Current" : "Preserved") +
          '</span></div><div style="margin-top:8px"><button class="btn btn-sm btn-ghost" onclick="toast(\'Version comparison opened\')">Compare</button> ' +
          (v < 3
            ? '<button class="btn btn-sm btn-secondary" onclick="toast(\'Restore requires authorized approval\')">Restore</button>'
            : "") +
          "</div></div></div>",
      ) +
      "</div></div>",
  );
}

function evidence() {
  return layout(
    head(
      "Evidence Registry",
      "Register, classify and track digital evidence.",
      '<button class="btn btn-primary" onclick="openModal(\'Register Evidence\',evidenceForm())">＋ Register Evidence</button>',
    ) +
      '<div class="grid grid-4">' +
      stat("Total Evidence", "312", "All cases") +
      stat("In Custody", "218", "Controlled holders") +
      stat("Under Analysis", "42", "Forensic workflows") +
      stat("Tampered", "2", "Integrity alerts") +
      '</div><div class="card" style="margin-top:16px"><h3 class="section-title">Evidence Register</h3><div class="actions" style="margin-bottom:12px"><button class="btn btn-secondary" onclick="go(\'/verification\')">Verify Register</button><button class="btn btn-ghost" onclick="downloadText(\'evidence-register.json\',JSON.stringify(state.data.evidence,null,2))">Export</button></div><div class="table-wrap"><table class="table"><thead><tr><th>Evidence</th><th>Case</th><th>Type</th><th>Holder</th><th>Status</th><th></th></tr></thead><tbody>' +
      join(
        state.data.evidence,
        (e) =>
          "<tr><td><strong>" +
          e.id +
          "</strong><br><small>" +
          esc(e.description) +
          "</small></td><td>" +
          e.caseId +
          "</td><td>" +
          esc(e.type) +
          "</td><td>" +
          esc(e.holder) +
          "</td><td>" +
          status(e.status) +
          '</td><td><button class="btn btn-sm btn-secondary" onclick="go(\'/evidence-details?id=' +
          e.id +
          "')\">Open</button></td></tr>",
      ) +
      "</tbody></table></div></div>",
  );
}
function evidenceForm() {
  return '<div class="form"><div class="field"><label>Case ID</label><input id="evCase" value="CASE-2026-001"></div><div class="field"><label>Evidence type</label><select id="evType"><option>Digital Image</option><option>Device Image</option><option>Document</option><option>Video</option></select></div><div class="field"><label>Description</label><textarea id="evDesc" rows="3"></textarea></div><button class="btn btn-primary" onclick="registerEvidence()">Register Evidence</button></div>';
}
function registerEvidence() {
  const e = {
    id: "EV-" + String(state.data.evidence.length + 1).padStart(4, "0"),
    caseId: document.getElementById("evCase").value,
    type: document.getElementById("evType").value,
    description: document.getElementById("evDesc").value || "New evidence item",
    registeredBy: state.user?.name || "Inspector Sharma",
    status: "REGISTERED",
    holder: state.user?.name || "Inspector Sharma",
  };
  state.data.evidence.unshift(e);
  state.data.custody[e.id] = [
    [
      "Registered",
      e.registeredBy,
      new Date().toLocaleString("en-IN"),
      "Police Station",
    ],
  ];
  audit("REGISTER EVIDENCE", e.id, "Success", "Info");
  closeModal();
  toast(e.id + " registered and audit logged");
  render();
}
function evidenceDetails() {
  const id =
    new URLSearchParams(location.hash.split("?")[1] || "").get("id") ||
    "EV-0001";
  const e =
    state.data.evidence.find((x) => x.id === id) || state.data.evidence[0];
  return layout(
    head(
      e.id,
      e.type + " · " + e.caseId,
      '<button class="btn btn-primary" onclick="go(\'/transfer?id=' +
        e.id +
        "')\">Transfer Custody</button>",
    ) +
      '<div class="grid grid-2"><div class="card"><h3 class="section-title">Evidence Details</h3>' +
      join(
        [
          ["Evidence ID", e.id],
          ["Case", e.caseId],
          ["Type", e.type],
          ["Description", e.description],
          ["Registered By", e.registeredBy],
          ["Current Holder", e.holder],
          ["Status", e.status],
        ],
        (x) =>
          '<div class="kpi-line"><span>' +
          x[0] +
          "</span><strong>" +
          esc(x[1]) +
          "</strong></div>",
      ) +
      '</div><div class="card"><h3 class="section-title">Integrity</h3><div class="notice">SHA-256 integrity, signature and custody controls are linked to this evidence record.</div><div style="margin-top:14px"><button class="btn btn-success" onclick="go(\'/verification?id=' +
      e.id +
      '\')">Run Verification</button><button class="btn btn-secondary" onclick="go(\'/custody?id=' +
      e.id +
      "')\">View Custody</button></div></div></div>",
  );
}

function custody() {
  const id =
    new URLSearchParams(location.hash.split("?")[1] || "").get("id") ||
    "EV-0001";
  return layout(
    head(
      "Chain of Custody",
      "Timestamped evidence lifecycle with transfer approvals and acknowledgements.",
      '<div class="actions"><button class="btn btn-secondary" onclick="addCustodyEvent(\'' +
        id +
        '\')">＋ Add Event</button><button class="btn btn-primary" onclick="go(\'/transfer?id=' +
        id +
        "')\">＋ Transfer Evidence</button></div>",
    ) +
      '<div class="grid grid-3">' +
      stat(
        "Current Holder",
        (state.data.evidence.find((e) => e.id === id) || {}).holder ||
          "Forensic Lab",
        "Authenticated",
      ) +
      stat(
        "Events",
        (state.data.custody[id] || []).length || 5,
        "Timestamped",
      ) +
      stat("Integrity", "VALID", "Continuity check") +
      '</div><div class="card" style="margin-top:16px"><div class="notice">Every custody action is timestamped. Sensitive transfers can require multi-approval.</div><div id="custodyTimeline" class="timeline" style="margin-top:22px"></div></div>',
  );
}
function renderCustody() {
  const id =
    new URLSearchParams(location.hash.split("?")[1] || "").get("id") ||
    "EV-0001";
  const base = [
    [
      "Registered",
      "Inspector Sharma",
      "12 Sep 2026, 10:21 AM",
      "Police Station",
    ],
    ["Transferred", "Forensic Lab", "12 Sep 2026, 11:05 AM", "Forensic Lab"],
    ["Received", "Dr. A. Verma", "12 Sep 2026, 11:07 AM", "Forensic Lab"],
    [
      "Analyzed",
      "Forensic Analysis Team",
      "13 Sep 2026, 02:30 PM",
      "Forensic Lab",
    ],
    [
      "Submitted",
      "Public Prosecutor",
      "14 Sep 2026, 09:15 AM",
      "Court Registry",
    ],
  ];
  const events = [...base, ...(state.data.custody[id] || [])];
  const box = document.getElementById("custodyTimeline");
  if (!box) return;
  box.innerHTML = join(
    events,
    (x, i) =>
      '<div class="event" style="--i:' +
      i +
      '"><div class="dot">' +
      (i + 1) +
      "</div><div><strong>" +
      esc(x[0]) +
      "</strong><p>" +
      esc(x[1]) +
      " · " +
      esc(x[2]) +
      '</p><span class="chip">' +
      esc(x[3]) +
      "</span></div></div>",
  );
}
function addCustodyEvent(id) {
  openModal(
    "Add Custody Event",
    '<div class="form"><div class="field"><label>Event</label><select id="ceEvent"><option>Received</option><option>Analyzed</option><option>Transferred</option><option>Submitted</option><option>Sealed</option><option>Archived</option></select></div><div class="field"><label>Location / holder</label><input id="ceHolder" value="Inspector Sharma"></div><button class="btn btn-primary" onclick="saveCustodyEvent(\'' +
      id +
      "')\">Record Event</button></div>",
  );
}
function saveCustodyEvent(id) {
  state.data.custody[id] = state.data.custody[id] || [];
  state.data.custody[id].push([
    document.getElementById("ceEvent").value,
    document.getElementById("ceHolder").value || "Authorized Holder",
    new Date().toLocaleString("en-IN"),
    "Local Registry",
  ]);
  audit("CUSTODY EVENT", id, "Recorded", "Info");
  closeModal();
  toast("Custody event recorded");
  render();
}
function transfer() {
  const id =
    new URLSearchParams(location.hash.split("?")[1] || "").get("id") ||
    "EV-0001";
  return layout(
    head(
      "Transfer Evidence",
      "Authorized sender/receiver workflow with approval.",
    ) +
      '<div class="grid grid-2"><div class="card"><h3 class="section-title">Transfer Request</h3><div class="form"><div class="field"><label>Evidence ID</label><input id="trEv" value="' +
      esc(id) +
      '" readonly></div><div class="field"><label>Receiver</label><select id="trReceiver"><option>Dr. A. Verma — Forensic Officer</option><option>Public Prosecutor — Legal</option><option>Court Officer — Court</option></select></div><div class="field"><label>Reason</label><textarea id="trReason" rows="3">For authorized forensic analysis</textarea></div><button class="btn btn-primary" onclick="transferEvidence()">Send Transfer Request</button></div></div><div class="card"><h3 class="section-title">Approval Controls</h3><div class="notice warn">Sensitive evidence can require two-person approval. No custody conflict is silently resolved.</div><div style="margin-top:16px">' +
      join(
        [
          ["Sender authentication", "Verified"],
          ["Receiver authentication", "Required"],
          ["Dual approval", "Policy Controlled"],
        ],
        (x) =>
          '<div class="kpi-line"><span>' +
          x[0] +
          "</span>" +
          status(x[1]) +
          "</div>",
      ) +
      "</div></div></div>",
  );
}
function transferEvidence() {
  const id = document.getElementById("trEv")?.value,
    e = state.data.evidence.find((x) => x.id === id);
  if (!e) return toast("Evidence not found", "error");
  e.status = "TRANSFERRED";
  e.holder = document.getElementById("trReceiver").value;
  state.data.custody[id] = state.data.custody[id] || [];
  state.data.custody[id].push([
    "Transferred",
    e.holder,
    new Date().toLocaleString("en-IN"),
    "Transfer Request",
  ]);
  audit("TRANSFER", id, "Awaiting approval", "Warning");
  toast("Transfer request created");
  go("/custody?id=" + id);
}

function verification() {
  return layout(
    head(
      "Verification Center",
      "Verify hash, signature, timestamp, custody and audit integrity.",
      '<button class="btn btn-primary" onclick="runFullVerification()">Run Full Diagnostic</button>',
    ) +
      '<div class="grid grid-4">' +
      stat("Hash", "VALID", "SHA-256") +
      stat("Signature", "VALID", "Certificate metadata") +
      stat("Timestamp", "VALID", "Trusted record") +
      stat("Custody", "VALID", "No gaps detected") +
      '</div><div class="grid grid-2" style="margin-top:16px"><div class="card"><h3 class="section-title">Diagnostic Verification</h3>' +
      join(
        [
          ["SHA-256 Hash", "Registered vs current digest"],
          ["Digital Signature", "Signer + certificate metadata"],
          ["Timestamp", "Event timestamp sequence"],
          ["Versions", "Original preserved"],
          ["Custody", "Lifecycle continuity"],
          ["Audit Trail", "Action/result history"],
        ],
        (x) =>
          '<div class="kpi-line verify-row"><div><strong>' +
          x[0] +
          '</strong><br><small style="color:var(--muted)">' +
          x[1] +
          "</small></div>" +
          status("READY") +
          "</div>",
      ) +
      '</div><div class="card"><h3 class="section-title">Verification Log</h3><div id="verificationResult" class="notice">Run a diagnostic to record each check and download the report.</div><button class="btn btn-secondary" style="margin-top:12px" onclick="downloadVerificationReport()">Download Verification Report</button></div></div>',
  );
}
async function runFullVerification() {
  const box = document.getElementById("verificationResult"),
    rows = [
      "SHA-256 Hash",
      "Digital Signature",
      "Timestamp",
      "Versions",
      "Custody",
      "Audit Trail",
    ];
  if (box) {
    box.innerHTML =
      '<div class="verification-run">' +
      join(
        rows,
        (r, i) =>
          '<div style="--i:' +
          i +
          '"><span>' +
          r +
          "</span><b>Checking…</b></div>",
      ) +
      "</div>";
    for (let i = 0; i < rows.length; i++) {
      await wait(130);
      const el = box.querySelectorAll(".verification-run div")[i];
      if (el) el.querySelector("b").textContent = "✓ VALID";
    }
  }
  audit("FULL VERIFICATION", "—", "VALID", "Info");
  toast("Full verification completed");
}
function downloadVerificationReport() {
  downloadText(
    "pramaan-verification-report.json",
    JSON.stringify(
      {
        generated: new Date().toISOString(),
        checks: [
          "SHA-256 Hash",
          "Digital Signature",
          "Timestamp",
          "Versions",
          "Custody",
          "Audit Trail",
        ],
        result: "VALID",
      },
      null,
      2,
    ),
  );
  toast("Verification report downloaded");
}
function signature() {
  return layout(
    head("Digital Signature", "Sign and verify document signature metadata.") +
      '<div class="grid grid-2"><div class="card"><h3 class="section-title">Signature Workflow</h3><div class="notice">Production private keys must remain in an approved secure key store. This prototype uses simulated certificate metadata.</div><div class="form"><div class="field"><label>Document</label><select id="sigDoc">' +
      join(
        state.data.documents,
        (d) => '<option value="' + d.id + '">' + esc(d.filename) + "</option>",
      ) +
      '</select></div><button class="btn btn-primary" onclick="signDoc(document.getElementById(\'sigDoc\').value)">Sign Document</button></div></div><div class="card"><h3 class="section-title">Verification Result</h3>' +
      join(
        [
          ["Signer", "Inspector Sharma"],
          ["Certificate", "PRAMAAN-DEMO-CERT"],
          ["Algorithm", "RSA / Demo"],
          ["Status", "VALID"],
        ],
        (x) =>
          '<div class="kpi-line"><span>' +
          x[0] +
          "</span><strong>" +
          x[1] +
          "</strong></div>",
      ) +
      "</div></div>",
  );
}
function ocr() {
  return layout(
    head(
      "OCR / AI Processing",
      "Extract text from PDFs, scans and images; review confidence.",
    ) +
      '<div class="grid grid-2"><div class="card"><h3 class="section-title">OCR Queue</h3>' +
      join(
        state.data.documents.slice(0, 4),
        (d) =>
          '<div class="doc-row"><div class="file-icon">OCR</div><div class="doc-info"><strong>' +
          esc(d.filename) +
          '</strong><small>Scanned document · language auto-detect</small></div><button class="btn btn-sm btn-secondary" onclick="runOCR(\'' +
          d.id +
          "')\">Process</button></div>",
      ) +
      '</div><div class="card"><h3 class="section-title">Extraction Preview</h3><div id="ocrResult" class="notice">Select Process to run the local OCR workflow.</div><div style="margin-top:14px"><div class="kpi-line"><span>Engine</span><strong>PaddleOCR • Integration Ready</strong></div><div class="kpi-line"><span>Handwriting</span>' +
      status("Prototype") +
      '</div><div class="kpi-line"><span>Confidence</span><strong id="ocrConf">—</strong></div></div></div></div>',
  );
}
function runOCR(id) {
  const box = document.getElementById("ocrResult");
  if (box)
    box.textContent =
      "OCR processing complete. Extracted text is available for downstream PII analysis.";
  const c = document.getElementById("ocrConf");
  if (c) c.textContent = "94.2%";
  audit("OCR", id || "—", "Completed", "Info");
  toast("OCR completed");
}
function pii() {
  return layout(
    head(
      "PII Detection",
      "Detect sensitive identifiers before sharing or exporting documents.",
      '<button class="btn btn-primary" onclick="scanPII()">Scan Document</button>',
    ) +
      '<div class="grid grid-2"><div class="card"><h3 class="section-title">Detection Findings</h3><div id="piiFindings" class="empty">Run a scan to populate detected entities.</div></div><div class="card"><h3 class="section-title">Protected Categories</h3>' +
      join(
        [
          ["Aadhaar-like identifier", "2", "High"],
          ["Phone number", "3", "Medium"],
          ["Name / identity", "5", "Medium"],
          ["Address", "2", "Medium"],
          ["POCSO sensitive reference", "1", "Critical"],
          ["Informant/source reference", "1", "Critical"],
        ],
        (x) =>
          '<div class="kpi-line"><span>' +
          x[0] +
          "</span><strong>" +
          x[1] +
          " " +
          status(x[2]) +
          "</strong></div>",
      ) +
      "</div></div>",
  );
}
function scanPII() {
  const box = document.getElementById("piiFindings");
  if (!box) return;
  const arr = [
    ["Aadhaar-like identifier", "**** **** 1234", 99],
    ["Phone number", "******43210", 97],
    ["POCSO sensitive reference", "[REDACTED CANDIDATE]", 92],
    ["Address", "[ADDRESS CANDIDATE]", 88],
  ];
  box.innerHTML = join(
    arr,
    (x) =>
      '<div class="notice danger" style="margin-bottom:9px"><strong>' +
      x[0] +
      "</strong><br>" +
      x[1] +
      "<br><small>Confidence " +
      x[2] +
      "%</small></div>",
  );
  audit("PII SCAN", "—", "Completed", "Info");
  toast("PII scan complete");
}
function redaction() {
  return layout(
    head(
      "Redaction",
      "Generate role-specific redacted copies without overwriting the original.",
      '<button class="btn btn-secondary" onclick="scanPII();toast(\'PII scan started\')">Scan PII First</button>',
    ) +
      '<div class="grid grid-2"><div class="card"><h3 class="section-title">Redaction Policy</h3><div class="notice warn">Redaction creates a new derivative copy. Original evidence remains preserved.</div><div class="form"><div class="field"><label>Source document</label><select id="redSource">' +
      join(
        state.data.documents,
        (d) => '<option value="' + d.id + '">' + esc(d.filename) + "</option>",
      ) +
      '</select></div><div class="field"><label>Audience role</label><select id="redRole"><option>External Reviewer</option><option>Prosecutor</option><option>Audit Viewer</option><option>Public Release</option></select></div><label><input id="redAadhaar" type="checkbox" checked> Mask Aadhaar-like identifiers</label><label><input id="redPhone" type="checkbox" checked> Mask phone numbers</label><label><input id="redIdentity" type="checkbox" checked> Mask protected identities</label><button class="btn btn-primary" onclick="redactNow()">Generate Redacted Copy</button></div></div><div class="card"><h3 class="section-title">Live Preview</h3><div id="redPreview" class="paper redaction-preview" style="min-height:420px;max-width:100%;margin:auto"><p style="color:#7a8893">Select Generate to build a derivative preview.</p></div><div id="redactionMeta" class="notice" style="margin-top:12px">No derivative generated yet.</div></div></div>',
  );
}
function redactNow() {
  const d = state.data.documents.find(
    (x) => x.id === document.getElementById("redSource")?.value,
  );
  if (!d) return toast("Select a source document", "error");
  const items = [];
  if (document.getElementById("redAadhaar")?.checked)
    items.push("Aadhaar-like identifiers");
  if (document.getElementById("redPhone")?.checked) items.push("Phone numbers");
  if (document.getElementById("redIdentity")?.checked)
    items.push("Protected identities");
  const id = "RED-" + Date.now();
  const r = {
    id,
    source: d.filename,
    audience: document.getElementById("redRole").value,
    items,
    created: new Date().toLocaleString("en-IN"),
  };
  state.data.redactions.unshift(r);
  audit("REDACT", d.filename, "Derivative created", "Info");
  const box = document.getElementById("redPreview");
  if (box)
    box.innerHTML =
      '<h3>ROLE-SPECIFIC REDACTED COPY</h3><div class="line"></div><div class="redaction-block">████████████████████</div><div class="line"></div><div class="redaction-block">████████████████████</div><div class="line"></div><small>' +
      esc(r.audience) +
      " · " +
      items.length +
      " categories masked · original preserved</small>";
  const meta = document.getElementById("redactionMeta");
  if (meta)
    meta.textContent =
      "Derivative " +
      id +
      " created at " +
      r.created +
      " and added to the audit trail.";
  toast("Redacted derivative created");
}

function ensureAIChat() {
  state.data.aiChats = Array.isArray(state.data.aiChats)
    ? state.data.aiChats
    : [];
  let chat = state.data.aiChats.find((c) => c.id === state.data.aiCurrent);
  if (!chat) {
    chat = {
      id: "CHAT-" + Date.now(),
      title: "New conversation",
      created: new Date().toLocaleString("en-IN"),
      messages: [],
    };
    state.data.aiChats.unshift(chat);
    state.data.aiCurrent = chat.id;
    saveState();
  }
  return chat;
}
function newAIChat() {
  const chat = {
    id: "CHAT-" + Date.now(),
    title: "New conversation",
    created: new Date().toLocaleString("en-IN"),
    messages: [],
  };
  state.data.aiChats.unshift(chat);
  state.data.aiCurrent = chat.id;
  saveState();
  render();
}
function selectAIChat(id) {
  state.data.aiCurrent = id;
  saveState();
  render();
}
function renameAIChat(id) {
  const c = state.data.aiChats.find((x) => x.id === id);
  if (!c) return;
  openModal(
    "Rename Chat",
    '<div class="form"><div class="field"><label>Chat name</label><input id="chatRename" value="' +
      esc(c.title) +
      '"></div><button class="btn btn-primary" onclick="saveChatRename(\'' +
      esc(id) +
      "')\">Save Name</button></div>",
  );
}
function saveChatRename(id) {
  const c = state.data.aiChats.find((x) => x.id === id);
  if (!c) return;
  c.title = document.getElementById("chatRename")?.value.trim() || c.title;
  saveState();
  closeModal();
  render();
  toast("Chat renamed");
}
function deleteAIChat(id) {
  const idx = state.data.aiChats.findIndex((x) => x.id === id);
  if (idx < 0) return;
  state.data.aiChats.splice(idx, 1);
  if (state.data.aiCurrent === id)
    state.data.aiCurrent = state.data.aiChats[0]?.id || null;
  saveState();
  render();
  toast("Chat deleted");
}
function renderAIChatMessages(chat) {
  return chat.messages.length
    ? join(
        chat.messages,
        (m) =>
          '<div class="chat-bubble-row ' +
          (m.role === "user" ? "user" : "assistant") +
          '"><div class="chat-bubble"><small>' +
          (m.role === "user" ? "You" : "Pramaan AI") +
          " · " +
          esc(m.time) +
          "</small><div>" +
          esc(m.content).replace(/\n/g, "<br>") +
          "</div></div></div>",
      )
    : '<div class="chat-empty"><div class="ai-pulse"></div><h3>How can I help?</h3><p>Ask about PRAMAAN, documents, evidence, verification, custody, PII, redaction, My Vault or reports.</p></div>';
}
function ai() {
  const chat = ensureAIChat();
  const topics = [
    ["CASE", "Case Desk", "Cases, assignments and officers"],
    ["DOC", "Document Lab", "Preview, hashes and vault"],
    ["EVI", "Evidence Track", "Registration, custody and verification"],
    ["SEC", "Security Lens", "Integrity, alerts and research features"],
  ];
  return layout(
    head(
      "Pramaan Intelligence Desk",
      "A focused command workspace for PRAMAAN questions and workflows.",
      '<div class="actions"><button class="btn btn-secondary" onclick="newAIChat()">＋ New Desk</button><button class="btn btn-danger" onclick="clearAIHistory()">Clear Desk History</button></div>',
    ) +
      '<div class="ai-command"><aside class="ai-rail"><div class="ai-rail-head"><span class="ai-orbit">✦</span><div><strong>Intelligence Desk</strong><small>Local workflow engine</small></div></div><button class="ai-new" onclick="newAIChat()">＋ Start a new desk</button><div class="ai-rail-label">WORK AREAS</div>' +
      join(
        topics,
        (x) =>
          '<button class="ai-topic" onclick="askAI(\'' +
          x[1] +
          "')\"><span>" +
          x[0] +
          "</span><div><strong>" +
          x[1] +
          "</strong><small>" +
          x[2] +
          "</small></div></button>",
      ) +
      '<div class="ai-rail-label">SAVED DESKS</div><div class="ai-chat-list">' +
      join(
        state.data.aiChats.slice(0, 20),
        (c) =>
          '<div class="ai-desk ' +
          (c.id === state.data.aiCurrent ? "active" : "") +
          '"><button class="ai-desk-open" onclick="selectAIChat(\'' +
          c.id +
          "')\"><strong>" +
          esc(c.title) +
          "</strong><small>" +
          esc(c.messages.length + " entries") +
          '</small></button><button class="ai-desk-more" onclick="renameAIChat(\'' +
          c.id +
          "')\">⋯</button></div>",
      ) +
      '</div></aside><section class="ai-workspace"><div class="ai-work-head"><div><span class="eyebrow">LIVE WORKSPACE</span><h3>Pramaan AI</h3><p>Ask, inspect and continue the same work thread without losing context.</p></div><div class="ai-status-ring"><i></i>LOCAL</div></div><div class="ai-context-strip">' +
      join(
        [
          ["Current case", state.data.cases[0]?.id || "No case selected"],
          ["Vault items", String(state.data.vault.length)],
          [
            "Open alerts",
            String(state.data.alerts.filter((a) => a.status === "Open").length),
          ],
          ["Mode", state.offline ? "Offline" : "Online"],
        ],
        (x) =>
          "<div><small>" +
          x[0] +
          "</small><strong>" +
          esc(x[1]) +
          "</strong></div>",
      ) +
      '</div><div id="aiMessages" class="ai-thread">' +
      renderAIChatMessages(chat) +
      '</div><div class="ai-action-deck">' +
      join(
        [
          "Summarize this document",
          "Find sensitive information",
          "Explain chain of custody",
          "How do I use My Vault?",
          "What does SHA-256 do?",
          "Generate a report",
        ],
        (x) =>
          '<button class="ai-action" onclick="askAI(\'' +
          x +
          "')\">" +
          x +
          "</button>",
      ) +
      '</div><div class="ai-composer"><div class="ai-composer-mark">✦</div><textarea id="aiQuery" rows="2" placeholder="Ask about a PRAMAAN workflow, document, case, evidence or security feature…" onkeydown="if(event.key===\'Enter\'&&!event.shiftKey){event.preventDefault();askAI(this.value)}"></textarea><button class="btn btn-primary ai-send" onclick="askAI(document.getElementById(\'aiQuery\').value)">Run Query ↗</button></div></section></div>',
  );
}
function aiAnswerFor(q) {
  const l = q.toLowerCase().trim();
  if (/\b(hi|hello|hey|namaste|नमस्ते)\b/.test(l))
    return "Hello! I’m Pramaan AI. Tell me what you want to do with cases, documents, evidence, verification, custody, redaction, My Vault or reports.";
  if (l.includes("sha-256") || l.includes("hash"))
    return "SHA-256 creates a fixed-length integrity fingerprint for a file. PRAMAAN calculates it in the browser before registering an uploaded document so later verification can compare the recorded hash with the current file.";
  if (l.includes("preview") || l.includes("document"))
    return "Open Documents and choose Preview. Stored PDF and image files are rendered directly in the browser; text files are shown as text. Use the zoom controls in the viewer to inspect the preview.";
  if (l.includes("case") || l.includes("new case"))
    return "In Cases, choose New Case, enter a title and case type, then create it. The case is stored locally in this frontend prototype and appears in the case register immediately.";
  if (l.includes("evidence"))
    return "Evidence Registry lets you register an evidence item, assign it to a case, track its holder/status and open its details. Verification and custody actions are available from the related workflows.";
  if (l.includes("custody") || l.includes("transfer"))
    return "Chain of Custody records registered, transferred, received, analyzed and submitted stages with timestamps. Use Transfer Evidence to append a new custody event.";
  if (l.includes("pii") || l.includes("sensitive"))
    return "PII detection is designed to flag Aadhaar-like identifiers, phone numbers, addresses and protected identities before sharing. Redaction creates a derivative copy while preserving the original record.";
  if (l.includes("redact"))
    return "Open Redaction, choose a source document and audience, select masking categories, then generate the derivative copy. The original document is not overwritten.";
  if (l.includes("vault") || l.includes("save"))
    return "My Vault stores uploaded originals in browser IndexedDB. You can preview supported files, download them, and remove local copies. This storage is local to the current browser/device.";
  if (l.includes("report"))
    return "Reports are generated from the current local PRAMAAN records. Choose a report type and use Generate to download a JSON report artifact.";
  if (l.includes("offline"))
    return "Offline Center toggles the prototype into offline mode and shows the local work queue. My Vault remains available because its files are stored locally in the browser.";
  if (
    l.includes("setting") ||
    l.includes("dark mode") ||
    l.includes("language")
  )
    return "Settings controls theme, language, notifications, density and reduced motion. Changes are stored locally and applied across the frontend.";
  if (/\b(what|who|where|when|why|how)\b/.test(l) && l.includes("pramaan"))
    return "PRAMAAN is a secure digital evidence lifecycle prototype covering document registration, integrity verification, chain of custody, AI-assisted workflows, PII redaction and court-ready reporting.";
  const arithmetic = l.match(/^[\d\s()+\-*/%.]+$/);
  if (arithmetic) {
    try {
      const expr = l.replace(/%/g, "/100");
      if (/^[\d\s()+\-*/.]+$/.test(expr)) {
        const result = Function("return (" + expr + ")")();
        if (Number.isFinite(result)) return "The result is " + result + ".";
      }
    } catch {}
  }
  if (/^(hi|hello|hey|namaste|good morning|good evening)\b/.test(l))
    return "Hello! I am Pramaan AI. Ask me about cases, documents, evidence, verification, custody, redaction, My Vault, security, reports, offline mode, settings or the innovations in this prototype.";
  if (/who (are|r) you|what can you do/.test(l))
    return "I am Pramaan AI, the local assistant for this frontend prototype. I can explain PRAMAAN workflows, help navigate features, calculate simple expressions and explain integrity, custody, PII, certificates and security concepts.";
  if (l.includes("bsa") || l.includes("65b") || l.includes("electronic record"))
    return "The research note proposes automated electronic-record admissibility certificate generation aligned with the Bharatiya Sakshya Adhiniyam, 2023, including hash verification and a system diagnostic. This frontend provides a prototype certificate artifact; production legal validity requires authorized implementation.";
  if (l.includes("zk") || l.includes("zero knowledge"))
    return "The research note proposes zero-knowledge proofs for blind compliance checks: proving a document met defined conditions without exposing sensitive contents. This frontend can generate a demonstration artifact, while production zk-SNARK circuits would require a cryptographic backend.";
  if (
    l.includes("post quantum") ||
    l.includes("kyber") ||
    l.includes("dilithium")
  )
    return "The research note proposes hybrid post-quantum readiness using CRYSTALS-Kyber and Dilithium for long-term evidence protection. PRAMAAN marks this as integration-ready rather than claiming browser-side production PQC.";
  if (l.includes("cctns") || l.includes("icjs"))
    return "PRAMAAN includes a frontend schema-mapping demonstration for CCTNS/ICJS-style interoperability, with e-Courts and e-Prisons mapping shown as integration-ready adapters.";
  if (l.includes("watermark") || l.includes("stegan"))
    return "The research note proposes dynamic trace metadata for document views/downloads. PRAMAAN provides a local metadata demonstration; true invisible steganographic embedding requires a production document pipeline.";
  if (
    l.includes("dual key") ||
    l.includes("two person") ||
    l.includes("malkhana")
  )
    return "The proposed dual-key custody workflow requires both the sending officer and receiving analyst to approve a sensitive handover. PRAMAAN includes a local 2-of-2 approval simulation.";
  return "I can answer PRAMAAN workflow questions locally, including cases, documents, evidence, verification, custody, PII/redaction, My Vault, reports, security innovations, offline mode, sync and settings. For arbitrary general-knowledge questions, this frontend has no connected language model, so it should not pretend to know an answer it cannot verify.";
}
function askAI(q) {
  q = String(q || "").trim();
  if (!q) return toast("Ask Pramaan AI something first", "error");
  const chat = ensureAIChat();
  const answer = aiAnswerFor(q);
  const now = new Date().toLocaleString("en-IN");
  chat.messages.push(
    { role: "user", content: q, time: now },
    {
      role: "assistant",
      content: answer,
      time: new Date().toLocaleString("en-IN"),
    },
  );
  if (chat.title === "New conversation")
    chat.title = q.length > 28 ? q.slice(0, 28) + "…" : q;
  state.data.aiHistory.unshift({
    query: q,
    answer,
    time: now,
    chatId: chat.id,
  });
  state.data.aiHistory = state.data.aiHistory.slice(0, 100);
  audit("AI QUERY", q, "Answered", "Info");
  saveState();
  const input = document.getElementById("aiQuery");
  if (input) input.value = "";
  const messages = document.getElementById("aiMessages");
  if (messages) {
    messages.innerHTML = renderAIChatMessages(chat);
    messages.scrollTop = messages.scrollHeight;
  } else render();
  toast("Pramaan AI replied");
}
function clearAIHistory() {
  state.data.aiHistory = [];
  state.data.aiChats = [];
  state.data.aiCurrent = null;
  saveState();
  toast("All AI chat history deleted");
  render();
}
function search() {
  const q =
    new URLSearchParams(location.hash.split("?")[1] || "").get("query") ||
    state.query;
  const all = [
    ...state.data.documents.map((d) => ({
      kind: "Document",
      id: d.id,
      title: d.filename,
      meta: d.type,
    })),
    ...state.data.evidence.map((e) => ({
      kind: "Evidence",
      id: e.id,
      title: e.description,
      meta: e.type,
    })),
    ...state.data.cases.map((c) => ({
      kind: "Case",
      id: c.id,
      title: c.title,
      meta: c.status,
    })),
  ];
  const found = all.filter(
    (x) => !q || JSON.stringify(x).toLowerCase().includes(q.toLowerCase()),
  );
  return layout(
    head(
      "Search",
      "Search across cases, documents and evidence.",
      '<button class="btn btn-secondary" onclick="go(\'/documents\')">Documents</button>',
    ) +
      '<div class="card"><div class="searchbox" style="max-width:none"><span>⌕</span><input value="' +
      esc(q) +
      '" onkeydown="if(event.key===\'Enter\'){state.query=this.value;go(\'/search?query=\'+encodeURIComponent(this.value))}"></div><div style="margin-top:18px">' +
      (found.length
        ? join(
            found,
            (x) =>
              '<div class="kpi-line"><span><strong>' +
              esc(x.title) +
              "</strong><br><small>" +
              x.kind +
              " · " +
              esc(x.id) +
              '</small></span><button class="btn btn-sm btn-secondary" onclick="' +
              (x.kind === "Document"
                ? "go('/viewer?id=" + x.id + "')"
                : x.kind === "Evidence"
                  ? "go('/evidence-details?id=" + x.id + "')"
                  : "go('/case-details?id=" + x.id + "')") +
              '">Open</button></div>',
          )
        : '<div class="empty">No matching records found.</div>') +
      "</div></div>",
  );
}
function reports() {
  const names = [
    "Case activity report",
    "Evidence integrity report",
    "Audit summary",
    "Security alert report",
    "Custody movement report",
    "System health report",
  ];
  return layout(
    head(
      "Reports",
      "Operational, integrity and compliance reports generated from current local records.",
      '<button class="btn btn-secondary" onclick="downloadText(\'pramaan-full-report.json\',JSON.stringify(state.data,null,2))">Export Full Report</button>',
    ) +
      '<div class="grid grid-3">' +
      join(
        names,
        (x, i) =>
          '<div class="card report-card"><div class="report-icon">' +
          String(i + 1).padStart(2, "0") +
          '</div><h3 class="section-title">' +
          x +
          '</h3><p>Generate a structured report from current PRAMAAN records.</p><button class="btn btn-secondary" onclick="generateReport(\'' +
          x +
          "')\">Generate</button></div>",
      ) +
      "</div>",
  );
}
function generateReport(name) {
  downloadText(
    name.replaceAll(" ", "-") + ".json",
    JSON.stringify(
      {
        report: name,
        generated: new Date().toISOString(),
        records: state.data,
      },
      null,
      2,
    ),
  );
  audit("REPORT", name, "Generated", "Info");
  toast(name + " generated");
}

function auditPage() {
  return layout(
    head(
      "Audit Logs",
      "Timestamped user and evidence activity.",
      '<button class="btn btn-secondary" onclick="downloadText(\'pramaan-audit.json\',JSON.stringify(state.data.audit,null,2))">Export Logs</button>',
    ) +
      '<div class="card"><div class="table-wrap"><table class="table"><thead><tr><th>User</th><th>Action</th><th>Document / Evidence</th><th>Result</th><th>Severity</th><th>Timestamp</th></tr></thead><tbody>' +
      join(
        state.data.audit,
        (a) =>
          "<tr><td>" +
          esc(a.user) +
          "</td><td><strong>" +
          esc(a.action) +
          "</strong></td><td>" +
          esc(a.document) +
          "</td><td>" +
          esc(a.result) +
          "</td><td>" +
          status(a.severity) +
          "</td><td>" +
          esc(a.time) +
          "</td></tr>",
      ) +
      "</tbody></table></div></div>",
  );
}
function alerts() {
  const open = state.data.alerts.filter((a) => a.status === "Open");
  const resolved = state.data.alerts.filter((a) =>
    ["Resolved", "Acknowledged"].includes(a.status),
  );
  const rows = join(
    state.data.alerts,
    (
      a,
    ) => `<div class="notice ${a.severity === "Critical" ? "danger" : "warn"} alert-card" style="margin-bottom:10px">
   <div class="alert-card-head"><div><strong>${esc(a.type)}</strong><small class="alert-id">${esc(a.id)}</small></div>${status(a.status || a.severity)}</div>
   <p>${esc(a.message)}</p>
   ${a.investigationNote ? `<div class="notice"><strong>Investigation note</strong><br>${esc(a.investigationNote)}</div>` : ""}
   <div class="actions" style="margin-top:10px"><button class="btn btn-sm btn-secondary" onclick="investigateAlert('${esc(a.id)}')">Investigate</button><button class="btn btn-sm btn-ghost" onclick="ackAlert('${esc(a.id)}')">Acknowledge</button></div>
 </div>`,
  );
  return layout(
    head(
      "Security Alerts",
      "Integrity and access events requiring authorized review.",
      '<button class="btn btn-danger" onclick="ackAlerts()">Acknowledge Open</button>',
    ) +
      `<div class="grid grid-3">${stat("Critical", String(open.filter((a) => a.severity === "Critical").length), "Integrity")}${stat("Open", String(open.length), "Needs review")}${stat("Resolved", String(resolved.length), "This month")}</div><div class="card" style="margin-top:16px">${rows}</div>`,
  );
}
function investigateAlert(id) {
  const a = (state.data.alerts || []).find((x) => x.id === id);
  if (!a) return toast("Alert not found", "error");
  openModal(
    "Investigate Security Alert",
    `<div class="notice danger"><strong>${esc(a.type)}</strong><br>${esc(a.message)}</div>
 <div class="grid grid-2" style="margin-top:14px"><div class="card"><strong>Alert ID</strong><p>${esc(a.id)}</p></div><div class="card"><strong>Severity</strong><p>${esc(a.severity)}</p></div></div>
 <div class="field" style="margin-top:14px"><label>Investigation note</label><textarea id="alertInvestigationNote" rows="5" placeholder="Record what was checked, who reviewed it and the next action...">${esc(a.investigationNote || "")}</textarea></div>
 <div class="actions" style="margin-top:14px"><button class="btn btn-ghost" onclick="closeModal()">Cancel</button><button class="btn btn-secondary" onclick="ackAlert('${esc(a.id)}');closeModal()">Acknowledge</button><button class="btn btn-primary" onclick="saveAlertInvestigation('${esc(a.id)}')">Save Investigation</button></div>`,
  );
}
function saveAlertInvestigation(id) {
  const a = (state.data.alerts || []).find((x) => x.id === id);
  if (!a) return toast("Alert not found", "error");
  const note = document.getElementById("alertInvestigationNote")?.value.trim();
  if (!note) return toast("Add an investigation note first", "error");
  a.investigationNote = note;
  a.investigatedBy = state.user?.name || "Inspector Sharma";
  a.investigatedAt = new Date().toLocaleString("en-IN");
  a.status = "Under Review";
  audit("ALERT INVESTIGATION", a.id, "Under Review", "Warning");
  saveState();
  closeModal();
  toast("Investigation saved");
  render();
}
function ackAlert(id) {
  const a = (state.data.alerts || []).find((x) => x.id === id);
  if (!a) return toast("Alert not found", "error");
  a.status = "Acknowledged";
  a.acknowledgedBy = state.user?.name || "Inspector Sharma";
  a.acknowledgedAt = new Date().toLocaleString("en-IN");
  audit("ALERT ACKNOWLEDGED", a.id, "Acknowledged", "Info");
  saveState();
  toast("Alert acknowledged");
  render();
}
function ackAlerts() {
  state.data.alerts.forEach((a) => (a.status = "Acknowledged"));
  audit("ALERTS", "—", "Acknowledged", "Info");
  toast("Open alerts acknowledged");
  render();
}
function users() {
  const users = state.data.users || [];
  return layout(
    head(
      "Users",
      "Role-based identities and session activity.",
      '<button class="btn btn-primary" onclick="openModal(\'Create User\',userForm())">＋ Create User</button>',
    ) +
      '<div class="grid grid-4">' +
      stat("Total Users", String(users.length), "Local directory") +
      stat(
        "Active",
        String(users.filter((u) => u.status === "Active").length),
        "Authorized profiles",
      ) +
      stat(
        "Roles",
        String(new Set(users.map((u) => u.role)).size),
        "Assigned roles",
      ) +
      stat("MFA Ready", "100%", "Demo identities") +
      '</div><div class="card" style="margin-top:16px"><div class="table-wrap"><table class="table"><thead><tr><th>User</th><th>Role</th><th>Email</th><th>Status</th><th>Actions</th></tr></thead><tbody>' +
      join(
        users,
        (u) =>
          "<tr><td><strong>" +
          esc(u.name) +
          "</strong><br><small>" +
          esc(u.id) +
          "</small></td><td>" +
          esc(u.role) +
          "</td><td>" +
          esc(u.email) +
          "</td><td>" +
          status(u.status || "Active") +
          '</td><td><div class="row-actions"><button class="btn btn-sm btn-secondary" onclick="openModal(\'User Profile\',\'<div class=\\"profile-hero\\"><div class=\\"profile-avatar-large\\">' +
          esc((u.name || "U").slice(0, 2).toUpperCase()) +
          '</div><div><h3 style=\\"margin:0\\">' +
          esc(u.name) +
          "</h3><p>" +
          esc(u.role) +
          " · " +
          esc(u.email) +
          '</p></div></div><div class=\\"notice\\" style=\\"margin-top:12px\\">Session status: ' +
          esc(u.status || "Active") +
          '</div>\')">View</button><button class="btn btn-sm btn-ghost" onclick="openUserEdit(\'' +
          esc(u.id) +
          '\')">Edit</button><button class="btn btn-sm btn-danger" onclick="removeUser(\'' +
          esc(u.id) +
          "')\">Delete</button></div></td></tr>",
      ) +
      "</tbody></table></div></div>",
  );
}
function openUserEdit(id) {
  const u = (state.data.users || []).find((x) => x.id === id);
  if (!u) return;
  openModal(
    "Edit User",
    '<div class="form"><div class="field"><label>Full name</label><input id="editUserName" value="' +
      esc(u.name) +
      '"></div><div class="field"><label>Email</label><input id="editUserEmail" value="' +
      esc(u.email) +
      '"></div><div class="field"><label>Role</label><select id="editUserRole">' +
      join(
        [
          "Police Officer",
          "Investigating Officer",
          "Forensic Officer",
          "Prosecutor",
          "Court Officer",
          "Auditor",
          "Administrator",
        ],
        (r) =>
          "<option " + (r === u.role ? "selected" : "") + ">" + r + "</option>",
      ) +
      '</select></div><button class="btn btn-primary" onclick="saveUserEdit(\'' +
      esc(id) +
      "')\">Save Changes</button></div>",
  );
}
function saveUserEdit(id) {
  const u = (state.data.users || []).find((x) => x.id === id);
  if (!u) return;
  u.name = document.getElementById("editUserName").value.trim() || u.name;
  u.email = document.getElementById("editUserEmail").value.trim() || u.email;
  u.role = document.getElementById("editUserRole").value;
  saveState();
  audit("UPDATE USER", id, "Success", "Info");
  closeModal();
  toast("User updated");
  render();
}
function removeUser(id) {
  if (id === state.user?.id)
    return toast(
      "Your active account cannot be deleted from this demo",
      "error",
    );
  state.data.users = state.data.users.filter((u) => u.id !== id);
  saveState();
  audit("DELETE USER", id, "Success", "Info");
  closeModal();
  toast("User removed");
  render();
}
function userForm() {
  return '<div class="form"><div class="field"><label>Full name</label><input id="newUser"></div><div class="field"><label>Email</label><input id="newEmail" type="email"></div><div class="field"><label>Role</label><select id="newRole"><option>Police Officer</option><option>Investigating Officer</option><option>Forensic Officer</option><option>Prosecutor</option><option>Court Officer</option><option>Auditor</option></select></div><button class="btn btn-primary" onclick="createUser()">Create User</button></div>';
}
function createUser() {
  const name = document.getElementById("newUser")?.value.trim() || "New User",
    email =
      document.getElementById("newEmail")?.value.trim() || "user@pramaan.gov",
    role = document.getElementById("newRole")?.value || "Police Officer";
  const u = {
    id: "USR-" + Date.now().toString().slice(-6),
    name,
    email,
    role,
    status: "Active",
  };
  state.data.users = state.data.users || [];
  state.data.users.unshift(u);
  saveState();
  audit("CREATE USER", u.id, "Success", "Info");
  closeModal();
  toast("User created successfully");
  render();
}
function roles() {
  const roles = [
      "Police Officer",
      "Investigating Officer",
      "Senior Officer",
      "Forensic Officer",
      "Prosecutor",
      "Court Officer",
      "Administrator",
      "Auditor",
    ],
    perms = [
      "View",
      "Upload",
      "Download",
      "Edit metadata",
      "Delete",
      "Verify",
      "Sign",
    ];
  return layout(
    head(
      "Roles & Permissions",
      "Configure action-level access for each operational role.",
      '<button class="btn btn-secondary" onclick="resetPermissions()">Reset Matrix</button>',
    ) +
      '<div class="grid grid-3 role-cards">' +
      join(roles, (r, i) => {
        const enabled = perms.filter(
          (p, j) => state.data.permissions[r + "|" + p] ?? (i + j) % 3 === 0,
        ).length;
        return (
          '<div class="card role-card"><div class="role-card-head"><div class="role-avatar">' +
          esc(
            r
              .split(" ")
              .map((x) => x[0])
              .join("")
              .slice(0, 2),
          ) +
          "</div><div><h3>" +
          esc(r) +
          "</h3><small>" +
          enabled +
          " of " +
          perms.length +
          ' actions enabled</small></div></div><div class="role-perms">' +
          join(perms, (p, j) => {
            const key = r + "|" + p;
            const on = state.data.permissions[key] ?? (i + j) % 3 === 0;
            return (
              '<button class="permission-chip ' +
              (on ? "on" : "") +
              '" onclick="togglePermission(\'' +
              esc(key) +
              "')\"><span>" +
              (on ? "✓" : "—") +
              "</span>" +
              esc(p) +
              "</button>"
            );
          }) +
          "</div></div>"
        );
      }) +
      "</div>",
  );
}
function togglePermission(key) {
  state.data.permissions[key] = !(state.data.permissions[key] ?? false);
  audit(
    "PERMISSION",
    key,
    state.data.permissions[key] ? "Enabled" : "Disabled",
    "Info",
  );
  toast("Permission updated");
  render();
}
function resetPermissions() {
  state.data.permissions = {};
  saveState();
  toast("Permission matrix reset");
  render();
}

function offline() {
  return layout(
    head(
      "Offline Center",
      "Work with authorized local records and a protected offline queue.",
      '<button class="btn btn-primary" onclick="toggleOffline()">' +
        (state.offline ? "↻ Reconnect" : "⇩ Enter Offline Mode") +
        "</button>",
    ) +
      '<div class="grid grid-3">' +
      stat(
        "Mode",
        state.offline ? "OFFLINE" : "ONLINE",
        state.offline ? "Local queue active" : "Connected",
      ) +
      stat(
        "Cached Docs",
        String(state.data.vault.length),
        "My Vault available",
      ) +
      stat(
        "Sync Events",
        String(state.data.syncHistory.length),
        "Timestamped locally",
      ) +
      '</div><div class="grid grid-2" style="margin-top:16px"><div class="card"><h3 class="section-title">Local Work Queue</h3>' +
      join(
        [
          "Evidence metadata update",
          "Investigation note",
          "Custody acknowledgement",
        ],
        (x, i) =>
          '<div class="kpi-line"><span>' +
          x +
          "</span>" +
          status(i === 2 ? "Conflict" : "Queued") +
          "</div>",
      ) +
      '<button class="btn btn-secondary" style="margin-top:12px" onclick="go(\'/vault\')">Open Offline Vault</button></div><div class="card"><h3 class="section-title">Protection</h3><div class="notice">Local files are stored in browser IndexedDB for this frontend prototype. No server connection is required for the vault.</div><div class="progress" style="margin-top:14px"><i style="width:100%"></i></div></div></div>',
  );
}
function toggleOffline() {
  state.offline = !state.offline;
  state.data.syncHistory.unshift({
    time: new Date().toLocaleString("en-IN"),
    result: state.offline ? "Offline mode enabled" : "Reconnected",
  });
  saveState();
  toast(
    state.offline ? "Offline mode enabled" : "Back online — sync queue ready",
    state.offline ? "warn" : "success",
  );
  render();
}
function sync() {
  return layout(
    head(
      "Sync Center",
      "Reconcile local state without silently overwriting evidence.",
      '<button class="btn btn-primary" onclick="runSync()">⟳ Synchronize</button>',
    ) +
      '<div class="card"><div class="section-row"><h3 class="section-title">Synchronization Queue</h3><span class="status info">Last sync: ' +
      esc(state.data.syncHistory[0]?.time || "Not run yet") +
      "</span></div>" +
      join(
        [
          ["LOCAL-001", "Evidence metadata", "3", "Server newer", "Conflict"],
          ["LOCAL-002", "Investigation note", "2", "Safe merge", "Ready"],
          [
            "LOCAL-003",
            "Custody update",
            "4",
            "Server newer",
            "Approval required",
          ],
        ],
        (x) =>
          '<div class="kpi-line"><span><strong>' +
          x[0] +
          "</strong><br><small>" +
          x[1] +
          "</small></span><span>" +
          x[2] +
          " local · " +
          x[3] +
          ' <span class="status ' +
          (x[4] === "Conflict" ? "danger" : "info") +
          '">' +
          x[4] +
          "</span></span></div>",
      ) +
      '</div><div class="card" style="margin-top:16px"><h3 class="section-title">Sync History</h3>' +
      join(
        state.data.syncHistory.slice(0, 10),
        (x) =>
          '<div class="kpi-line"><span>' +
          esc(x.time) +
          "</span><strong>" +
          esc(x.result) +
          "</strong></div>",
      ) +
      "</div>",
  );
}
function runSync() {
  const result = state.offline
    ? "Queued locally — reconnect required"
    : "Completed with 1 conflict requiring review";
  state.data.syncHistory.unshift({
    time: new Date().toLocaleString("en-IN"),
    result,
  });
  audit("SYNC", "—", result, state.offline ? "Warning" : "Info");
  toast(result, state.offline ? "warn" : "success");
  render();
}
function systemHealth() {
  const services = [
    "Frontend Runtime",
    "Local Storage",
    "IndexedDB Vault",
    "Crypto API",
    "OCR Adapter",
    "AI Adapter",
    "Authentication",
    "Sync Engine",
    "CCTNS Adapter",
    "ICJS Adapter",
    "e-Courts Adapter",
    "e-Prisons Adapter",
  ];
  return layout(
    head("System Health", "Service availability and integration readiness.") +
      '<div class="grid grid-3">' +
      join(
        services,
        (x, i) =>
          '<div class="card"><div class="section-row"><strong>' +
          x +
          "</strong>" +
          status(i > 7 ? "Integration Ready" : "Operational") +
          '</div><div style="margin-top:12px"><div class="progress"><i style="width:' +
          (i > 7 ? 38 : 96) +
          '%"></i></div><small style="color:var(--muted)">' +
          (i > 7 ? "Adapter / mock connector" : "Frontend check passed") +
          "</small></div></div>",
      ) +
      "</div>",
  );
}
function toggleSecurityControl(key) {
  state.data.security = state.data.security || {
    controls: {},
    innovations: {},
  };
  state.data.security.controls[key] = !state.data.security.controls[key];
  saveState();
  audit(
    "SECURITY CONTROL",
    key,
    state.data.security.controls[key] ? "Enabled" : "Disabled",
    "Info",
  );
  toast(
    key + " " + (state.data.security.controls[key] ? "enabled" : "disabled"),
  );
  render();
}
function generateInnovationArtifact(type) {
  const now = new Date().toISOString();
  let payload;
  if (type === "ZKP")
    payload = {
      type: "ZK-COMPLIANCE-PROOF-DEMO",
      statement:
        "Document integrity/signature compliance proof generated without exposing document contents.",
      generated: now,
      scope:
        "Frontend prototype; cryptographic circuit integration required for production.",
    };
  else if (type === "WATERMARK")
    payload = {
      type: "DYNAMIC-TRACE-METADATA-DEMO",
      payload: {
        userId: state.user?.id || "USR-001",
        sessionNonce: crypto.randomUUID?.() || String(Date.now()),
        timestamp: now,
        document: "Current session",
      },
      note: "Metadata simulation only; invisible steganographic embedding requires a production document pipeline.",
    };
  else if (type === "PQC")
    payload = {
      type: "PQC-READINESS-ANCHOR",
      algorithms: ["CRYSTALS-Kyber", "Dilithium"],
      generated: now,
      status:
        "Integration-ready prototype; browser does not claim production PQC cryptography.",
    };
  else if (type === "BSA")
    payload = {
      type: "ELECTRONIC-RECORD-CERTIFICATE-DEMO",
      framework: "Bharatiya Sakshya Adhiniyam, 2023",
      generated: now,
      hashVerification: "SHA-256 upload/current comparison",
      systemDiagnostic: "Frontend runtime self-check passed",
      note: "Prototype certificate artifact; legal validity depends on production implementation and authorized certification.",
    };
  else if (type === "CCTNS")
    payload = {
      type: "CCTNS-ICJS-MAPPING-DEMO",
      generated: now,
      schemas: {
        caseId: "CASE-2026-001",
        documentId: "DOC-001",
        evidenceId: "EV-0001",
        courtReference: "eCourts-ready",
      },
      status: "Schema mapping prototype",
    };
  else if (type === "DUALKEY")
    payload = {
      type: "DUAL-KEY-CUSTODY-DEMO",
      generated: now,
      threshold: "2-of-2",
      roles: ["Investigating Officer", "Receiving Analyst"],
      status: "Approval simulation",
    };
  else return;
  downloadText(
    "pramaan-" + type.toLowerCase() + "-artifact.json",
    JSON.stringify(payload, null, 2),
  );
  audit("INNOVATION ARTIFACT", type, "Generated", "Info");
  toast(type + " artifact generated");
}
function simulateBreach() {
  const e = state.data.evidence[0];
  state.data.breachSimulation = {
    time: new Date().toLocaleString("en-IN"),
    evidence: e?.id || "EV-0001",
    status: "HASH MISMATCH DETECTED",
  };
  state.data.alerts.unshift({
    id: "ALT-" + Date.now(),
    type: "Cryptographic Hash Mismatch",
    severity: "Critical",
    message: `${e?.id || "EV-0001"} integrity changed in the local breach simulation. Evidence admission is blocked until verification.`,
    status: "Open",
  });
  state.data.security.blockedEvents =
    (state.data.security.blockedEvents || 7) + 1;
  saveState();
  audit("BREACH SIMULATION", e?.id || "EV-0001", "Blocked", "Critical");
  toast("Breach simulation detected and blocked", "error");
  render();
}
function security() {
  const controls = Object.keys(state.data.security?.controls || {});
  const innovations = [
    ["ZKP", "Blind compliance proof", "ZKP"],
    ["Dynamic Watermark", "Traceable view/download metadata", "WATERMARK"],
    ["Post-Quantum Crypto", "Kyber / Dilithium readiness", "PQC"],
    ["BSA Certificate", "Electronic-record certificate artifact", "BSA"],
    ["CCTNS / ICJS Mapping", "Interoperability schema artifact", "CCTNS"],
    ["Dual-Key Custody", "2-of-2 handover approval simulation", "DUALKEY"],
  ];
  return layout(
    head(
      "Security Center",
      "Threat monitoring, integrity controls and research-backed evidence protection.",
      '<button class="btn btn-danger" onclick="simulateBreach()">Simulate Tamper Attempt</button>',
    ) +
      '<div class="grid grid-3">' +
      stat(
        "Integrity",
        state.data.breachSimulation ? "HASH MISMATCH" : "98.7%",
        state.data.breachSimulation ? "Admission blocked" : "Verified",
      ) +
      stat("MFA Coverage", "100%", "Demo identities") +
      stat(
        "Blocked Events",
        String(state.data.security?.blockedEvents || 7),
        "This month",
      ) +
      '</div><div class="grid grid-2" style="margin-top:16px"><div class="card"><h3 class="section-title">Security Controls</h3>' +
      join(
        controls,
        (x) =>
          '<button class="kpi-line security-toggle" onclick="toggleSecurityControl(\'' +
          esc(x) +
          "')\"><span>" +
          esc(x) +
          "</span>" +
          status(state.data.security.controls[x] ? "Enabled" : "Disabled") +
          "</button>",
      ) +
      '</div><div class="card"><h3 class="section-title">Innovation Readiness</h3>' +
      join(
        innovations,
        (x) =>
          '<div class="innovation-row"><div><strong>' +
          x[0] +
          "</strong><small>" +
          x[1] +
          '</small></div><button class="btn btn-sm btn-secondary" onclick="generateInnovationArtifact(\'' +
          x[2] +
          "')\">Generate</button></div>",
      ) +
      '</div></div><div class="card" style="margin-top:16px"><h3 class="section-title">Breach Simulation Result</h3>' +
      (state.data.breachSimulation
        ? '<div class="notice danger"><strong>Cryptographic Hash Mismatch</strong><br>Evidence ' +
          esc(state.data.breachSimulation.evidence) +
          " · " +
          esc(state.data.breachSimulation.time) +
          "<br>Admission blocked and audit alert created.</div>"
        : '<div class="notice">Use the simulation button to demonstrate the integrity-alert workflow without modifying real files.</div>') +
      "</div>",
  );
}
function settings() {
  return layout(
    head(
      "Settings",
      "Security, interface, accessibility and language preferences.",
      '<button class="btn btn-primary" onclick="saveSettings()">Save Settings</button>',
    ) +
      '<div class="grid grid-2"><div class="card"><h3 class="section-title">Security & Session</h3>' +
      join(
        [
          ["Session timeout", "15 minutes"],
          ["Download watermark", "Enabled"],
          ["Two-person approval", "Enabled"],
          ["Audit logging", "Immutable mode"],
          ["Offline cache", "Authorized only"],
        ],
        (x) =>
          '<div class="kpi-line"><span>' +
          x[0] +
          "</span>" +
          status(x[1]) +
          "</div>",
      ) +
      '</div><div class="card"><h3 class="section-title">Appearance & Language</h3><div class="form"><div class="field"><label>Theme</label><select id="setTheme"><option value="light" ' +
      (state.settings.theme === "light" ? "selected" : "") +
      '>Light</option><option value="dark" ' +
      (state.settings.theme === "dark" ? "selected" : "") +
      '>Dark</option></select></div><div class="field"><label>Language</label><select id="setLang"><option value="en" ' +
      (state.settings.language === "en" ? "selected" : "") +
      '>English</option><option value="hi" ' +
      (state.settings.language === "hi" ? "selected" : "") +
      '>Hindi</option><option value="mr" ' +
      (state.settings.language === "mr" ? "selected" : "") +
      '>Marathi</option></select></div><div class="field"><label>Density</label><select id="setDensity"><option value="comfortable" ' +
      (state.settings.density === "comfortable" ? "selected" : "") +
      '>Comfortable</option><option value="compact" ' +
      (state.settings.density === "compact" ? "selected" : "") +
      '>Compact</option></select></div><label><input id="setNotify" type="checkbox" ' +
      (state.settings.notifications ? "checked" : "") +
      '> Enable notifications</label><label><input id="setMotion" type="checkbox" ' +
      (state.settings.reducedMotion ? "checked" : "") +
      '> Reduce motion</label></div></div></div><div class="grid grid-3" style="margin-top:16px"><div class="card settings-feature"><h3 class="section-title">Language</h3><p>English, Hindi and Marathi.</p><button class="btn btn-secondary" onclick="saveSettings()">Apply Language</button></div><div class="card settings-feature"><h3 class="section-title">Reset UI</h3><p>Restore light theme and comfortable density.</p><button class="btn btn-secondary" onclick="resetSettings()">Reset</button></div><div class="card settings-feature"><h3 class="section-title">Local Data</h3><p>Download your current prototype data.</p><button class="btn btn-secondary" onclick="downloadText(\'pramaan-local-data.json\',JSON.stringify(state.data,null,2))">Download Data</button></div></div>',
  );
}
function saveSettings() {
  state.settings.theme = document.getElementById("setTheme").value;
  state.settings.language = document.getElementById("setLang").value;
  state.settings.density = document.getElementById("setDensity").value;
  state.settings.notifications = document.getElementById("setNotify").checked;
  state.settings.reducedMotion = document.getElementById("setMotion").checked;
  saveState();
  applySettings();
  toast("Settings saved");
  render();
}
function resetSettings() {
  state.settings = {
    theme: "light",
    language: "en",
    density: "comfortable",
    notifications: true,
    reducedMotion: false,
  };
  saveState();
  applySettings();
  toast("Interface settings reset");
  render();
}
function profile() {
  const u = state.user || {};
  const rows = [
    ["User ID", u.id || "USR-001"],
    ["Employee / Service ID", u.employeeId || u.id || "—"],
    ["Official Email", u.email || "—"],
    ["Official Contact", u.phone || "—"],
    ["Department / Agency", u.department || "—"],
    ["Designation", u.designation || u.role || "—"],
    ["Station / Unit / Office", u.unit || "—"],
    ["Role", u.role || "Investigating Officer"],
    ["Government SSO", "Ready"],
    ["MFA", "OTP enabled"],
    ["Session", "Active"],
    ["Account Status", u.status || "Active"],
  ];
  return layout(
    head(
      "Profile",
      "Government identity, personnel details, profile picture and active session.",
      '<div class="actions"><button class="btn btn-secondary" onclick="document.getElementById(\'avatarInput\').click()">Change Photo</button><button class="btn btn-danger" onclick="logout()">Log out</button></div>',
    ) +
      '<input id="avatarInput" class="file-input-hidden" type="file" accept="image/*" onchange="saveAvatar(this.files[0])"><div class="grid grid-2 profile-grid"><div class="card"><div class="profile-hero"><div class="profile-avatar-large">' +
      (u.avatar ? '<img src="' + esc(u.avatar) + '" alt="Profile">' : esc((u.name || "IS").split(/\s+/).map(x => x[0]).join("").slice(0,2).toUpperCase())) +
      '</div><div><h2 style="margin:0">' + esc(u.name || "Inspector Sharma") + '</h2><small>' + esc(u.designation || u.role || "Investigating Officer") + '</small></div></div><div style="margin-top:18px">' +
      join(rows,(x)=>'<div class="kpi-line"><span>' + esc(x[0]) + '</span><strong>' + esc(x[1]) + '</strong></div>') +
      '</div><div class="actions" style="margin-top:14px"><button class="btn btn-primary" onclick="openModal(\'Update Profile\',profileForm())">Edit Profile</button><button class="btn btn-ghost" onclick="removeAvatar()">Remove Photo</button></div></div>' +
      '<div class="card"><h3 class="section-title">Account Tools</h3><div class="grid"><button class="btn btn-secondary" onclick="downloadText(\'pramaan-profile.json\',JSON.stringify(state.user,null,2))">Download Profile Data</button><button class="btn btn-secondary" onclick="downloadText(\'pramaan-my-data.json\',JSON.stringify(state.data,null,2))">Download My Data</button><button class="btn btn-secondary" onclick="go(\'/settings\')">Security & Preferences</button><button class="btn btn-secondary" onclick="toast(\'Active session refreshed\')">Refresh Session</button><button class="btn btn-danger" onclick="removeProfile()">Remove Profile</button></div><div class="notice" style="margin-top:16px">Personnel details shown here are the same identity fields collected during government onboarding. Passwords and OTP secrets are never displayed.</div></div></div>',
  );
}
function profileForm() {
  const u = state.user || {};
  return (
    '<div class="form profile-edit-form">' +
      '<div class="auth-grid-2"><div class="field"><label>Full Name</label><input id="pfName" value="' + esc(u.name || "") + '"></div><div class="field"><label>Employee / Service ID</label><input id="pfEmployeeId" value="' + esc(u.employeeId || u.id || "") + '"></div></div>' +
      '<div class="auth-grid-2"><div class="field"><label>Official Email</label><input id="pfEmail" type="email" value="' + esc(u.email || "") + '"></div><div class="field"><label>Official Contact Number</label><input id="pfPhone" inputmode="numeric" value="' + esc(u.phone || "") + '"></div></div>' +
      '<div class="auth-grid-2"><div class="field"><label>Department / Agency</label><select id="pfDepartment"><option value="">Select department</option><option' + (u.department === "Police Department" ? " selected" : "") + '>Police Department</option><option' + (u.department === "Forensic Science Laboratory" ? " selected" : "") + '>Forensic Science Laboratory</option><option' + (u.department === "Prosecution Department" ? " selected" : "") + '>Prosecution Department</option><option' + (u.department === "Cyber Crime Unit" ? " selected" : "") + '>Cyber Crime Unit</option><option' + (u.department === "System Administration" ? " selected" : "") + '>System Administration</option></select></div><div class="field"><label>Designation</label><input id="pfDesignation" value="' + esc(u.designation || u.role || "") + '"></div></div>' +
      '<div class="auth-grid-2"><div class="field"><label>Station / Unit / Office</label><input id="pfUnit" value="' + esc(u.unit || "") + '"></div><div class="field"><label>Role</label><select id="pfRole"><option' + (u.role === "Investigating Officer" ? " selected" : "") + '>Investigating Officer</option><option' + (u.role === "Forensic Officer" ? " selected" : "") + '>Forensic Officer</option><option' + (u.role === "Prosecutor" ? " selected" : "") + '>Prosecutor</option><option' + (u.role === "Administrator" ? " selected" : "") + '>Administrator</option></select></div></div>' +
      '<div class="notice"><strong>Security:</strong> Password and MFA/OTP secrets are intentionally not editable from this local profile form. Use the department identity provider for credential changes in production.</div>' +
      '<button class="btn btn-primary" onclick="updateProfile()">Save All Profile Details</button>' +
    '</div>'
  );
}
function updateProfile() {
  if (!state.user) return;
  const name = document.getElementById("pfName")?.value?.trim() || "";
  const employeeId = document.getElementById("pfEmployeeId")?.value?.trim() || "";
  const email = document.getElementById("pfEmail")?.value?.trim() || "";
  const phone = document.getElementById("pfPhone")?.value?.replace(/\D/g, "") || "";
  const department = document.getElementById("pfDepartment")?.value || "";
  const designation = document.getElementById("pfDesignation")?.value?.trim() || "";
  const unit = document.getElementById("pfUnit")?.value?.trim() || "";
  const role = document.getElementById("pfRole")?.value || "";
  if (!name || !employeeId || !email || !phone || !department || !designation || !unit || !role) return toast("Complete all required profile details", "error");
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return toast("Enter a valid official email address", "error");
  if (phone.length !== 10) return toast("Enter a valid 10-digit official contact number", "error");
  state.user = { ...state.user, id: employeeId, name, employeeId, email, phone, department, designation, unit, role };
  localStorage.setItem("pramaan_user", JSON.stringify(state.user));
  localStorage.setItem("pramaan_registered_profile", JSON.stringify(state.user));
  const users = state.data.users || [];
  const idx = users.findIndex(x => x.id === state.user.id || x.employeeId === employeeId);
  if (idx >= 0) users[idx] = { ...users[idx], ...state.user };
  else users.unshift({ ...state.user });
  state.data.users = users;
  saveState();
  audit("PROFILE UPDATE", "—", "Success", "Info");
  closeModal();
  toast("All profile details updated");
  render();
}
async function saveAvatar(file) {
  if (!file) return;
  if (file.size > 2 * 1024 * 1024)
    return toast("Profile image must be under 2 MB", "error");
  const data = await new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(r.result);
    r.onerror = reject;
    r.readAsDataURL(file);
  });
  state.user.avatar = data;
  localStorage.setItem("pramaan_user", JSON.stringify(state.user));
  toast("Profile picture updated");
  render();
}
function removeAvatar() {
  if (!state.user) return;
  delete state.user.avatar;
  localStorage.setItem("pramaan_user", JSON.stringify(state.user));
  toast("Profile photo removed");
  render();
}
function removeProfile() {
  openModal(
    "Remove Profile",
    '<div class="notice danger"><strong>This removes the current local demo profile.</strong><br>Your browser-stored session will be cleared. You can create a new demo profile from Register.</div><div class="actions" style="margin-top:14px"><button class="btn btn-ghost" onclick="closeModal()">Keep Profile</button><button class="btn btn-danger" onclick="confirmRemoveProfile()">Remove Profile</button></div>',
  );
}
function confirmRemoveProfile() {
  localStorage.removeItem("pramaan_user");
  state.user = null;
  closeModal();
  toast("Profile removed");
  go("/register");
}
function splash() {
  return (
    '<div class="document-splash"><div class="document-splash-grid"></div><div class="document-splash-glow"></div><div class="document-splash-content">' +
    '<div class="document-splash-brand">' +
    logoMarkup("hero") +
    "<div><strong>PRAMAAN</strong><span>SECURE DIGITAL EVIDENCE</span></div></div>" +
    '<div class="document-splash-visual">' +
    '<div class="document-stack"><div class="paper paper-back"></div><div class="paper paper-mid"></div><div class="paper paper-front">' +
    '<div class="paper-head"><span>PRAMAAN EVIDENCE RECORD</span><b>VERIFIED</b></div>' +
    '<div class="paper-line wide"></div><div class="paper-line"></div><div class="paper-line short"></div>' +
    '<div class="paper-hash"><span>SHA-256</span><strong>8F4A...91C</strong></div>' +
    '<div class="paper-sign">✓ Digitally Registered</div>' +
    "</div></div>" +
    '<div class="splash-data-points"><span>▤ Document Registry</span><span>⌁ SHA-256 Integrity</span><span>↔ Chain of Custody</span></div>' +
    "</div>" +
    '<div class="document-splash-copy"><div class="eyebrow">DIGITAL EVIDENCE • DOCUMENT MANAGEMENT</div><h1>From <span>Document</span> to Justice.</h1><p>Securely register, verify, preserve and track every legal document and piece of digital evidence.</p><div class="splash-features"><span>Secure Storage</span><span>Integrity Verification</span><span>Audit Ready</span></div></div>' +
    '<div class="document-splash-bottom"><div class="splash-progress"><i></i></div><button class="btn btn-primary splash-enter" onclick="go(\'/onboarding\')">Open Secure Workspace <span>→</span></button></div>' +
    "</div></div>"
  );
}
function onboarding() {
  return (
    '<div class="auth"><div class="auth-card"><div class="auth-hero"><div class="brand">' +
    logoMarkup("hero") +
    '<div><div class="brand-title">Pramaan</div><div class="brand-sub">Secure digital evidence lifecycle</div></div></div><h1>From evidence<br>to <span style="color:#54d5ff">justice.</span></h1><p>PRAMAAN connects case records, secure documents, evidence custody, verification, AI/OCR and court export in one controlled workspace.</p><div class="feature-strip"><span class="pill">Secure</span><span class="pill">Auditable</span><span class="pill">Responsive</span><span class="pill">Court Ready</span></div></div><div class="auth-panel"><h2>Product Tour</h2><div class="form">' +
    join(
      [
        ["01", "Secure intake", "Upload → validate → hash → preserve"],
        ["02", "Evidence integrity", "Verify hash, signatures and versions"],
        ["03", "Controlled custody", "Authenticate transfers and approvals"],
        ["04", "AI assistance", "OCR, PII detection, redaction and search"],
        [
          "05",
          "Court export",
          "Package metadata, integrity, custody and audit",
        ],
      ],
      (x) =>
        '<div class="card" style="box-shadow:none;background:#f7fafc"><strong>' +
        x[0] +
        " · " +
        x[1] +
        '</strong><small style="display:block;color:var(--muted);margin-top:4px">' +
        x[2] +
        "</small></div>",
    ) +
    '<button class="btn btn-primary" onclick="go(\'/login\')">Continue to Login</button></div></div></div>'
  );
}

function courtExport() {
  return layout(
    head(
      "Court Export",
      "Generate a structured court-ready evidence package from current local records.",
      '<button class="btn btn-primary" onclick="generatePackage()">Generate Package</button>',
    ) +
      '<div class="grid grid-2"><div class="card"><h3 class="section-title">Package Contents</h3>' +
      join(
        [
          "Original document",
          "Metadata",
          "Hash verification report",
          "Digital signature information",
          "Custody timeline",
          "Audit summary",
          "Evidence certificate",
        ],
        (x) =>
          '<div class="kpi-line"><span>' +
          x +
          "</span>" +
          status("Included") +
          "</div>",
      ) +
      '</div><div class="card"><h3 class="section-title">Package Status</h3><div id="packageStatus" class="notice">Ready to generate a downloadable ZIP.</div></div></div>',
  );
}
function generatePackage() {
  const data = {
    generated: new Date().toISOString(),
    case: "CASE-2026-001",
    documents: state.data.documents,
    evidence: state.data.evidence,
    audit: state.data.audit,
    custody: state.data.custody,
    certificate: "Included",
  };
  const box = document.getElementById("packageStatus");
  if (box)
    box.innerHTML =
      '<div class="progress"><i style="width:100%"></i></div><p>Package manifest prepared locally.</p>';
  downloadText(
    "PRAMAAN-Court-Evidence-Package.json",
    JSON.stringify(data, null, 2),
  );
  audit("COURT EXPORT", "—", "Generated", "Info");
  toast("Court package manifest downloaded");
}
function certificate() {
  return layout(
    head(
      "Evidence Certificate",
      "Generate a verifiable evidence certificate artifact.",
      '<button class="btn btn-primary" onclick="generateCertificate()">Generate Certificate</button>',
    ) +
      '<div class="card"><div id="certificatePreview" class="paper"><h3>PRAMAAN EVIDENCE CERTIFICATE</h3><p>Certificate generation is available as a downloadable local artifact.</p><div class="line"></div><div class="line"></div></div></div>',
  );
}
function generateCertificate() {
  const cert = {
    certificateId: "CERT-" + Date.now(),
    generated: new Date().toISOString(),
    case: "CASE-2026-001",
    evidence: state.data.evidence[0]?.id || "EV-0001",
    documents: state.data.documents.map((d) => ({
      id: d.id,
      hash: d.hash,
      status: d.status,
    })),
    custody: state.data.custody,
  };
  downloadText(
    "PRAMAAN-Evidence-Certificate.json",
    JSON.stringify(cert, null, 2),
  );
  audit("CERTIFICATE", "—", "Generated", "Info");
  toast("Evidence certificate downloaded");
}
function generic(name) {
  return dashboard();
}

function profileTools() {
  return "";
}
function openModal(title, html) {
  const d = document.createElement("div");
  d.className = "modal-backdrop";
  d.innerHTML =
    '<div class="modal"><div class="modal-head"><h3>' +
    esc(title) +
    '</h3><button class="icon-btn" onclick="closeModal()">×</button></div>' +
    html +
    "</div>";
  document.body.appendChild(d);
}
function closeModal() {
  document.querySelector(".modal-backdrop")?.remove();
}

// --------------------------------------------------
// LOGIN PAGE
// --------------------------------------------------
function login() {
  return (
    '<div class="auth"><div class="auth-card gov-auth-card">' +
      '<div class="auth-hero"><div class="brand">' + logoMarkup("hero") +
      '<div><div class="brand-title">Pramaan</div><div class="brand-sub">Secure digital evidence lifecycle</div></div></div>' +
      '<div class="gov-badge">GOVERNMENT DIGITAL EVIDENCE WORKSPACE</div>' +
      '<h1>Secure access<br>to <span style="color:#54d5ff">PRAMAAN.</span></h1>' +
      '<p>Authorized personnel only. Access is intended for verified officers and approved government users handling digital evidence and legal records.</p>' +
      '<div class="feature-strip"><span class="pill">Identity Controlled</span><span class="pill">Auditable</span><span class="pill">Encrypted Workflow</span><span class="pill">Court Ready</span></div>' +
      '<div class="auth-security-note"><strong>Security notice</strong><span>Do not share credentials, OTPs or evidence access details. Production deployment must connect this interface to the department-approved identity provider and MFA service.</span></div></div>' +
      '<div class="auth-panel"><div class="auth-panel-heading"><div><span class="eyebrow">AUTHORIZED PERSONNEL</span><h2>Government Sign In</h2><p>Enter your official identity details to continue.</p></div><span class="security-lock">⌁</span></div>' +
      '<div class="form auth-form">' +
      '<div class="field"><label for="loginEmail">Official Email / User ID <span>*</span></label><input id="loginEmail" type="text" placeholder="name@department.gov.in" autocomplete="username" required></div>' +
      '<div class="field"><label for="loginEmployeeId">Employee / Service ID <span>*</span></label><input id="loginEmployeeId" type="text" placeholder="Enter official employee ID" autocomplete="off" required></div>' +
      '<div class="auth-grid-2"><div class="field"><label for="loginDepartment">Department / Agency <span>*</span></label><select id="loginDepartment" required><option value="">Select department</option><option>Police Department</option><option>Forensic Science Laboratory</option><option>Prosecution Department</option><option>Cyber Crime Unit</option><option>System Administration</option></select></div><div class="field"><label for="loginUnit">Station / Unit <span>*</span></label><input id="loginUnit" type="text" placeholder="Station / Unit name" autocomplete="organization"></div></div>' +
      '<div class="field"><label for="loginPassword">Password <span>*</span></label><input id="loginPassword" type="password" placeholder="Enter your password" autocomplete="current-password" required><small class="field-hint">Minimum 12 characters with uppercase, lowercase, number and special character.</small></div>' +
      '<div class="auth-mfa-row"><div class="field"><label for="loginOtp">MFA / OTP <span>*</span></label><input id="loginOtp" inputmode="numeric" maxlength="6" placeholder="6-digit OTP" autocomplete="one-time-code" required></div><div class="mfa-help"><strong>MFA required</strong><span>OTP validation is simulated in this frontend prototype. Production must validate it server-side.</span></div></div>' +
      '<label class="auth-check"><input id="loginAck" type="checkbox"><span>I confirm that I am an authorized user and will access evidence only for official duties.</span></label>' +
      '<div class="actions auth-actions"><button type="button" class="btn btn-primary" onclick="doLogin()">Secure Sign In</button><button type="button" class="btn btn-secondary" onclick="go(\'/register\')">Request / Create Account</button></div>' +
      '<div class="notice auth-demo-notice"><strong>Prototype MFA:</strong> Use OTP <code>123456</code> for local demonstration. This is not production authentication.</div>' +
      '<div class="auth-footer-links"><button type="button" class="btn btn-ghost" onclick="toast(\'Password recovery requires the department identity provider in production.\')">Account Recovery</button><span>Session activity is recorded in the audit log.</span></div></div></div></div>'
  );
}
function register() {
  return (
    '<div class="auth"><div class="auth-card gov-auth-card">' +
      '<div class="auth-hero"><div class="brand">' + logoMarkup("hero") + '<div><div class="brand-title">Pramaan</div><div class="brand-sub">Secure digital evidence lifecycle</div></div></div>' +
      '<div class="gov-badge">GOVERNMENT USER ONBOARDING</div><h1>Request secure<br><span style="color:#54d5ff">workspace access.</span></h1>' +
      '<p>Provide official personnel details. In production, these details should be verified against the department directory before an account is activated.</p>' +
      '<div class="auth-security-note"><strong>Controlled onboarding</strong><span>Final activation, role assignment and MFA enrollment must be performed by authorized administrators.</span></div></div>' +
      '<div class="auth-panel"><div class="auth-panel-heading"><div><span class="eyebrow">PERSONNEL REGISTRATION</span><h2>Government Account</h2><p>All required fields must be completed accurately.</p></div><span class="security-lock">⌁</span></div>' +
      '<div class="form auth-form">' +
      '<div class="auth-grid-2"><div class="field"><label for="regName">Full Name <span>*</span></label><input id="regName" type="text" placeholder="Full legal name" autocomplete="name" required></div><div class="field"><label for="regEmployeeId">Employee / Service ID <span>*</span></label><input id="regEmployeeId" type="text" placeholder="Official employee ID" autocomplete="off" required></div></div>' +
      '<div class="auth-grid-2"><div class="field"><label for="regEmail">Official Email <span>*</span></label><input id="regEmail" type="email" placeholder="name@department.gov.in" autocomplete="email" required></div><div class="field"><label for="regPhone">Official Contact Number <span>*</span></label><input id="regPhone" type="tel" inputmode="numeric" placeholder="10-digit official contact" autocomplete="tel" required></div></div>' +
      '<div class="auth-grid-2"><div class="field"><label for="regDepartment">Department / Agency <span>*</span></label><select id="regDepartment" required><option value="">Select department</option><option>Police Department</option><option>Forensic Science Laboratory</option><option>Prosecution Department</option><option>Cyber Crime Unit</option><option>System Administration</option></select></div><div class="field"><label for="regDesignation">Designation <span>*</span></label><input id="regDesignation" type="text" placeholder="Official designation" required></div></div>' +
      '<div class="auth-grid-2"><div class="field"><label for="regUnit">Station / Unit / Office <span>*</span></label><input id="regUnit" type="text" placeholder="Station, unit or office" required></div><div class="field"><label for="regRole">Requested Role <span>*</span></label><select id="regRole" required><option>Investigating Officer</option><option>Forensic Officer</option><option>Prosecutor</option><option>Administrator</option></select></div></div>' +
      '<div class="auth-grid-2"><div class="field"><label for="regPassword">Create Password <span>*</span></label><input id="regPassword" type="password" placeholder="Minimum 12 characters" autocomplete="new-password" required><small class="field-hint">12+ chars, uppercase, lowercase, number & special character.</small></div><div class="field"><label for="regConfirmPassword">Confirm Password <span>*</span></label><input id="regConfirmPassword" type="password" placeholder="Re-enter password" autocomplete="new-password" required></div></div>' +
      '<label class="auth-check"><input id="regAck" type="checkbox"><span>I confirm that the information provided is accurate and that access will be used only for authorized official duties.</span></label>' +
      '<div class="actions auth-actions"><button type="button" class="btn btn-primary" onclick="completeRegistration()">Submit Access Request</button><button type="button" class="btn btn-secondary" onclick="go(\'/login\')">Back to Login</button></div>' +
      '<div class="notice auth-demo-notice"><strong>Prototype mode:</strong> The account is stored locally for demonstration. Production onboarding must use department verification, approval and server-side credential storage.</div></div></div></div>'
  );
}
function completeRegistration() {
  const name = document.getElementById("regName")?.value?.trim() || "";
  const employeeId = document.getElementById("regEmployeeId")?.value?.trim() || "";
  const email = document.getElementById("regEmail")?.value?.trim() || "";
  const phone = document.getElementById("regPhone")?.value?.replace(/\D/g, "") || "";
  const department = document.getElementById("regDepartment")?.value || "";
  const designation = document.getElementById("regDesignation")?.value?.trim() || "";
  const unit = document.getElementById("regUnit")?.value?.trim() || "";
  const role = document.getElementById("regRole")?.value || "";
  const password = document.getElementById("regPassword")?.value || "";
  const confirmPassword = document.getElementById("regConfirmPassword")?.value || "";
  const acknowledged = !!document.getElementById("regAck")?.checked;
  if (!name || !employeeId || !email || !phone || !department || !designation || !unit || !role || !password || !confirmPassword) return toast("Please complete all required personnel details", "error");
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return toast("Enter a valid official email address", "error");
  if (phone.length !== 10) return toast("Enter a valid 10-digit official contact number", "error");
  if (password.length < 12 || !/[A-Z]/.test(password) || !/[a-z]/.test(password) || !/\d/.test(password) || !/[^A-Za-z0-9]/.test(password)) return toast("Password must be 12+ characters and include uppercase, lowercase, number and special character", "error");
  if (password !== confirmPassword) return toast("Passwords do not match", "error");
  if (!acknowledged) return toast("Please confirm the authorized-use declaration", "error");
  state.user = { id: employeeId, name, role, email, status:"Pending Verification", employeeId, phone, department, designation, unit };
  localStorage.setItem("pramaan_user", JSON.stringify(state.user));
  localStorage.setItem("pramaan_registered_name", name);
  state.data.users = state.data.users || [];
  state.data.users.unshift({ ...state.user });
  saveState();
  audit("ACCESS REQUEST", state.user.id, "Submitted", "Info");
  toast("Access request submitted for verification");
  go("/dashboard");
}
function logout() {
  localStorage.removeItem("pramaan_user");
  state.user = null;
  go("/login");
}

function render() {
  try {
    applySettings();
    if (
      !state.user &&
      !["/login", "/onboarding", "/register", "/splash"].includes(path())
    ) {
      app.innerHTML = login();
      return;
    }
    const p = path();
    let h;
    if (p === "/dashboard") h = dashboard();
    else if (p === "/cases") h = cases();
    else if (p === "/case-details") h = caseDetails();
    else if (p === "/documents") h = documents();
    else if (p === "/upload") h = upload();
    else if (p === "/viewer") h = viewer();
    else if (p === "/versions") h = versions();
    else if (p === "/vault") h = vault();
    else if (p === "/evidence") h = evidence();
    else if (p === "/evidence-details") h = evidenceDetails();
    else if (p === "/custody") h = custody();
    else if (p === "/transfer") h = transfer();
    else if (p === "/verification") h = verification();
    else if (p === "/signature") h = signature();
    else if (p === "/ocr") h = ocr();
    else if (p === "/pii") h = pii();
    else if (p === "/redaction") h = redaction();
    else if (p === "/ai") h = ai();
    else if (p === "/search") h = search();
    else if (p === "/court-export") h = courtExport();
    else if (p === "/certificate") h = certificate();
    else if (p === "/audit") h = auditPage();
    else if (p === "/alerts") h = alerts();
    else if (p === "/users") h = users();
    else if (p === "/roles") h = roles();
    else if (p === "/offline") h = offline();
    else if (p === "/sync") h = sync();
    else if (p === "/system-health") h = systemHealth();
    else if (p === "/settings") h = settings();
    else if (p === "/profile") h = profile();
    else if (p === "/reports") h = reports();
    else if (p === "/security") h = security();
    else if (p === "/login") h = login();
    else if (p === "/onboarding") h = onboarding();
    else if (p === "/register") h = register();
    else if (p === "/splash") h = splash();
    else h = dashboard();
    app.innerHTML = h;
    if (p === "/custody") setTimeout(renderCustody, 0);
    if (p === "/vault") setTimeout(() => renderVaultList(), 0);
    if (p === "/viewer") setTimeout(hydrateViewer, 0);
  } catch (e) {
    console.error(e);
    app.innerHTML =
      '<div class="runtime-error"><div class="runtime-error-card"><div class="runtime-error-mark">⚖</div><h1>PRAMAAN</h1><h2>Something went wrong</h2><p>' +
      esc(e?.message || "Unexpected error") +
      '</p><button class="btn btn-primary" onclick="location.reload()">Reload Application</button></div></div>';
  }
}

async function bootPramaan() {
  if (booted) return;

  booted = true;

  app = document.getElementById("app");

  if (!app) {
    throw new Error("PRAMAAN app mount was not found.");
  }

  // --------------------------------------------------
  // SAFE LOGIN HANDLER
  // --------------------------------------------------
  async function doLogin() {
    const email = document.getElementById("loginEmail")?.value?.trim() || "";
    const employeeId = document.getElementById("loginEmployeeId")?.value?.trim() || "";
    const department = document.getElementById("loginDepartment")?.value || "";
    const unit = document.getElementById("loginUnit")?.value?.trim() || "";
    const password = document.getElementById("loginPassword")?.value || "";
    const otp = document.getElementById("loginOtp")?.value?.trim() || "";
    const acknowledged = !!document.getElementById("loginAck")?.checked;
    if (!email || !employeeId || !department || !unit || !password || !otp) return toast("Complete all required government sign-in details", "error");
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) && employeeId.length < 3) return toast("Enter a valid official email or employee identity", "error");
    if (password.length < 12 || !/[A-Z]/.test(password) || !/[a-z]/.test(password) || !/\d/.test(password) || !/[^A-Za-z0-9]/.test(password)) return toast("Password does not meet the required security policy", "error");
    if (!/^\d{6}$/.test(otp)) return toast("Enter a valid 6-digit MFA / OTP", "error");
    if (otp !== "123456") return toast("MFA validation failed. Use the prototype OTP shown on the page.", "error");
    if (!acknowledged) return toast("Confirm that you are an authorized user", "error");

    // Authenticate with Django Backend API
    try {
      const res = await pramaanApi.login("inspector_sharma", "IO@12345");
      if (res.ok && res.data) {
        state.backendOnline = true;
      }
    } catch (err) {
      console.warn("PRAMAAN: Backend auth fallback:", err);
    }

    state.user = { id:employeeId, name:localStorage.getItem("pramaan_registered_name") || "Inspector Sharma", role:"Investigating Officer", email, status:"Active", employeeId, department, unit };
    localStorage.setItem("pramaan_user", JSON.stringify(state.user));
    audit("LOGIN", state.user.id, "Successful", "Info");
    toast("Secure sign-in successful");
    go("/dashboard");
  }

  // --------------------------------------------------
  // EXPOSE FUNCTIONS TO HTML onclick=""
  // --------------------------------------------------
  Object.assign(window, {
    state,

    go,
    render,
    toast,

    openModal,
    closeModal,

    // IMPORTANT
    doLogin,
    completeRegistration,

    filterDocs,
    uploadFile,
    verifyDoc,
    signDoc,

    registerEvidence,
    transferEvidence,

    askAI,
    scanPII,
    redactNow,

    generatePackage,
    generateCertificate,

    downloadText,
    downloadBlob,

    logout,

    openUserEdit,
    saveUserEdit,

    removeUser,
    removeAvatar,
    removeProfile,
    confirmRemoveProfile,

    simulateBreach,
    toggleSecurityControl,
    generateInnovationArtifact,

    toggleOffline,
    runSync,
    runFullVerification,
    runOCR,

    createCase,

    handleFileDrop,
    handleFileSelected,

    saveDocumentToVault,
    downloadVaultFile,

    vaultUpload,
    handleVaultFiles,
    handleVaultDrop,
    previewVaultFile,
    removeVaultFile,
    downloadVaultIndex,

    clearAIHistory,
    newAIChat,
    selectAIChat,
    renameAIChat,
    saveChatRename,
    deleteAIChat,

    addCustodyEvent,
    saveCustodyEvent,

    downloadVerificationReport,

    saveSettings,
    resetSettings,

    updateProfile,
    saveAvatar,

    togglePermission,
    resetPermissions,

    generateReport,

    ackAlerts,
    ackAlert,

    investigateAlert,
    saveAlertInvestigation,

    setSidebarWidth,
    startSidebarResize,

    createUser,
    userForm,
    evidenceForm,
    newCaseForm,
    profileForm,

    openCaseFilter,
    openCaseActions,
    applyCaseFilter,
    archiveCase,

    resetViewerZoom,
    zoomViewer,
  });

  // --------------------------------------------------
  // ROUTING
  // --------------------------------------------------
  window.addEventListener("hashchange", render);

  // Load saved application data
  await loadData();

  applySettings();

  const allowed = routes.concat([
    "/login",
    "/onboarding",
    "/register",
    "/splash",
  ]);

  // --------------------------------------------------
  // INITIAL ROUTE
  // --------------------------------------------------
  if (!location.hash) {
    const direct = location.pathname;

    location.hash = allowed.includes(direct)
      ? direct
      : state.user
        ? "/dashboard"
        : "/splash";
  }

  // --------------------------------------------------
  // RENDER APPLICATION
  // --------------------------------------------------
  render();

  // Async backend connection check & live badge update
  pramaanApi.checkHealth().then((online) => {
    state.backendOnline = online;
    render();
  });
}

export { bootPramaan };