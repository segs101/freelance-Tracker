import os
from flask import Flask, render_template,request, redirect, url_for,flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_migrate import Migrate
from datetime import datetime, date
from sqlalchemy import func,extract
from dateutil.relativedelta import relativedelta


app = Flask(__name__)
app.config["SECRET_KEY"] = "gugugaga618$$"
app.debug = True

##CREATE DATABASE
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL") or "sqlite:///project_tracker.db"

# Create the extension
db = SQLAlchemy(model_class=Base)
# Initialise the app with the extension
db.init_app(app)
migrate = Migrate(app, db)

today = datetime.now().date()     # get todays date
# get the monthly income percentage change
def get_percentage_monthly_income(last_month, this_month):
    if last_month > 0:
        percent_change = ((this_month - last_month) / last_month) * 100
    else:
        percent_change = 0   # avoid divide by zero
    return round(percent_change, 2)


# First day of this month
first_day_this_month = today.replace(day=1)

# First day of last month
first_day_last_month = first_day_this_month - relativedelta(months=1)



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
    income = db.relationship("Income", back_populates="project", cascade="all, delete")

class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(250), nullable=False)
    status = db.Column(db.String(50), default="Pending")
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))
    deadline = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    project = db.relationship("Project", back_populates="tasks")

class Income(db.Model):
    __tablename__ = "income"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), name="fk_income_project_id")
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default="Unpaid")
    date = db.Column(db.String, default=str(date.today()))
    due_date = db.Column(db.String(50), nullable=True)
    project = db.relationship("Project", back_populates="income")
    
with app.app_context():
    db.create_all()


# ------------------ ROUTES ------------------
from sqlalchemy import func
from datetime import datetime

def monthly_payments(date, amount, status):
    monthly = (
        db.session.query(
            func.strftime("%Y-%m", date).label("month"),  # SQLite
            func.sum(amount).label("total")
        )
        .filter(status.in_(["paid", "partially paid"]))
        .group_by("month")
        .order_by("month")
        .all()
    )

    results = [
        {"month": datetime.strptime(m, "%Y-%m").strftime("%B %Y"), "total": total or 0}
        for m, total in monthly
    ]
    return results

def total_income1(amount, status):
    this_month_income = (
    db.session.query(func.sum(amount))
    .filter(
        status.in_(["paid", "partially paid"]) 
      
    ).scalar()or 0)
    return this_month_income

def this_month_income1(amount, status):
    this_month_income = (
        db.session.query(func.sum(amount))
        .filter(
            func.strftime("%Y-%m", Income.date) == today.strftime("%Y-%m"),
            status.in_(["paid", "partially paid"])
        )
        .scalar() or 0
    )
    return this_month_income

def last_month_income1(amount, status, date):
    last_month_income = (
        db.session.query(func.sum(amount))
        .filter(
            extract('year', date) == first_day_last_month.year,
            extract('month', date) == first_day_last_month.month,
            status == "paid"
        )
        .scalar() or 0
    )
    return last_month_income


@app.route("/")
def index():
    projects = Project.query.count()
    task = Task.query.count()
    ongoing_task =Task.query.filter_by(status="in-progress").count()|0
    this_month = this_month_income1(Income.amount, Income.status)
    ongoing_projects = Project.query.filter_by(status="in-progress").count()
    last_months = last_month_income1(Income.amount, Income.status, Income.date)
    percentage = get_percentage_monthly_income(last_months,this_month)
    monthly_datas = monthly_payments(Income.date,Income.amount,Income.status)

    return render_template("dashboard.html", projects=projects,tasks=task,this_month_income=this_month,     pending_task=ongoing_task,percentage=percentage,monthly_data=monthly_datas,ongoing_projects=ongoing_projects)

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
@app.route("/income", methods=["GET","POST"])
def income():
    if request.method == "POST":
        project = request.form.get("project")
        amount = request.form.get("amount")
        status = request.form.get("status")
        due_date = request.form.get("due_date")
        
        new_income = Income(
            amount=amount,
            status=status,
            project_id=project,
            date=today,
            due_date=due_date
        )
        
        db.session.add(new_income)
        db.session.commit()
        
        flash("Income added successfully!", "success")
        return redirect(url_for('income'))  
    income = Income.query.all()
    project = Project.query.all()
     # Example values
    
    total_income = total_income1(Income.amount,Income.status)
    this_month_income = this_month_income1(Income.amount, Income.status)
    # Last month income
    last_month_income = last_month_income1(Income.amount, Income.status, Income.date)
    paid = Income.query.filter_by(status="paid").with_entities(db.func.sum(Income.amount)).scalar() or 0
    pending_income = Income.query.filter_by(status="unpaid").with_entities(db.func.sum(Income.amount)).scalar() or 0
    overdue_income = Income.query.filter_by(status="overdue").with_entities(db.func.sum(Income.amount)).scalar() or 0   
    percentage = get_percentage_monthly_income(last_month_income, this_month_income)  # call the function to get percentage change
    monthly_data = monthly_payments(Income.date,Income.amount,Income.status)
    
    return render_template("income.html", 
        projects=project,
        incomes=income
        ,total_income=total_income,
        this_month_income=this_month_income,
        pending_income=pending_income,
        overdue_income=overdue_income,
        percentage=percentage,
        paid = paid    
        ,monthly_data=monthly_data
        )

# =================================================================
@app.route("/update-income/<int:income_id>", methods=["GET", "POST"])
def update_income(income_id):
    income = Income.query.get_or_404(income_id)
    projects = Project.query.all()
    if request.method == "POST":
        income.amount = request.form["amount"]
        income.status = request.form["status"]
        income.project_id = request.form["project"]
        income.due_date = request.form["due_date"]

        db.session.commit()
        flash("Income updated successfully!", "success")
        return redirect(url_for("income"))
    return render_template("income.html", projects=projects, income=income)
# ==================================================================
@app.route("/delete-income/<int:income_id>", methods=["POST"])
def delete_income(income_id):
    income = Income.query.get_or_404(income_id)
    db.session.delete(income)
    db.session.commit()
    flash("Income deleted successfully!", "danger")
    return redirect(url_for("income"))



@app.route("/vision")
def vision():
    return render_template("vision.html")

if __name__ == "__main__":
    app.run()