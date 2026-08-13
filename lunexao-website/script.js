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

const trainingCategories = [
  { title: "Business Technology", summary: "Understand how CRM, HR, finance, projects and operations platforms support daily management decisions." },
  { title: "Digital Transformation", summary: "Learn how to move from scattered digital tools to coordinated change programs with measurable outcomes." },
  { title: "Process Automation", summary: "Map repetitive work, define approval rules and identify workflows that can be simplified or automated." },
  { title: "Cybersecurity", summary: "Build safer habits around identity, phishing, data handling, incident reporting and everyday risk awareness." },
  { title: "Cloud & Infrastructure", summary: "Get practical grounding in cloud readiness, infrastructure planning, resilience and service operations." },
  { title: "Data & Analytics", summary: "Turn operational data into dashboards, useful KPIs and reporting routines that managers can trust." },
  { title: "AI & Emerging Technology", summary: "Evaluate AI use cases through business value, governance, data readiness and human review controls." },
  { title: "IT Governance", summary: "Strengthen policy, access control, audit evidence, technology ownership and compliance reporting." },
  { title: "Business Applications", summary: "Equip users to work confidently inside the systems that run sales, HR, finance and delivery." },
];
const contactEndpoint = "https://lunexao-api.onrender.com/api/public/contact";
const whatsappNumber = "254728775106";
const lunexaoMailboxes = {
  general: "contact@lunexao.com",
  info: "info@lunexao.com",
  careers: "careers@lunexao.com",
  training: "training@lunexao.com",
  webinars: "webinars@lunexao.com",
  support: "support@lunexao.com",
};
const botReplies = [
  { keys: ["price", "cost", "pricing"], answer: "Lunexao prices work based on scope, service area, delivery model and support needs. Share the solution you are considering and we can prepare a practical estimate." },
  { keys: ["demo", "book", "meeting"], answer: "You can book a demo from any solution card or use the contact form. Tell us the product area, team size and preferred date." },
  { keys: ["training", "academy", "course"], answer: "Lunexao Academy covers business technology, automation, cybersecurity, cloud, data, AI, governance and business applications. Corporate training can be customised." },
  { keys: ["career", "job", "apply"], answer: "Open roles are listed on the Careers page. Use the career application form there so your application is labelled correctly." },
  { keys: ["crm", "hr", "finance", "project"], answer: "Our business technology work covers CRM, HR and workforce management, finance workflows, projects, analytics and integrated operating platforms." },
  { keys: ["automation", "workflow", "approval"], answer: "We help map processes, define rules, automate approvals, route documents and create reporting visibility across teams." },
  { keys: ["contact", "email", "whatsapp"], answer: "Use the contact form or the WhatsApp agent button. Website enquiries are routed to the relevant Lunexao mailbox." },
];

function getMailboxRoute(payload, form) {
  const text = [
    payload.interest,
    payload.subject,
    payload.role,
    payload.form_type,
    window.location.search,
    window.location.pathname,
  ].join(" ").toLowerCase();
  if (form?.id === "career-form" || text.includes("career") || text.includes("job") || text.includes("apply")) {
    return { label: "Careers", email: lunexaoMailboxes.careers };
  }
  if (text.includes("training") || text.includes("academy") || text.includes("course")) {
    return { label: "Training", email: lunexaoMailboxes.training };
  }
  if (text.includes("webinar") || text.includes("event")) {
    return { label: "Webinars", email: lunexaoMailboxes.webinars };
  }
  if (text.includes("support") || text.includes("customer success")) {
    return { label: "Support", email: lunexaoMailboxes.support };
  }
  if (text.includes("partnership") || text.includes("media")) {
    return { label: "Info", email: lunexaoMailboxes.info };
  }
  return { label: "General Enquiry", email: lunexaoMailboxes.general };
}

