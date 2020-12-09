import os
import sys

import pytest
import contextlib

from app import app


@pytest.fixture
def client():

    print("*****SETUP*****")

    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            yield client
    print("******TEARDOWN******")
