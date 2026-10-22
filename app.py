from flask import Flask, jsonify, request, render_template
import sqlite3
from pathlib import Path
from datetime import date, timedelta

app = Flask(__name__)
DB_PATH = Path(__file__).with_name("smartattend.db")
SUBJECTS = [("Data Structures", "DS"), ("Python Programming", "PY"), ("Mathematics", "MATH"), ("Computer Organization", "COA")]
NAMES = ["Aarav Sharma","Aditi Verma","Arjun Singh","Ananya Gupta","Vihaan Mishra","Ishita Yadav","Reyansh Kumar","Saanvi Jain","Aditya Pandey","Myra Singh","Kabir Joshi","Kiara Agarwal","Dev Patel","Pari Saxena","Rudra Tiwari","Navya Das","Krish Malhotra","Diya Kapoor","Atharv Shukla","Sara Khan","Dhruv Bansal","Meera Nair","Vivaan Rao","Riya Chawla","Yash Thakur","Anvi Sinha","Advait Bose","Prisha Roy","Shaurya Gill","Tara Mehta"]

def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con

def init_db():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS students(roll INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS subjects(code TEXT PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS attendance(id INTEGER PRIMARY KEY AUTOINCREMENT, roll INTEGER NOT NULL REFERENCES students(roll) ON DELETE CASCADE, subject_code TEXT NOT NULL REFERENCES subjects(code), class_date TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('Present','Absent')), UNIQUE(roll,subject_code,class_date));
        """)
        if con.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
            con.executemany("INSERT INTO students(roll,name,email) VALUES(?,?,?)", [(i+1,n,f"student{i+1:02}@smartattend.demo") for i,n in enumerate(NAMES)])
        if con.execute("SELECT COUNT(*) FROM subjects").fetchone()[0] == 0:
            con.executemany("INSERT INTO subjects(name,code) VALUES(?,?)", [(n,c) for n,c in SUBJECTS])
        if con.execute("SELECT COUNT(*) FROM attendance").fetchone()[0] == 0:
            today = date.today()
            rows = []
            for d in range(1,11):
                day = (today-timedelta(days=d)).isoformat()
                for si, (_,code) in enumerate(SUBJECTS):
                    for roll in range(1,31):
                        absent = ((roll*3+d*2+si*5)%11) < (2+(roll%4))
                        rows.append((roll,code,day,"Absent" if absent else "Present"))
            con.executemany("INSERT OR IGNORE INTO attendance(roll,subject_code,class_date,status) VALUES(?,?,?,?)", rows)

def payload():
    with connect() as con:
        students = [dict(r) for r in con.execute("SELECT * FROM students ORDER BY roll")]
        subjects = [dict(r) for r in con.execute("SELECT * FROM subjects ORDER BY name")]
        records = [dict(r) for r in con.execute("""SELECT a.roll,s.name AS student_name,a.subject_code,sub.name AS subject_name,a.class_date,a.status
            FROM attendance a JOIN students s ON s.roll=a.roll JOIN subjects sub ON sub.code=a.subject_code
            ORDER BY a.class_date DESC, a.subject_code, a.roll""")]
    by_roll = {}
    for r in records:
        x = by_roll.setdefault(r["roll"], {"roll":r["roll"],"name":r["student_name"],"present":0,"held":0})
        x["held"] += 1
        x["present"] += r["status"] == "Present"
    stats = []
    for s in students:
        x = by_roll.get(s["roll"], {"present":0,"held":0})
        stats.append({**s, **x, "percentage": round(x["present"]*100/x["held"]) if x["held"] else 0})
    total = sum(x["held"] for x in stats)
    present = sum(x["present"] for x in stats)
    low = [s for s in stats if s["held"] and s["percentage"] < 75]
    today = date.today().isoformat()
    todays = [r for r in records if r["class_date"] == today]
    return {"students":students,"subjects":subjects,"records":records,"student_stats":stats,
        "metrics":{"total_students":len(students),"total_subjects":len(subjects),"overall":round(present*100/total) if total else 0,
        "below75":len(low),"low_students":low,"today_classes":len({r["subject_code"] for r in todays}),
        "today_present":sum(r["status"]=="Present" for r in todays),"today_records":len(todays)}}

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/api/bootstrap")
def bootstrap():
    return jsonify(payload())

@app.post("/api/attendance")
def save_attendance():
    data = request.get_json(silent=True) or {}
    code, day, rows = data.get("subject_code"), data.get("class_date"), data.get("records", [])
    if not code or not day or not isinstance(rows,list):
        return jsonify({"error":"Subject, date, and attendance records are required."}), 400
    with connect() as con:
        if not con.execute("SELECT 1 FROM subjects WHERE code=?", (code,)).fetchone():
            return jsonify({"error":"Unknown subject."}), 404
        for row in rows:
            if row.get("status") not in ("Present","Absent"):
                return jsonify({"error":"Status must be Present or Absent."}), 400
            con.execute("""INSERT INTO attendance(roll,subject_code,class_date,status) VALUES(?,?,?,?)
                ON CONFLICT(roll,subject_code,class_date) DO UPDATE SET status=excluded.status""",
                (row.get("roll"),code,day,row["status"]))
    return jsonify({"ok":True,"data":payload()})

@app.post("/api/students")
def add_student():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name","")).strip()
    email = str(data.get("email","")).strip()
    if not name:
        return jsonify({"error":"Student name is required."}), 400
    with connect() as con:
        roll = con.execute("SELECT COALESCE(MAX(roll),0)+1 FROM students").fetchone()[0]
        con.execute("INSERT INTO students(roll,name,email) VALUES(?,?,?)",(roll,name,email))
    return jsonify({"ok":True,"data":payload()}), 201

@app.delete("/api/students/<int:roll>")
def delete_student(roll):
    with connect() as con:
        cur = con.execute("DELETE FROM students WHERE roll=?",(roll,))
        if not cur.rowcount:
            return jsonify({"error":"Student not found."}), 404
    return jsonify({"ok":True,"data":payload()})

@app.post("/api/subjects")
def add_subject():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name","")).strip()
    code = str(data.get("code","")).strip().upper()
    if not name or not code:
        return jsonify({"error":"Subject name and code are required."}), 400
    try:
        with connect() as con:
            con.execute("INSERT INTO subjects(code,name) VALUES(?,?)",(code,name))
    except sqlite3.IntegrityError:
        return jsonify({"error":"That subject code already exists."}), 409
    return jsonify({"ok":True,"data":payload()}), 201

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
