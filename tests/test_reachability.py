import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import check_reachability as reach
from app.tests.fixtures import client
from app.views import skill_documents

PUBLIC_PATHS = list(reach.BASE_PATHS) + [
    f"/.well-known/agent-skills/{name}/SKILL.md" for name in skill_documents()
]
DIGEST = "sha256:" + ("ab" * 32)
SCHEMA = "https://schemas.agentskills.io/discovery/0.2.0/schema.json"


def hop(url, status=200, headers=None, body=b"", error=None, total=0.02):
    headers = {key.lower(): value for key, value in (headers or {}).items()}
    return {
        "url": url,
        "status": status,
        "headers": headers,
        "body": body,
        "remote_ip": "203.0.113.10",
        "ssl_verify_result": 0 if urlsplit(url).scheme == "https" else None,
        "time_starttransfer": 0.01,
        "time_total": total,
        "content_type": headers.get("content-type"),
        "error": error,
    }


def html(url):
    return hop(url, headers={"content-type": "text/html"}, body=b"<html><h1>Eli Hickox</h1></html>")


def health(url):
    return hop(url, headers={"content-type": "application/json"}, body=b'{"status":"ok"}')


class Script:
    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def exchange(self, url, user_agent):
        self.calls.append((url, user_agent))
        if url in self.routes:
            response = self.routes[url]
            return response(url) if callable(response) else response
        parts = urlsplit(url)
        if parts.scheme == "http":
            dest = urlunsplit(("https", parts.netloc, parts.path or "/", "", ""))
            return hop(url, 301, {"location": dest, "content-type": "text/html"}, b"redirect")
        path = parts.path or "/"
        if path == "/healthz":
            return health(url)
        if path == "/llms.txt" or path.endswith("/SKILL.md"):
            return hop(url, headers={"content-type": "text/markdown"}, body=b"# Eli Hickox\n")
        if path == "/robots.txt":
            return hop(url, headers={"content-type": "text/plain"}, body=b"User-agent: *\nAllow: /\n")
        return html(url)


def run(transport, **kwargs):
    kwargs.setdefault("lookup", False)
    kwargs.setdefault("hosts", ("https://elihickox.com",))
    kwargs.setdefault("paths", ("/healthz",))
    return reach.run_check(transport=transport, **kwargs)


def skill(name, url, digest=DIGEST):
    return {"name": name, "type": "skill-md", "description": "Eli skill", "url": url, "digest": digest}


def index_body(skills):
    return json.dumps({"$schema": SCHEMA, "skills": skills}).encode()


def test_llms_redirect_to_home_fails():
    start = "https://elihickox.com/llms.txt"
    home = "https://elihickox.com/"
    transport = Script({start: hop(start, 301, {"location": home, "content-type": "text/html"}, b"moved")})
    report = run(transport, paths=("/llms.txt",))
    request = report["requests"][0]
    assert request["ordinal"] == 0 and request["cold_state"] == "UNKNOWN"
    assert not request["ok"]
    assert any("path changed from /llms.txt to /" in error for error in request["errors"])
    assert not report["ok"]


def test_external_and_relative_redirects():
    start = "https://elihickox.com/healthz"
    evil = urljoin(start, "//evil.com/healthz")
    absolute = "https://example.com/healthz"
    transport = Script({start: hop(start, 301, {"location": "//evil.com/healthz"})})
    report = run(transport)
    assert evil.startswith("https://evil.com/")
    assert transport.calls[0][0] == start
    assert all("evil.com" not in url for url, _ua in transport.calls)
    assert any("external redirect" in error for error in report["requests"][0]["errors"])

    transport = Script({start: hop(start, 301, {"location": absolute})})
    report = run(transport)
    assert transport.calls[0][0] == start
    assert all("example.com" not in url for url, _ua in transport.calls)
    assert any("external redirect" in error for error in report["requests"][0]["errors"])

    relative = "https://www.elihickox.com/healthz"
    nxt = urljoin(relative, "foo/../healthz?via=rel")
    assert urlsplit(nxt).hostname == "www.elihickox.com"
    assert reach.normal_path(urlsplit(nxt).path) == "/healthz"
    assert urlsplit(nxt).query == "via=rel"
    transport = Script(
        {
            relative: hop(relative, 301, {"location": "foo/../healthz?via=rel"}),
            nxt: health(nxt),
        }
    )
    report = run(transport, hosts=("https://www.elihickox.com",))
    assert nxt in [url for url, _ua in transport.calls]
    assert report["requests"][0]["ok"]
    assert reach.classify_redirect(start, "http://elihickox.com/healthz", []) == "https downgrade"
    assert "nonstandard port" in reach.classify_redirect(start, "https://elihickox.com:8443/healthz", [])


