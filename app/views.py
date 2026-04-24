import hashlib
import html
import os
import re
from typing import Iterable

import requests
from flask import Response, abort, jsonify, redirect, render_template, request

from app import app
from app.controller import get_projects, get_works

SITE_URL = os.environ.get("SITE_URL", "https://www.elihickox.com").rstrip("/")
SITE_NAME = "Eli Hickox"
SITE_DESCRIPTION = (
    "Software Architect based in the San Francisco Bay Area, specializing in "
    "agentic architecture, AI infrastructure, and scalable systems."
)
PUBLIC_EMAIL = "eli@elihickox.com"

HTML_ENDPOINTS = {"index", "about", "projects", "works", "docs_api"}
HOME_DISCOVERY_LINKS = (
    '</.well-known/api-catalog>; rel="api-catalog"',
    '</docs/api>; rel="service-doc"; type="text/html"',
    '</openapi.json>; rel="service-desc"; type="application/openapi+json"',
    '</llms.txt>; rel="describedby"; type="text/markdown"',
    '</api/agent-profile>; rel="describedby"; type="application/json"',
    '</.well-known/agent-skills/index.json>; rel="describedby"; type="application/json"',
)


def absolute_url(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    normalized = path if path.startswith("/") else f"/{path}"
    return f"{SITE_URL}{normalized}"


def canonical_pages() -> list[dict[str, str]]:
    return [
        {
            "endpoint": "index",
            "path": "/",
            "canonical_url": absolute_url("/"),
            "title": "Home",
            "description": "Homepage and public profile overview for Eli Hickox.",
        },
        {
            "endpoint": "about",
            "path": "/about",
            "canonical_url": absolute_url("/about"),
            "title": "About",
            "description": "Career background and biography for Eli Hickox.",
        },
        {
            "endpoint": "projects",
            "path": "/projects",
            "canonical_url": absolute_url("/projects"),
            "title": "Projects",
            "description": "Selected software projects and portfolio highlights.",
        },
        {
            "endpoint": "works",
            "path": "/works",
            "canonical_url": absolute_url("/works"),
            "title": "Collected Works",
            "description": "Published literary works and creative writing.",
        },
        {
            "endpoint": "docs_api",
            "path": "/docs/api",
            "canonical_url": absolute_url("/docs/api"),
            "title": "API Docs",
            "description": "Human-readable documentation for the public site APIs.",
        },
    ]


def career_highlights() -> list[str]:
    return [
        "Built predictive systems and real-time content controls at RelateIQ, SalesforceIQ, and Einstein.",
        "Worked across infrastructure and security at Salesforce using AWS, Terraform, and Chef.",
        "Built experimentation, monitoring, and ingestion systems at Split Software.",
        "Designed reservation optimization systems at Lyric Hospitality.",
        "Built gateway, compliance, and analytics systems at Eaze.",
        "Worked on large-scale blockchain ingestion and investigations API infrastructure at Chainalysis.",
        "Currently focused on agentic architecture and AI infrastructure leadership at AnySoft.",
    ]


def site_profile() -> dict:
    return {
        "name": SITE_NAME,
        "title": "Software Architect",
        "location": "San Francisco Bay Area",
        "summary": SITE_DESCRIPTION,
        "canonical_homepage": absolute_url("/"),
        "contact_email": PUBLIC_EMAIL,
        "links": {
            "about": absolute_url("/about"),
            "projects": absolute_url("/projects"),
            "works": absolute_url("/works"),
            "api_docs": absolute_url("/docs/api"),
            "api_catalog": absolute_url("/.well-known/api-catalog"),
            "agent_profile": absolute_url("/api/agent-profile"),
            "llms": absolute_url("/llms.txt"),
            "skills_index": absolute_url("/.well-known/agent-skills/index.json"),
        },
        "social": {
            "github": "https://github.com/ehickox/",
            "gitlab": "https://gitlab.com/ehickox/",
            "linkedin": "https://www.linkedin.com/in/elihickox/",
            "x": "https://x.com/elihickox",
        },
    }


def serialize_project(project) -> dict:
    payload = {
        "title": project.title,
        "tagline": project.tagline,
        "date": project.date,
        "description": html_fragment_to_markdown(project.description),
        "copyright": project.copywrite,
    }
    if project.link:
        payload["link"] = project.link
    if project.download:
        payload["download"] = project.download
    if project.git_url:
        payload["repository"] = project.git_url
    return payload


def agent_profile_payload() -> dict:
    return {
        "profile": site_profile(),
        "canonical_pages": canonical_pages(),
        "career_highlights": career_highlights(),
        "projects": [serialize_project(project) for project in get_projects()],
        "works": [serialize_work(work) for work in get_works()],
        "citation_guidance": [
            "Use https://www.elihickox.com/ as the canonical homepage.",
            "Prefer canonical first-party pages and public JSON endpoints when citing Eli Hickox profile information.",
            "Use the public contact email only for relevant professional contact.",
        ],
    }


def serialize_work(work) -> dict:
    payload = {
        "title": work.title,
        "date": work.date,
        "description": html_fragment_to_markdown(work.description),
        "copyright": work.copywrite,
    }
    if work.download:
        payload["download"] = work.download
    return payload


def html_fragment_to_markdown(fragment: str) -> str:
    text = fragment
    replacements = (
        (r"<br\s*/?>", "\n"),
        (r"</p>", "\n\n"),
        (r"<p[^>]*>", ""),
        (r"<strong>(.*?)</strong>", r"**\1**"),
        (r"<em>(.*?)</em>", r"*\1*"),
        (r"<samp>(.*?)</samp>", r"`\1`"),
    )
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE | re.DOTALL)

    text = re.sub(
        r"<a\s+href=['\"]([^'\"]+)['\"][^>]*>(.*?)</a>",
        lambda match: f"[{strip_tags(match.group(2)).strip()}]({match.group(1)})",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    text = strip_tags(text)
    text = html.unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value)


