from flask import Flask, request, render_template_string, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "hostel_system_key"

# ================= DATABASE =================
conn = sqlite3.connect("hostel.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    name TEXT,
    gender TEXT,
    fee_paid INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT,
    hostel TEXT,
    room INTEGER
)
""")

conn.commit()

ROOM_LIMIT = 50

hostels = {
    "Heany": "female",
    "Ilanda": "female",
    "Napier": "female",
    "Weir": "male",
    "Chaminuka": "male"
}

# ================= HOME =================
@app.route("/")
def home():
    return """
    <h2>HOSTEL SYSTEM</h2>
    <a href='/student_login'>Student Login</a> |
    <a href='/admin_login'>Admin Login</a>
    """

# ================= ADMIN LOGIN =================
@app.route("/admin_login", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            session["admin"] = True
            return redirect("/admin")
        return "Wrong login"

    return """
    <form method='post'>
        <input name='username' placeholder='Username'><br>
        <input name='password' type='password' placeholder='Password'><br>
        <button>Login</button>
    </form>
    """

# ================= ADMIN =================
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/admin_login")

    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    cursor.execute("""
        SELECT b.id, s.name, s.gender, b.hostel, b.room
        FROM bookings b
        JOIN students s ON s.student_id=b.student_id
    """)
    bookings = cursor.fetchall()

    html = "<h1>ADMIN DASHBOARD</h1>"

    html += """
    <form method='post' action='/register'>
        <input name='student_id' placeholder='ID'>
        <input name='name' placeholder='Name'>
        <select name='gender'>
            <option>male</option>
            <option>female</option>
        </select>
        <select name='fee_paid'>
            <option value='1'>PAID</option>
            <option value='0'>NOT PAID</option>
        </select>
        <button>Register</button>
    </form>
    """

    html += "<h3>Students</h3>"
    for s in students:
        fee = "PAID" if s[3] == 1 else "NOT PAID"
        html += f"<p>{s[0]} - {s[1]} - {fee}</p>"

    html += "<h3>Bookings</h3>"
    for b in bookings:
        html += f"""
        <p>{b[1]} | {b[2]} | {b[3]} | Room {b[4]}
        <a href='/delete/{b[0]}'>Delete</a></p>
        """

    return html

# ================= REGISTER =================
@app.route("/register", methods=["POST"])
def register():
    if not session.get("admin"):
        return "Unauthorized"

    cursor.execute("""
        INSERT OR REPLACE INTO students VALUES (?,?,?,?)
    """, (
        request.form["student_id"],
        request.form["name"],
        request.form["gender"],
        request.form["fee_paid"]
    ))

    conn.commit()
    return redirect("/admin")

# ================= STUDENT LOGIN =================
@app.route("/student_login", methods=["GET","POST"])
def student_login():
    if request.method == "POST":
        sid = request.form["student_id"]

        cursor.execute("SELECT * FROM students WHERE student_id=?", (sid,))
        student = cursor.fetchone()

        if not student:
            return "NOT REGISTERED"

        session["student_id"] = sid
        return redirect("/book")

    return """
    <form method='post'>
        <input name='student_id' placeholder='Student ID'><br>
        <button>Login</button>
    </form>
    """

# ================= BOOK =================
@app.route("/book", methods=["GET","POST"])
def book():
    sid = session.get("student_id")
    if not sid:
        return redirect("/student_login")

    cursor.execute("SELECT * FROM students WHERE student_id=?", (sid,))
    student = cursor.fetchone()

    if student[3] == 0:
        return "FEES NOT PAID"

    gender = student[2]
    allowed = [h for h in hostels if hostels[h] == gender]

    if request.method == "POST":
        hostel = request.form["hostel"]
        room = int(request.form["room"])

        cursor.execute("SELECT * FROM bookings WHERE hostel=? AND room=?", (hostel, room))
        if cursor.fetchone():
            return "ROOM TAKEN"

        cursor.execute("""
            INSERT INTO bookings(student_id, hostel, room)
            VALUES (?,?,?)
        """, (sid, hostel, room))

        conn.commit()
        return "BOOKED SUCCESS"

    options = "".join([f"<option>{h}</option>" for h in allowed])

    return f"""
    <form method='post'>
        <select name='hostel'>{options}</select>
        <input name='room' placeholder='1-50'>
        <button>BOOK</button>
    </form>
    """

# ================= DELETE =================
@app.route("/delete/<int:bid>")
def delete(bid):
    if not session.get("admin"):
        return "Unauthorized"

    cursor.execute("DELETE FROM bookings WHERE id=?", (bid,))
    conn.commit()
    return redirect("/admin")

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)