def test_invalid_targets_are_not_fetched():
    transport = Script({})
    for host in (
        "https://evil.example",
        "ftp://elihickox.com",
        "https://user:pw@elihickox.com",
        "https://elihickox.com:8443",
    ):
        report = run(transport, hosts=(host,))
        assert transport.calls == []
        assert not report["ok"]
        assert report["requests"][0]["errors"]


def test_curl_command_does_not_follow_or_retry():
    command = reach.curl_command("https://elihickox.com/", reach.DEFAULT_UA, "h", "b")
    assert command[command.index("--proto") + 1] == "=http,https"
    assert command[command.index("--retry") + 1] == "0"
    assert command[command.index("--max-redirs") + 1] == "0"
    assert command[command.index("--connect-timeout") + 1] == "5"
    assert command[command.index("--max-time") + 1] == "15"
    assert "%{json}" in command
    assert "-L" not in command and "-k" not in command and "--insecure" not in command
    assert reach.DEFAULT_UA in command


def test_agent_specific_robots_and_content_signals():
    allowed = (
        "User-agent: *\nAllow: /\nContent-Signal: ai-train=no, search=yes, ai-input=yes\n"
    ).encode()
    assert reach.robots_restrictions(allowed, ["/", "/llms.txt"]) == []
    assert reach.validate_document("/robots.txt", 200, {"content-type": "text/plain"}, allowed) == []
    blocked = "User-agent: *\nAllow: /\n\nUser-agent: GPTBot\nDisallow: /\n".encode()
    errors = reach.validate_document("/robots.txt", 200, {"content-type": "text/plain"}, blocked)
    assert any("GPTBot disallow" in error and "/llms.txt" in error for error in errors)
    start = "https://elihickox.com/robots.txt"
    report = run(Script({start: hop(start, headers={"content-type": "text/plain"}, body=blocked)}), paths=("/robots.txt", "/llms.txt"))
    assert not report["ok"]
    assert any("GPTBot" in error for error in report["requests"][0]["errors"])
    page = {"content-type": "text/html", "x-robots-tag": "GPTBot: noindex"}
    assert reach.robot_header_errors(page)
    assert reach.validate_document("/", 200, {"content-type": "text/html", "x-robots-tag": "noai-training"}, b"<html>Eli</html>") == []
    assert reach.validate_document("/", 200, {"content-type": "text/html", "x-robots-tag": "ai-train=no"}, b"<html>Eli</html>") == []
    assert reach.validate_document("/", 200, {"content-type": "text/html", "x-robots-tag": "googlebot: noindex"}, b"<html>Eli</html>") == []


