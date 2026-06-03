const samples = [
  {
    subject: "Urgent account locked",
    body: "Verify your password immediately or your account will be suspended within 24 hours.",
    urls: "http://secure-login.example-work.xyz/verify",
    html:
      '<p>Verify your account at <a href="http://secure-login.example-work.xyz/verify">https://employee.example.com/security</a>.</p><img src="http://secure-login.example-work.xyz/open-pixel.gif" width="1" height="1" alt="">',
    images: "http://secure-login.example-work.xyz/open-pixel.gif",
    attachments: "account-review.html",
    sender: "security-alerts@company-support-reset.xyz",
    replyTo: "helpdesk.verify@gmail.com",
    expectedDomain: "example.com",
  },
  {
    subject: "Weekly engineering sync",
    body: "The engineering sync is moved to Thursday at 10 AM. Agenda is in the project workspace.",
    urls: "https://workspace.example.com/engineering/agenda",
    html: "",
    images: "",
    attachments: "",
    sender: "engineering@example.com",
    replyTo: "engineering@example.com",
    expectedDomain: "example.com",
  },
];

const $ = (id) => document.getElementById(id);

function riskClass(score) {
  if (score >= 75) return "risk-high";
  if (score >= 45) return "risk-medium";
  return "risk-low";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function splitList(value) {
  return String(value)
    .split(/[,\s]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

async function refreshHealth() {
  try {
    const health = await api("/api/health");
    $("healthStatus").textContent = health.model_ready ? "Service ready" : "Model loading";
  } catch (error) {
    $("healthStatus").textContent = "Service offline";
  }
}

async function refreshMetrics() {
  const metrics = await api("/api/metrics");
  $("clickRate").textContent = `${metrics.click_rate}%`;
  $("reportRate").textContent = `${metrics.report_rate}%`;
  $("submitRate").textContent = `${metrics.submit_rate}%`;
  $("detectionsTotal").textContent = metrics.detection_total;

  $("riskList").innerHTML = metrics.highest_risk
    .map(
      (person) => `
      <div class="person-row">
        <div>
          <strong>${escapeHtml(person.name)}</strong>
          <small>${escapeHtml(person.department)} &middot; ${escapeHtml(person.level)}</small>
        </div>
        <div class="score ${riskClass(person.risk_score)}">${person.risk_score}</div>
      </div>`
    )
    .join("");
}

async function refreshEmployees() {
  const payload = await api("/api/employees");
  $("employeeSelect").innerHTML = payload.items
    .map((person) => `<option value="${person.id}">${escapeHtml(person.name)} (${escapeHtml(person.department)})</option>`)
    .join("");

  $("leaderboard").innerHTML = payload.items
    .map(
      (person, index) => `
      <div class="person-row">
        <div>
          <strong>${index + 1}. ${escapeHtml(person.name)}</strong>
          <small>${escapeHtml(person.level)} &middot; Risk ${person.risk_score}</small>
        </div>
        <div class="score">${person.awareness_points}</div>
        <div class="badge-line">${person.badges.map(escapeHtml).join(" &middot; ")}</div>
      </div>`
    )
    .join("");
}

async function runDetection() {
  $("detectionResult").textContent = "Analyzing...";
  const urls = splitList($("urlInput").value);
  const imageUrls = splitList($("imageInput").value);
  const attachmentNames = splitList($("attachmentInput").value);

  const result = await api("/api/detect", {
    method: "POST",
    body: JSON.stringify({
      subject: $("subjectInput").value,
      body: $("bodyInput").value,
      html_body: $("htmlInput").value,
      urls,
      image_urls: imageUrls,
      attachment_names: attachmentNames,
      sender_email: $("senderInput").value,
      reply_to_email: $("replyToInput").value,
      expected_domain: $("expectedDomainInput").value,
    }),
  });

  const labelClass = result.label === "phishing" ? "risk-high" : "risk-low";
  const sender = result.sender_analysis || {};
  const structure = result.structure_analysis || {};
  $("detectionResult").className = "result-box";
  $("detectionResult").innerHTML = `
    <strong class="${labelClass}">${result.label.toUpperCase()}</strong>
    <p>Confidence: ${(result.confidence * 100).toFixed(1)}% &middot; Phishing probability: ${(result.phishing_probability * 100).toFixed(1)}%</p>
    <p>Content risk: ${(result.content_probability * 100).toFixed(1)}% &middot; Structure risk: ${(result.structure_probability * 100).toFixed(1)}%</p>
    <p>Sender verdict: ${escapeHtml(sender.verdict || "unknown")} (${sender.risk_score ?? 0}/100) &middot; Structure verdict: ${escapeHtml(structure.verdict || "low")} (${structure.risk_score ?? 0}/100)</p>
    <p>Risk level: ${escapeHtml(result.risk_level)} &middot; Model accuracy: ${(result.model_accuracy * 100).toFixed(1)}%</p>
    <ul>${result.reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")}</ul>
    <p><strong>Sender checks</strong></p>
    <ul>${(sender.findings || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    <p><strong>Email structure checks</strong></p>
    <ul>${(structure.findings || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
  `;
  await refreshMetrics();
}

async function recordEvent() {
  const eventType = $("eventSelect").value;
  const employeeId = $("employeeSelect").value;
  const payload = await api("/api/events", {
    method: "POST",
    body: JSON.stringify({
      employee_id: employeeId,
      campaign_id: "camp-demo",
      event_type: eventType,
    }),
  });

  $("eventResult").className = "result-box";
  $("eventResult").innerHTML = `
    <strong>${escapeHtml(payload.employee.name)}</strong>
    <p>${escapeHtml(eventType)} recorded. Risk score is now ${payload.employee.risk_score}; awareness points are ${payload.employee.awareness_points}.</p>
  `;
  await refreshMetrics();
  await refreshEmployees();
}

function renderMetadata(title, items, formatter) {
  if (!items || items.length === 0) {
    return "";
  }
  return `
    <p><strong>${title}</strong></p>
    <ul>${items.map((item) => `<li>${formatter(item)}</li>`).join("")}</ul>
  `;
}

async function generateChallenge() {
  const payload = await api("/api/training/challenge", {
    method: "POST",
    body: JSON.stringify({
      scenario: $("scenarioSelect").value,
      difficulty: $("difficultySelect").value,
      employee_name: "Learner",
      company_name: "Example Co",
      base_url: window.location.origin,
    }),
  });

  const linkList = renderMetadata(
    "Links",
    payload.links || [],
    (item) => `<a href="${escapeHtml(item.url)}" target="_blank" rel="noopener">${escapeHtml(item.label)}</a> <span class="muted">(${escapeHtml(item.purpose)})</span>`
  );
  const imageList = renderMetadata(
    "Images",
    payload.images || [],
    (item) => `<span>${escapeHtml(item.role)}</span>: <a href="${escapeHtml(item.url)}" target="_blank" rel="noopener">${escapeHtml(item.alt_text || item.url)}</a>`
  );

  $("challengeResult").className = "challenge-box";
  $("challengeResult").innerHTML = `
    <strong>${escapeHtml(payload.subject)}</strong>
    <iframe class="email-render" sandbox="" srcdoc="${escapeHtml(payload.html_body || payload.body)}"></iframe>
    <details>
      <summary>Plain text fallback</summary>
      <div class="email-preview">${escapeHtml(payload.plain_text_body || payload.body)}</div>
    </details>
    ${linkList}
    ${imageList}
    <p><strong>Red flags</strong></p>
    <ul>${payload.red_flags.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    <p><strong>Hints</strong></p>
    <ul>${payload.hints.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
  `;
}

async function checkGophish() {
  const status = await api("/api/gophish/status");
  $("gophishStatus").className = "result-box";
  $("gophishStatus").innerHTML = `
    <strong>${status.reachable ? "Connected" : "Not connected"}</strong>
    <p>Configured: ${status.configured ? "yes" : "no"} &middot; Base URL: ${escapeHtml(status.base_url || "not set")}</p>
    <p>${escapeHtml(status.message || `Campaigns available: ${status.campaign_count}`)}</p>
  `;
}

function bindEvents() {
  $("detectButton").addEventListener("click", runDetection);
  $("eventButton").addEventListener("click", recordEvent);
  $("challengeButton").addEventListener("click", generateChallenge);
  $("gophishButton").addEventListener("click", checkGophish);
  $("sampleButton").addEventListener("click", () => {
    const sample = samples[Math.floor(Math.random() * samples.length)];
    $("subjectInput").value = sample.subject;
    $("bodyInput").value = sample.body;
    $("htmlInput").value = sample.html;
    $("urlInput").value = sample.urls;
    $("imageInput").value = sample.images;
    $("attachmentInput").value = sample.attachments;
    $("senderInput").value = sample.sender;
    $("replyToInput").value = sample.replyTo;
    $("expectedDomainInput").value = sample.expectedDomain;
  });
}

async function boot() {
  bindEvents();
  await refreshHealth();
  await refreshMetrics();
  await refreshEmployees();
}

boot().catch((error) => {
  $("healthStatus").textContent = "Service error";
  console.error(error);
});
