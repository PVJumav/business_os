const API_BASE_URL = process.env.BUSINESSOS_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
const EMAIL = process.env.BUSINESSOS_EMAIL || "";
const PASSWORD = process.env.BUSINESSOS_PASSWORD || "";

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, options);
  } catch (error) {
    throw new Error(`Cannot reach ${API_BASE_URL}${path}. Start the backend first, or set BUSINESSOS_API_URL. ${error.message}`);
  }
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json") ? await response.json().catch(() => null) : await response.text().catch(() => "");
  if (!response.ok) {
    throw new Error(`${options.method || "GET"} ${path} failed (${response.status}): ${JSON.stringify(body)}`);
  }
  return body;
}

async function login() {
  if (!EMAIL || !PASSWORD) return null;
  const payload = await request("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: EMAIL, password: PASSWORD }),
  });
  return payload.access_token;
}

async function main() {
  const checks = [];
  const add = async (name, fn) => {
    const started = Date.now();
    try {
      const result = await fn();
      checks.push({ name, status: "pass", ms: Date.now() - started, result });
    } catch (error) {
      checks.push({ name, status: "fail", ms: Date.now() - started, error: error.message });
    }
  };

  await add("API health", () => request("/api/health/database"));
  await add("Reports list", () => request("/api/reports"));
  await add("Reports summary", () => request("/api/reports/summary"));
  await add("CEO report sections", () => request("/api/reports/ceo/sections"));

  const token = await login().catch((error) => {
    checks.push({ name: "Authenticated login", status: "fail", ms: 0, error: error.message });
    return null;
  });

  if (token) {
    const authHeaders = { Authorization: `Bearer ${token}` };
    checks.push({ name: "Authenticated login", status: "pass", ms: 0, result: "token received" });
    await add("Current user", () => request("/api/auth/me", { headers: authHeaders }));
    await add("Phase 1 dashboard", () => request("/api/phase1/integrations/dashboard", { headers: authHeaders }));
    await add("Phase 1 events", () => request("/api/phase1/integrations/events", { headers: authHeaders }));
    await add("Policy check", () => request("/api/phase1/integrations/policy/check?module=crm&action=read", { headers: authHeaders }));
    await add("Integrations summary", () => request("/api/integrations/summary", { headers: authHeaders }));
    await add("Connectors list", () => request("/api/enterprise/connectors", { headers: authHeaders }));
    await add("Imports list", () => request("/api/enterprise/imports", { headers: authHeaders }));
  } else {
    checks.push({
      name: "Authenticated workflow checks",
      status: "skip",
      ms: 0,
      error: "Set BUSINESSOS_EMAIL and BUSINESSOS_PASSWORD to test protected endpoints.",
    });
  }

  const failed = checks.filter((check) => check.status === "fail");
  console.table(checks.map(({ name, status, ms, error }) => ({ name, status, ms, error: error || "" })));
  if (failed.length) process.exit(1);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
