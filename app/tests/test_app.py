from app.tests.fixtures import client


def test_flask_app(client):
    """Test you can GET the app at the root URL"""

    rv = client.get("/")
    assert rv.data