def test_json_shapes_skill_urls_and_digests():
    profile = {
        "profile": ["Eli"],
        "hiring_summary": "Eli Hickox",
        "notable_facts": [{"claim": "named inventor"}],
        "expertise": ["agentic architecture"],
        "canonical_pages": [{"path": "/"}],
        "career_highlights": ["RelateIQ"],
        "projects": [{"title": "Site"}],
        "works": [{"title": "Poems"}],
        "citation_guidance": ["cite Eli"],
    }
    errors = reach.shape_errors("/api/agent-profile", profile)
    assert any("profile must be an object" in error for error in errors)
    skills = index_body(["nope"])
    assert any("skill entry must be an object" in error for error in reach.validate_document(
        "/.well-known/agent-skills/index.json", 200, {"content-type": "application/json"}, skills
    ))
    bad = index_body([
        skill("http", "http://elihickox.com/.well-known/agent-skills/a/SKILL.md"),
        skill("user", "https://user@elihickox.com/.well-known/agent-skills/a/SKILL.md"),
        skill("port", "https://elihickox.com:8443/.well-known/agent-skills/a/SKILL.md"),
        skill("external", "https://evil.example/.well-known/agent-skills/a/SKILL.md"),
        skill("one", "https://elihickox.com/.well-known/agent-skills/a/SKILL.md"),
        skill("dup", "https://www.elihickox.com/.well-known/agent-skills/a/SKILL.md"),
        skill("digest", "https://elihickox.com/.well-known/agent-skills/b/SKILL.md", "sha256:not-a-digest"),
    ])
    errors = reach.validate_document("/.well-known/agent-skills/index.json", 200, {"content-type": "application/json"}, bad)
    assert any(error.startswith("skill url scheme") for error in errors)
    assert any("userinfo" in error for error in errors)
    assert any("skill url port" in error for error in errors)
    assert any(error.startswith("external skill url") for error in errors)
    assert any(error.startswith("duplicate skill path") for error in errors)
    assert any("malformed skill digest" in error for error in errors)
    start = "https://elihickox.com/.well-known/agent-skills/index.json"
    transport = Script({start: hop(start, headers={"content-type": "application/json"}, body=index_body([
        skill("external", "https://evil.example/.well-known/agent-skills/a/SKILL.md")
    ]))})
    report = run(transport, paths=("/.well-known/agent-skills/index.json",))
    assert not report["ok"]
    assert all("evil.example" not in url for url, _ua in transport.calls)
    assert any("external skill url" in error for error in report["requests"][0]["errors"])


def test_http_upgrade_probe_follows_https_and_rejects_plaintext():
    https = "https://elihickox.com/healthz"
    http = "http://elihickox.com/"
    transport = Script({https: health(https), http: hop(http, 200, {"content-type": "text/html"}, b"<html>Eli</html>")})
    report = run(transport)
    assert transport.calls[0][0].startswith("https://")
    http_request = next(item for item in report["requests"] if item["user_agent_label"] == "http-upgrade")
    assert not http_request["ok"]
    assert "http did not upgrade" in http_request["errors"]
    transport = Script({https: health(https)})
    report = run(transport)
    http_request = next(item for item in report["requests"] if item["initial_url"] == http)
    assert http_request["ok"]
    assert http_request["final_url"].startswith("https://")
    assert report["requests"][0]["ordinal"] == 0
    assert report["ok"]


def test_challenge_status_mime_and_network(tmp_path):
    assert any("cloudflare challenge" in error or "cf-mitigated" in error for error in reach.validate_document(
        "/", 200, {"content-type": "text/html", "cf-mitigated": "challenge"}, b"<html>Eli</html>"
    ))
    assert reach.validate_document(
        "/", 200, {"content-type": "text/html"}, b"<html>Eli <a href='/cdn-cgi/l/email-protection#abc'>mail</a></html>"
    ) == []
    assert any(error.startswith("status") for error in reach.validate_document("/healthz", 403, {"content-type": "application/json"}, b'{"status":"ok"}'))
    assert any("invalid json" in error for error in reach.validate_document("/healthz", 200, {"content-type": "application/json"}, b"{"))
    assert any(error.startswith("mime") for error in reach.validate_document("/healthz", 200, {"content-type": "text/plain"}, b'{"status":"ok"}'))
    calls = []

    class Once:
        def exchange(self, url, user_agent):
            calls.append(url)
            if urlsplit(url).scheme == "http":
                return hop(url, 301, {"location": "https://elihickox.com/"})
            raise OSError("network down")

    output = tmp_path / "reach.json"
    report = run(Once(), output=output)
    assert calls.count("https://elihickox.com/healthz") == 1
    assert output.exists() and not report["ok"]
    assert any("network down" in error for error in report["requests"][0]["errors"])


