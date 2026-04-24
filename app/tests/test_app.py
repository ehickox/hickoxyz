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
    assert response.get_data(as_text=True).startswith("# Eli Hickox")


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
    assert "Content-Signal: ai-train=no, search=yes, ai-input=no" in body


def test_sitemap_lists_canonical_urls(client):
    response = client.get("/sitemap.xml")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "<loc>https://www.elihickox.com/</loc>" in body
    assert "<loc>https://www.elihickox.com/about</loc>" in body
    assert "<loc>https://www.elihickox.com/projects</loc>" in body
    assert "<loc>https://www.elihickox.com/works</loc>" in body
    assert "<loc>https://www.elihickox.com/docs/api</loc>" in body


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

    first_skill = payload["skills"][0]
    skill_path = first_skill["url"].replace("https://www.elihickox.com", "")
    skill_response = client.get(skill_path, headers={"Accept": "text/markdown"})
    served_digest = hashlib.sha256(skill_response.data).hexdigest()

    assert first_skill["digest"] == f"sha256:{served_digest}"


def test_agent_profile_and_llms_txt_are_published(client):
    profile_response = client.get("/api/agent-profile")
    llms_response = client.get("/llms.txt")

    profile_payload = profile_response.get_json()
    llms_body = llms_response.get_data(as_text=True)

    assert profile_response.status_code == 200
    assert profile_payload["profile"]["name"] == "Eli Hickox"
    assert profile_payload["profile"]["links"]["llms"].endswith("/llms.txt")
    assert len(profile_payload["projects"]) >= 1
    assert len(profile_payload["works"]) >= 1
    assert "citation_guidance" in profile_payload

    assert llms_response.status_code == 200
    assert llms_response.headers["Content-Type"].startswith("text/markdown")
    assert "# Eli Hickox" in llms_body
    assert "Agent Profile JSON" in llms_body


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
