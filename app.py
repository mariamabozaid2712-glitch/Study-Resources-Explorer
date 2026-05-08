from flask import Flask, render_template, request
import sqlite3
import os

app = Flask(__name__)

# Database file path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "study_resources.db")


# Connect to SQLite database
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# Run SQL query and return rows
def query_db(query, params=()):
    conn = get_db_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


# Get summary numbers for Home page
def get_summary():
    total_resources = query_db(
        "SELECT COUNT(*) AS count FROM resources"
    )[0]["count"]

    total_subjects = query_db(
        "SELECT COUNT(DISTINCT subject) AS count FROM resources"
    )[0]["count"]

    total_sources = query_db(
        "SELECT COUNT(DISTINCT source) AS count FROM resources"
    )[0]["count"]

    total_types = query_db(
        "SELECT COUNT(DISTINCT type) AS count FROM resources"
    )[0]["count"]

    return {
        "total_resources": total_resources,
        "total_subjects": total_subjects,
        "total_sources": total_sources,
        "total_types": total_types
    }


# Home page
@app.route("/")
@app.route("/index.html")
def home():
    summary = get_summary()
    return render_template("index.html", **summary)


# Dashboard page
@app.route("/dashboard.html")
def dashboard():
    summary = get_summary()
    return render_template("dashboard.html", **summary)


# Explore Resources page
@app.route("/explorer.html")
def explorer():
    subject = request.args.get("subject", "")
    source = request.args.get("source", "")
    level = request.args.get("level", "")
    resource_type = request.args.get("type", "")

    # Pagination
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1

    if page < 1:
        page = 1

    per_page = 10
    offset = (page - 1) * per_page

    base_query = """
    FROM resources
    WHERE 1=1
    """

    params = []

    if subject:
        base_query += " AND subject = ?"
        params.append(subject)

    if source:
        base_query += " AND source = ?"
        params.append(source)

    if level:
        base_query += " AND level = ?"
        params.append(level)

    if resource_type:
        base_query += " AND type = ?"
        params.append(resource_type)

    # Count all matching resources
    count_query = "SELECT COUNT(*) AS total " + base_query
    total_resources = query_db(count_query, params)[0]["total"]

    # Calculate total pages
    total_pages = (total_resources + per_page - 1) // per_page

    if total_pages == 0:
        total_pages = 1

    if page > total_pages:
        page = total_pages
        offset = (page - 1) * per_page

    # Get resources for the current page only
    data_query = """
    SELECT subject, title, source, type, level, link
    """ + base_query + """
    ORDER BY subject, title
    LIMIT ? OFFSET ?
    """

    resources = query_db(data_query, params + [per_page, offset])

    # Index range shown above the table
    start_index = offset + 1 if total_resources > 0 else 0
    end_index = min(offset + len(resources), total_resources)

    # Dropdown values
    subjects = query_db("SELECT DISTINCT subject FROM resources ORDER BY subject")
    sources = query_db("SELECT DISTINCT source FROM resources ORDER BY source")
    levels = query_db("SELECT DISTINCT level FROM resources ORDER BY level")
    types = query_db("SELECT DISTINCT type FROM resources ORDER BY type")

    return render_template(
        "explorer.html",
        resources=resources,
        subjects=subjects,
        sources=sources,
        levels=levels,
        types=types,
        selected_subject=subject,
        selected_source=source,
        selected_level=level,
        selected_type=resource_type,
        page=page,
        total_pages=total_pages,
        total_resources=total_resources,
        start_index=start_index,
        end_index=end_index
    )


# SQL Insights page
@app.route("/insights.html")
def insights():
    resources_per_subject = query_db("""
        SELECT subject, COUNT(*) AS resource_count
        FROM resources
        GROUP BY subject
        ORDER BY resource_count DESC
    """)

    resources_per_source = query_db("""
        SELECT source, COUNT(*) AS resource_count
        FROM resources
        GROUP BY source
        ORDER BY resource_count DESC
    """)

    resources_per_level = query_db("""
        SELECT level, COUNT(*) AS resource_count
        FROM resources
        GROUP BY level
        ORDER BY resource_count DESC
    """)

    resources_per_type = query_db("""
        SELECT type, COUNT(*) AS resource_count
        FROM resources
        GROUP BY type
        ORDER BY resource_count DESC
    """)

    subjects_more_than_50 = query_db("""
        SELECT subject, COUNT(*) AS resource_count
        FROM resources
        GROUP BY subject
        HAVING resource_count > 50
        ORDER BY resource_count DESC
    """)

    return render_template(
        "insights.html",
        resources_per_subject=resources_per_subject,
        resources_per_source=resources_per_source,
        resources_per_level=resources_per_level,
        resources_per_type=resources_per_type,
        subjects_more_than_50=subjects_more_than_50
    )


if __name__ == "__main__":
    app.run(debug=True)