function buildSubmissionSubject(payload, route) {
  const subject = payload.subject || payload.role || payload.interest || "Website enquiry";
  return `[${route.label}] ${subject}`;
}

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
      ${past ? "" : `<a class="button primary" href="/contact/?interest=webinars&subject=${encodeURIComponent(item.title)}">Register</a>`}
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
      <a class="button primary" href="#career-application" data-role="${item.title}">Apply</a>
    </article>
  `).join("");
}

function renderTraining() {
  const categories = document.getElementById("training-categories");
  if (categories) {
    categories.innerHTML = trainingCategories.map((item) => `<article class="card"><h3>${item.title}</h3><p>${item.summary}</p><a href="/contact/?interest=training&subject=${encodeURIComponent(item.title)}">Enquire</a></article>`).join("");
  }
  const list = document.getElementById("training-list");
  if (list) {
    list.innerHTML = [
      { title: "Business Technology Enablement", summary: "Hands-on sessions for teams adopting CRM, HR, finance, project and analytics workflows." },
      { title: "Process Automation Clinic", summary: "A guided workshop where teams identify candidate workflows and draft automation-ready process maps." },
      { title: "Cybersecurity Awareness for Teams", summary: "Practical user training on phishing, passwords, data handling, incident reporting and safe collaboration." },
    ].map((item) => `<article class="card"><span class="card-icon">Upcoming</span><h3>${item.title}</h3><p>${item.summary}</p><a href="/contact/?interest=training&subject=${encodeURIComponent(item.title)}">Register interest</a></article>`).join("");
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

function bindRoutedForm(formId, statusId, submitId, buttonText, successText) {
  const form = document.getElementById(formId);
  if (!form) return;
  const status = document.getElementById(statusId);
  const submit = document.getElementById(submitId);
  if (!status || !submit) return;
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
    const route = getMailboxRoute(payload, form);
    const subject = buildSubmissionSubject(payload, route);
    try {
      const response = await fetch(contactEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          ...payload,
          routed_to: route.email,
          lunexao_mailbox: route.email,
          department: route.label,
          form_source: formId,
          _replyto: payload.email,
          _subject: subject,
        }),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.error || "Message could not be sent. Please try again.");
      form.reset();
      status.textContent = `${successText} Routed to ${route.email}.`;
      status.classList.add("success");
    } catch (error) {
      status.textContent = error.message || "Message could not be sent. Please try again.";
      status.classList.add("error");
    } finally {
      submit.disabled = false;
      submit.textContent = buttonText;
    }
  });
}

function bindContactForm() {
  const params = new URLSearchParams(window.location.search);
  const contactForm = document.getElementById("contact-form");
  if (contactForm) {
    const interest = params.get("interest") || params.get("demo") || params.get("package") || params.get("solution") || params.get("intent");
    const subject = params.get("subject");
    if (interest && contactForm.elements.interest) {
      const select = contactForm.elements.interest;
      const normalized = interest.toLowerCase();
      const match = Array.from(select.options).find((option) => option.text.toLowerCase().includes(normalized) || normalized.includes(option.text.toLowerCase().split(" ")[0]));
      if (match) select.value = match.value || match.text;
    }
    if (subject && contactForm.elements.subject) contactForm.elements.subject.value = subject;
    if (!subject && interest && contactForm.elements.subject) contactForm.elements.subject.value = `${interest.replace(/[-_]/g, " ")} enquiry`;
  }
  bindRoutedForm(
    "contact-form",
    "contact-status",
    "contact-submit",
    "Send Message",
    "Thank you for contacting Lunexao. Your message has been received."
  );
  bindRoutedForm(
    "career-form",
    "career-status",
    "career-submit",
    "Submit Application",
    "Thank you for applying to Lunexao. Your application has been received."
  );
  document.querySelectorAll("[data-role]").forEach((link) => {
    link.addEventListener("click", () => {
      const roleInput = document.querySelector("#career-form [name='role']");
      if (roleInput) roleInput.value = link.getAttribute("data-role") || "";
    });
  });
}

function addUtilityWidgets() {
  if (document.querySelector(".site-tools")) return;
  document.body.insertAdjacentHTML("beforeend", `
    <div class="site-tools" aria-label="Site assistance tools">
      <button class="tool-button contrast-toggle" type="button" aria-label="Change contrast mode">Contrast</button>
      <button class="tool-button whatsapp-agent" type="button" aria-expanded="false" aria-controls="whatsapp-panel">WhatsApp</button>
      <button class="tool-button chat-toggle" type="button" aria-expanded="false" aria-controls="chatbot-panel">Chat</button>
    </div>
    <section id="whatsapp-panel" class="chatbot-panel whatsapp-panel" aria-label="WhatsApp agent" hidden>
      <div class="chatbot-header">
        <div><strong>WhatsApp Lunexao</strong><span>Type your question and continue in WhatsApp</span></div>
        <button class="whatsapp-close chat-close" type="button" aria-label="Close WhatsApp panel">x</button>
      </div>
      <form id="whatsapp-form" class="chatbot-form whatsapp-form">
        <textarea name="message" rows="4" placeholder="Type your WhatsApp question" required></textarea>
        <button type="submit">Open WhatsApp</button>
      </form>
    </section>
    <section id="chatbot-panel" class="chatbot-panel" aria-label="Lunexao chatbot" hidden>
      <div class="chatbot-header">
        <div><strong>Lunexao Assistant</strong><span>Basic customer questions</span></div>
        <button class="chat-close" type="button" aria-label="Close chatbot">x</button>
      </div>
      <div id="chatbot-log" class="chatbot-log">
        <p><strong>Lunexao:</strong> Hi. Ask about demos, pricing, training, careers, automation, CRM, HR, finance or contact options.</p>
      </div>
      <form id="chatbot-form" class="chatbot-form">
        <input name="question" placeholder="Type your question" autocomplete="off" required />
        <button type="submit">Send</button>
      </form>
    </section>
  `);
}

function bindContrastToggle() {
  const modes = ["standard", "dark", "high"];
  const saved = localStorage.getItem("lunexaoContrast") || "standard";
  document.documentElement.dataset.contrast = saved;
  document.querySelector(".contrast-toggle")?.addEventListener("click", () => {
    const current = document.documentElement.dataset.contrast || "standard";
    const next = modes[(modes.indexOf(current) + 1) % modes.length];
    document.documentElement.dataset.contrast = next;
    localStorage.setItem("lunexaoContrast", next);
  });
}

function bindChatbot() {
  const panel = document.getElementById("chatbot-panel");
  const toggle = document.querySelector(".chat-toggle");
  const close = document.querySelector(".chat-close");
  const form = document.getElementById("chatbot-form");
  const log = document.getElementById("chatbot-log");
  if (!panel || !toggle || !form || !log) return;
  const setOpen = (open) => {
    panel.hidden = !open;
    toggle.setAttribute("aria-expanded", String(open));
  };
  toggle.addEventListener("click", () => setOpen(panel.hidden));
  close?.addEventListener("click", () => setOpen(false));
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const input = form.elements.question;
    const question = input.value.trim();
    if (!question) return;
    const lower = question.toLowerCase();
    const matched = botReplies.find((item) => item.keys.some((key) => lower.includes(key)));
    const answer = matched?.answer || "I can help with common Lunexao questions. For a specific request, use the contact form or book a demo and the team will follow up.";
    log.insertAdjacentHTML("beforeend", `<p><strong>You:</strong> ${question.replace(/[<>&]/g, "")}</p><p><strong>Lunexao:</strong> ${answer}</p>`);
    input.value = "";
    log.scrollTop = log.scrollHeight;
  });
}

function bindWhatsAppAgent() {
  const panel = document.getElementById("whatsapp-panel");
  const toggle = document.querySelector(".whatsapp-agent");
  const close = document.querySelector(".whatsapp-close");
  const form = document.getElementById("whatsapp-form");
  if (!panel || !toggle || !form) return;
  const setOpen = (open) => {
    panel.hidden = !open;
    toggle.setAttribute("aria-expanded", String(open));
  };
  toggle.addEventListener("click", () => setOpen(panel.hidden));
  close?.addEventListener("click", () => setOpen(false));
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const message = form.elements.message.value.trim();
    if (!message) {
      form.reportValidity();
      return;
    }
    const text = encodeURIComponent(`Hello Lunexao, ${message}`);
    window.open(`https://wa.me/${whatsappNumber}?text=${text}`, "_blank", "noopener");
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
addUtilityWidgets();
bindContrastToggle();
bindChatbot();
bindWhatsAppAgent();
