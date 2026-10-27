# Agent reachability checks

`scripts/check_reachability.py` fetches the public discovery surface with the system `curl` and validates the bytes. It is the regression check for the 2026-10-27 Cloudflare Browser Integrity Check block. Background and evidence: [RCA](rca/2026-10-27-agent-reachability.md).

## Usage

```bash
python scripts/check_reachability.py
python scripts/check_reachability.py --output /tmp/reachability.json
python scripts/check_reachability.py --extended
python scripts/check_reachability.py --fail-on-slow
```

The default User-Agent is `Python-urllib/3.11`. That is the signature Cloudflare BIC blocked, and every run sends it. Exit status is 1 when any check fails. The JSON report is written even when a request fails. Failures are not retried. The whole run stops at 180 seconds.

Both `https://elihickox.com` and `https://www.elihickox.com` are checked, including skill documents discovered from the skills index. After those HTTPS requests, the checker GETs `http://` on `/` for each host and requires an upgrade to HTTPS on the same path. The first request stays HTTPS so a cold start is not warmed by the HTTP probe.

Redirects are followed manually, at most four hops, and only between those two hosts on HTTP or HTTPS with no userinfo and no non-default port. `curl` is limited to `--proto =http,https` and `--retry 0`. A redirect may change host or upgrade HTTP to HTTPS. It may not change the requested path, downgrade HTTPS, loop, or leave the site. `urljoin` resolves `//host` and relative locations such as `../`.

`--extended` repeats `/`, `/llms.txt`, `/api/agent-profile`, `/openapi.json`, and `/healthz` with a desktop Chrome User-Agent, `curl/8.7.1`, and the published GPTBot, ChatGPT-User, ClaudeBot, and PerplexityBot strings. Those requests are labeled simulated. They are not genuine crawler traffic.

A response at or above 15 seconds is a warning. `--fail-on-slow` turns that warning into a failure. The first request is ordinal 0. Cold-start state is `UNKNOWN`.

## What a failure means

- `path changed` means the final path is not the path that was requested. A 200 homepage returned for `/llms.txt` is a failure.
- `http did not upgrade` means an HTTP root responded without redirecting to HTTPS on `/`.
- `cf-mitigated: challenge`, `cf-chl`, `challenge-platform`, or error 1010 means Cloudflare challenged the client. The Python-urllib BIC block was HTTP 403 and error 1010. `/cdn-cgi/l/email-protection` is not a challenge.
- Status other than 200, the wrong media type, JSON that does not match the documented object shape, or a bad skill URL (external host, HTTP, userinfo, non-default port, duplicate path, or malformed digest) means the origin response is not the public contract.
- A skill `sha256:` digest that does not match the fetched `SKILL.md`.
- Sitemap XML that does not parse. HTML must contain Eli, and `/docs/api` must contain API. Markdown needs a heading and Eli.
- `robots.txt` disallowing a checked path for `Python-urllib`, `GPTBot`, `ChatGPT-User`, `ClaudeBot`, or `PerplexityBot`, including agent-specific groups. The same tokens are checked in the default run, not only with `--extended`. `X-Robots-Tag: noindex` or `GPTBot: noindex` fails. `Content-Signal: ai-train=no` and `noai-training` do not.
- External, looping, HTTPS-to-HTTP, or non-default-port redirects, or an initial URL whose scheme or host is not one of the two site names.

GitHub Actions runs this at 03:17 and 15:17 UTC, on manual dispatch, and after a successful Deploy to Fly.io workflow, on `ubuntu-latest` and `macos-latest`. The JSON artifact is kept for 7 days. A failed check uses normal Actions failure notifications. Deploys run the test suite first (`uv sync --frozen --dev`, then pytest). This checker does not change the app, Fly config, or Cloudflare.

## Confirmed state (2026-10-27)

Cloudflare skips BIC only, for GET and HEAD, on both hosts, for the 17 exact public paths. After that change, all 238 User-Agent requests returned 200 (34 of them had been Python-urllib 403s). AWS and GCP probes passed every route on both IP families. Two cold starts returned 200 in 5.787s (AWS) and 5.136s (GCP). Scale-to-zero stays on.

OpenAI's retrieval tool still returns internal errors, including against a warm direct Fly hostname. The exact cause is unresolved. Genuine Claude and Perplexity crawler access is unverified. Simulated bot User-Agents only show what this client receives with those headers.