def test_bad_skill_hash_and_deadline(tmp_path):
    path = "/.well-known/agent-skills/hiring-brief/SKILL.md"
    body = b"# Eli\n\nnot the indexed bytes\n"
    start = "https://elihickox.com/.well-known/agent-skills/index.json"
    doc = "https://elihickox.com" + path
    transport = Script(
        {
            start: hop(start, headers={"content-type": "application/json"}, body=index_body([skill("hiring-brief", doc)])),
            doc: hop(doc, headers={"content-type": "text/markdown"}, body=body),
        }
    )
    report = run(transport, paths=("/.well-known/agent-skills/index.json",))
    assert not report["ok"]
    assert any("digest mismatch" in error for error in report["requests"][1]["errors"])
    clock = {"now": 0.0}

    class Late:
        def __call__(self):
            return clock["now"]

        def exchange(self, url, user_agent):
            clock["now"] = 1000.0
            calls.append(url)
            return health(url)

    calls = []
    report = run(Late(), paths=("/healthz", "/llms.txt"), monotonic=Late(), output=tmp_path / "deadline.json")
    assert calls == ["https://elihickox.com/healthz"]
    assert (tmp_path / "deadline.json").exists()
    assert "deadline exceeded" in report["errors"] and not report["ok"]


def test_slow_response_and_extended_agents_keep_python_ua():
    start = "https://elihickox.com/healthz"
    slow = health(start)
    slow["time_total"] = 15.0
    transport = Script({start: slow})
    warned = run(transport)
    assert warned["ok"] and warned["requests"][0]["warnings"]
    failed = run(Script({start: slow}), fail_on_slow=True)
    assert not failed["ok"]
    seen = []

    class Record:
        def exchange(self, url, user_agent):
            seen.append(user_agent)
            if urlsplit(url).scheme == "http":
                return hop(url, 301, {"location": url.replace("http://", "https://", 1)})
            return health(url) if urlsplit(url).path == "/healthz" else html(url)

    report = run(Record(), extended=True)
    assert seen[0] == reach.DEFAULT_UA
    assert reach.EXTENDED_UAS[2] in seen
    assert "GPTBot/1.4" in reach.EXTENDED_UAS[2]
    assert "ChatGPT-User/1.0" in reach.EXTENDED_UAS[3]
    assert "PerplexityBot/1.0" in reach.EXTENDED_UAS[5]
    assert "Macintosh" in reach.EXTENDED_UAS[0] and reach.EXTENDED_UAS[1] == "curl/8.7.1"
    assert reach.EXTENDED_UAS[4] == "ClaudeBot"
    assert any(item["user_agent_label"] == reach.SIMULATED for item in report["requests"])


@pytest.mark.parametrize("path", PUBLIC_PATHS)
def test_public_route_contract(client, path):
    response = client.get(path)
    headers = {key.lower(): value for key, value in response.headers.items()}
    errors = reach.validate_document(path, response.status_code, headers, response.data)
    assert errors == [], (path, errors)
    if path.endswith("/SKILL.md"):
        index = client.get("/.well-known/agent-skills/index.json").get_json()
        match = next(item for item in index["skills"] if urlsplit(item["url"]).path == path)
        assert match["digest"] == "sha256:" + hashlib.sha256(response.data).hexdigest()


class FlaskTransport:
    def __init__(self, flask_client):
        self.client = flask_client

    def exchange(self, url, user_agent):
        parts = urlsplit(url)
        if parts.scheme == "http":
            dest = urlunsplit(("https", parts.netloc, parts.path or "/", "", ""))
            return hop(url, 301, {"location": dest})
        response = self.client.get(parts.path or "/", headers={"User-Agent": user_agent}, follow_redirects=False)
        headers = {key.lower(): value for key, value in response.headers.items()}
        return hop(url, response.status_code, headers, response.data)


def test_flask_transport_covers_skills_and_http_upgrade(client):
    report = run(
        FlaskTransport(client),
        hosts=reach.DEFAULT_HOSTS,
        paths=reach.BASE_PATHS,
    )
    assert report["requests"][0]["ordinal"] == 0
    assert report["requests"][0]["cold_state"] == "UNKNOWN"
    assert report["requests"][0]["initial_url"].startswith("https://")
    assert report["skill_checks"] and all(item["ok"] for item in report["skill_checks"])
    assert any(item["user_agent_label"] == "http-upgrade" and item["ok"] for item in report["requests"])
    assert report["ok"], [item for item in report["requests"] if not item["ok"]]
