#!venv/bin/python
from app import app

if __name__ == "__main__":
    app.debug = False
    app.run("0.0.0.0", 5000)
