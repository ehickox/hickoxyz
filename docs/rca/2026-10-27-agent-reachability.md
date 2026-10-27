# AI-agent reachability RCA — 2026-10-27

## Findings and confidence

**Confirmed, high confidence:** Cloudflare Browser Integrity Check (BIC) denied legitimate automated GET requests based on client signature. At all 17 documented public routes on both hostnames, `Python-urllib/3.11` received HTTP 403 with `error code: 1010`. Changing only the User-Agent in the same HTTP client/network produced 200. The Python signature returned 200 directly from `hickoxyz.fly.dev`. Cloudflare authenticated configuration showed BIC on, no User-Agent blocking rules, no existing custom WAF rules, Bot Fight Mode off, and AI crawler protections disabled. Cloudflare Security Events filtered to service `bic` explicitly identify the audit requests as Block / Browser integrity check (including 21:10:22–32 UTC and 21:14:29/46 UTC before propagation). An expanded event identifies Python-urllib/3.11, GET www /sitemap.xml, Ray a514b026cd4c3884, service BIC and action Block. Subsequent AWS/GCP requests appear as Skip / Custom rules. This localizes the confirmed defect to Cloudflare, not Flask authentication, endpoint generation, DNS or Fly startup.

**Not established:** This defect explains OpenAI web retrieval's internal failures. The genuine OpenAI retrieval tool failed before the change and still returned internal errors after the change, including for the warm direct Fly hostname (which bypasses Cloudflare). The tool exposes neither HTTP status nor request/Ray ID, source IP, DNS/TLS trace or precise upstream timing. It is not possible to correlate these calls conclusively with edge/origin logs. Do not present BIC as the proven cause of OpenAI's failures, or spoofed User-Agents as verified genuine OpenAI/Claude/Perplexity crawler access.

**Confirmed cold-start latency, no observed cold-start HTTP failure:** Authenticated Fly machine view showed both machines stopped immediately before an AWS Singapore probe requested `/llms.txt`. Response was 200, total 5,787 ms, post-connect first-byte phase 5,762 ms. One machine then showed started. Fly logs at 21:12:51 UTC show PM11 (recently stopped machine unavailable), autostart, VM start ~1.34 s, Gunicorn workers at 21:12:54 and reachable at 21:12:55 (~2.25 s). The proxy recovered and delivered the original request successfully. A stricter third-party deadline could be sensitive to this latency, but its actual deadline is unknown. A second independent cold test from Google Cloud Charleston requested `/api/agent-profile` with both machines stopped: 200, total 5,136 ms, first-byte phase 5,051 ms; the other machine then started. Both external cold measurements returned 200; Globalping does not expose a per-attempt retry history in these artifacts. Scale-to-zero is retained; there is no evidence justifying an always-on machine or new edge hosting.

## Production remediation

Deployed 2026-10-27 21:14:44 UTC using the authenticated Cloudflare dashboard:

- Ruleset `31f6604b02f748778cd8298db9621aeb`, rule `8adccf26f52a431eb3c63d8046de12eb`.
- Exact hosts `elihickox.com` and `www.elihickox.com`, methods GET/HEAD, and an explicit set of the 17 public route paths.
- Skip **only** BIC (`action_parameters.products = ["bic"]`). Match logging enabled.
- No WAF phases, custom rules, rate limits, security level, IP access rules or DDoS controls skipped. Global BIC remains on. Scope controls verified Python HEAD on llms/profile returns 200 while Python GET /about and POST /llms.txt remain BIC-blocked 403; ordinary-client POST still returns Flask 405. No User-Agent allowlist pretending to authenticate crawlers.
- No changes to Fly machine count, size, auto-stop or minimum running machines; no Workers or new infrastructure.
- Endpoint URLs, bodies, schemas, headers and existing redirect behavior preserved.

