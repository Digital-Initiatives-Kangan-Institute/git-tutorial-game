"use strict";

// The page draws what the watcher sends and holds no git logic of its own.
// All text from the server is escaped before any markup is added, so level
// prose and file names can never inject HTML.

const TOKEN = document.querySelector('meta[name="wt-token"]').content;
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
const $ = id => document.getElementById(id);

const ui = {
  seq: -1,
  lastEvent: 0,
  level: null,
  phase: null,
  moveKey: null,
  stampDismissed: null,
  glossary: {},
  state: null,
  pingAt: 0,
};

// ---- text -----------------------------------------------------------------

function esc(text) {
  return String(text ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

// Escape first, then mark up: `code`, **strong**, *emphasis*.
function inline(text) {
  return esc(text)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*(\S[^*]*?\S|\S)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(\S[^*]*?\S|\S)\*/g, "<em>$1</em>");
}

function blocks(list, { terminal = true } = {}) {
  let html = "";
  let bullets = [];
  const flush = () => {
    if (bullets.length) html += `<ul>${bullets.join("")}</ul>`;
    bullets = [];
  };
  for (const block of list || []) {
    if (block.type === "li") { bullets.push(`<li>${inline(block.text)}</li>`); continue; }
    flush();
    if (block.type === "p") html += `<p>${inline(block.text)}</p>`;
    else if (block.type === "h") html += `<h3>${inline(block.text)}</h3>`;
    else if (block.type === "pre") html += `<pre>${esc(block.lines.join("\n"))}</pre>`;
    else if (block.type === "try") {
      html += terminal ? terminalCard(block.commands)
                       : `<pre>${esc(block.commands.join("\n"))}</pre>`;
    }
  }
  flush();
  return html;
}

function terminalCard(commands) {
  const rows = commands.map(command =>
    `<div class="cmd"><code>${esc(command)}</code>` +
    `<button type="button" data-copy="${esc(command)}" aria-label="Copy ${esc(command)}">copy</button></div>`
  ).join("");
  return `<div class="terminal"><div class="label">At your terminal</div>${rows}</div>`;
}

document.addEventListener("click", event => {
  const button = event.target.closest("[data-copy]");
  if (!button) return;
  navigator.clipboard?.writeText(button.dataset.copy).then(() => {
    button.textContent = "copied";
    setTimeout(() => { button.textContent = "copy"; }, 1200);
  });
});

// ---- talking to the watcher ---------------------------------------------------

async function post(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-WT-Token": TOKEN },
    body: JSON.stringify(body || {}),
  });
  const result = await response.json().catch(() => ({ ok: false, error: "no reply" }));
  if (!result.ok) toast(result.error || "that did not work");
  return result;
}

function toast(text) {
  const box = $("toast");
  box.textContent = text;
  box.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => { box.hidden = true; }, 4000);
}

function ping() {
  const now = Date.now();
  if (now - ui.pingAt < 20000) return;
  ui.pingAt = now;
  post("/ping", {}).catch(() => {});
}

// ---- top bar --------------------------------------------------------------

function renderCourse(course) {
  $("actmap").innerHTML = (course || []).map(act => {
    const here = act.levels.some(l => l.status === "current");
    const dots = act.levels.map(l =>
      `<span class="dot ${l.status}" title="${esc(l.number)}. ${esc(l.title)}"></span>`).join("");
    // Only the current act spells out its name; the rest keep to a number,
    // with the name on hover, so six acts still fit on one line.
    const name = here ? `${esc(act.act)}. ${esc(act.title)}` : esc(act.act);
    return `<div class="act${here ? " here" : ""}" title="${esc(act.act)}. ${esc(act.title)}: ${esc(act.subject)}">` +
      `<span class="name">${name}</span><span class="dots">${dots}</span></div>`;
  }).join("");
}

// ---- the job ----------------------------------------------------------------

