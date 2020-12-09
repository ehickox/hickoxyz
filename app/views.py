from flask import render_template
from app import app
from app.controller import get_projects, get_last_years_commits, get_works


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    resume = "https://www.icloud.com/pages/AwBWCAESEOU8CQnJ3M3kFEYvX6Hxqw0aKmQ2Gp-X0T4SqBCfN1c-HZF8Ku8l_awERyo6yGzj3H0b0CRkvwjfRb9htQMCUCAQEEIGJNodczFQ7M68OHsNeDA-C3jjPff-FVEMIKYLrJ9IkT#Eli_Hickox_Resume"
    return render_template("about.html", resume=resume)


@app.route("/projects")
def projects():
    projects_list = get_projects()
    return render_template("projects.html", projects=projects_list)


@app.route("/works")
def works():
    projects_list = get_works()
    return render_template("works.html", projects=projects_list)


@app.route("/stats")
def stats():
    (
        commits_by_date,
        quarterly_totals,
        quarterly_avgs,
        exes_list,
    ) = get_last_years_commits()
    return render_template(
        "stats.html",
        commits_by_date=commits_by_date,
        quarterly_totals=quarterly_totals,
        quarterly_avgs=quarterly_avgs,
        exes_list=exes_list,
    )
