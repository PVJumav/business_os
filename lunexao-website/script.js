const insights = [
  { title: "Why Businesses Are Still Running Critical Processes on Spreadsheets", category: "Business Technology", summary: "A practical look at the hidden operational risks created by spreadsheet-heavy work.", slug: "spreadsheet-process-risk" },
  { title: "The Hidden Cost of Manual Business Processes", category: "Process Automation", summary: "How repeated manual work affects speed, visibility, accountability and customer experience.", slug: "hidden-cost-manual-processes" },
  { title: "From Digitalisation to Digital Transformation", category: "Digital Transformation", summary: "Why scanning, portals and software are only part of a deeper transformation journey.", slug: "digitalisation-to-transformation" },
  { title: "How Organisations Should Approach Business Process Automation", category: "Process Automation", summary: "A simple framework for selecting, designing and governing automation projects.", slug: "business-process-automation-approach" },
  { title: "Technology Strategy: Where Should Your Organisation Invest Next?", category: "Technology Strategy", summary: "How to connect technology priorities to business objectives and operating pain points.", slug: "technology-strategy-investment" },
  { title: "AI and Emerging Technology Without the Noise", category: "AI & Emerging Technology", summary: "How leaders can evaluate AI opportunities using value, risk and readiness.", slug: "ai-without-noise" },
];

const webinars = [
  { title: "Building an Automation Roadmap", category: "Process Automation", date: "2026-09-18", time: "10:00 EAT", speaker: "Lunexao Advisory Team", description: "How to identify the best workflows to automate first.", past: false },
  { title: "Technology Strategy for Growing Organisations", category: "Technology Strategy", date: "2026-10-09", time: "11:00 EAT", speaker: "Lunexao Technology Advisor", description: "A practical session on prioritising technology investments.", past: false },
  { title: "CRM to Finance: Closing the Revenue Loop", category: "Business Technology", date: "2026-07-12", time: "On demand", speaker: "Lunexao Operations Team", description: "Connecting sales, quotations, projects, invoicing and collections.", past: true },
];

const jobs = [
  { title: "Business Technology Consultant", category: "technology", location: "Hybrid / Nairobi", type: "Full-time or contract", requirements: "Business process mapping, CRM/ERP exposure, client communication.", summary: "Support clients with business systems, workflows, documentation and rollout planning." },
  { title: "Technology Advisory Associate", category: "operations", location: "Hybrid", type: "Full-time", requirements: "Research, documentation, process analysis and stakeholder engagement.", summary: "Assist with assessments, technology roadmaps and transformation planning." },
  { title: "Training Facilitator", category: "training", location: "Remote and on-site", type: "Part-time pool", requirements: "Workshop delivery, business applications knowledge and strong facilitation skills.", summary: "Deliver practical training across business technology, cybersecurity and automation topics." },
  { title: "Business Development Executive", category: "sales", location: "Nairobi", type: "Full-time", requirements: "B2B sales, relationship management and proposal coordination.", summary: "Build customer relationships and support growth of Lunexao technology services." },
];

const trainingCategories = ["Business Technology", "Digital Transformation", "Process Automation", "Cybersecurity", "Cloud & Infrastructure", "Data & Analytics", "AI & Emerging Technology", "IT Governance", "Business Applications"];

function html(strings, ...values) {
  return strings.reduce((acc, part, index) => acc + part + (values[index] ?? ""), "");
}

function renderInsights(targetId, limit) {
  const target = document.getElementById(targetId);
  if (!target) return;
  const search = document.getElementById("insight-search");
  const category = document.getElementById("insight-category");
  const categories = ["all", ...new Set(insights.map((item) => item.category))];
  if (category && category.options.length <= 1) {
    category.innerHTML = categories.map((item) => `<option value="${item}">${item === "all" ? "All categories" : item}</option>`).join("");
  }
  const term = (search?.value || "").trim().toLowerCase();
  const selected = category?.value || "all";
  const visible = insights
    .filter((item) => selected === "all" || item.category === selected)
    .filter((item) => [item.title, item.category, item.summary].join(" ").toLowerCase().includes(term))
    .slice(0, limit || insights.length);
  target.innerHTML = visible.map((item) => html`
    <article class="card">
      <span class="card-icon">${item.category}</span>
      <h3>${item.title}</h3>
      <p>${item.summary}</p>
      <a href="/insights/${item.slug}/">Read insight</a>
    </article>
  `).join("") || `<p class="muted">No insights match the selected filter.</p>`;
}