function renderJob(level, arrived) {
  const card = $("jobcard");
  if (!level) {
    card.innerHTML = "<h1>Every job is done</h1><p>You have finished the course.</p>";
    return;
  }
  const job = level.job || { ticket: level.id, from: "", title: level.title };
  const learns = (level.teaches || []).map(t => `<span class="chip">${esc(t)}</span>`).join("");
  card.innerHTML =
    `<div class="ticket"><span class="no">${esc(job.ticket)}</span>` +
    `<span>${esc(level.label)}</span>${job.from ? `<span>from ${esc(job.from)}</span>` : ""}</div>` +
    `<h1>${esc(job.title)}</h1>` +
    (learns ? `<div class="learns">learns ${learns}</div>` : "") +
    `<div class="prose">${blocks(level.intro)}</div>`;
  $("brief").innerHTML = `<div class="prose">${blocks(level.brief, { terminal: false })}</div>`;
  if (arrived && !reduced) {
    card.classList.remove("arrived");
    void card.offsetWidth;
    card.classList.add("arrived");
  }
}

// The job sheet is updated in place, so a half-typed answer is never wiped
// by a redraw that arrived while the student was typing.
function renderGoals(goals, levelId) {
  const list = $("goals");
  const same = list.dataset.level === levelId && list.children.length === goals.length;
  if (!same) {
    list.dataset.level = levelId || "";
    list.innerHTML = goals.map(goalShell).join("");
  }
  goals.forEach((goal, index) => {
    const item = list.children[index];
    item.classList.toggle("passed", goal.passed && !goal.error);
    item.classList.toggle("error", Boolean(goal.error));
    item.querySelector(".found").textContent = goal.error || goal.found || "";
    item.querySelector(".want").textContent = goal.want || "";
    const input = item.querySelector("input");
    if (input && goal.answer && document.activeElement !== input && !input.dataset.dirty) {
      input.value = goal.answer.value || "";
      input.classList.toggle("saved", Boolean(goal.answer.value));
    }
  });
}

function goalShell(goal) {
  const answer = goal.answer ? `
    <form class="answer" data-id="${esc(goal.answer.id)}">
      <label class="visually-hidden" for="a-${esc(goal.answer.id)}">${esc(goal.answer.prompt)}</label>
      <input id="a-${esc(goal.answer.id)}" autocomplete="off" spellcheck="false"
             placeholder="${goal.answer.input === "sha" ? "a commit hash, e.g. 1a2b3c4" : "your answer"}">
      <button type="submit" class="secondary">Save</button>
    </form>` : "";
  return `<li class="goal">
    <span class="box" aria-hidden="true"></span>
    <span class="label">${inline(goal.label)}</span>
    ${goal.story ? `<span class="story">${inline(goal.story)}</span>` : ""}
    ${goal.advisory ? `<span class="advisory">Recommended, not required.</span>` : ""}
    ${answer}
    <details><summary>what wt sees</summary>
      <div>wants: <span class="want"></span></div>
      <div>found: <span class="found"></span></div>
    </details>
  </li>`;
}

$("goals").addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.target.closest("form.answer");
  if (!form || !ui.level) return;
  const input = form.querySelector("input");
  const result = await post("/answer", { level: ui.level, id: form.dataset.id, value: input.value });
  if (result.ok) {
    delete input.dataset.dirty;
    input.classList.add("saved");
  }
});
$("goals").addEventListener("input", event => {
  if (event.target.matches("input")) {
    event.target.dataset.dirty = "1";
    event.target.classList.remove("saved");
    ping();
  }
});

function pulseGoal(key) {
  const index = parseInt(String(key).split(":")[0], 10);
  const item = $("goals").children[index];
  if (!item || reduced) return;
  item.classList.remove("pulse");
  void item.offsetWidth;
  item.classList.add("pulse");
}

// ---- hints ----------------------------------------------------------------

function renderHints(hints, fresh) {
  const list = $("hint-list");
  if (!hints.shown.length) {
    list.innerHTML = `<li class="none-li" style="background:none;border:none;padding:0">` +
      `<p class="none">Stuck? Hints arrive on their own if you go quiet, or ask for one.</p></li>`;
  } else {
    list.innerHTML = hints.shown.map(h =>
      `<li class="${fresh && h === hints.shown[hints.shown.length - 1] ? "fresh" : ""}">` +
      `<span class="rung">hint ${esc(h.rung)} of ${esc(hints.total)}</span>` +
      `<div class="prose">${blocks(h.blocks, { terminal: false })}</div></li>`).join("");
  }
  const button = $("hint-button");
  button.disabled = !hints.more;
  button.textContent = hints.more
    ? `Ask for a hint (${hints.shown.length + 1} of ${hints.total})`
    : "No more hints";
}