def markdown_token_count(markdown_text: str) -> int:
    return len(re.findall(r"\S+", markdown_text))


def normalize_markdown(markdown_text: str) -> str:
    return markdown_text.strip() + "\n"


def append_vary(response: Response, value: str) -> None:
    existing = response.headers.get("Vary", "")
    values = [item.strip() for item in existing.split(",") if item.strip()]
    if value not in values:
        values.append(value)
    if values:
        response.headers["Vary"] = ", ".join(values)


def wants_markdown() -> bool:
    if request.method != "GET":
        return False
    best = request.accept_mimetypes.best_match(["text/html", "text/markdown"])
    if best != "text/markdown":
        return False
    return (
        request.accept_mimetypes["text/markdown"]
        > request.accept_mimetypes["text/html"]
    )


def markdown_response(markdown_text: str, status_code: int = 200) -> Response:
    normalized = normalize_markdown(markdown_text)
    response = Response(normalized, status=status_code)
    response.headers["Content-Type"] = "text/markdown; charset=utf-8"
    response.headers["X-Markdown-Tokens"] = str(markdown_token_count(normalized))
    append_vary(response, "Accept")
    return response


def render_markdown_or_html(template_name: str, markdown_text: str, **context):
    if wants_markdown():
        return markdown_response(markdown_text)
    return render_template(template_name, **context)


