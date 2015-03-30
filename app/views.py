from flask import render_template
from app import app
import controller

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/projects')
def projects():
    projects_list = controller.get_projects()
    return render_template('projects.html', projects=projects_list)
