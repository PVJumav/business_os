# Lunexao DNS and Email Records

Use Cloudflare DNS for `lunexao.com`.

## Website Records

Cloudflare Pages usually creates these automatically when you add custom domains.

```text
lunexao.com       -> Lunexao website Pages project
www.lunexao.com   -> Lunexao website Pages project
app.lunexao.com   -> BusinessOS frontend Pages project
api.lunexao.com   -> Render backend custom domain
```

For Render custom domain, Render will provide a target such as:

```text
api.lunexao.com CNAME <render-target>
```

Set proxy mode based on Render's instructions. If TLS validation fails, temporarily set DNS only, then enable proxy later.

## Cloudflare Email Routing to Gmail

Destination:

```text
pauljumav@gmail.com
```

Aliases:

```text
info@lunexao.com      -> pauljumav@gmail.com
careers@lunexao.com   -> pauljumav@gmail.com
training@lunexao.com  -> pauljumav@gmail.com
support@lunexao.com   -> pauljumav@gmail.com
admin@lunexao.com     -> pauljumav@gmail.com
```

MX records:

```text
Type  Name          Mail server                  Priority
MX    lunexao.com   route1.mx.cloudflare.net     5
MX    lunexao.com   route2.mx.cloudflare.net     10
MX    lunexao.com   route3.mx.cloudflare.net     20
```

SPF:

```text
Type  Name          Value
TXT   lunexao.com   v=spf1 include:_spf.mx.cloudflare.net ~all
```

DMARC:

```text
Type  Name                 Value
TXT   _dmarc.lunexao.com   v=DMARC1; p=none; rua=mailto:pauljumav@gmail.com
```

Note: Cloudflare Email Routing handles receiving/forwarding. To send from `info@lunexao.com`, use Google Workspace, Zoho Mail, or configure a transactional SMTP provider.