$("hint-button").addEventListener("click", () => { if (ui.level) post("/hint", { level: ui.level }); });
$("reset-button").addEventListener("click", () => {
  if (!ui.level) return;
  if (confirm("Put your workspace back to the start of this job? Uncommitted changes in it will be lost.")) {
    post("/reset", { level: ui.level });
  }
});

// ---- glossary ---------------------------------------------------------------

function renderGlossary(course) {
  const reached = new Set();
  for (const act of course || []) {
    for (const level of act.levels) {
      if (level.status !== "locked") reached.add(level.id);
    }
  }
  const taught = ui.taught || {};
  const terms = Object.entries(ui.glossary).filter(([, entry]) =>
    !entry.level || reached.has(entry.level) || taught[entry.level]);
  $("glossary").innerHTML = terms.length ? terms.map(([term, entry]) =>
    `<dt>${esc(entry.command || term)}</dt><dd>${inline(entry.definition || "")}` +
    (entry.warehouse ? ` <span class="wh">In the warehouse: ${esc(entry.warehouse)}.</span>` : "") +
    `</dd>`).join("") : "<dd>Terms appear here as you meet them.</dd>";
}

// ---- completion -------------------------------------------------------------

function renderPhase(state) {
  const done = state.phase !== "working" && state.level;
  const stamp = $("stamp");
  const bar = $("done-bar");
  if (!done) {
    stamp.hidden = true;
    bar.hidden = true;
    return;
  }
  const last = state.success && state.success.last;
  $("stamp-title").textContent = state.level.job ? state.level.job.title : state.level.title;
  $("stamp-body").innerHTML = blocks(state.success ? state.success.blocks : [], { terminal: false });
  const learned = (state.success && state.success.learned) || [];
  $("stamp-learned").innerHTML = learned.length
    ? `You can now use: ${learned.map(t => `<span class="chip">${esc(t)}</span>`).join(" ")}` : "";
  for (const id of ["next-button", "next-button-2"]) {
    $(id).hidden = Boolean(last);
  }
  $("stay-button").textContent = last ? "Close" : "Look around first";
  const dismissed = ui.stampDismissed === state.level.id;
  stamp.hidden = dismissed;
  bar.hidden = !dismissed || Boolean(last);
  if (!dismissed) $("next-button").focus({ preventScroll: true });
}

async function startNext() {
  for (const id of ["next-button", "next-button-2"]) $(id).disabled = true;
  const result = await post("/next", { level: ui.level });
  for (const id of ["next-button", "next-button-2"]) $(id).disabled = false;
  if (result.ok) ui.stampDismissed = null;
}
$("next-button").addEventListener("click", startNext);
$("next-button-2").addEventListener("click", startNext);
$("stay-button").addEventListener("click", () => {
  ui.stampDismissed = ui.level;
  $("stamp").hidden = true;
  $("done-bar").hidden = Boolean(ui.state && ui.state.success && ui.state.success.last);
});
document.addEventListener("keydown", event => {
  if (event.key === "Escape" && !$("stamp").hidden) $("stay-button").click();
});

// ---- the warehouse ----------------------------------------------------------

const FORKLIFT = `<svg viewBox="0 0 62 52" aria-hidden="true">
  <rect x="2" y="4" width="4" height="36" fill="#555"/><rect x="6" y="34" width="12" height="4" fill="#555"/>
  <rect x="18" y="16" width="30" height="22" rx="3" fill="#f2b705" stroke="#7a5a00"/>
  <rect x="26" y="4" width="16" height="14" rx="2" fill="none" stroke="#333" stroke-width="3"/>
  <circle cx="24" cy="42" r="7" fill="#333"/><circle cx="44" cy="42" r="7" fill="#333"/>
  <circle cx="24" cy="42" r="2.5" fill="#bbb"/><circle cx="44" cy="42" r="2.5" fill="#bbb"/></svg>`;

