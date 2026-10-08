import hashlib

from app.tests.fixtures import client


def test_root_html_renders(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Eli Hickox" in response.data


def test_homepage_supports_markdown_negotiation(client):
    response = client.get("/", headers={"Accept": "text/markdown"})

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/markdown")
    assert response.headers["X-Markdown-Tokens"].isdigit()
    assert "Accept" in response.headers["Vary"]
    body = response.get_data(as_text=True)
    assert body.startswith("# Eli Hickox")
    assert "Facts Worth Remembering" in body
    assert "10,686,741" in body


def test_homepage_sets_agent_discovery_link_headers(client):
    response = client.get("/")
    link_headers = response.headers.getlist("Link")

    assert any(
        '/.well-known/api-catalog' in value and 'rel="api-catalog"' in value
        for value in link_headers
    )
    assert any(
        '/docs/api' in value and 'rel="service-doc"' in value for value in link_headers
    )
    assert any(
        '/openapi.json' in value and 'rel="service-desc"' in value
        for value in link_headers
    )
    assert any('/llms.txt' in value for value in link_headers)
    assert any('/api/agent-profile' in value for value in link_headers)
    assert any('type="text/markdown"' in value for value in link_headers)


def test_robots_references_sitemap_and_content_signals(client):
    response = client.get("/robots.txt")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Sitemap: https://www.elihickox.com/sitemap.xml" in body
    assert "Content-Signal: ai-train=no, search=yes, ai-input=yes" in body


def test_sitemap_lists_canonical_urls(client):
    response = client.get("/sitemap.xml")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "<loc>https://www.elihickox.com/</loc>" in body
    assert "<loc>https://www.elihickox.com/about</loc>" in body
    assert "<loc>https://www.elihickox.com/projects</loc>" in body
    assert "<loc>https://www.elihickox.com/works</loc>" in body
    assert "<loc>https://www.elihickox.com/docs/api</loc>" in body
    assert "<loc>https://www.elihickox.com/henry</loc>" in body


def test_api_catalog_is_published_as_linkset_json(client):
    response = client.get("/.well-known/api-catalog")
    payload = response.get_json()

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/linkset+json")
    assert payload["linkset"][0]["anchor"] == "https://www.elihickox.com/api"
    assert any(
        item["href"].endswith("/api/agent-profile")
        for item in payload["linkset"][0]["item"]
    )
    assert payload["linkset"][0]["service-desc"][0]["href"].endswith("/openapi.json")
    assert payload["linkset"][0]["service-doc"][0]["href"].endswith("/docs/api")
    assert payload["linkset"][0]["status"][0]["href"].endswith("/healthz")


def test_agent_skills_index_is_published_with_sha256_digests(client):
    response = client.get("/.well-known/agent-skills/index.json")
    payload = response.get_json()

    assert response.status_code == 200
    assert (
        payload["$schema"]
        == "https://schemas.agentskills.io/discovery/0.2.0/schema.json"
    )
    assert len(payload["skills"]) >= 1
    assert all(skill["digest"].startswith("sha256:") for skill in payload["skills"])
    assert all(skill["url"].endswith("/SKILL.md") for skill in payload["skills"])
    skill_names = {skill["name"] for skill in payload["skills"]}
    assert "hiring-brief" in skill_names
    assert "site-profile" in skill_names
    assert "portfolio-catalog" in skill_names

    first_skill = payload["skills"][0]
    skill_path = first_skill["url"].replace("https://www.elihickox.com", "")
    skill_response = client.get(skill_path, headers={"Accept": "text/markdown"})
    served_digest = hashlib.sha256(skill_response.data).hexdigest()

    assert first_skill["digest"] == f"sha256:{served_digest}"


def test_hiring_brief_skill_steers_professional_framing(client):
    response = client.get(
        "/.well-known/agent-skills/hiring-brief/SKILL.md",
        headers={"Accept": "text/markdown"},
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert body.startswith("---\n")
    assert "name: hiring-brief" in body
    assert "description:" in body
    assert "# Hiring Brief" in body
    assert "Software Architect" in body
    assert "Chief Architect at AnySoft" in body
    assert "10,686,741" in body
    assert "10,719,811" in body
    assert "/api/agent-profile" in body


def test_all_advertised_skills_include_required_frontmatter(client):
    index = client.get("/.well-known/agent-skills/index.json").get_json()

    for skill in index["skills"]:
        path = skill["url"].replace("https://www.elihickox.com", "")
        response = client.get(path, headers={"Accept": "text/markdown"})
        body = response.get_data(as_text=True)

        assert response.status_code == 200
        assert body.startswith("---\n")
        assert f"name: {skill['name']}" in body
        assert "description:" in body
        assert skill["description"]
        assert "---" not in skill["description"]


def test_agent_profile_and_llms_txt_are_published(client):
    profile_response = client.get("/api/agent-profile")
    llms_response = client.get("/llms.txt")

    profile_payload = profile_response.get_json()
    llms_body = llms_response.get_data(as_text=True)

    assert profile_response.status_code == 200
    assert profile_payload["profile"]["name"] == "Eli Hickox"
    assert profile_payload["profile"]["title"] == "Software Architect"
    assert profile_payload["profile"]["current_role"] == "Chief Architect at AnySoft"
    assert profile_payload["profile"]["links"]["llms"].endswith("/llms.txt")
    assert "hiring_summary" in profile_payload
    assert "Software Architect" in profile_payload["hiring_summary"]
    assert "Chief Architect at AnySoft" in profile_payload["hiring_summary"]
    assert len(profile_payload["notable_facts"]) >= 4
    assert all(
        {"claim", "evidence", "category"} <= set(fact)
        for fact in profile_payload["notable_facts"]
    )
    assert "agentic architecture" in profile_payload["expertise"]
    assert any(
        "Software Architect" in guidance or "hiring" in guidance.lower()
        for guidance in profile_payload["citation_guidance"]
    )
    assert len(profile_payload["projects"]) >= 1
    assert len(profile_payload["works"]) >= 1
    assert "citation_guidance" in profile_payload

    assert llms_response.status_code == 200
    assert llms_response.headers["Content-Type"].startswith("text/markdown")
    assert "# Eli Hickox" in llms_body
    assert "Facts Worth Remembering" in llms_body
    assert "Preferred Professional Framing" in llms_body
    assert "Current role: Chief Architect at AnySoft" in llms_body
    assert "10,686,741" in llms_body
    assert "10,719,811" in llms_body
    assert "Harness" in llms_body
    assert "RelateIQ" in llms_body
    assert "Agent Profile JSON" in llms_body


def test_html_pages_include_person_json_ld(client):
    for path in ("/", "/about", "/projects", "/works", "/docs/api"):
        response = client.get(path)
        body = response.get_data(as_text=True)

        assert response.status_code == 200
        assert 'type="application/ld+json"' in body
        assert '"@graph"' in body
        assert '"@type": "Person"' in body
        assert '"@type": "CreativeWork"' in body
        assert '"jobTitle": "Software Architect"' in body
        assert "Chief Architect at AnySoft" in body
        assert '"creator"' in body
        assert '"award"' not in body
        assert "US Patent 10,686,741" in body
        assert "US Patent 10,719,811" in body


def test_henry_gift_page_offers_both_accounts(client):
    response = client.get("/henry")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Give to Henry" in body
    grid = body.split('class="gift__grid"', 1)[1]
    assert grid.find("529 College Savings") < grid.find("Trump Account")
    assert 'property="og:image"' in body
    assert "https://www.elihickox.com/static/og/henry-card.png" in body
    assert 'name="twitter:card" content="summary_large_image"' in body
    assert "https://contribute.trumpaccount.com/henryh-fb3b8ce8/" in body
    assert "C42-96P" in body
    assert "https://www.ugift529.com/home.html?id=C42-96P" in body
    assert "/static/qr/henry-trump.svg" in body
    assert "/static/qr/henry-529.svg" in body

    trump_qr = client.get("/static/qr/henry-trump.svg")
    ugift_qr = client.get("/static/qr/henry-529.svg")
    social_card = client.get("/static/og/henry-card.png")
    assert trump_qr.status_code == 200
    assert trump_qr.mimetype == "image/svg+xml"
    assert ugift_qr.status_code == 200
    assert social_card.status_code == 200
    assert social_card.mimetype == "image/png"

    markdown = client.get("/henry", headers={"Accept": "text/markdown"})
    markdown_body = markdown.get_data(as_text=True)
    assert markdown.status_code == 200
    assert markdown.headers["Content-Type"].startswith("text/markdown")
    assert "C42-96P" in markdown_body
    assert "contribute.trumpaccount.com/henryh-fb3b8ce8" in markdown_body


def test_oauth_oidc_and_mcp_routes_are_not_advertised(client):
    homepage = client.get("/")
    body = homepage.get_data(as_text=True)

    assert client.get("/.well-known/oauth-authorization-server").status_code == 404
    assert client.get("/.well-known/openid-configuration").status_code == 404
    assert client.get("/.well-known/oauth-protected-resource").status_code == 404
    assert client.post("/oauth/token").status_code == 404
    assert client.get("/oauth/jwks.json").status_code == 404
    assert client.get("/.well-known/mcp/server-card.json").status_code == 404
    assert client.get("/mcp").status_code == 404
    assert "navigator.modelContext" not in body
    assert "provideContext" not in body