def list_markdown(items: Iterable[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def index_markdown() -> str:
    profile = site_profile()
    return (
        f"# {SITE_NAME}\n\n"
        "Software Architect based in the San Francisco Bay Area.\n\n"
        f"{profile['summary']}\n\n"
        "## Explore\n\n"
        f"- [About]({absolute_url('/about')})\n"
        f"- [Projects]({absolute_url('/projects')})\n"
        f"- [Collected Works]({absolute_url('/works')})\n"
        f"- [API Docs]({absolute_url('/docs/api')})\n\n"
        "## Contact\n\n"
        f"- Email: [{PUBLIC_EMAIL}](mailto:{PUBLIC_EMAIL})\n"
        "- LinkedIn: [elihickox](https://www.linkedin.com/in/elihickox/)\n"
        "- GitHub: [ehickox](https://github.com/ehickox/)\n"
        "- GitLab: [ehickox](https://gitlab.com/ehickox/)\n"
    )


def about_markdown() -> str:
    return (
        f"# About {SITE_NAME}\n\n"
        f"{SITE_DESCRIPTION}\n\n"
        "Eli Hickox is a software architect with experience spanning backend engineering, "
        "data systems, cloud infrastructure, and AI-adjacent platform design.\n\n"
        "## Career Highlights\n\n"
        f"{list_markdown(career_highlights())}\n\n"
        "## Explore More\n\n"
        f"- [Selected Projects]({absolute_url('/projects')})\n"
        f"- [Collected Works]({absolute_url('/works')})\n"
        f"- [Public API Docs]({absolute_url('/docs/api')})\n"
    )


def projects_markdown(projects_list) -> str:
    sections = ["# Selected Projects", ""]
    for project in projects_list:
        sections.append(f"## {project.title}")
        if project.tagline:
            sections.append(project.tagline)
        if project.date:
            sections.append(f"*{project.date}*")
        sections.append("")
        sections.append(html_fragment_to_markdown(project.description))
        links = []
        if project.link:
            links.append(f"[Visit]({project.link})")
        if project.download:
            links.append(f"[Download]({project.download})")
        if project.git_url:
            links.append(f"[Repository]({project.git_url})")
        if links:
            sections.append("")
            sections.append("Links: " + " | ".join(links))
        sections.append("")
    return "\n".join(sections).strip() + "\n"


def works_markdown(works_list) -> str:
    sections = ["# Collected Works", ""]
    for work in works_list:
        sections.append(f"## {work.title}")
        if work.date:
            sections.append(f"*{work.date}*")
        sections.append("")
        sections.append(html_fragment_to_markdown(work.description))
        if work.download:
            sections.append("")
            sections.append(f"Download: [Torrent]({work.download})")
        sections.append("")
    return "\n".join(sections).strip() + "\n"


def api_docs_markdown() -> str:
    public_endpoints = [
        "`GET /api` - API index and endpoint discovery",
        "`GET /api/agent-profile` - canonical agent-readable profile bundle",
        "`GET /api/profile` - public profile metadata",
        "`GET /api/projects` - selected projects as JSON",
        "`GET /api/works` - collected works as JSON",
        "`GET /healthz` - health status",
    ]
    discovery_endpoints = [
        "`GET /llms.txt` - concise markdown guide for LLMs and agents",
        "`GET /.well-known/api-catalog` - RFC 9727 API catalog",
        "`GET /.well-known/agent-skills/index.json` - agent skills discovery index",
        "`GET /openapi.json` - OpenAPI description",
        "`GET /sitemap.xml` - sitemap with canonical URLs",
        "`GET /robots.txt` - crawl and AI content preferences",
    ]
    return (
        "# API Documentation\n\n"
        "This site exposes a small read-only JSON API for profile and portfolio discovery, plus "
        "machine-readable discovery endpoints for agents.\n\n"
        "## Public Endpoints\n\n"
        f"{list_markdown(public_endpoints)}\n\n"
        "## Discovery Endpoints\n\n"
        f"{list_markdown(discovery_endpoints)}\n"
    )


def llms_markdown() -> str:
    profile = site_profile()
    projects_list = get_projects()
    works_list = get_works()
    return (
        f"# {SITE_NAME}\n\n"
        "This is the canonical agent-readable summary for Eli Hickox.\n\n"
        "## Identity\n\n"
        f"- Name: {profile['name']}\n"
        f"- Title: {profile['title']}\n"
        f"- Location: {profile['location']}\n"
        f"- Summary: {profile['summary']}\n"
        f"- Canonical homepage: {profile['canonical_homepage']}\n"
        f"- Public contact email: {profile['contact_email']}\n\n"
        "## Career Highlights\n\n"
        f"{list_markdown(career_highlights())}\n\n"
        "## Canonical Resources\n\n"
        f"- About: {absolute_url('/about')}\n"
        f"- Projects: {absolute_url('/projects')}\n"
        f"- Collected Works: {absolute_url('/works')}\n"
        f"- Agent Profile JSON: {absolute_url('/api/agent-profile')}\n"
        f"- Public API Docs: {absolute_url('/docs/api')}\n"
        f"- OpenAPI: {absolute_url('/openapi.json')}\n\n"
        "## Projects\n\n"
        f"{list_markdown([project.title for project in projects_list])}\n\n"
        "## Collected Works\n\n"
        f"{list_markdown([work.title for work in works_list])}\n\n"
        "## Citation Guidance\n\n"
        "- Prefer first-party canonical URLs from this site when citing profile information.\n"
        "- Use JSON endpoints for structured retrieval and page URLs for human-readable citations.\n"
    )


def skill_documents() -> dict[str, str]:
    return {
        "site-profile": (
            "# Site Profile Discovery\n\n"
            "Use this skill to discover Eli Hickox's public profile, contact details, and "
            "navigation surface.\n\n"
            "## Recommended Resources\n\n"
            f"- Homepage: {absolute_url('/')}\n"
            f"- About page: {absolute_url('/about')}\n"
            f"- Profile API: {absolute_url('/api/profile')}\n"
            f"- API docs: {absolute_url('/docs/api')}\n\n"
            "## Notes\n\n"
            "- Prefer canonical URLs from the sitemap when citing site pages.\n"
            "- Public contact email is listed in the profile API and homepage.\n"
        ),
        "portfolio-catalog": (
            "# Portfolio Catalog Discovery\n\n"
            "Use this skill to browse Eli Hickox's selected software projects and published works.\n\n"
            "## Recommended Resources\n\n"
            f"- Projects page: {absolute_url('/projects')}\n"
            f"- Works page: {absolute_url('/works')}\n"
            f"- Projects API: {absolute_url('/api/projects')}\n"
            f"- Works API: {absolute_url('/api/works')}\n"
            f"- OpenAPI document: {absolute_url('/openapi.json')}\n\n"
            "## Notes\n\n"
            "- Project descriptions are concise summaries suitable for agent consumption.\n"
            "- Use the API catalog for machine-readable discovery of the JSON API surface.\n"
        ),
    }


@app.after_request
def add_agent_headers(response: Response):
    if request.endpoint in HTML_ENDPOINTS:
        append_vary(response, "Accept")
        response.headers.add(
            "Link",
            f'<{request.path}>; rel="alternate"; type="text/markdown"',
        )

    if request.endpoint == "index":
        for link_header in HOME_DISCOVERY_LINKS:
            response.headers.add("Link", link_header)

    return response


@app.route("/robots.txt")
def robots():
    response = Response(
        "User-agent: *\n"
        "Allow: /\n"
        "Sitemap: "
        f"{absolute_url('/sitemap.xml')}\n"
        "Content-Signal: ai-train=no, search=yes, ai-input=no\n",
        mimetype="text/plain",
    )
    return response


@app.route("/sitemap.xml")
def sitemap():
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for page in canonical_pages():
        lines.extend(
            [
                "  <url>",
                f"    <loc>{page['canonical_url']}</loc>",
                "  </url>",
            ]
        )
    lines.append("</urlset>")
    return Response("\n".join(lines) + "\n", mimetype="application/xml")


@app.route("/")
def index():
    return render_markdown_or_html(
        "index.html",
        index_markdown(),
        canonical_url=absolute_url("/"),
    )


@app.route("/about")
def about():
    return render_markdown_or_html(
        "about.html",
        about_markdown(),
        title="about - elihickox.com",
        canonical_url=absolute_url("/about"),
    )


@app.route("/projects")
def projects():
    projects_list = get_projects()
    return render_markdown_or_html(
        "projects.html",
        projects_markdown(projects_list),
        projects=projects_list,
        title="projects - elihickox.com",
        canonical_url=absolute_url("/projects"),
    )


@app.route("/patents")
def patents():
    return redirect("https://patents.justia.com/inventor/eli-spencer-hickox", code=302)


@app.route("/works")
def works():
    works_list = get_works()
    return render_markdown_or_html(
        "works.html",
        works_markdown(works_list),
        projects=works_list,
        title="collected works - elihickox.com",
        canonical_url=absolute_url("/works"),
    )


@app.route("/blog")
def blog():
    return redirect("https://www.ehlabs.net/blog/u/eli?articles=true", code=302)


@app.route("/docs/api")
def docs_api():
    return render_markdown_or_html(
        "docs_api.html",
        api_docs_markdown(),
        title="api docs - elihickox.com",
        canonical_url=absolute_url("/docs/api"),
        public_endpoints=[
            {"method": "GET", "path": "/api", "description": "API index and endpoint discovery"},
            {
                "method": "GET",
                "path": "/api/agent-profile",
                "description": "Canonical profile bundle for agents",
            },
            {"method": "GET", "path": "/api/profile", "description": "Public profile metadata"},
            {"method": "GET", "path": "/api/projects", "description": "Selected projects as JSON"},
            {"method": "GET", "path": "/api/works", "description": "Collected works as JSON"},
            {"method": "GET", "path": "/healthz", "description": "Health status"},
        ],
        discovery_endpoints=[
            "/llms.txt",
            "/.well-known/api-catalog",
            "/.well-known/agent-skills/index.json",
            "/openapi.json",
            "/sitemap.xml",
            "/robots.txt",
        ],
    )


@app.route("/api")
def api_root():
    return jsonify(
        name="elihickox.com public API",
        version="1.0.0",
        public=True,
        agent_profile=absolute_url("/api/agent-profile"),
        profile=absolute_url("/api/profile"),
        projects=absolute_url("/api/projects"),
        works=absolute_url("/api/works"),
        openapi=absolute_url("/openapi.json"),
        documentation=absolute_url("/docs/api"),
        api_catalog=absolute_url("/.well-known/api-catalog"),
    )


@app.route("/llms.txt")
def llms_txt():
    return markdown_response(llms_markdown())


@app.route("/api/agent-profile")
def api_agent_profile():
    return jsonify(agent_profile_payload())


@app.route("/api/profile")
def api_profile():
    return jsonify(site_profile())


@app.route("/api/projects")
def api_projects():
    return jsonify(projects=[serialize_project(project) for project in get_projects()])


@app.route("/api/works")
def api_works():
    return jsonify(works=[serialize_work(work) for work in get_works()])


@app.route("/healthz")
def healthz():
    return jsonify(status="ok")


@app.route("/openapi.json")
def openapi():
    document = {
        "openapi": "3.1.0",
        "info": {
            "title": "elihickox.com API",
            "version": "1.0.0",
            "description": "Read-only API for profile, projects, works, and agent discovery.",
        },
        "servers": [{"url": SITE_URL}],
        "paths": {
            "/api": {
                "get": {
                    "summary": "Discover API endpoints",
                    "responses": {"200": {"description": "API index"}},
                }
            },
            "/api/agent-profile": {
                "get": {
                    "summary": "Get canonical agent profile bundle",
                    "responses": {"200": {"description": "Agent profile bundle"}},
                }
            },
            "/api/profile": {
                "get": {
                    "summary": "Get public profile metadata",
                    "responses": {"200": {"description": "Profile metadata"}},
                }
            },
            "/api/projects": {
                "get": {
                    "summary": "List selected projects",
                    "responses": {"200": {"description": "Projects list"}},
                }
            },
            "/api/works": {
                "get": {
                    "summary": "List collected works",
                    "responses": {"200": {"description": "Works list"}},
                }
            },
            "/healthz": {
                "get": {
                    "summary": "Health check",
                    "responses": {"200": {"description": "Service health"}},
                }
            },
        },
    }
    response = jsonify(document)
    response.headers["Content-Type"] = "application/openapi+json"
    return response


@app.route("/.well-known/api-catalog")
def api_catalog():
    payload = {
        "linkset": [
            {
                "anchor": absolute_url("/api"),
                "item": [
                    {
                        "href": absolute_url("/api/agent-profile"),
                        "type": "application/json",
                    },
                    {"href": absolute_url("/api/profile"), "type": "application/json"},
                    {"href": absolute_url("/api/projects"), "type": "application/json"},
                    {"href": absolute_url("/api/works"), "type": "application/json"},
                    {"href": absolute_url("/llms.txt"), "type": "text/markdown"},
                ],
                "service-desc": [
                    {
                        "href": absolute_url("/openapi.json"),
                        "type": "application/openapi+json",
                    }
                ],
                "service-doc": [
                    {"href": absolute_url("/docs/api"), "type": "text/html"}
                ],
                "status": [{"href": absolute_url("/healthz"), "type": "application/json"}],
            },
        ]
    }
    response = jsonify(payload)
    response.headers["Content-Type"] = (
        'application/linkset+json; profile="https://www.rfc-editor.org/info/rfc9727"'
    )
    return response


@app.route("/.well-known/agent-skills/index.json")
def agent_skills_index():
    skills = []
    for skill_name, document in skill_documents().items():
        normalized_document = normalize_markdown(document)
        digest = hashlib.sha256(normalized_document.encode("utf-8")).hexdigest()
        skills.append(
            {
                "name": skill_name,
                "type": "skill-md",
                "description": document.splitlines()[0].removeprefix("# ").strip(),
                "url": absolute_url(f"/.well-known/agent-skills/{skill_name}/SKILL.md"),
                "digest": f"sha256:{digest}",
            }
        )

    return jsonify(
        {
            "$schema": "https://schemas.agentskills.io/discovery/0.2.0/schema.json",
            "skills": skills,
        }
    )


@app.route("/.well-known/agent-skills/<skill_name>/SKILL.md")
def agent_skill_document(skill_name: str):
    document = skill_documents().get(skill_name)
    if document is None:
        abort(404)
    return markdown_response(document)


@app.route("/radio/", defaults={"subpath": ""})
@app.route("/radio/<path:subpath>")
def radio(subpath):
    target_url = f"https://qsl.net/k6bcw/{subpath}"
    response = requests.get(target_url)
    excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
    headers = [
        (name, value)
        for name, value in response.raw.headers.items()
        if name.lower() not in excluded_headers
    ]
    return Response(response.content, response.status_code, headers)
