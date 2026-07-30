// Gedeeld tussen index.html en archief.html: Supabase-client, avatars, identiteit.

const SUPABASE_URL = "https://xjzfehxazcsqilczsxhe.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_BE2naLXZCC5UiRBHwAJSXA_JqelydgT";

let sb = null;
try {
  if (SUPABASE_URL && SUPABASE_ANON_KEY && window.supabase) {
    sb = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  }
} catch (e) {
  console.error("Supabase-client kon niet aangemaakt worden:", e);
}

const PEOPLE = [
  { name: "Bert", avatar: "avatars/bert.png" },
  { name: "Roan", avatar: "avatars/roan.png" },
  { name: "Lara", avatar: "avatars/lara.png" },
  { name: "Peter", avatar: "avatars/peter.png" },
  { name: "Niels", avatar: "avatars/niels.png" },
  { name: "Thijs", avatar: "avatars/thijs.png" },
  { name: "Seppe", avatar: "avatars/seppe.png" },
  { name: "Robbe", avatar: "avatars/robbe.png" },
  { name: "Maarten", avatar: null },
  { name: "Julie", avatar: null },
];

// Wie in aanmerking komt voor de "wie werkt mee"-selectie op de daily --
// een bewust kleinere subset dan de volledige PEOPLE-lijst.
const MAKER_PEOPLE = PEOPLE.filter(p => !["Robbe", "Maarten", "Julie"].includes(p.name));

function currentUser() {
  return localStorage.getItem("de7_user") || "";
}
function setCurrentUser(name) {
  if (name) localStorage.setItem("de7_user", name);
}
function clearCurrentUser() {
  localStorage.removeItem("de7_user");
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}

function hashHue(s) {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 360;
  return h;
}

function avatarHtml(name, size) {
  const person = PEOPLE.find(p => p.name === name);
  if (person && person.avatar) {
    return `<img class="avatar" src="${escapeHtml(person.avatar)}" alt="${escapeHtml(name)}" data-tooltip="${escapeHtml(name)}" style="width:${size}px;height:${size}px">`;
  }
  const initials = (name || "?").trim().slice(0, 2).toUpperCase();
  const hue = hashHue(name || "?");
  return `<div class="avatar avatar-initials" data-tooltip="${escapeHtml(name || "")}" style="width:${size}px;height:${size}px;font-size:${Math.round(size * 0.4)}px;background:hsl(${hue},50%,42%)">${escapeHtml(initials)}</div>`;
}

function brusselsDateStr(d) {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Brussels" }).format(d || new Date());
}

// Lucide-iconen (inline SVG, geen extra library nodig).
const PIN_ICON = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 17v5"/><path d="M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z"/></svg>`;
const EYE_OFF_ICON = `<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.733 5.076a10.744 10.744 0 0 1 11.205 6.575 1 1 0 0 1 0 .696 10.747 10.747 0 0 1-1.444 2.49"/><path d="M14.084 14.158a3 3 0 0 1-4.242-4.242"/><path d="M17.479 17.499a10.75 10.75 0 0 1-15.417-5.151 1 1 0 0 1 0-.696 10.75 10.75 0 0 1 4.446-5.143"/><path d="m2 2 20 20"/></svg>`;
