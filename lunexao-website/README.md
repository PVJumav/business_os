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
- `/api/contact` - Cloudflare Pages Function for contact form email delivery

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

The contact form posts to `/api/contact`; it does not use `mailto:` and does not expose Gmail credentials in frontend code.

Messages are sent to:

- `pauljumav@gmail.com`

Configure these Cloudflare Pages environment variables/secrets:

- `EMAIL_TO=pauljumav@gmail.com`
- `EMAIL_FROM` - Gmail account or verified sender used by the Gmail API
- `GMAIL_CLIENT_ID`
- `GMAIL_CLIENT_SECRET`
- `GMAIL_REFRESH_TOKEN`

Cloudflare Email Routing can forward domain addresses such as `info@lunexao.com` into `pauljumav@gmail.com`, but the website form still needs a server-side sender to deliver the submitted form as an email. The current implementation uses the Gmail API from the Cloudflare Pages Function. The Gmail account must have an OAuth refresh token with permission to send mail. If these values are missing, `/api/contact` returns an error and the frontend will not display a false success message.

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
