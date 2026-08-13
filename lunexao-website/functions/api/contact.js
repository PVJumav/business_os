const REQUIRED_FIELDS = ["name", "company", "email", "interest", "subject", "message"];
const FORMSPREE_ENDPOINT = "https://formspree.io/f/xaewordo";
const MAILBOXES = {
  general: "contact@lunexao.com",
  info: "info@lunexao.com",
  careers: "careers@lunexao.com",
  training: "training@lunexao.com",
  webinars: "webinars@lunexao.com",
  support: "support@lunexao.com",
};

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "no-store",
    },
  });
}

function isEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || "").trim());
}

function clean(value, max = 1000) {
  return String(value || "").trim().slice(0, max);
}

function base64Url(input) {
  const bytes = new TextEncoder().encode(input);
  let binary = "";
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function getMailboxRoute(data) {
  const text = [data.interest, data.subject, data.form_type, data.role].join(" ").toLowerCase();
  if (text.includes("career") || text.includes("job") || text.includes("apply")) return { label: "Careers", email: MAILBOXES.careers };
  if (text.includes("training") || text.includes("academy") || text.includes("course")) return { label: "Training", email: MAILBOXES.training };
  if (text.includes("webinar") || text.includes("event")) return { label: "Webinars", email: MAILBOXES.webinars };
  if (text.includes("support") || text.includes("customer success")) return { label: "Support", email: MAILBOXES.support };
  if (text.includes("partnership") || text.includes("media")) return { label: "Info", email: MAILBOXES.info };
  return { label: "General Enquiry", email: MAILBOXES.general };
}

function buildMessage(env, data) {
  const route = getMailboxRoute(data);
  const to = env.EMAIL_TO || route.email;
  const from = env.EMAIL_FROM || "contact@lunexao.com";
  const submittedAt = new Date().toISOString();
  const subject = `[${route.label}] ${data.subject}`;
  const text = [
    `Name: ${data.name}`,
    `Company: ${data.company}`,
    `Email: ${data.email}`,
    `Phone: ${data.phone || "Not provided"}`,
    `Routed To: ${to}`,
    `Area of Interest: ${data.interest}`,
    `Subject: ${data.subject}`,
    "",
    "Message:",
    data.message,
    "",
    `Submitted At: ${submittedAt}`,
  ].join("\n");
  return { to, from, subject, text, replyTo: data.email, route };
}

async function sendCloudflareEmail(env, data) {
  if (!env.EMAIL || typeof env.EMAIL.send !== "function") {
    throw new Error("Cloudflare Email binding is not available.");
  }
  const message = buildMessage(env, data);
  await env.EMAIL.send({
    to: message.to,
    from: message.from,
    subject: message.subject,
    text: message.text,
    replyTo: message.replyTo,
  });
}

async function getGmailAccessToken(env) {
  const response = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      client_id: env.GMAIL_CLIENT_ID,
      client_secret: env.GMAIL_CLIENT_SECRET,
      refresh_token: env.GMAIL_REFRESH_TOKEN,
      grant_type: "refresh_token",
    }),
  });
  const payload = await response.json();
  if (!response.ok || !payload.access_token) {
    throw new Error(payload.error_description || "Gmail authentication failed.");
  }
  return payload.access_token;
}

async function sendGmail(env, data) {
  const message = buildMessage(env, data);
  const raw = [
    `To: ${message.to}`,
    `From: ${message.from}`,
    `Reply-To: ${data.email}`,
    `Subject: ${message.subject}`,
    "Content-Type: text/plain; charset=UTF-8",
    "",
    message.text,
  ].join("\r\n");
  const accessToken = await getGmailAccessToken(env);
  const response = await fetch("https://gmail.googleapis.com/gmail/v1/users/me/messages/send", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ raw: base64Url(raw) }),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error?.message || "Gmail delivery failed.");
  }
}

async function sendFormspree(env, data) {
  const message = buildMessage(env, data);
  const response = await fetch(FORMSPREE_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      name: data.name,
      company: data.company,
      email: data.email,
      phone: data.phone,
      interest: data.interest,
      subject: message.subject,
      message: data.message,
      _replyto: data.email,
      _subject: message.subject,
      recipient: message.to,
      submitted_to: message.to,
      lunexao_mailbox: message.to,
      department: message.route.label,
      text: message.text,
    }),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || payload.message || "Formspree delivery failed.");
  }
}

export async function onRequestOptions() {
  return new Response(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    },
  });
}

export async function onRequestPost({ request, env }) {
  let payload;
  try {
    payload = await request.json();
  } catch {
    return json({ error: "Invalid request body." }, 400);
  }

  if (clean(payload.website, 200)) {
    return json({ ok: true });
  }

  const data = {
    name: clean(payload.name, 120),
    company: clean(payload.company, 160),
    email: clean(payload.email, 180),
    phone: clean(payload.phone, 80),
    interest: clean(payload.interest, 80),
    subject: clean(payload.subject, 160),
    message: clean(payload.message, 4000),
    form_type: clean(payload.form_type, 80),
    role: clean(payload.role, 160),
  };

  const missing = REQUIRED_FIELDS.filter((field) => !data[field]);
  if (missing.length) {
    return json({ error: `Missing required field: ${missing[0]}.` }, 400);
  }
  if (!isEmail(data.email)) {
    return json({ error: "Please provide a valid email address." }, 400);
  }
  if (data.message.length < 10) {
    return json({ error: "Please provide a longer message." }, 400);
  }
  try {
    if (FORMSPREE_ENDPOINT) {
      await sendFormspree(env, data);
    } else if (env.EMAIL) {
      await sendCloudflareEmail(env, data);
    } else if (env.GMAIL_CLIENT_ID && env.GMAIL_CLIENT_SECRET && env.GMAIL_REFRESH_TOKEN) {
      await sendGmail(env, data);
    } else {
      return json({ error: "Email delivery is not configured. Add Formspree, the Cloudflare EMAIL binding, or Gmail API secrets." }, 503);
    }
    return json({ ok: true });
  } catch (error) {
    return json({ error: error.message || "Message could not be sent." }, 502);
  }
}