const TRUCK = `<svg viewBox="0 0 90 56" aria-hidden="true">
  <rect x="2" y="8" width="56" height="34" rx="3" fill="#f7f3ea" stroke="#5b4636" stroke-width="2"/>
  <rect x="14" y="16" width="20" height="18" fill="#c8955a" stroke="#8a5f31"/>
  <path d="M58 18 h16 l12 12 v12 h-28 z" fill="#b5543c" stroke="#5b4636" stroke-width="2"/>
  <rect x="64" y="21" width="10" height="9" fill="#dfe9f2"/>
  <circle cx="18" cy="46" r="7" fill="#333"/><circle cx="70" cy="46" r="7" fill="#333"/></svg>`;

const MARKS = {
  "~": ["m-mod", "~", "modified"],
  "+": ["m-add", "+", "added"],
  "-": ["m-del", "−", "deleted"],
  "?": ["m-new", "?", "untracked"],
  "!": ["m-conflict", "!", "conflict"],
};

function fileCard(item) {
  const [cls, glyph, base] = MARKS[item.mark] || MARKS["~"];
  // A held file says what kind of dispute it is and how much is left.
  const left = item.blocks == null ? "" : item.blocks === 0 ? " · no markers left"
    : ` · ${item.blocks} block${item.blocks === 1 ? "" : "s"} left`;
  const why = item.detail ? `${item.detail}${left}` : base;
  return `<div class="card ${cls}" data-key="f:${esc(item.path)}" title="${esc(item.path)}: ${why}">
    <span class="badge">${glyph}</span><span class="why">${why}</span>
    <span class="name">${esc(item.path)}</span></div>`;
}

// Tags are seals on the crate they mark. Keyed by name, so pushing a tag
// flies its seal across the road to Head Office.
let sealsBySha = new Map();

function seal(name) {
  return `<span class="seal" data-key="t:${esc(name)}" title="tag ${esc(name)}">${esc(name)}</span>`;
}

function crate(c, extra = "") {
  const seals = (sealsBySha.get(c.sha) || []).map(seal).join("");
  return `<div class="crate${c.merge ? " merge" : ""}${extra}" data-key="c:${esc(c.sha)}"
    title="${esc(c.short)} ${esc(c.subject)}"><span class="sha">${esc(c.short)}</span>
    <span class="subj">${esc(c.subject)}</span>${seals ? `<span class="seals">${seals}</span>` : ""}</div>`;
}

function fileCards(items, empty) {
  return items.length ? `<div class="cards">${items.map(fileCard).join("")}</div>`
                      : `<div class="empty">${empty}</div>`;
}

function shelf(s) {
  const zones = [`branch ${s.name}`];
  if (s.head) zones.push("last commit");
  const tip = s.crates.length - 1;
  const crates = s.crates.map((c, i) => crate(c, s.head && i === tip ? " head-tip" : "")).join("");
  const lift = s.head ? `<div class="forklift" data-key="head"><span class="tag">HEAD</span>${FORKLIFT}</div>` : "";
  const up = s.upstream ? `<span class="up">tracks ${esc(s.upstream)}</span>` : "";
  return `<div class="shelf${s.head ? " current" : ""}" data-zones="${esc(zones.join("|"))}">
    <div class="plate">branch <b>${esc(s.name)}</b>${up}</div>
    <div class="rack"><div class="crates">${crates || '<span class="empty">no commits</span>'}</div></div>
    ${lift}</div>`;
}

