const REQUIRED_FIELDS = ["name", "company", "email", "interest", "subject", "message"];

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
  const to = env.EMAIL_TO || "chatgptaccpresales@gmail.com";
  const from = env.EMAIL_FROM || "me";
  const submittedAt = new Date().toISOString();
  const subject = `New Lunexao Website Enquiry - ${data.subject}`;
  const body = [
    `Name: ${data.name}`,
    `Company: ${data.company}`,
    `Email: ${data.email}`,
    `Phone: ${data.phone || "Not provided"}`,
    `Area of Interest: ${data.interest}`,
    `Subject: ${data.subject}`,
    "",
    "Message:",
    data.message,
    "",
    `Submitted At: ${submittedAt}`,
  ].join("\n");
  const raw = [
    `To: ${to}`,
    `From: ${from}`,
    `Reply-To: ${data.email}`,
    `Subject: ${subject}`,
    "Content-Type: text/plain; charset=UTF-8",
    "",
    body,
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
  if (!env.GMAIL_CLIENT_ID || !env.GMAIL_CLIENT_SECRET || !env.GMAIL_REFRESH_TOKEN) {
    return json({ error: "Email delivery is not configured yet." }, 503);
  }

  try {
    await sendGmail(env, data);
    return json({ ok: true });
  } catch (error) {
    return json({ error: error.message || "Message could not be sent." }, 502);
  }
}
