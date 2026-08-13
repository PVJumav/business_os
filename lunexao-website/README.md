# Lunexao Website

Standalone public website for `lunexao.com`.

This folder is separate from the Business OS application frontend. Deploy it as its own Cloudflare Pages project so the Business OS system remains unchanged.

## Routes

- `/` - Home
- `/about/` - About / company profile
- `/solutions/` - Business technology, process automation and digital platforms
- `/advisory/` - Technology advisory and transformation consulting
- `/training/` - Lunexao Academy / training programs
- `/webinars/` - Upcoming and past webinars
- `/insights/` - Lunexao Insights listing with search and category filters
- `/careers/` - Open positions and recruitment
- `/contact/` - Secure contact form
- `/api/contact` - optional Cloudflare Pages Function fallback for contact form email delivery

## Cloudflare Pages Settings

Use these settings for the standalone website deployment:

- Framework preset: None / Static
- Root directory: `lunexao-website`
- Build command: leave empty
- Build output directory: `.`

This folder includes its own `wrangler.toml`:

```toml
pages_build_output_dir = "."
```

Then add the custom domains:

- `lunexao.com`
- optionally `www.lunexao.com`

## Contact Form Email

The contact form posts directly to Formspree; it does not use `mailto:` and does not expose Gmail credentials in frontend code.

Messages are sent to:

- `pauljumav@gmail.com`

The current production setup uses Formspree:

- Endpoint: `https://formspree.io/f/xaewordo`
- Destination inbox configured in Formspree: `pauljumav@gmail.com`

This works on Cloudflare Pages Free because the browser submits directly to Formspree over HTTPS. The `/api/contact` Pages Function remains in the repo as an optional fallback, but the live form does not depend on Cloudflare Email Sending.

Cloudflare Email Service remains available as a future fallback if you later upgrade to Workers Paid, but it is not configured in `wrangler.toml` because Cloudflare Pages rejects `send_email` bindings during Pages deployment validation.

Optional environment variables:

- `EMAIL_TO=pauljumav@gmail.com`
- `EMAIL_FROM=contact@lunexao.com`
- `GMAIL_CLIENT_ID`
- `GMAIL_CLIENT_SECRET`
- `GMAIL_REFRESH_TOKEN`

Cloudflare Email Routing can forward domain addresses such as `info@lunexao.com` into `pauljumav@gmail.com`. It does not send website form submissions by itself. The live form now uses Formspree directly. If you later want a private server-side sender, switch the frontend back to `/api/contact` and configure either Cloudflare Email Service or Gmail API.

## Spam Protection

The form includes:

- Client-side required field validation
- Server-side required field validation
- Server-side email validation
- Honeypot field for bot submissions
- Duplicate-submit prevention while the request is in progress

## Local Testing

Static pages can be opened directly in a browser. To test the Cloudflare Pages Function locally, use Wrangler from this folder:

```bash
npx wrangler pages dev .
```

Then open:

```text
http://localhost:8788/contact/
```
