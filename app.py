import os
import sqlite3
from flask import Flask, render_template, request, redirect, jsonify, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "civic-demo-secret-key"

DB_PATH = "civic.db"
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.template_filter("status_class")
def status_class_filter(status):
    if status == "Resolved":
        return "bg-green-100 text-green-700"
    if status == "In Progress":
        return "bg-blue-100 text-blue-700"
    if status == "Acknowledged":
        return "bg-yellow-100 text-yellow-700"
    if status == "Rejected":
        return "bg-red-100 text-red-700"
    return "bg-orange-100 text-orange-700"


app.jinja_env.globals["status_class"] = status_class_filter


SCHEMA = """
CREATE TABLE IF NOT EXISTS report (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  category TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  photo TEXT,
  resolution_photo TEXT,
  lat REAL,
  lng REAL,
  ward TEXT DEFAULT 'Ward 12',
  status TEXT DEFAULT 'Submitted',
  upvotes INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS status_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  report_id INTEGER NOT NULL,
  status TEXT NOT NULL,
  note TEXT,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scheme (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  category TEXT,
  description TEXT,
  eligibility TEXT,
  link TEXT,
  deadline TEXT,
  max_income INTEGER DEFAULT 99999999,
  allowed_categories TEXT DEFAULT 'General,SC,ST,OBC,EWS',
  min_age INTEGER DEFAULT 0,
  max_age INTEGER DEFAULT 120
);

CREATE TABLE IF NOT EXISTS career_item (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  type TEXT,
  title TEXT,
  description TEXT,
  link TEXT
);

CREATE TABLE IF NOT EXISTS job (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT,
  skill TEXT,
  wage TEXT,
  lat REAL,
  lng REAL,
  contact TEXT,
  description TEXT,
  posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def seed_schemes(db):
    schemes = [
        ("PM Kisan Samman Nidhi", "Agriculture", "Rs 6000/year income support to small farmers.", "Small and marginal farmers with land records", "https://pmkisan.gov.in", "31 Oct 2026", 500000, "General,SC,ST,OBC,EWS", 18, 120),
        ("Ayushman Bharat (PM-JAY)", "Health", "Rs 5 lakh health cover per family per year.", "Low income families", "https://pmjay.gov.in", "Open", 300000, "General,SC,ST,OBC,EWS", 0, 120),
        ("PM Awas Yojana", "Housing", "Financial assistance for building pucca houses.", "Homeless or kutcha house dwellers", "https://pmaymis.gov.in", "31 Dec 2026", 300000, "General,SC,ST,OBC,EWS", 18, 120),
        ("Sukanya Samriddhi Yojana", "Women", "High-interest savings scheme for girl children.", "Parents of girl child below 10 years", "https://www.india.gov.in", "Open", 99999999, "General,SC,ST,OBC,EWS", 0, 10),
        ("PM Ujjwala Yojana", "Women", "Free LPG connection for BPL women.", "Women from BPL households", "https://pmuy.gov.in", "Open", 200000, "General,SC,ST,OBC,EWS", 18, 120),
        ("Atal Pension Yojana", "Pension", "Guaranteed pension after 60 for unorganised sector.", "Unorganised sector workers aged 18-40", "https://npscra.nsdl.co.in", "Open", 500000, "General,SC,ST,OBC,EWS", 18, 40),
        ("PM Fasal Bima Yojana", "Agriculture", "Crop insurance against natural calamities.", "Farmers growing notified crops", "https://pmfby.gov.in", "Seasonal", 500000, "General,SC,ST,OBC,EWS", 18, 120),
        ("Skill India Mission", "Skill", "Free vocational training and certification.", "Youth aged 15-45, minimum 8th pass", "https://skillindia.gov.in", "Open", 99999999, "General,SC,ST,OBC,EWS", 15, 45),
        ("National Merit Scholarship", "Scholarship", "Rs 25000/year for top-performing students.", "Class 12 pass with 80 percent+ marks, family income below 8L", "https://scholarships.gov.in", "15 Nov 2026", 800000, "General,SC,ST,OBC,EWS", 17, 25),
        ("Post-Matric SC Scholarship", "Scholarship", "Full tuition and maintenance for SC students.", "SC students pursuing post-matric education", "https://scholarships.gov.in", "30 Nov 2026", 250000, "SC", 15, 30),
        ("Minority Merit Scholarship", "Scholarship", "Scholarship for minority community students.", "Minority students with 50 percent+ marks", "https://scholarships.gov.in", "20 Nov 2026", 200000, "General,OBC,EWS", 15, 30),
        ("PM Research Fellowship", "Scholarship", "Rs 80000/month for PhD scholars.", "PhD students in recognised institutions", "https://pmrf.in", "31 Dec 2026", 99999999, "General,SC,ST,OBC,EWS", 21, 35),
    ]
    for s in schemes:
        db.execute("""INSERT INTO scheme
            (name, category, description, eligibility, link, deadline, max_income, allowed_categories, min_age, max_age)
            VALUES (?,?,?,?,?,?,?,?,?,?)""", s)
    db.commit()


def seed_jobs(db):
    jobs = [
        ("Construction Helper", "Construction", "Rs 600/day", 12.9716, 77.5946, "9876543210", "Carrying materials, mixing cement. 8 AM to 5 PM."),
        ("Plumber Needed", "Plumbing", "Rs 800/day", 12.9750, 77.6000, "9876543211", "Fix leakage in apartment. Tools provided."),
        ("Delivery Partner", "Delivery", "Rs 500/day plus fuel", 12.9680, 77.5900, "9876543212", "Two-wheeler required. Flexible hours."),
        ("House Cleaning", "Cleaning", "Rs 400/day", 12.9730, 77.6050, "9876543213", "3BHK deep cleaning. 1 day work."),
        ("Electrician", "Electrical", "Rs 900/day", 12.9700, 77.5950, "9876543214", "Wiring work for new shop."),
        ("Painter", "Painting", "Rs 700/day", 12.9760, 77.6100, "9876543215", "2BHK interior painting. 3 days."),
        ("Gardener", "Gardening", "Rs 450/day", 12.9690, 77.5980, "9876543216", "Weekly garden maintenance."),
        ("Carpenter", "Carpentry", "Rs 850/day", 12.9720, 77.6020, "9876543217", "Furniture repair work."),
    ]
    for j in jobs:
        db.execute("""INSERT INTO job (title, skill, wage, lat, lng, contact, description)
                      VALUES (?,?,?,?,?,?,?)""", j)
    db.commit()


def seed_career(db):
    items = [
        ("Aptitude", "Free Aptitude Test - Quantitative", "Practice quantitative aptitude with 50 questions.", "https://www.indiabix.com"),
        ("Aptitude", "Logical Reasoning Test", "Sharpen your logical reasoning skills.", "https://www.indiabix.com/logical-reasoning/"),
        ("Course", "Python for Beginners", "Free 4-week Python course by Google.", "https://developers.google.com/edu/python"),
        ("Course", "Digital Marketing Basics", "Learn SEO, social media, and ads.", "https://learndigital.withgoogle.com"),
        ("Placement", "TCS Off-Campus Drive", "Freshers hiring for 2026 batch.", "https://www.tcs.com/careers"),
        ("Placement", "Infosys Walk-In", "Walk-in interviews for support roles.", "https://www.infosys.com/careers"),
        ("Scholarship Alert", "National Scholarship Portal Open", "Apply before 30 Nov for central scholarships.", "https://scholarships.gov.in"),
        ("Career Path", "How to become a Data Analyst", "Step-by-step guide with free resources.", "https://www.coursera.org"),
    ]
    for c in items:
        db.execute("INSERT INTO career_item (type, title, description, link) VALUES (?,?,?,?)", c)
    db.commit()


def seed_reports(db):
    demo = [
        ("garbage", "Garbage not collected for 3 days", "Bin overflowing near Gandhi Park.", None, 12.9716, 77.5946, "Ward 12", "Resolved", 8),
        ("pothole", "Big pothole on MG Road", "Dangerous for two-wheelers at night.", None, 12.9750, 77.6000, "Ward 12", "In Progress", 15),
        ("streetlight", "Streetlight not working", "Pole SL-42 dark since Monday.", None, 12.9680, 77.5900, "Ward 12", "Submitted", 4),
        ("power", "Power outage since morning", "No electricity since 7 AM.", None, 12.9730, 77.6050, "Ward 12", "In Progress", 12),
        ("drainage", "Drain blocked near school", "Water logging at school gate.", None, 12.9700, 77.5950, "Ward 12", "Resolved", 6),
        ("suggestion", "Add more buses on Route 12", "Crowded during peak hours.", None, 12.9760, 77.6100, "Ward 12", "Acknowledged", 22),
    ]
    for r in demo:
        cur = db.execute("""INSERT INTO report
            (category, title, description, photo, lat, lng, ward, status, upvotes)
            VALUES (?,?,?,?,?,?,?,?,?)""", r)
        rid = cur.lastrowid
        db.execute("INSERT INTO status_log (report_id, status, note) VALUES (?,?,?)",
                   (rid, "Submitted", "Report received"))
        if r[7] in ("Acknowledged", "In Progress", "Resolved"):
            db.execute("INSERT INTO status_log (report_id, status, note) VALUES (?,?,?)",
                       (rid, "Acknowledged", "Forwarded to department"))
        if r[7] in ("In Progress", "Resolved"):
            db.execute("INSERT INTO status_log (report_id, status, note) VALUES (?,?,?)",
                       (rid, "In Progress", "Worker assigned"))
        if r[7] == "Resolved":
            db.execute("INSERT INTO status_log (report_id, status, note) VALUES (?,?,?)",
                       (rid, "Resolved", "Work completed"))
    db.commit()


def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()
    if db.execute("SELECT COUNT(*) FROM scheme").fetchone()[0] == 0:
        seed_schemes(db)
    if db.execute("SELECT COUNT(*) FROM job").fetchone()[0] == 0:
        seed_jobs(db)
    if db.execute("SELECT COUNT(*) FROM career_item").fetchone()[0] == 0:
        seed_career(db)
    if db.execute("SELECT COUNT(*) FROM report").fetchone()[0] == 0:
        seed_reports(db)
    db.close()


# ---------- CITIZEN ROUTES ----------

@app.route("/")
def home():
    db = get_db()
    reports = db.execute("SELECT * FROM report ORDER BY id DESC LIMIT 3").fetchall()
    scheme = db.execute("SELECT * FROM scheme ORDER BY RANDOM() LIMIT 1").fetchone()
    job = db.execute("SELECT * FROM job ORDER BY RANDOM() LIMIT 1").fetchone()
    db.close()
    return render_template("home.html", reports=reports, scheme=scheme, job=job)


@app.route("/report/new", methods=["GET", "POST"])
def report_new():
    if request.method == "POST":
        photo = None
        f = request.files.get("photo")
        if f and f.filename:
            fn = secure_filename(f.filename)
            f.save(os.path.join(UPLOAD_FOLDER, fn))
            photo = fn
        db = get_db()
        cur = db.execute("""INSERT INTO report
            (category, title, description, photo, lat, lng, ward)
            VALUES (?,?,?,?,?,?,?)""",
            (request.form["category"], request.form["title"],
             request.form.get("description", ""), photo,
             request.form.get("lat") or None,
             request.form.get("lng") or None,
             "Ward 12"))
        rid = cur.lastrowid
        db.execute("INSERT INTO status_log (report_id, status, note) VALUES (?,?,?)",
                   (rid, "Submitted", "Report received"))
        db.commit()
        db.close()
        return redirect(f"/reports/{rid}")
    cat = request.args.get("cat", "garbage")
    return render_template("report_new.html", cat=cat)


@app.route("/reports")
def reports():
    db = get_db()
    rows = db.execute("SELECT * FROM report ORDER BY id DESC").fetchall()
    db.close()
    return render_template("reports.html", reports=rows)


@app.route("/reports/<int:rid>")
def report_detail(rid):
    db = get_db()
    r = db.execute("SELECT * FROM report WHERE id=?", (rid,)).fetchone()
    logs = db.execute("SELECT * FROM status_log WHERE report_id=? ORDER BY id", (rid,)).fetchall()
    db.close()
    if not r:
        return "Not found", 404
    return render_template("report_detail.html", r=r, logs=logs)


@app.route("/reports/<int:rid>/upvote", methods=["POST"])
def report_upvote(rid):
    db = get_db()
    db.execute("UPDATE report SET upvotes = upvotes + 1 WHERE id=?", (rid,))
    db.commit()
    db.close()
    return jsonify({"ok": True})


@app.route("/map")
def map_view():
    return render_template("map.html")


# ---------- SERVICES ----------

@app.route("/services")
def services():
    return render_template("services.html")


@app.route("/schemes")
def schemes():
    db = get_db()
    q = request.args.get("q", "").strip()
    if q:
        rows = db.execute("SELECT * FROM scheme WHERE name LIKE ? OR category LIKE ? ORDER BY name",
                          (f"%{q}%", f"%{q}%")).fetchall()
    else:
        rows = db.execute("SELECT * FROM scheme ORDER BY category, name").fetchall()
    db.close()
    return render_template("schemes.html", schemes=rows, q=q)


@app.route("/schemes/<int:sid>")
def scheme_detail(sid):
    db = get_db()
    s = db.execute("SELECT * FROM scheme WHERE id=?", (sid,)).fetchone()
    db.close()
    if not s:
        return "Not found", 404
    return render_template("scheme_detail.html", s=s)


@app.route("/scholarships", methods=["GET", "POST"])
def scholarships():
    results = []
    form = {}
    if request.method == "POST":
        form = {
            "age": request.form.get("age", ""),
            "income": request.form.get("income", ""),
            "category": request.form.get("category", ""),
        }
        try:
            age = int(form["age"])
            income = int(form["income"])
            cat = form["category"]
            db = get_db()
            rows = db.execute("SELECT * FROM scheme WHERE category='Scholarship'").fetchall()
            db.close()
            for r in rows:
                allowed = [c.strip() for c in (r["allowed_categories"] or "").split(",")]
                if (cat in allowed and income <= (r["max_income"] or 0)
                        and (r["min_age"] or 0) <= age <= (r["max_age"] or 120)):
                    results.append(dict(r))
        except (ValueError, TypeError):
            pass
    return render_template("scholarships.html", results=results, form=form)


@app.route("/career")
def career():
    db = get_db()
    rows = db.execute("SELECT * FROM career_item ORDER BY type, title").fetchall()
    db.close()
    grouped = {}
    for r in rows:
        grouped.setdefault(r["type"], []).append(r)
    return render_template("career.html", grouped=grouped)


@app.route("/jobs")
def jobs():
    db = get_db()
    skill = request.args.get("skill", "").strip()
    q = "SELECT * FROM job"
    params = []
    if skill:
        q += " WHERE skill LIKE ?"
        params.append(f"%{skill}%")
    q += " ORDER BY id DESC"
    rows = db.execute(q, params).fetchall()
    skills = db.execute("SELECT DISTINCT skill FROM job ORDER BY skill").fetchall()
    db.close()
    return render_template("jobs.html", jobs=rows, skills=skills, selected=skill)


@app.route("/jobs/new", methods=["GET", "POST"])
def job_new():
    if request.method == "POST":
        db = get_db()
        db.execute("""INSERT INTO job (title, skill, wage, lat, lng, contact, description)
                      VALUES (?,?,?,?,?,?,?)""",
                   (request.form["title"], request.form["skill"], request.form["wage"],
                    request.form.get("lat") or 12.97, request.form.get("lng") or 77.59,
                    request.form["contact"], request.form.get("description", "")))
        db.commit()
        db.close()
        return redirect("/jobs")
    return render_template("job_new.html")


@app.route("/jobs/<int:jid>")
def job_detail(jid):
    db = get_db()
    j = db.execute("SELECT * FROM job WHERE id=?", (jid,)).fetchone()
    db.close()
    if not j:
        return "Not found", 404
    return render_template("job_detail.html", j=j)


# ---------- ADMIN ----------

@app.route("/admin")
def admin_dashboard():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM report").fetchone()[0]
    submitted = db.execute("SELECT COUNT(*) FROM report WHERE status='Submitted'").fetchone()[0]
    progress = db.execute("SELECT COUNT(*) FROM report WHERE status='In Progress'").fetchone()[0]
    resolved = db.execute("SELECT COUNT(*) FROM report WHERE status='Resolved'").fetchone()[0]
    recent = db.execute("SELECT * FROM report ORDER BY id DESC LIMIT 8").fetchall()
    db.close()
    return render_template("admin_dashboard.html",
                           total=total, submitted=submitted,
                           progress=progress, resolved=resolved, recent=recent)


@app.route("/admin/complaints")
def admin_queue():
    db = get_db()
    status = request.args.get("status", "")
    category = request.args.get("category", "")
    q = "SELECT * FROM report WHERE 1=1"
    params = []
    if status:
        q += " AND status=?"
        params.append(status)
    if category:
        q += " AND category=?"
        params.append(category)
    q += " ORDER BY id DESC"
    rows = db.execute(q, params).fetchall()
    db.close()
    return render_template("admin_queue.html", reports=rows, status=status, category=category)


@app.route("/admin/complaints/<int:rid>", methods=["GET", "POST"])
def admin_detail(rid):
    db = get_db()
    if request.method == "POST":
        new_status = request.form["status"]
        note = request.form.get("note", "")
        db.execute("UPDATE report SET status=? WHERE id=?", (new_status, rid))
        f = request.files.get("resolution_photo")
        if f and f.filename:
            fn = secure_filename(f.filename)
            f.save(os.path.join(UPLOAD_FOLDER, fn))
            db.execute("UPDATE report SET resolution_photo=? WHERE id=?", (fn, rid))
        db.execute("INSERT INTO status_log (report_id, status, note) VALUES (?,?,?)",
                   (rid, new_status, note or f"Status changed to {new_status}"))
        db.commit()
        db.close()
        return redirect(f"/admin/complaints/{rid}")
    r = db.execute("SELECT * FROM report WHERE id=?", (rid,)).fetchone()
    logs = db.execute("SELECT * FROM status_log WHERE report_id=? ORDER BY id", (rid,)).fetchall()
    db.close()
    if not r:
        return "Not found", 404
    return render_template("admin_detail.html", r=r, logs=logs)


# ---------- API ----------

@app.route("/api/reports")
def api_reports():
    db = get_db()
    rows = db.execute("SELECT id, category, title, status, lat, lng, upvotes, created_at FROM report ORDER BY id DESC").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


init_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)