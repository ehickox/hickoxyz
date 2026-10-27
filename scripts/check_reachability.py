#!/usr/bin/env python3
"""Fetch and validate the public elihickox.com agent surface with curl."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import socket
import subprocess
import tempfile
import time
import urllib.robotparser
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

ALLOWED_HOSTS = frozenset({"elihickox.com", "www.elihickox.com"})
DEFAULT_HOSTS = ("https://elihickox.com", "https://www.elihickox.com")
DEFAULT_UA = "Python-urllib/3.11"
EXTENDED_UAS = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "curl/8.7.1",
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.4; +https://openai.com/gptbot",
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot",
    "ClaudeBot",
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)",
)
ROBOT_AGENTS = (DEFAULT_UA, "GPTBot", "ChatGPT-User", "ClaudeBot", "PerplexityBot")
WATCHED_ROBOTS = {"*", "python-urllib", "gptbot", "chatgpt-user", "claudebot", "perplexitybot"}
ROBOT_BLOCK = {"none", "noindex", "noai"}
API_PATHS = ("/api", "/api/agent-profile", "/api/profile", "/api/projects", "/api/works", "/healthz")
SIMULATED = "simulated; not a genuine crawler"
BASE_PATHS = (
    "/",
    "/robots.txt",
    "/llms.txt",
    "/api",
    "/api/agent-profile",
    "/api/profile",
    "/api/projects",
    "/api/works",
    "/openapi.json",
    "/healthz",
    "/.well-known/api-catalog",
    "/.well-known/agent-skills/index.json",
    "/sitemap.xml",
    "/docs/api",
)
MAIN_ROUTES = ("/", "/llms.txt", "/api/agent-profile", "/openapi.json", "/healthz")
MIME = {
    "/": "text/html",
    "/docs/api": "text/html",
    "/robots.txt": "text/plain",
    "/llms.txt": "text/markdown",
    "/sitemap.xml": "application/xml",
    "/openapi.json": "application/openapi+json",
    "/.well-known/api-catalog": "application/linkset+json",
    "/.well-known/agent-skills/index.json": "application/json",
    "/healthz": "application/json",
    "/api": "application/json",
    "/api/agent-profile": "application/json",
    "/api/profile": "application/json",
    "/api/projects": "application/json",
    "/api/works": "application/json",
}
JSON_KEYS = {
    "/api": ("name", "version", "public", "agent_profile", "profile", "projects", "works", "openapi", "documentation", "api_catalog"),
    "/api/profile": ("name", "title", "current_role", "summary", "canonical_homepage", "contact_email", "links"),
    "/api/agent-profile": ("profile", "hiring_summary", "notable_facts", "expertise", "canonical_pages", "career_highlights", "projects", "works", "citation_guidance"),
    "/api/projects": ("projects",),
    "/api/works": ("works",),
    "/openapi.json": ("openapi", "info", "paths"),
}
REDIRECTS = {301, 302, 303, 307, 308}
CHALLENGE = ("cf-chl", "challenge-platform", "cf-browser-verification", "error code: 1010", "just a moment", "checking your browser")
MAX_REDIRECTS = 4
MAX_BODY = 2 * 1024 * 1024
DEADLINE_S = 180.0
SLOW_S = 15.0
REDACT = {"set-cookie", "cookie", "authorization", "proxy-authorization"}


def media_type(value: str | None) -> str:
    return (value or "").split(";", 1)[0].strip().lower()


def expected_mime(path: str) -> str | None:
    return MIME.get(path) or ("text/markdown" if path.endswith("/SKILL.md") else None)


def normal_path(path: str) -> str:
    segments: list[str] = []
    for segment in (path or "/").split("/"):
        if segment in ("", "."):
            continue
        if segment == "..":
            if segments:
                segments.pop()
            continue
        segments.append(segment)
    return "/" + "/".join(segments)


def canonical(url: str) -> str:
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    port = parts.port
    netloc = host if port in (None, 80, 443) else f"{host}:{port}"
    return urlunsplit((parts.scheme.lower(), netloc, normal_path(parts.path), parts.query, ""))


def _port_ok(scheme: str, port: int | None) -> bool:
    return (scheme == "https" and port in (None, 443)) or (scheme == "http" and port in (None, 80))


def endpoint_problem(url: str) -> str | None:
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    if parts.scheme not in {"http", "https"}:
        return f"unsupported scheme {parts.scheme or 'missing'}"
    if host not in ALLOWED_HOSTS:
        return f"host not allowed {host or url}"
    if parts.username or parts.password:
        return "userinfo not allowed"
    if not _port_ok(parts.scheme, parts.port):
        return f"nonstandard port {parts.port}"
    return None


def classify_redirect(current: str, nxt: str, visited: list[str]) -> str | None:
    dst = urlsplit(nxt)
    host = (dst.hostname or "").lower()
    if dst.scheme not in {"http", "https"}:
        return f"unsupported redirect scheme {dst.scheme or 'missing'}"
    if host not in ALLOWED_HOSTS or dst.username or dst.password:
        return f"external redirect to {host or nxt}"
    if not _port_ok(dst.scheme, dst.port):
        return f"nonstandard port {dst.port}"
    if urlsplit(current).scheme == "https" and dst.scheme != "https":
        return "https downgrade"
    dest = canonical(nxt)
    if dest in {canonical(item) for item in visited} or dest == canonical(current):
        return "redirect loop"
    return None


def curl_command(url: str, user_agent: str, header_path: str, body_path: str) -> list[str]:
    return [
        "curl", "-sS", "--proto", "=http,https", "--retry", "0",
        "--connect-timeout", "5", "--max-time", "15", "--max-redirs", "0",
        "--max-filesize", str(MAX_BODY), "-D", header_path, "-o", body_path, "-A", user_agent,
        "-w", "%{json}", "--url", url,
    ]


def _num(value, kind):
    if value in (None, ""):
        return None
    try:
        return kind(value)
    except (TypeError, ValueError):
        return None


def parse_headers(raw: str) -> tuple[int | None, dict[str, str]]:
    blocks = [block.strip() for block in raw.replace("\r\n", "\n").split("\n\n") if block.strip()]
    if not blocks:
        return None, {}
    lines = blocks[-1].split("\n")
    status = None
    if lines and lines[0].lower().startswith("http/"):
        bits = lines[0].split()
        status = int(bits[1]) if len(bits) > 1 and bits[1].isdigit() else None
        lines = lines[1:]
    headers: dict[str, str] = {}
    for line in lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        if key in REDACT:
            continue
        value = value.strip()
        headers[key] = f"{headers[key]}, {value}" if key in headers else value
    return status, headers


def blank_hop(url: str, error: str) -> dict:
    return {
        "url": url, "status": None, "headers": {}, "body": b"", "remote_ip": None,
        "ssl_verify_result": None, "time_starttransfer": None, "time_total": None,
        "content_type": None, "error": error,
    }


class CurlTransport:
    def exchange(self, url: str, user_agent: str) -> dict:
        try:
            with tempfile.TemporaryDirectory(prefix="reach-") as tmp:
                header_path, body_path = str(Path(tmp) / "h"), str(Path(tmp) / "b")
                try:
                    proc = subprocess.run(
                        curl_command(url, user_agent, header_path, body_path),
                        capture_output=True, timeout=20, check=False,
                    )
                except subprocess.TimeoutExpired:
                    return blank_hop(url, "curl timed out")
                except OSError as exc:
                    return blank_hop(url, f"curl failed: {exc}")
                raw = proc.stdout.decode("utf-8", "replace").strip()
                try:
                    meta = json.loads(raw) if raw else {}
                except json.JSONDecodeError:
                    meta = {}
                header_file, body_file = Path(header_path), Path(body_path)
                status, headers = parse_headers(header_file.read_text("utf-8", "replace") if header_file.exists() else "")
                body = body_file.read_bytes()[: MAX_BODY + 1] if body_file.exists() else b""
                error = None
                if proc.returncode != 0:
                    error = proc.stderr.decode("utf-8", "replace").strip() or f"curl exit {proc.returncode}"
                if len(body) > MAX_BODY:
                    body = body[:MAX_BODY]
                    error = f"{error}; body exceeds 2MB" if error else "body exceeds 2MB"
                http_code = _num(meta.get("http_code"), int) or status
                if http_code == 0:
                    http_code = None
                content_type = meta.get("content_type") or headers.get("content-type")
                remote = meta.get("remote_ip") or None
                return {
                    "url": url, "status": http_code, "headers": headers, "body": body,
                    "remote_ip": remote or None, "ssl_verify_result": _num(meta.get("ssl_verify_result"), int),
                    "time_starttransfer": _num(meta.get("time_starttransfer"), float),
                    "time_total": _num(meta.get("time_total"), float),
                    "content_type": content_type or None, "error": error,
                }
        except Exception as exc:  # one attempt; caller records the error
            return blank_hop(url, f"{type(exc).__name__}: {exc}")


def challenge_errors(headers: dict, body: bytes) -> list[str]:
    errors = []
    if "challenge" in headers.get("cf-mitigated", "").lower():
        errors.append("cf-mitigated challenge")
    blob = "\n".join(f"{key}: {value}" for key, value in headers.items()).lower()
    text = re.sub(r"/cdn-cgi/l/email-protection\S*", "", body.decode("utf-8", "replace").lower())
    if "cf-chl" in blob or "challenge-platform" in blob or any(marker in text for marker in CHALLENGE):
        errors.append("cloudflare challenge")
    return errors


def robot_header_errors(headers: dict) -> list[str]:
    blocked = []
    for part in headers.get("x-robots-tag", "").split(","):
        text = part.strip()
        if not text:
            continue
        lower = text.lower()
        if lower == "noai-training" or lower.startswith("ai-train="):
            continue
        if ":" in text:
            left, right = [piece.strip().lower() for piece in text.split(":", 1)]
            if left in {"unavailable_after", "max-snippet", "max-image-preview", "max-video-preview"}:
                continue
            if left in ROBOT_BLOCK:
                blocked.append(left)
                continue
            if left in WATCHED_ROBOTS or left.split("/")[0] in WATCHED_ROBOTS:
                for directive in re.split(r"[;\s]+", right):
                    if directive in ROBOT_BLOCK:
                        blocked.append(f"{left}: {directive}")
            continue
        if lower in ROBOT_BLOCK:
            blocked.append(lower)
    return [f"robots header restricts access: {', '.join(blocked)}"] if blocked else []


def robots_restrictions(body: bytes, paths: list[str]) -> list[str]:
    parser = urllib.robotparser.RobotFileParser()
    parser.parse(body.decode("utf-8", "replace").splitlines())
    found = []
    for agent in ROBOT_AGENTS:
        blocked = [path for path in paths if path != "/robots.txt" and not parser.can_fetch(agent, f"https://elihickox.com{path}")]
        if blocked:
            found.append(f"{agent} disallow {', '.join(blocked)}")
    return found


def skill_url_problem(url: str) -> str | None:
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    if parts.scheme != "https":
        return f"skill url scheme {parts.scheme or 'missing'}"
    if host not in ALLOWED_HOSTS:
        return f"external skill url {url}"
    if parts.username or parts.password:
        return f"skill url userinfo {url}"
    if parts.port not in (None, 443):
        return f"skill url port {parts.port}"
    if not (parts.path or "").endswith("/SKILL.md"):
        return f"skill url path {parts.path or '/'}"
    return None


def _titles(items, label: str) -> list[str]:
    if not isinstance(items, list) or not items or any(not isinstance(item, dict) or not item.get("title") for item in items):
        return [f"{label} missing titled entries"]
    return []


def _object_list(items, label: str, fields: tuple[str, ...]) -> list[str]:
    if not isinstance(items, list) or not items:
        return [f"{label} must be a non-empty list"]
    for item in items:
        if not isinstance(item, dict) or any(not isinstance(item.get(field), str) or not item.get(field) for field in fields):
            return [f"{label} entries must be objects with {', '.join(fields)}"]
    return []


def shape_errors(path: str, payload) -> list[str]:
    if not isinstance(payload, dict):
        return ["json is not an object"]
    errors = [f"missing {key}" for key in JSON_KEYS.get(path, ()) if key not in payload]
    if path == "/api":
        if not isinstance(payload.get("version"), str) or not payload.get("version"):
            errors.append("api version")
        if not isinstance(payload.get("public"), bool):
            errors.append("api public flag")
    if path == "/healthz" and payload.get("status") != "ok":
        errors.append("health not ok")
    if path == "/api/profile":
        if not isinstance(payload.get("name"), str) or "Eli" not in payload.get("name", ""):
            errors.append("profile missing Eli")
        if not isinstance(payload.get("links"), dict):
            errors.append("profile links must be an object")
    if path == "/api/agent-profile":
        profile = payload.get("profile")
        if not isinstance(profile, dict):
            errors.append("profile must be an object")
        elif "Eli" not in str(profile.get("name", "")) or not isinstance(profile.get("links"), dict):
            errors.append("agent profile missing Eli")
        if not isinstance(payload.get("hiring_summary"), str):
            errors.append("hiring_summary type")
        errors += _titles(payload.get("projects"), "projects")
        errors += _titles(payload.get("works"), "works")
        facts = payload.get("notable_facts")
        if not isinstance(facts, list) or not facts or any(not isinstance(fact, dict) or not isinstance(fact.get("claim"), str) for fact in facts):
            errors.append("notable_facts missing claims")
        if not isinstance(payload.get("expertise"), list):
            errors.append("expertise type")
        errors += _object_list(payload.get("canonical_pages"), "canonical_pages", ("path",))
    if path in {"/api/projects", "/api/works"}:
        errors += _titles(payload.get("projects" if path.endswith("projects") else "works"), path)
    if path == "/openapi.json":
        info = payload.get("info")
        paths = payload.get("paths")
        if not isinstance(info, dict) or not isinstance(info.get("version"), str) or not info.get("version"):
            errors.append("openapi version")
        if not isinstance(paths, dict) or any(item not in paths for item in API_PATHS):
            errors.append("openapi missing api paths")
    if path == "/.well-known/api-catalog":
        linkset = payload.get("linkset")
        anchor = linkset[0].get("anchor") if isinstance(linkset, list) and linkset and isinstance(linkset[0], dict) else ""
        if not isinstance(linkset, list) or not isinstance(anchor, str) or not anchor.endswith("/api"):
            errors.append("api catalog missing linkset")
    if path == "/.well-known/agent-skills/index.json":
        skills = payload.get("skills")
        if payload.get("$schema") != "https://schemas.agentskills.io/discovery/0.2.0/schema.json" or not isinstance(skills, list) or not skills:
            errors.append("skills index shape")
        else:
            seen: set[str] = set()
            for item in skills:
                if not isinstance(item, dict):
                    errors.append("skill entry must be an object")
                    continue
                if not isinstance(item.get("name"), str) or not item.get("name"):
                    errors.append("skill name missing")
                digest = item.get("digest")
                if not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
                    errors.append("malformed skill digest")
                url = item.get("url")
                if not isinstance(url, str):
                    errors.append("skill url missing")
                    continue
                problem = skill_url_problem(url)
                if problem:
                    errors.append(problem)
                    continue
                normalized = normal_path(urlsplit(url).path)
                if normalized in seen:
                    errors.append(f"duplicate skill path {normalized}")
                seen.add(normalized)
    return errors


def validate_document(path: str, status: int | None, headers: dict, body: bytes) -> list[str]:
    errors = []
    if status != 200:
        errors.append(f"status {status}")
    errors += challenge_errors(headers, body)
    errors += robot_header_errors(headers)
    expected = expected_mime(path)
    got = media_type(headers.get("content-type"))
    if expected and got != expected:
        errors.append(f"mime {got or 'missing'} != {expected}")
        return errors
    if path == "/robots.txt" and status == 200:
        blocked = robots_restrictions(body, list(BASE_PATHS))
        if blocked:
            errors.append("robots disallow " + "; ".join(blocked))
        return errors
    if path == "/sitemap.xml":
        try:
            root = ET.fromstring(body)
        except ET.ParseError as exc:
            return errors + [f"sitemap xml: {exc}"]
        locs = [node.text or "" for node in root.iter() if node.tag.endswith("loc")]
        if not any("elihickox.com" in loc for loc in locs):
            errors.append("sitemap missing loc")
        return errors
    if expected == "text/html":
        text = body.decode("utf-8", "replace")
        if "Eli" not in text:
            errors.append("html missing Eli")
        if path == "/docs/api" and "API" not in text:
            errors.append("html missing API")
        return errors
    if expected == "text/markdown":
        text = body.decode("utf-8", "replace")
        if not re.search(r"(?m)^#\s+\S", text):
            errors.append("markdown missing heading")
        if "Eli" not in text:
            errors.append("markdown missing Eli")
        return errors
    if expected == "application/json" or expected and expected.endswith("+json"):
        try:
            payload = json.loads(body.decode("utf-8-sig"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            return errors + [f"invalid json: {exc}"]
        return errors + shape_errors(path, payload)
    if expected is None:
        errors.append(f"no validator for {path}")
    return errors


def lookup_dns(hosts: tuple[str, ...]) -> dict:
    found = {}
    for host in dict.fromkeys(urlsplit(item).hostname for item in hosts):
        if not host:
            continue
        previous = socket.getdefaulttimeout()
        socket.setdefaulttimeout(5)
        try:
            infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
            found[host] = {"addresses": sorted({item[4][0] for item in infos})}
        except OSError as exc:
            found[host] = {"addresses": [], "error": str(exc)}
        finally:
            socket.setdefaulttimeout(previous)
    return found


def join_url(host: str, path: str) -> str:
    return host.rstrip("/") + (path if path.startswith("/") else "/" + path)


def skill_paths(body: bytes) -> list[tuple[str, str, str]]:
    try:
        payload = json.loads(body.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError):
        return []
    found, seen = [], set()
    for skill in payload.get("skills") or []:
        if not isinstance(skill, dict):
            continue
        url = skill.get("url")
        if not isinstance(url, str) or skill_url_problem(url):
            continue
        digest = skill.get("digest")
        path = urlsplit(url).path
        if (
            normal_path(path) in seen
            or not isinstance(skill.get("name"), str)
            or not skill.get("name")
            or not isinstance(digest, str)
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest)
        ):
            continue
        seen.add(normal_path(path))
        found.append((str(skill["name"]), path, digest))
    return found


def public_hop(hop: dict) -> dict:
    return {
        "url": hop["url"], "status": hop["status"], "mime": media_type(hop.get("content_type")),
        "remote_ip": hop.get("remote_ip"), "ssl_verify_result": hop.get("ssl_verify_result"),
        "time_starttransfer": hop.get("time_starttransfer"), "time_total": hop.get("time_total"),
        "headers": hop.get("headers") or {}, "error": hop.get("error"), "body_bytes": len(hop.get("body") or b""),
    }


def write_json(path: str | Path, report: dict) -> None:
    Path(path).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_check(*, hosts=DEFAULT_HOSTS, paths=BASE_PATHS, extended=False, output=None, fail_on_slow=False,
              deadline_s=DEADLINE_S, transport=None, monotonic=None, lookup=True) -> dict:
    clock = monotonic or time.monotonic
    started = clock()
    transport = transport or CurlTransport()
    report: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(), "platform": platform.platform(),
        "cold_state": "UNKNOWN", "deadline_s": deadline_s, "default_user_agent": DEFAULT_UA,
        "extended": extended, "extended_user_agents": SIMULATED if extended else None,
        "dns": lookup_dns(tuple(hosts)) if lookup else {}, "requests": [], "skill_checks": [],
        "errors": [], "ok": True,
    }
    queue: list[tuple[str, str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    def enqueue(host: str, path: str, user_agent: str, label: str) -> None:
        key = (host, path, user_agent)
        if key not in seen:
            seen.add(key)
            queue.append(key + (label,))

    for host in hosts:
        for path in paths:
            enqueue(host, path, DEFAULT_UA, "default")
    if extended:
        for host in hosts:
            for path in MAIN_ROUTES:
                for user_agent in EXTENDED_UAS:
                    enqueue(host, path, user_agent, SIMULATED)
    documents: dict[tuple[str, str, str], bytes] = {}
    index = 0
    http_probes = False
    try:
        while True:
            if index >= len(queue):
                if http_probes:
                    break
                http_probes = True
                for host in hosts:
                    parts = urlsplit(host)
                    hostname = (parts.hostname or "").lower()
                    if parts.scheme == "https" and hostname in ALLOWED_HOSTS and parts.port in (None, 443) and not parts.username:
                        enqueue(f"http://{hostname}", "/", DEFAULT_UA, "http-upgrade")
                continue
            if clock() - started >= deadline_s:
                report["errors"].append("deadline exceeded")
                break
            host, path, user_agent, label = queue[index]
            index += 1
            initial = join_url(host, path)
            blocked_target = endpoint_problem(initial)
            if blocked_target:
                report["requests"].append({
                    "ordinal": len(report["requests"]), "cold_state": "UNKNOWN", "host": host, "path": path,
                    "final_path": path, "initial_url": initial, "final_url": initial, "user_agent": user_agent,
                    "user_agent_label": label, "peer_ip": None, "chain": [], "errors": [blocked_target],
                    "warnings": [], "ok": False,
                })
                continue
            current, chain, visited, policy = initial, [], [], None
            for hop_index in range(MAX_REDIRECTS + 1):
                if clock() - started >= deadline_s:
                    report["errors"].append("deadline exceeded")
                    break
                try:
                    hop = transport.exchange(current, user_agent)
                except Exception as exc:
                    hop = blank_hop(current, f"{type(exc).__name__}: {exc}")
                chain.append(hop)
                if hop.get("error") or hop.get("status") not in REDIRECTS:
                    break
                location = (hop.get("headers") or {}).get("location")
                if not location:
                    policy = "redirect missing location"
                    break
                nxt = urljoin(current, location)
                problem = classify_redirect(current, nxt, visited)
                if problem:
                    policy = problem
                    break
                if hop_index == MAX_REDIRECTS:
                    policy = "redirect limit"
                    break
                visited.append(current)
                current = nxt
            if not chain:
                break
            terminal = chain[-1]
            final_path = urlsplit(terminal["url"]).path or "/"
            errors, warnings = [], []
            for hop in chain:
                if hop.get("error"):
                    errors.append(hop["error"])
                if urlsplit(hop["url"]).scheme == "https" and hop.get("ssl_verify_result") not in (0, None):
                    errors.append(f"tls verify failed ({hop.get('ssl_verify_result')})")
            elapsed = sum(hop.get("time_total") or 0 for hop in chain)
            if elapsed >= SLOW_S or any((hop.get("time_total") or 0) >= SLOW_S for hop in chain):
                warnings.append(f"slow response {elapsed:.3f}s")
            path_ok = normal_path(path) == normal_path(final_path)
            final_scheme = urlsplit(terminal["url"]).scheme
            http_failed = urlsplit(initial).scheme == "http" and final_scheme != "https"
            if not path_ok:
                errors.append(f"path changed from {path} to {final_path}")
            elif http_failed:
                errors.append("http did not upgrade")
            if policy:
                errors.append(policy)
            transport_error = any(hop.get("error") for hop in chain)
            if path_ok and not http_failed and not policy and not transport_error:
                doc_headers = dict(terminal.get("headers") or {})
                if terminal.get("content_type"):
                    doc_headers["content-type"] = terminal["content_type"]
                body = terminal.get("body") or b""
                errors.extend(validate_document(path, terminal.get("status"), doc_headers, body))
                documents[(host, path, user_agent)] = body
                if label == "default" and path.endswith("/index.json"):
                    for _name, skill_path, _digest in skill_paths(body):
                        enqueue(host, skill_path, user_agent, label)
            report["requests"].append({
                "ordinal": len(report["requests"]), "cold_state": "UNKNOWN", "host": host, "path": path,
                "final_path": final_path, "initial_url": initial, "final_url": terminal["url"],
                "user_agent": user_agent, "user_agent_label": label, "peer_ip": terminal.get("remote_ip"),
                "chain": [public_hop(hop) for hop in chain], "errors": errors, "warnings": warnings,
                "ok": not errors and not (fail_on_slow and warnings),
            })
            if "deadline exceeded" in report["errors"]:
                break
    except Exception as exc:
        report["errors"].append(f"checker crashed: {exc}")
    for (host, path, user_agent), body in documents.items():
        if path != "/.well-known/agent-skills/index.json":
            continue
        for name, skill_path, digest in skill_paths(body):
            actual_body = documents.get((host, skill_path, user_agent))
            actual = hashlib.sha256(actual_body).hexdigest() if actual_body is not None else None
            ok = actual is not None and digest == f"sha256:{actual}"
            report["skill_checks"].append({"name": name, "path": skill_path, "expected": digest, "actual": f"sha256:{actual}" if actual else None, "ok": ok})
            if not ok:
                for request in report["requests"]:
                    if request["host"] == host and request["user_agent"] == user_agent and request["path"] == skill_path:
                        request["errors"].append(f"skill {name} digest mismatch")
                        request["ok"] = False
                if actual_body is None:
                    report["errors"].append(f"missing skill document {skill_path}")
    for request in report["requests"]:
        if request["path"] != "/robots.txt" or request["user_agent"] != DEFAULT_UA:
            continue
        body = documents.get((request["host"], "/robots.txt", DEFAULT_UA))
        if body is None:
            continue
        extra = []
        seen_paths: set[str] = set()
        for item in report["requests"]:
            if item["host"] != request["host"] or item["user_agent"] != DEFAULT_UA or item["path"] in seen_paths:
                continue
            if item.get("user_agent_label") == "http-upgrade":
                continue
            seen_paths.add(item["path"])
            if item["path"] not in BASE_PATHS:
                extra.append(item["path"])
        blocked = robots_restrictions(body, extra)
        if blocked and not any(err.startswith("robots disallow") for err in request["errors"]):
            request["errors"].append("robots disallow " + "; ".join(blocked))
            request["ok"] = False
    failed = [item for item in report["requests"] if not item["ok"]]
    report["summary"] = {
        "total": len(report["requests"]), "failed": len(failed),
        "warnings": sum(1 for item in report["requests"] if item["warnings"]),
        "ok": len(report["requests"]) - len(failed),
    }
    report["ok"] = not failed and not report["errors"]
    if output:
        write_json(output, report)
    return report


def summary_markdown(report: dict) -> str:
    summary = report.get("summary") or {}
    lines = [
        "# Reachability", "",
        f"{summary.get('failed', 0)} failed, {summary.get('warnings', 0)} warnings, {summary.get('ok', 0)} ok of {summary.get('total', 0)}.",
        "",
        "Failures are agent-facing regressions. `cf-mitigated: challenge`, `cf-chl`, `challenge-platform`, or error 1010 means Cloudflare challenged the client (the Python-urllib BIC block returned 403 and error 1010). A digest mismatch means a SKILL.md no longer matches the index. External, looping, and HTTPS-to-HTTP redirects fail. `Content-Signal: ai-train=no` is allowed. A 15s response is a warning unless `--fail-on-slow` is set. Cold-start state in this report is UNKNOWN.",
        "",
        "This job does not explain OpenAI retrieval's internal errors; that cause is still unresolved. Extended User-Agents are simulated, not genuine crawlers.",
        "",
        "See docs/AGENT_REACHABILITY.md and docs/rca/2026-10-27-agent-reachability.md.",
    ]
    details = []
    for request in report.get("requests") or []:
        if request.get("errors"):
            details.append(f"- `{request.get('initial_url')}` ({request.get('user_agent')}): {'; '.join(request['errors'])}")
    for error in report.get("errors") or []:
        details.append(f"- {error}")
    if details:
        lines[2:2] = ["", *details]
    return "\n".join(lines)


def print_report(report: dict) -> None:
    summary = report["summary"]
    print(f"{summary['failed']} failed, {summary['warnings']} warnings, {summary['ok']} ok, {summary['total']} checked")
    for request in report["requests"]:
        if request["errors"]:
            print(f"FAIL {request['initial_url']} {request['user_agent']}: {'; '.join(request['errors'])}")
        elif request["warnings"]:
            print(f"WARN {request['initial_url']}: {'; '.join(request['warnings'])}")
    for error in report["errors"]:
        print(f"FAIL {error}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check production reachability of elihickox.com")
    parser.add_argument("--output", default="reachability.json")
    parser.add_argument("--extended", action="store_true")
    parser.add_argument("--fail-on-slow", action="store_true")
    parser.add_argument("--deadline", type=float, default=DEADLINE_S)
    parser.add_argument("--summarize", metavar="REPORT")
    parser.add_argument("--host", action="append", dest="hosts")
    return parser.parse_args(argv)


def summarize_file(path: str) -> int:
    file = Path(path)
    text = summary_markdown(json.loads(file.read_text(encoding="utf-8"))) if file.exists() else f"Reachability report missing at {path}."
    print(text)
    destination = os.environ.get("GITHUB_STEP_SUMMARY")
    if destination:
        with open(destination, "a", encoding="utf-8") as handle:
            handle.write(text + "\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.summarize:
        return summarize_file(args.summarize)
    report = {"ok": False, "errors": [], "requests": [], "summary": {"failed": 1, "warnings": 0, "ok": 0, "total": 0}}
    try:
        report = run_check(
            hosts=tuple(args.hosts) if args.hosts else DEFAULT_HOSTS, extended=args.extended,
            output=args.output, fail_on_slow=args.fail_on_slow, deadline_s=args.deadline,
        )
    except Exception as exc:
        report["errors"].append(f"checker crashed: {exc}")
        report["ok"] = False
        try:
            write_json(args.output, report)
        except OSError:
            pass
    print_report(report)
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
