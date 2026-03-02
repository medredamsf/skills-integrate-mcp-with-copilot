"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""


from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
import sqlite3

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


# SQLite database setup
DB_PATH = os.path.join(current_dir, "activities.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            name TEXT PRIMARY KEY,
            description TEXT,
            schedule TEXT,
            max_participants INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            activity_name TEXT,
            email TEXT,
            PRIMARY KEY (activity_name, email),
            FOREIGN KEY (activity_name) REFERENCES activities(name)
        )
    """)
    conn.commit()
    # Pré-remplir si vide
    c.execute("SELECT COUNT(*) FROM activities")
    if c.fetchone()[0] == 0:
        default_activities = [
            ("Chess Club", "Learn strategies and compete in chess tournaments", "Fridays, 3:30 PM - 5:00 PM", 12, ["michael@mergington.edu", "daniel@mergington.edu"]),
            ("Programming Class", "Learn programming fundamentals and build software projects", "Tuesdays and Thursdays, 3:30 PM - 4:30 PM", 20, ["emma@mergington.edu", "sophia@mergington.edu"]),
            ("Gym Class", "Physical education and sports activities", "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM", 30, ["john@mergington.edu", "olivia@mergington.edu"]),
            ("Soccer Team", "Join the school soccer team and compete in matches", "Tuesdays and Thursdays, 4:00 PM - 5:30 PM", 22, ["liam@mergington.edu", "noah@mergington.edu"]),
            ("Basketball Team", "Practice and play basketball with the school team", "Wednesdays and Fridays, 3:30 PM - 5:00 PM", 15, ["ava@mergington.edu", "mia@mergington.edu"]),
            ("Art Club", "Explore your creativity through painting and drawing", "Thursdays, 3:30 PM - 5:00 PM", 15, ["amelia@mergington.edu", "harper@mergington.edu"]),
            ("Drama Club", "Act, direct, and produce plays and performances", "Mondays and Wednesdays, 4:00 PM - 5:30 PM", 20, ["ella@mergington.edu", "scarlett@mergington.edu"]),
            ("Math Club", "Solve challenging problems and participate in math competitions", "Tuesdays, 3:30 PM - 4:30 PM", 10, ["james@mergington.edu", "benjamin@mergington.edu"]),
            ("Debate Team", "Develop public speaking and argumentation skills", "Fridays, 4:00 PM - 5:30 PM", 12, ["charlotte@mergington.edu", "henry@mergington.edu"]),
        ]
        for name, desc, sched, maxp, emails in default_activities:
            c.execute("INSERT INTO activities (name, description, schedule, max_participants) VALUES (?, ?, ?, ?)", (name, desc, sched, maxp))
            for email in emails:
                c.execute("INSERT INTO participants (activity_name, email) VALUES (?, ?)", (name, email))
        conn.commit()
    conn.close()

init_db()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")



@app.get("/activities")
def get_activities():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM activities")
    activities_list = []
    for row in c.fetchall():
        c2 = conn.cursor()
        c2.execute("SELECT email FROM participants WHERE activity_name = ?", (row["name"],))
        participants = [r[0] for r in c2.fetchall()]
        activities_list.append({
            "name": row["name"],
            "description": row["description"],
            "schedule": row["schedule"],
            "max_participants": row["max_participants"],
            "participants": participants
        })
    conn.close()
    return {a["name"]: {k: v for k, v in a.items() if k != "name"} for a in activities_list}



@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM activities WHERE name = ?", (activity_name,))
    activity = c.fetchone()
    if not activity:
        conn.close()
        raise HTTPException(status_code=404, detail="Activity not found")
    c.execute("SELECT COUNT(*) FROM participants WHERE activity_name = ?", (activity_name,))
    count = c.fetchone()[0]
    if count >= activity["max_participants"]:
        conn.close()
        raise HTTPException(status_code=400, detail="Activity is full")
    c.execute("SELECT * FROM participants WHERE activity_name = ? AND email = ?", (activity_name, email))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Student is already signed up")
    c.execute("INSERT INTO participants (activity_name, email) VALUES (?, ?)", (activity_name, email))
    conn.commit()
    conn.close()
    return {"message": f"Signed up {email} for {activity_name}"}



@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM activities WHERE name = ?", (activity_name,))
    activity = c.fetchone()
    if not activity:
        conn.close()
        raise HTTPException(status_code=404, detail="Activity not found")
    c.execute("SELECT * FROM participants WHERE activity_name = ? AND email = ?", (activity_name, email))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")
    c.execute("DELETE FROM participants WHERE activity_name = ? AND email = ?", (activity_name, email))
    conn.commit()
    conn.close()
    return {"message": f"Unregistered {email} from {activity_name}"}
