// dashboard/static/dashboard.js
// Auto-updates stats without full page reload

const API = {
  stats:  '/api/stats',
  issues: '/api/issues',
};

// How often to refresh (ms)
const REFRESH_MS = 10_000;

// ──────────────────────────────────────────────────────────────

async function fetchJSON(url) {
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`Failed to fetch ${url}:`, err);
    return null;
  }
}

// ──────────────────────────────────────────────────────────────

function updateElement(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function updateBadge(id, status) {
  const el = document.getElementById(id);
  if (!el) return;
  // Remove all badge classes and add the right one
  el.className = el.className.replace(/badge-\w+/g, '');
  el.classList.add(`badge-${status}`);
  el.textContent = status;
}

// ──────────────────────────────────────────────────────────────

async function refreshStats() {
  const data = await fetchJSON(API.stats);
  if (!data) return;

  // System overview
  updateElement('stat-issues',   data.total_issues_processed ?? '-');
  updateElement('stat-prs',      data.total_prs_created      ?? '-');
  updateElement('stat-pending',  data.queue_stats?.pending   ?? '-');
  updateElement('stat-running',  data.queue_stats?.in_progress ?? '-');
  updateElement('stat-completed',data.queue_stats?.completed  ?? '-');
  updateElement('stat-failed',   data.queue_stats?.failed     ?? '-');

  // Agent statuses
  const agents = data.agents ?? {};
  for (const [name, info] of Object.entries(agents)) {
    const badgeId = `agent-status-${name.replace(/_/g, '-')}`;
    updateBadge(badgeId, info.status);

    const rateId = `agent-rate-${name.replace(/_/g, '-')}`;
    updateElement(rateId, `${Math.round(info.success_rate ?? 0)}%`);
  }

  // Timestamp
  updateElement('last-updated', new Date().toLocaleTimeString());
}

// ──────────────────────────────────────────────────────────────

async function refreshIssues() {
  const issues = await fetchJSON(API.issues);
  if (!issues) return;

  const container = document.getElementById('issue-list');
  if (!container) return;

  container.innerHTML = issues.slice(0, 15).map(issue => `
    <div class="issue-row">
      <span>
        <span class="issue-number">#${issue.issue_number}</span>
        <span class="badge badge-${issue.status}">${issue.status}</span>
      </span>
      ${issue.pr_url
        ? `<a class="pr-link" href="${issue.pr_url}" target="_blank">→ PR</a>`
        : ''}
    </div>
  `).join('');
}

// ──────────────────────────────────────────────────────────────

async function refresh() {
  await Promise.all([refreshStats(), refreshIssues()]);
}

// Initial load + periodic refresh
refresh();
setInterval(refresh, REFRESH_MS);