function renderWarehouse(w) {
  const stage = $("stage");
  if (!w) { stage.innerHTML = ""; return; }
  sealsBySha = new Map();
  for (const tag of w.tags || []) {
    sealsBySha.set(tag.sha, [...(sealsBySha.get(tag.sha) || []), tag.name]);
  }
  const shelves = w.shelves.map(shelf).join("");
  const more = w.more_shelves ? `<div class="shelf"><span class="more">+${w.more_shelves} more branches</span></div>` : "";
  const detached = w.head.detached ? `<div class="shelf current" data-zones="HEAD (detached)|last commit">
      <p class="detached-note"><b>HEAD (detached)</b>: the forklift is not parked at any branch</p>
      <div class="rack"><div class="crates"></div></div>
      <div class="forklift" data-key="head"><span class="tag">HEAD</span>${FORKLIFT}</div></div>` : "";
  const hold = !w.hold ? "" : w.hold_from === "pull"
    ? `<div class="hold" data-zones="paused">your <code>git pull</code> stopped on a conflict: settle it, or <code>git merge --abort</code></div>`
    : `<div class="hold" data-zones="paused">${esc(w.hold)} in progress: finish it, or abort it</div>`;
  const stash = Array.from({ length: Math.min(w.stash, 6) }, (_, i) =>
    `<div class="stashbox" data-key="s:${i}">stash@{${i}}</div>`).join("");
  const yard = w.yard.map(c => crate(c)).join("");
  const remotes = w.remotes.length ? w.remotes.map(r => `
    <div class="shelf${r.stale ? " stale" : ""}" data-zones="${esc(r.name)}">
      <div class="plate"><b>${esc(r.name)}</b></div>
      <div class="note">${r.stale
        ? "Head Office has deleted this branch. <code>git fetch --prune</code> takes the note down."
        : "what Head Office had at your last fetch"}</div>
      <div class="rack"><div class="crates">${r.crates.map(c => crate(c)).join("") || '<span class="empty">no commits</span>'}</div></div>
    </div>`).join("") : `<div class="empty">This repository has no remote.</div>`;
  const unseen = w.unseen || 0;
  const pile = Array.from({ length: Math.min(unseen, 6) }, (_, i) =>
    `<div class="crate ghost" data-key="u:${i}">?</div>`).join("");
  const pileText = w.unseen == null ? "unknown: Head Office is not on this computer"
    : unseen ? `${unseen} new commit${unseen === 1 ? "" : "s"} you have not fetched yet`
    : "nothing new since your last fetch";
  const out = w.ahead ? `<div class="sign busy"><b>${w.ahead}</b>ahead<br><code>git push</code> →</div>`
                      : `<div class="sign quiet">nothing to push</div>`;
  const inbound = w.behind ? `<div class="sign busy"><b>${w.behind}</b>behind<br>← <code>git pull</code></div>`
    : unseen ? `<div class="sign busy"><b>${unseen}</b>not fetched<br>← <code>git fetch</code></div>`
    : `<div class="sign quiet">nothing to pull</div>`;

  stage.innerHTML = `
  <section class="building local">
    <div class="roof">your repository <small>(the warehouse)</small></div>
    <div class="walls">
      ${hold}
      <div class="zone floorzone" data-zones="working tree">
        <h3>working tree <small>(loading floor)</small></h3>${fileCards(w.floor, "clean: nothing changed")}
      </div>
      <div class="zone bench" data-zones="staging area">
        <h3>staging area <small>(packing bench)</small></h3>
        <div class="table">${fileCards(w.bench, "empty: <code>git add</code> puts files here")}</div>
      </div>
      <div class="zone racks">
        <h3>branches <small>(shelves of commits, newest on the right)</small></h3>
        ${detached}${shelves}${more}
      </div>
      <div class="annex">
        <div class="zone backroom" data-zones="stash">
          <h3>stash <small>(back room)</small></h3>
          ${stash ? `<div class="boxes">${stash}</div>` : '<div class="empty">empty</div>'}
        </div>
        <div class="zone yard" data-zones="reflog only|off the branch">
          <h3>reflog only <small>(the yard)</small></h3>
          ${yard ? `<div class="crates">${yard}</div><div class="note">No branch points at these any more. The reflog still remembers them.</div>`
                 : '<div class="empty">nothing here: every commit is on a shelf</div>'}
        </div>
      </div>
    </div>
  </section>
  <section class="road">
    ${out}
    <div class="lane"><div id="truck">${TRUCK}</div></div>
    ${inbound}
  </section>
  <section class="building supplier">
    <div class="roof">origin <small>(Head Office)</small></div>
    <div class="walls">
      <div class="zone">
        <h3>remote-tracking branches <small>(your copy of Head Office's records)</small></h3>
        ${remotes}
      </div>
      <div class="zone" data-zones="origin">
        <h3>at Head Office now</h3>
        <div class="pile">${pile ? `<div class="crates">${pile}</div>` : ""}<div class="note">${esc(pileText)}</div>
          ${officeList(w.office)}</div>
      </div>
    </div>
  </section>`;
  fitShelves();
}

