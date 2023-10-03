from flask import render_template, redirect, send_from_directory
from app import app
from app.controller import get_projects, get_works



@app.route("/robots.txt")
def robots():
    return send_from_directory(app.static_folder, 'robots.txt')

@app.route("/")
def index():
    return render_template("v2/index.html")


@app.route("/about")
def about():
    return render_template("v2/about.html",
                            title="about - elihickox.com")


@app.route("/projects")
def projects():
    projects_list = get_projects()
    return render_template("v2/projects.html", projects=projects_list, title="projects - elihickox.com")

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

@app.route("/radio")
def radio():
    return redirect("https://qsl.net/ko6bcw", code=302)
