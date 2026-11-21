/* User-initiated, bounded public GitHub issues lookup.
 * No background requests, credentials, telemetry, local storage or HTML injection.
 * Public issues are an activity sample, not Root/PB runtime state. */
(function () {
  "use strict";
  const button = document.getElementById("refresh-activity");
  const status = document.getElementById("activity-status");
  const list = document.getElementById("activity-list");
  if (!button || !status || !list) return;

  const ENDPOINT = "https://api.github.com/repos/Footloose9/hyperfabric-evolution/issues?state=all&sort=updated&direction=desc&per_page=20";
  const URL_PREFIX = "https://github.com/Footloose9/hyperfabric-evolution/issues/";
  const MAX_ENTRIES = 8;

  function safeIssue(entry) {
    if (!entry || typeof entry !== "object" || entry.pull_request) return null;
    if (!Number.isSafeInteger(entry.number) || entry.number <= 0) return null;
    if (typeof entry.title !== "string" || !entry.title.trim()) return null;
    if (!["open", "closed"].includes(entry.state)) return null;
    if (typeof entry.updated_at !== "string" || !/^\d{4}-\d{2}-\d{2}T/.test(entry.updated_at)) return null;
    const normalized = new Date(entry.updated_at);
    if (!Number.isFinite(normalized.getTime())) return null;
    const expected = URL_PREFIX + entry.number;
    if (entry.html_url !== expected) return null;
    return {
      number: entry.number,
      title: entry.title.trim().slice(0, 180),
      state: entry.state,
      updated: normalized.toISOString().slice(0, 10),
      url: expected
    };
  }

  function draw(issues) {
    const valid = issues.map(safeIssue).filter(Boolean).slice(0, MAX_ENTRIES);
    list.replaceChildren();
    for (const issue of valid) {
      const item = document.createElement("li");
      const link = document.createElement("a");
      link.href = issue.url;
      link.textContent = "#" + issue.number + " · " + issue.title;
      link.rel = "noopener noreferrer";
      const label = document.createElement("small");
      label.textContent = "Issue " + issue.state + " · last updated " + issue.updated + " (GitHub reported)";
      item.append(link, label);
      list.appendChild(item);
    }
    list.hidden = valid.length === 0;
    return valid.length;
  }

  button.addEventListener("click", async function () {
    if (button.disabled) return;
    button.disabled = true;
    status.textContent = "Checking GitHub for a limited sample of recent public issues...";
    const controller = new AbortController();
    const timeout = setTimeout(function () { controller.abort(); }, 9000);
    /* Do not recursively retry on provider failures, quota limits or timeouts. */
    let response;
    try {
      response = await fetch(ENDPOINT, {
        method: "GET",
        mode: "cors",
        credentials: "omit",
        redirect: "error",
        headers: {Accept: "application/vnd.github+json"},
        signal: controller.signal
      });
      if (!response.ok) throw new Error("GitHub unavailable (HTTP " + response.status + ")");
      const payload = await response.json();
      if (!Array.isArray(payload) || payload.length > 20) throw new Error("Unexpected GitHub response");
      const count = draw(payload);
      const when = new Date().toLocaleTimeString();
      status.textContent = count
        ? "GitHub responded at " + when + ". Showing " + count + " recent public issues (sample only, not full project progress)."
        : "GitHub responded at " + when + ", but this sample contained no displayable public issues.";
    } catch (_error) {
      list.hidden = true;
      list.replaceChildren();
      status.textContent = "Live issue sample unavailable. Public research cards and roadmap remain accessible; use the GitHub links to view current work.";
    } finally {
      clearTimeout(timeout);
      controller.abort();
      button.disabled = false;
    }
  });
}());
