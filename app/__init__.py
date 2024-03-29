from flask import Flask, url_for, Blueprint
import os

app = Flask(__name__)
app.config["DEBUG"] = False
app.config["SECRET_KEY"] = "SECRET_KEY_CH1ng3me"

# Determines the destination of the build. Only usefull if you're using Frozen-Flask
app.config["FREEZER_DESTINATION"] = (
    os.path.dirname(os.path.abspath(__file__)) + "/../build"
)

# Function to easily find your assets
# In your template use <link rel=stylesheet href="{{ static('filename') }}">
app.jinja_env.globals["static"] = lambda filename: url_for("static", filename=filename)

from app import views