function officeList(office) {
  if (!office) return "";
  const branches = office.branches.map(b => `<span class="chip">${esc(b)}</span>`).join(" ");
  const tags = office.tags.map(t => seal(t.name)).join(" ");
  return `<div class="office"><div><span class="what">branches</span> ${branches || "<i>none</i>"}</div>` +
    (tags ? `<div><span class="what">tags</span> ${tags}</div>` : "") + `</div>`;
}

// The oldest crates make way: a shelf shows what fits and says how many
// older commits are not drawn, rather than spilling out of the walls.
function fitShelves() {
  for (const box of $("stage").querySelectorAll(".rack .crates")) {
    let hidden = 0;
    let marker = null;
    while (box.scrollWidth > box.clientWidth + 1 && box.querySelectorAll(".crate").length > 1) {
      box.querySelector(".crate").remove();
      hidden += 1;
      if (!marker) {
        marker = document.createElement("span");
        marker.className = "older";
        box.prepend(marker);
      }
      marker.textContent = `+${hidden} older`;
    }
  }
}

function renderCaption(move, fresh) {
  const caption = $("caption");
  if (!move) {
    caption.innerHTML = `<span class="tag">waiting</span>` +
      `<span class="detail">Run a git command in your terminal and watch it happen here.</span>`;
    return;
  }
  const route = move.source ? `${esc(move.source)} → ${esc(move.dest)}` : esc(move.dest);
  caption.innerHTML = `<span class="tag">last move</span><code class="cmd">${esc(move.command)}</code>` +
    `<span class="route">${route}</span><span class="detail">${esc(move.detail)}</span>`;
  if (fresh && !reduced) {
    caption.classList.remove("flash");
    void caption.offsetWidth;
    caption.classList.add("flash");
  }
}

// Every keyed element remembers where it was. After a redraw, anything that
// turned up somewhere new flies there from its old place; anything new flies
// in from the move's source; anything gone flies off to its destination.
function zoneOf(el) {
  const holder = el.closest("[data-zones]");
  return holder ? holder.dataset.zones : "";
}

function measure() {
  const seen = new Map();
  for (const el of $("stage").querySelectorAll("[data-key]")) {
    const list = seen.get(el.dataset.key) || [];
    list.push({ zone: zoneOf(el), rect: el.getBoundingClientRect(), html: el.outerHTML });
    seen.set(el.dataset.key, list);
  }
  return seen;
}

function anchor(name) {
  if (!name) return null;
  for (const el of $("stage").querySelectorAll("[data-zones]")) {
    if (el.dataset.zones.split("|").includes(name)) return el.getBoundingClientRect();
  }
  return null;
}

function center(rect, size) {
  return { left: rect.left + rect.width / 2 - size.width / 2, top: rect.top + rect.height / 2 - size.height / 2 };
}

function fly(el, from, far) {
  const to = el.getBoundingClientRect();
  const dx = from.left - to.left;
  const dy = from.top - to.top;
  if (Math.abs(dx) < 2 && Math.abs(dy) < 2) return;
  el.classList.add("flying");
  const lift = far ? -70 : 0;
  const run = el.animate([
    { transform: `translate(${dx}px, ${dy}px)` },
    { transform: `translate(${dx / 2}px, ${dy / 2 + lift}px) rotate(${far ? -5 : 0}deg)`, offset: 0.5 },
    { transform: "none" },
  ], { duration: far ? 1100 : 450, easing: "ease-in-out" });
  run.onfinish = () => el.classList.remove("flying");
}