The live rule was read back independently after UI deployment. After edge propagation the formerly blocked Python request returned 200. Post-change matrix: all 238 local UA requests returned final HTTP 200, including all 34 formerly blocked Python requests. Repeated 44-measurement / 88-response AWS/GCP matrix again returned 200 on apex/origin and correct 301 on www, including native IPv6. An additional 32-measurement / 64-response matrix verified every remaining route on both hostnames over native IPv6, origin IPv6, and HTTP→HTTPS redirects from AWS/GCP; all returned the expected 200 or 301. See ua-after.json, external-after.json and external-extended-after.json.

Rollback: disable only rule `8adccf26f52a431eb3c63d8046de12eb` in this zone's Security → Security rules. This intentionally restores the old BIC restriction; do not switch BIC off globally. When adding new public discovery routes, extend the exact path set and regression checker together.

## DNS, TLS, redirects and application audit

Both hostnames are proxied Cloudflare CNAMEs to `hickoxyz.fly.dev`; apex is flattened. External A records: `104.21.9.110`, `172.67.159.195`. AAAA: `2606:4700:3033::6815:96e`, `2606:4700:3037::ac43:9fc3`. Origin observed IPv4 `66.241.125.159` (Fly dashboard also shows IPv6 `2a09:8280:1::e8:c523:0`). DNS records were not changed. Zone and account IP Access Rule lists are empty. No Worker route matches apex/www (the only existing Worker route is on a separate calendar subdomain). IPv6 is enabled; Always Online is off; agent responses were DYNAMIC rather than edge-cached.

Cloudflare's active page rule redirects `www.elihickox.com/*` to `https://elihickox.com/$1` with one 301. Both destination and source path were verified. App metadata defaults to the www hostname, so published links incur this extra hop; this is not a loop and is not a demonstrated failure. Preserved rather than making an unrelated URL/schema change.

AWS and Google probes verified trusted TLSv1.3 on both hostnames, SANs apex and wildcard, certificate expiry 2026-12-17. Direct Fly TLS was valid too. A separate no-retry curl control used --resolve to force both custom hostnames directly to Fly IPv4 66.241.125.159 while retaining their original Host/SNI: llms, agent-profile and OpenAPI all returned 200 with ssl_verify_result=0 using Python-urllib/3.11. This verifies origin TLS for the actual custom hostnames, not just fly.dev; authenticated Fly Certificates view reports both apex and www certificates Issued. Cloudflare origin TLS setting is `full`, not `full (strict)`; unchanged to avoid an unrelated origin-trust migration. A separate strict-mode assessment could improve origin certificate enforcement.

Flask discovery routes are public, render server-side and have correct JSON/Markdown/plaintext/OpenAPI/linkset/XML types. `robots.txt` allows all paths and explicitly permits search/AI input while declining AI training. No auth or JS dependency was found. The API catalog and skills index identify all three published skill documents, with SHA-256 digests. The unrelated `/radio/` proxy makes an external network call; discovery/profile routes do not depend on it.

Fly runtime is 2 × shared 1 CPU / 256 MB in EWR, Gunicorn 2 gevent workers, scale-to-zero enabled, no configured HTTP readiness checks. Existing startup logs show workers becoming ready; no observed discovery-route application exception. Gunicorn access logs are not enabled, so absence of access-log entries cannot prove that a particular request did not reach the app. No speculative startup/health-check tuning was applied.

Existing GitHub deploy workflow uses the existing FLY_API_TOKEN secret. At baseline deploy and tests ran independently on master pushes, so a failing test did not gate deployment. Regression/monitoring implementation addresses that pipeline gap.

## Before/after evidence and limitations

Evidence files in `evidence/2026-10-27/` contain public HTTP/network metadata; no credentials or session cookies.

