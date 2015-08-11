from flask import render_template
from app import app
import controller

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    resume = "https://www.icloud.com/pages/AwBWCAESEOU8CQnJ3M3kFEYvX6Hxqw0aKmQ2Gp-X0T4SqBCfN1c-HZF8Ku8l_awERyo6yGzj3H0b0CRkvwjfRb9htQMCUCAQEEIGJNodczFQ7M68OHsNeDA-C3jjPff-FVEMIKYLrJ9IkT#Eli_Hickox_Resume"
    return render_template('about.html', resume=resume)

@app.route('/projects')
def projects():
    projects_list = controller.get_projects()
    return render_template('projects.html', projects=projects_list)
