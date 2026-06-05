const blogs = [
  {
    title: "How growing companies move from spreadsheets to operating systems",
    category: "Operations",
    summary: "A practical look at replacing scattered tools with workflows, approvals, dashboards, and accountable data.",
  },
  {
    title: "Recruitment automation without losing the human interview",
    category: "Recruitment",
    summary: "How HR teams can publish roles, track applicants, run interviews, and convert successful candidates cleanly.",
  },
  {
    title: "Cybersecurity habits every business user should practice",
    category: "Security",
    summary: "Simple, repeatable behaviors that reduce phishing, account misuse, and data exposure risk.",
  },
  {
    title: "Finance dashboards that managers actually use",
    category: "Finance",
    summary: "A guide to useful KPIs, approval queues, cash visibility, budgets, and drill-downs.",
  },
  {
    title: "Training programs that survive after the workshop",
    category: "Training",
    summary: "Why adoption improves when training is tied to role journeys, work examples, and manager routines.",
  },
];

const jobs = [
  {
    title: "CRM Implementation Consultant",
    category: "technology",
    location: "Hybrid / Nairobi",
    type: "Contract or full-time",
    summary: "Configure sales workflows, reports, account structures, and adoption plans for client CRM programs.",
  },
  {
    title: "Business Development Executive",
    category: "sales",
    location: "Nairobi",
    type: "Full-time",
    summary: "Build customer relationships, coordinate proposals, and support technology solution growth.",
  },
  {
    title: "Training Facilitator",
    category: "training",
    location: "Remote and on-site",
    type: "Part-time pool",
    summary: "Deliver practical workshops for business systems, cybersecurity awareness, and digital adoption.",
  },
  {
    title: "Operations Analyst",
    category: "operations",
    location: "Hybrid",
    type: "Full-time",
    summary: "Map processes, document controls, support dashboards, and help clients improve daily operating rhythm.",
  },
];

const webinars = [
  {
    title: "Building an HRMS-ready organization",
    date: "Monthly session",
    summary: "Employee data, roles, approvals, recruitment, onboarding, payroll readiness, and compliance records.",
  },
  {
    title: "CRM to Finance: closing the revenue loop",
    date: "Quarterly briefing",
    summary: "Lead-to-quote, LPO, project handover, invoicing, revenue forecast, and collections alignment.",
  },
  {
    title: "Cyber awareness for business leaders",
    date: "On demand",
    summary: "Identity, incident response, data handling, third-party risk, and board-level security metrics.",
  },
];

function renderBlogs(filter = "") {
  const list = document.getElementById("blog-list");
  const term = filter.trim().toLowerCase();
  const visible = blogs.filter((item) =>
    [item.title, item.category, item.summary].join(" ").toLowerCase().includes(term)
  );
  list.innerHTML = visible
    .map(
      (item) => `
        <article class="card">
          <span class="card-icon">${item.category}</span>
          <h3>${item.title}</h3>
          <p>${item.summary}</p>
        </article>
      `
    )
    .join("");
}

function renderJobs(filter = "all") {
  const list = document.getElementById("job-list");
  const visible = jobs.filter((item) => filter === "all" || item.category === filter);
  list.innerHTML = visible
    .map(
      (item) => `
        <article class="job-card">
          <div>
            <h3>${item.title}</h3>
            <p>${item.summary}</p>
            <div class="pill-row">
              <span>${item.location}</span>
              <span>${item.type}</span>
              <span>${item.category}</span>
            </div>
          </div>
          <a class="button primary" href="mailto:careers@lunexao.com?subject=${encodeURIComponent(`Application: ${item.title}`)}">Apply</a>
        </article>
      `
    )
    .join("");
}

function renderWebinars() {
  const list = document.getElementById("webinar-list");
  list.innerHTML = webinars
    .map(
      (item) => `
        <article class="event-card">
          <p class="eyebrow">${item.date}</p>
          <h3>${item.title}</h3>
          <p>${item.summary}</p>
        </article>
      `
    )
    .join("");
}

function bindNavigation() {
  const toggle = document.querySelector(".nav-toggle");
  const nav = document.querySelector(".site-nav");
  toggle.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(open));
  });
  nav.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      nav.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
    });
  });
}

function bindContactForm() {
  document.getElementById("contact-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const subject = encodeURIComponent(`Lunexao inquiry: ${form.get("interest")}`);
    const body = encodeURIComponent(
      `Name: ${form.get("name")}\nEmail: ${form.get("email")}\nInterest: ${form.get("interest")}\n\n${form.get("message")}`
    );
    window.location.href = `mailto:info@lunexao.com?subject=${subject}&body=${body}`;
  });
}

document.getElementById("year").textContent = String(new Date().getFullYear());
document.getElementById("blog-search").addEventListener("input", (event) => renderBlogs(event.target.value));
document.getElementById("job-filter").addEventListener("change", (event) => renderJobs(event.target.value));

renderBlogs();
renderJobs();
renderWebinars();
bindNavigation();
bindContactForm();