function vanish(prev, dest) {
  const holder = document.createElement("div");
  holder.innerHTML = prev.html;
  const el = holder.firstElementChild;
  el.classList.add("ghost-fly");
  Object.assign(el.style, { left: `${prev.rect.left}px`, top: `${prev.rect.top}px`,
                            width: `${prev.rect.width}px`, height: `${prev.rect.height}px` });
  document.body.appendChild(el);
  const end = dest ? center(dest, prev.rect) : prev.rect;
  const dx = end.left - prev.rect.left;
  const dy = end.top - prev.rect.top;
  const run = el.animate([
    { transform: "none", opacity: 1 },
    { transform: `translate(${dx}px, ${dy - (dest ? 40 : 0)}px) scale(.8)`, opacity: 0.9, offset: 0.6 },
    { transform: `translate(${dx}px, ${dy}px) scale(.4)`, opacity: 0 },
  ], { duration: dest ? 1000 : 500, easing: "ease-in" });
  run.onfinish = () => el.remove();
}

function animate(before, move) {
  const after = new Set();
  const source = move ? anchor(move.source) : null;
  for (const el of $("stage").querySelectorAll("[data-key]")) {
    const key = el.dataset.key;
    after.add(key);
    const prev = before.get(key);
    const zone = zoneOf(el);
    const same = prev && prev.find(p => p.zone === zone);
    if (same) { fly(el, same.rect, false); continue; }
    if (prev && prev.length) { fly(el, prev[0].rect, true); continue; }
    if (source) { fly(el, center(source, el.getBoundingClientRect()), true); continue; }
    el.animate([{ transform: "scale(.6)", opacity: 0 }, { transform: "none", opacity: 1 }], { duration: 400 });
  }
  const dest = move ? anchor(move.dest) : null;
  for (const [key, list] of before) {
    if (!after.has(key)) list.forEach(prev => vanish(prev, dest));
  }
}

function drive(move) {
  const truck = $("truck");
  if (!truck || !move) return;
  if (move.command === "git push") truck.classList.add("out");
  else if (move.command === "git fetch" || move.command === "git pull") truck.classList.add("in");
}

// ---- applying a state ---------------------------------------------------------

function apply(state, first) {
  ui.state = state;
  const level = state.level;
  const levelId = level ? level.id : null;
  const arrived = !first && levelId !== ui.level;
  ui.level = levelId;

  const live = $("live");
  live.textContent = state.error ? `problem reading the workspace: ${state.error}` : "watching";
  live.classList.toggle("off", Boolean(state.error));

  renderCourse(state.course);
  if (arrived || first || JSON.stringify(level) !== ui.levelKey) {
    ui.levelKey = JSON.stringify(level);
    renderJob(level, arrived);
  }
  renderGoals(state.goals || [], levelId);
  const newHint = (state.events || []).some(e => e.id > ui.lastEvent && e.kind === "hint");
  renderHints(state.hints || { shown: [], total: 0, more: false }, newHint && !first);
  renderGlossary(state.course);

  const moveKey = JSON.stringify(state.move);
  const freshMove = !first && moveKey !== ui.moveKey;
  ui.moveKey = moveKey;
  // A new job rebuilds the whole floor; nothing moved, so nothing flies.
  const before = first || arrived || reduced ? null : measure();
  renderWarehouse(state.warehouse);
  renderCaption(state.move, freshMove);
  if (before) {
    animate(before, freshMove ? state.move : null);
    if (freshMove) drive(state.move);
  }

  if (!first) {
    for (const event of state.events || []) {
      if (event.id <= ui.lastEvent) continue;
      if (event.kind === "assertion_passed") pulseGoal(event.goal);
    }
  }
  ui.lastEvent = Math.max(ui.lastEvent, ...(state.events || []).map(e => e.id), 0);
  renderPhase(state);
}

async function loadGlossary() {
  try {
    const response = await fetch("/glossary.json", { cache: "no-store" });
    ui.glossary = await response.json();
  } catch (err) {
    ui.glossary = {};
  }
}

async function loop() {
  await loadGlossary();
  for (;;) {
    try {
      const response = await fetch(`/state?since=${ui.seq}`, { cache: "no-store" });
      const state = await response.json();
      $("offline").hidden = true;
      if (state.seq !== ui.seq) {
        apply(state, ui.seq === -1);
        ui.seq = state.seq;
      }
    } catch (err) {
      $("live").textContent = "disconnected";
      $("live").classList.add("off");
      $("offline").hidden = false;
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
}

loop();
