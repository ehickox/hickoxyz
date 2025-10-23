from flask import render_template, redirect, send_from_directory, Response
from app import app
from app.controller import get_projects, get_works
import requests



@app.route("/robots.txt")
def robots():
    return send_from_directory(app.static_folder, 'robots.txt')

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html",
                            title="about - elihickox.com")


@app.route("/projects")
def projects():
    projects_list = get_projects()
    return render_template("projects.html", projects=projects_list, title="projects - elihickox.com")

@app.route("/patents")
def patents():
    return redirect("https://patents.justia.com/inventor/eli-spencer-hickox", code=302)

@app.route("/works")
def works():
    projects_list = get_works()
    return render_template("works.html", projects=projects_list, title="collected works - elihickox.com")

@app.route("/blog")
def blog():
    return redirect("https://www.ehlabs.net/blog/u/eli", code=302)


# @app.route("/radio/", defaults={'subpath': ''})
# @app.route("/radio/<path:subpath>")
# def radio(subpath):
#     if subpath:
#         return redirect(f"https://qsl.net/k6bcw/{subpath}", code=302)
#     else:
#         return redirect("https://qsl.net/k6bcw", code=302)
    

@app.route("/radio/", defaults={'subpath': ''})
@app.route("/radio/<path:subpath>")
def radio(subpath):
    target_url = f"https://qsl.net/k6bcw/{subpath}"
    response = requests.get(target_url)
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for name, value in response.raw.headers.items()
               if name.lower() not in excluded_headers]
    return Response(response.content, response.status_code, headers)
