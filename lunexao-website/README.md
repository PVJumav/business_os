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

## Cloudflare Pages Settings

Use these settings for the standalone website deployment:

- Framework preset: None / Static
- Root directory: `lunexao-website`
- Build command: leave empty
- Build output directory: `.`

This folder intentionally does not include its own `wrangler.toml`; Cloudflare Pages should use the dashboard build settings above.

Then add the custom domains:

- `lunexao.com`
- optionally `www.lunexao.com`

## Contact Form Email

The contact form posts to the Business OS backend public endpoint and the backend sends email through Zoho SMTP. Zoho credentials are stored only in the backend hosting environment, never in browser code.

Messages are labelled for the relevant Lunexao domain mailbox:

- `contact@lunexao.com` - general website enquiries and demos
- `info@lunexao.com` - partnerships and general information
- `careers@lunexao.com` - career applications
- `training@lunexao.com` - training and academy enquiries
- `webinars@lunexao.com` - webinar registrations
- `support@lunexao.com` - support or customer success enquiries

The current production endpoint is:

- Endpoint: `https://lunexao-api.onrender.com/api/public/contact`

Add these environment variables to the Render backend service:

- `ZOHO_SMTP_HOST=smtp.zoho.com`
- `ZOHO_SMTP_PORT=465`
- `ZOHO_SMTP_USER=contact@lunexao.com`
- `ZOHO_SMTP_PASSWORD=<Zoho app password or mailbox password>`
- `CONTACT_FROM_EMAIL=contact@lunexao.com`

The backend routes submissions to a fixed allowlist of Lunexao mailboxes. It does not trust a browser-submitted recipient value, so the endpoint cannot be used as an arbitrary-recipient mail relay.

The live form does not use Formspree or Cloudflare Email Sending.

## Spam Protection

The form includes:

- Client-side required field validation
- Server-side required field validation
- Server-side email validation
- Honeypot field for bot submissions
- Duplicate-submit prevention while the request is in progress

## Local Testing

Static pages can be opened directly in a browser. To test form delivery, run the Business OS backend with the Zoho SMTP environment variables configured, then submit the contact form.
