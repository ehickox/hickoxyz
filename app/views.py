from flask import render_template, redirect
from app import app
from app.controller import get_projects, get_last_years_commits, get_works


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


@app.route("/works")
def works():
    projects_list = get_works()
    return render_template("works.html", projects=projects_list, title="collected works - elihickox.com")

@app.route("/blog")
def blog():
    return redirect("https://www.ehlabs.net/blog/u/eli", code=302)