- Baseline: 44 Globalping measurements / 88 responses, using AWS AS16509 and Google Cloud AS396982. All 17 paths on both hostnames over IPv4; `/`, `/llms.txt`, `/api/agent-profile`, `/openapi.json` on both over native IPv6; origin homepage and llms over IPv4. Apex/origin 200, www 301 to the correct apex path. Measured total times 20–576 ms in that warm matrix.
- Baseline local UA matrix: 238 requests = 17 paths × 2 hosts × 7 UAs. Browser/curl/GPTBot/ChatGPT-User/ClaudeBot/PerplexityBot: 204 successful final 200s. Python urllib: 34 HTTP 403s. Headers spoof identity only; genuine crawler networks were not tested through these UAs.
- A separate post-fix matrix with full published OpenAI/Perplexity UA strings, a realistic browser UA, curl and ClaudeBot returned 200 for all 60 requests on the five primary routes across both hosts. These remain simulated headers, not real crawler network verification.
- Globalping overrides the User-Agent, so these cloud tests use its own automated client, not our requested bot signatures.
- Globalping returns only the first 10 KB of response bodies. Most discovery responses were complete and JSON/XML parsed, Markdown checked and skill digests validated. Homepage, agent-profile and HTML API docs exceeded that limit: status, MIME, TLS, headers and body prefix were observed, **not full body/schema validation from those probes**. The full-body monitoring checker provides complementary validation from its execution environment.
- Local `curl -6` resolved IPv4-mapped addresses in this runtime, so it was not accepted as native IPv6 evidence. The cloud probes record actual `2606:4700:...` addresses.
- Genuine OpenAI retrieval continues to fail without an observable HTTP response, including direct origin. Claude and Perplexity genuine crawler access is unverified. Cooperation from crawler operators (time, source IP/request ID and error trace) is required to determine their exact failure mechanism.
- Sampled tests cannot establish indefinite uptime or that every future cold start will fit every third-party deadline. Periodic monitoring deliberately does not keep the service continuously warm.

## References

- [Cloudflare error 1010](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/)
- [Selective BIC exceptions](https://developers.cloudflare.com/waf/tools/browser-integrity-check/)
- [Skip product scope](https://developers.cloudflare.com/waf/custom-rules/skip/options/)
- [Globalping measurement API and response limits](https://api.globalping.io/v1/spec.yaml)

- [OpenAI crawler header examples](https://developers.openai.com/api/docs/bots)
- [Perplexity crawler header examples](https://docs.perplexity.ai/docs/resources/perplexity-crawlers)
- [Anthropic crawler identification](https://privacy.anthropic.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler)

## Regression and monitoring implementation

Implementation commit: `35be258` (checker, tests, workflow gating and monitoring instructions). No application route, schema, runtime config or dependency changes.

Coordinator independently verified `uv run pytest -q`: **41 passed**; `uv lock --check` and `git diff --check` passed. The full production checker (`--extended`) completed **96/96 successful checks**, zero failures/warnings, including both hosts, six skill digests and HTTP upgrades. See `local-full-validation.json`. This supplements, not replaces, the independent AWS/GCP probes above.

The default automated run covers 36 checks: all 17 endpoints on each hostname, plus two HTTP upgrade probes. It always uses the formerly blocked Python-urllib signature. Regression tests reject challenge pages including HTTP 200 challenges, malformed JSON/MIME/schema, wrong-path redirects, external/insecure/looping redirect policies, bad discovery URLs/digests, bot-specific robots restrictions, network failures and missed run deadlines. It never retries a failed HTTP retrieval or claims that an unobserved machine was cold.

[Reachability workflow](https://github.com/ehickox/hickoxyz/actions/workflows/reachability.yml) runs on Ubuntu and macOS after successful deployment, on manual dispatch, and twice daily (03:17/15:17 UTC). Standard public-repository runners are free; Linux/Windows run in Azure, macOS in GitHub's macOS cloud ([GitHub runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)). No extra hosting service or always-on machine was added. JSON reports retain public response headers, strict-TLS result, actual peer IP, DNS results, redirect chains, per-hop TTFB/total, content validation and first-request ordinal; sensitive response headers are excluded. Artifacts expire after 7 days.

Use normal GitHub Actions failure notifications; inspect the failed job's summary and JSON artifact, then follow [operator instructions](../AGENT_REACHABILITY.md). A 15-second response is reported as slow; `--fail-on-slow` makes it fail. Scheduled checks measure the first request but do not deliberately stop production machines or keep them continuously warm. Deploy now depends on the passing test job, rather than racing it.