function renderWebinars(targetId, past) {
  const target = document.getElementById(targetId);
  if (!target) return;
  const visible = webinars.filter((item) => item.past === past);
  target.innerHTML = visible.map((item) => html`
    <article class="event-card">
      <p class="eyebrow">${item.category}</p>
      <h3>${item.title}</h3>
      <p>${item.description}</p>
      <div class="pill-row"><span>${item.date}</span><span>${item.time}</span><span>${item.speaker}</span></div>
      ${past ? "" : `<a class="button primary" href="/contact/">Register</a>`}
    </article>
  `).join("");
}

function renderJobs(filter = "all") {
  const list = document.getElementById("job-list");
  if (!list) return;
  const visible = jobs.filter((item) => filter === "all" || item.category === filter);
  list.innerHTML = visible.map((item) => html`
    <article class="job-card">
      <div>
        <h3>${item.title}</h3>
        <p>${item.summary}</p>
        <p><strong>Requirements:</strong> ${item.requirements}</p>
        <div class="pill-row"><span>${item.location}</span><span>${item.type}</span><span>${item.category}</span></div>
      </div>
      <a class="button primary" href="/contact/">Apply</a>
    </article>
  `).join("");
}

function renderTraining() {
  const categories = document.getElementById("training-categories");
  if (categories) {
    categories.innerHTML = trainingCategories.map((item) => `<article class="card"><h3>${item}</h3><p>Practical training designed for business users, managers and technical teams.</p><a href="/contact/">Enquire</a></article>`).join("");
  }
  const list = document.getElementById("training-list");
  if (list) {
    list.innerHTML = ["Business Technology Enablement", "Process Automation Clinic", "Cybersecurity Awareness for Teams"].map((item) => `<article class="card"><span class="card-icon">Upcoming</span><h3>${item}</h3><p>Available for corporate cohorts and scheduled public sessions.</p><a href="/contact/">Register interest</a></article>`).join("");
  }
}

function bindNavigation() {
  const toggle = document.querySelector(".nav-toggle");
  const nav = document.querySelector(".site-nav");
  if (!toggle || !nav) return;
  toggle.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(open));
  });
  nav.querySelectorAll("a").forEach((link) => link.addEventListener("click", () => {
    nav.classList.remove("open");
    toggle.setAttribute("aria-expanded", "false");
  }));
}

function bindContactForm() {
  const form = document.getElementById("contact-form");
  if (!form) return;
  const status = document.getElementById("contact-status");
  const submit = document.getElementById("contact-submit");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    status.textContent = "";
    status.className = "form-status";
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }
    submit.disabled = true;
    submit.textContent = "Sending...";
    const payload = Object.fromEntries(new FormData(form).entries());
    try {
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.error || "Message could not be sent. Please try again.");
      form.reset();
      status.textContent = "Thank you for contacting Lunexao. Your message has been received and our team will get back to you shortly.";
      status.classList.add("success");
    } catch (error) {
      status.textContent = error.message || "Message could not be sent. Please try again.";
      status.classList.add("error");
    } finally {
      submit.disabled = false;
      submit.textContent = "Send Message";
    }
  });
}

document.getElementById("year")?.replaceChildren(String(new Date().getFullYear()));
document.getElementById("insight-search")?.addEventListener("input", () => renderInsights("insights-list"));
document.getElementById("insight-category")?.addEventListener("change", () => renderInsights("insights-list"));
document.getElementById("job-filter")?.addEventListener("change", (event) => renderJobs(event.target.value));

renderInsights("home-insights", 3);
renderInsights("insights-list");
renderWebinars("home-webinars", false);
renderWebinars("upcoming-webinars", false);
renderWebinars("past-webinars", true);
renderJobs();
renderTraining();
bindNavigation();
bindContactForm();
