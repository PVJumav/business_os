# Lunexao Website

Standalone public website for `lunexao.com`.

This folder is separate from the BusinessOS application frontend. Deploy it as its own Cloudflare Pages project so the BusinessOS system remains unchanged.

## Pages/Sections

- Company profile
- Advertisement/services
- Blogs and resources
- Job openings and recruitment
- Webinars
- Training programs
- Contact inquiry form

## Cloudflare Pages Settings

Use these settings for a static site deployment:

- Framework preset: None / Static
- Root directory: `lunexao-website`
- Build command: leave empty
- Build output directory: `.`

This folder includes its own `wrangler.toml` with:

```toml
pages_build_output_dir = "."
```

That prevents Cloudflare from using the root BusinessOS Wrangler config, which is meant for the Next.js app.

Then add the custom domain:

- `lunexao.com`
- optionally `www.lunexao.com`

If the domain is already managed in Cloudflare DNS, Pages can attach the DNS records automatically. Otherwise, Cloudflare will show the records to add at your DNS provider.

## Contact Emails

The current buttons use:

- `info@lunexao.com`
- `careers@lunexao.com`

Update `script.js` if you want different inboxes.
