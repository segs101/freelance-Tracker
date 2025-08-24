from flask import Flask, render_template,request, redirect, url_for,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


app = Flask(__name__)
app.config["SECRET_KEY"] = "gugugaga618$$"
app.debug = True

##CREATE DATABASE
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///project.db"

# Create the extension
db = SQLAlchemy(model_class=Base)
# Initialise the app with the extension
db.init_app(app)

##CREATE TABLE
# ------------------ MODELS ------------------
class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(250), nullable=False)
    description = db.Column(db.Text)
    client = db.Column(db.String(250), nullable=False)
    status = db.Column(db.String(250), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    deadline = db.Column(db.String(20), nullable=True)
    tasks = db.relationship("Task", back_populates="project", cascade="all, delete")

class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(250), nullable=False)
    status = db.Column(db.String(50), default="Pending")
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))
    deadline = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    project = db.relationship("Project", back_populates="tasks")

with app.app_context():
    db.create_all()


# ------------------ ROUTES ------------------




@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/projects", methods=["GET","POST"])
def project():
    # to add a new project
    if request.method == "POST":
        project_name = request.form.get("name")
        client = request.form.get("client")
        status = request.form.get("status")
        payment = request.form.get("price")
        deadline = request.form.get("deadline")
        description = request.form.get("description")


        new_project = Project(
            project_name=project_name,
            description=description,
            client=client,
            status=status,
            price=payment,
            deadline=deadline
        )
        
        db.session.add(new_project)
        db.session.commit()

        flash("Project added successfully!", "success")
        return redirect(url_for('project'))
    total_projects = Project.query.count()
    completed_projects = Project.query.filter_by(status="done").count()
    ongoing_projects = Project.query.filter_by(status="in-progress").count()
    not_started_projects = Project.query.filter_by(status="not-started").count()
    # to display all projects
    projects = Project.query.all()
    return render_template("project.html", 
                           projects=projects,total_projects=total_projects,completed_projects=completed_projects,
                           ongoing_projects=ongoing_projects
                           ,not_started_projects=not_started_projects)

# =============================================================================
@app.route("/update-project/<int:project_id>", methods=["GET", "POST"])
def update_project(project_id):
    print("FORM RECEIVED:", request.form.to_dict())
    project = Project.query.get_or_404(project_id)   # get the project or 404
    
    if request.method == "POST":
        project.project_name = request.form["project_name"]
        project.description = request.form["description"]
        project.client = request.form["client"]
        project.status = request.form["status"]
        project.price = request.form["price"]
        project.deadline = request.form["deadline"]

        db.session.commit()
        flash("Project updated successfully!", "success")
        return redirect(url_for("project"))

    return render_template("update_project.html", project=project)

# ====================================================================
@app.route("/delete-project/<int:project_id>", methods=["POST"])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash("Project deleted successfully!", "danger")
    return redirect(url_for("project"))

# ==============================================================
@app.route("/task", methods=["GET","POST"])
def task():
    
    if request.method == "POST":
        task_name = request.form.get("task_name")

        status = request.form.get("status")
        project = request.form.get("project")
        deadline = request.form.get("deadline")
        description = request.form.get("description")

        new_task = Task(
            task_name=task_name,

            status=status,
            project_id=project,
            deadline=deadline,
            description=description
        )
        
        db.session.add(new_task)
        db.session.commit()
        
        flash("Task added successfully!", "success")
        return redirect(url_for('task'))
    task = Task.query.all()
    project = Project.query.all()
    total_task = Task.query.count()
    completed_task =Task.query.filter_by(status="done").count()
    ongoing_task =Task.query.filter_by(status="in-progress").count()
    not_started_task =Task.query.filter_by(status="not-started").count()
    
    return render_template("task.html", projects=project,
                            tasks=task
                            ,total_task=total_task,completed_task=completed_task,
                            ongoing_task=ongoing_task,not_started_task=not_started_task)

# ===============================================================
@app.route("/update-task/<int:task_id>", methods=["GET", "POST"])
def update_task(task_id):
    print("FORM RECEIVED:", request.form.to_dict())
    task = Task.query.get_or_404(task_id)
    projects = Project.query.all()
    if request.method == "POST":
        task.task_name = request.form["task_name"]
        task.description = request.form["description"]
        task.status = request.form["status"]
        task.project_id = request.form["project"]
        task.deadline = request.form["deadline"]

        db.session.commit()
        flash("Task updated successfully!", "success")
        return redirect(url_for("task"))
    return render_template("task.html", projects=projects, task=task)
# ==================================================================
@app.route("/delete-task/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted successfully!", "danger")
    return redirect(url_for("task"))
# ==================================================================
@app.route("/income")
def income():
    return render_template("income.html")

@app.route("/vision")
def vision():
    return render_template("vision.html")

if __name__ == "__main__":
    app.run()