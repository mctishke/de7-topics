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
  { name: "Peter", avatar: "avatars/peter.png" },
  { name: "Niels", avatar: "avatars/niels.png" },
  { name: "Thijs", avatar: "avatars/thijs.png" },
  { name: "Seppe", avatar: "avatars/seppe.png" },
  { name: "Robbe", avatar: "avatars/robbe.png" },
  { name: "Lara", avatar: "avatars/lara.png" },
  { name: "Maarten", avatar: null },
  { name: "Julie", avatar: null },
];

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
    return `<img class="avatar" src="${escapeHtml(person.avatar)}" alt="${escapeHtml(name)}" title="${escapeHtml(name)}" style="width:${size}px;height:${size}px">`;
  }
  const initials = (name || "?").trim().slice(0, 2).toUpperCase();
  const hue = hashHue(name || "?");
  return `<div class="avatar avatar-initials" title="${escapeHtml(name || "")}" style="width:${size}px;height:${size}px;font-size:${Math.round(size * 0.4)}px;background:hsl(${hue},50%,42%)">${escapeHtml(initials)}</div>`;
}

function brusselsDateStr(d) {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Brussels" }).format(d || new Date());
}
