"""
School Desk - a Streamlit UI for the student / teacher management code.

Run:
    pip install streamlit
    streamlit run app.py

It reads and writes the same school_data.json file your console program uses
(keep app.py in the same folder as that file).
"""

import hmac
import json
import re
from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd
import streamlit as st

DB = Path(__file__).with_name("school_data.json")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# --------------------------------------------------------------------------
# Data layer
# --------------------------------------------------------------------------
def load_data():
    data = {"students": [], "teachers": []}
    if DB.exists():
        try:
            content = DB.read_text(encoding="utf-8").strip()
            if content:
                loaded = json.loads(content)
                data["students"] = loaded.get("students", [])
                data["teachers"] = loaded.get("teachers", [])
        except json.JSONDecodeError:
            st.error("school_data.json is not valid JSON. Fix or delete it, then reload.")
    return data


def save(data):
    DB.write_text(json.dumps(data, indent=4), encoding="utf-8")


# --------------------------------------------------------------------------
# Classes (same structure as your console code, but they take values
# as arguments and return (ok, message) instead of using input()/print())
# --------------------------------------------------------------------------
class Persons(ABC):
    @abstractmethod
    def get_roles(self):
        ...

    @abstractmethod
    def register(self, data, **details):
        ...

    @staticmethod
    def validate_email(email):
        return bool(EMAIL_RE.match(email))


class Student(Persons):
    def get_roles(self):
        return "student"

    def register(self, data, name, age, email, roll_no):
        name, email, roll_no = name.strip(), email.strip(), roll_no.strip()
        if not name or not roll_no:
            return False, "Name and roll number are required."
        if not Persons.validate_email(email):
            return False, "Enter a valid email address, for example name@school.com."
        if any(s["roll_no"] == roll_no for s in data["students"]):
            return False, f"Roll number {roll_no} is already registered."
        data["students"].append(
            {"name": name, "age": int(age), "email": email, "roll_no": roll_no, "grades": {}}
        )
        save(data)
        return True, f"{name} is registered with roll number {roll_no}."

    def add_grade(self, data, roll_no, subject, marks):
        subject = subject.strip()
        if not subject:
            return False, "Enter a subject name."
        if not 0 <= marks <= 100:
            return False, "Marks must be between 0 and 100."
        for s in data["students"]:
            if s["roll_no"] == roll_no:
                verb = "Updated" if subject in s["grades"] else "Added"
                s["grades"][subject] = float(marks)
                save(data)
                return True, f"{verb} {subject}: {marks:g} for {s['name']}."
        return False, "Student not found."

    @staticmethod
    def average(student):
        grades = student.get("grades", {})
        return sum(grades.values()) / len(grades) if grades else None


class Teacher(Persons):
    def get_roles(self):
        return "teacher"

    def register(self, data, name, age, email, subject, emp_id):
        name, email, subject, emp_id = name.strip(), email.strip(), subject.strip(), emp_id.strip()
        if not name or not subject or not emp_id:
            return False, "Name, subject and employee ID are required."
        if not Persons.validate_email(email):
            return False, "Enter a valid email address, for example name@school.com."
        if any(t["emp_id"] == emp_id for t in data["teachers"]):
            return False, f"Employee ID {emp_id} is already registered."
        data["teachers"].append(
            {"name": name, "age": int(age), "email": email, "subject": subject, "emp_id": emp_id}
        )
        save(data)
        return True, f"{name} is registered as a {subject} teacher."


# --------------------------------------------------------------------------
# Look and feel
# --------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* No forced page background or text color: Streamlit's own light/dark theme
   (system default) decides those, so everything stays readable in both. */
html, body, .stApp, button, input, textarea, select,
[data-testid="stMarkdownContainer"] * {
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.block-container { padding-top: 2.2rem; max-width: 1080px; }

h1, h2, h3 { letter-spacing: -0.02em; font-weight: 800; }

/* The sidebar keeps its own dark navy with light text in both themes */
section[data-testid="stSidebar"] { background: #14213D; }
section[data-testid="stSidebar"] * { color: #E8EEF7 !important; }
section[data-testid="stSidebar"] h3 { font-size: 1.4rem; margin-bottom: 0.2rem; }
section[data-testid="stSidebar"] .stButton > button,
section[data-testid="stSidebar"] [data-testid="stDownloadButton"] > button {
    background: transparent; border: 1px solid #5B6B8C; border-radius: 10px;
}

/* Cards use a faint grey tint, so they work on light and dark backgrounds */
[data-testid="stMetric"] {
    background: rgba(128, 128, 128, 0.08);
    border: 1px solid rgba(128, 128, 128, 0.28);
    border-left: 4px solid #0F9D9A;
    border-radius: 12px;
    padding: 16px 18px;
}
[data-testid="stMetricValue"] { font-weight: 800; }

[data-testid="stForm"] {
    background: rgba(128, 128, 128, 0.06);
    border: 1px solid rgba(128, 128, 128, 0.28);
    border-radius: 14px;
    padding: 1.25rem 1.4rem;
}

/* Teal buttons with white text read well on both backgrounds */
[data-testid="stFormSubmitButton"] > button,
.stButton > button[kind="primary"] {
    background: #0F9D9A; color: #FFFFFF; border: 0; border-radius: 10px;
    font-weight: 700; padding: 0.55rem 1.3rem;
}
[data-testid="stFormSubmitButton"] > button:hover,
.stButton > button[kind="primary"]:hover { background: #0B7C7A; color: #FFFFFF; }

.stTabs [data-baseweb="tab"] { font-weight: 600; }
.stTabs [data-baseweb="tab-highlight"] { background-color: #0F9D9A !important; }

/* Profile header is a solid navy block with white text in both themes */
.profile-head {
    background: #14213D; color: #FFFFFF; border-radius: 14px;
    padding: 1.3rem 1.6rem; margin-bottom: 1rem;
}
.profile-head h2 { color: #FFFFFF; margin: 0; }
.profile-head p { color: #C5D0E2; margin: 0.25rem 0 0 0; }
</style>
"""


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------
def page_dashboard(data):
    st.title("Dashboard")
    st.caption("A quick look at the school right now.")

    students, teachers = data["students"], data["teachers"]
    all_marks = [m for s in students for m in s.get("grades", {}).values()]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Students", len(students))
    c2.metric("Teachers", len(teachers))
    c3.metric("Grades recorded", len(all_marks))
    c4.metric("School average", f"{sum(all_marks) / len(all_marks):.1f}" if all_marks else "-")

    if not students:
        st.info("No students yet. Open Register in the sidebar to add the first one.")
        return

    left, right = st.columns([3, 2])
    with left:
        st.subheader("Top students by average")
        ranked = [(s["name"], Student.average(s)) for s in students if Student.average(s) is not None]
        if ranked:
            ranked.sort(key=lambda x: x[1], reverse=True)
            df = pd.DataFrame(ranked[:8], columns=["Student", "Average"]).set_index("Student")
            st.bar_chart(df, color="#0F9D9A")
        else:
            st.info("Averages appear here once you add grades.")
    with right:
        st.subheader("Newest students")
        recent = pd.DataFrame(students[-5:][::-1])[["name", "roll_no"]]
        recent.columns = ["Name", "Roll no"]
        st.dataframe(recent, hide_index=True)


def page_register(data):
    st.title("Register")
    st.caption("Add a new student or teacher to the school records.")
    st.info(
        "To collect registrations from students, send them your app link with "
        "?form=student added at the end. They see only the registration form, never your data."
    )

    tab_s, tab_t = st.tabs(["Student", "Teacher"])

    with tab_s:
        with st.form("student_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Full name")
            roll_no = c2.text_input("Roll number")
            email = c1.text_input("Email")
            age = c2.number_input("Age", min_value=3, max_value=100, value=16)
            submitted = st.form_submit_button("Register student", type="primary")
        if submitted:
            ok, msg = Student().register(data, name, age, email, roll_no)
            (st.success if ok else st.error)(msg)

    with tab_t:
        with st.form("teacher_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Full name", key="t_name")
            emp_id = c2.text_input("Employee ID")
            email = c1.text_input("Email", key="t_email")
            subject = c2.text_input("Subject taught")
            age = c1.number_input("Age", min_value=18, max_value=100, value=30, key="t_age")
            submitted = st.form_submit_button("Register teacher", type="primary")
        if submitted:
            ok, msg = Teacher().register(data, name, age, email, subject, emp_id)
            (st.success if ok else st.error)(msg)


def page_grades(data):
    st.title("Add grades")
    st.caption("Record marks for a student. Saving a subject again replaces the old mark.")

    students = data["students"]
    if not students:
        st.info("Register a student first, then come back to add grades.")
        return

    labels = {s["roll_no"]: f'{s["name"]} (Roll {s["roll_no"]})' for s in students}
    roll_no = st.selectbox("Student", list(labels), format_func=labels.get)

    with st.form("grade_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        subject = c1.text_input("Subject")
        marks = c2.number_input("Marks (out of 100)", min_value=0.0, max_value=100.0, step=0.5)
        submitted = st.form_submit_button("Save grade", type="primary")
    if submitted:
        ok, msg = Student().add_grade(data, roll_no, subject, marks)
        (st.success if ok else st.error)(msg)

    student = next(s for s in students if s["roll_no"] == roll_no)
    st.subheader("Current grades")
    if student["grades"]:
        grades_df = pd.DataFrame(
            {"Subject": list(student["grades"]), "Marks": list(student["grades"].values())}
        )
        st.dataframe(grades_df, hide_index=True)
    else:
        st.info(f"No grades recorded for {student['name']} yet.")


def page_directory(data):
    st.title("Directory")
    st.caption("Search everyone in the school.")

    query = st.text_input("Search by name, ID or email", placeholder="Start typing...").strip().lower()
    tab_s, tab_t = st.tabs([f"Students ({len(data['students'])})", f"Teachers ({len(data['teachers'])})"])

    with tab_s:
        rows = []
        for s in data["students"]:
            if query and not any(query in str(s[k]).lower() for k in ("name", "roll_no", "email")):
                continue
            avg = Student.average(s)
            rows.append(
                {
                    "Name": s["name"],
                    "Roll no": s["roll_no"],
                    "Age": s["age"],
                    "Email": s["email"],
                    "Subjects": len(s.get("grades", {})),
                    "Average": round(avg, 1) if avg is not None else None,
                }
            )
        if rows:
            st.dataframe(pd.DataFrame(rows), hide_index=True)
        else:
            st.info("No students match.")

    with tab_t:
        rows = []
        for t in data["teachers"]:
            if query and not any(query in str(t[k]).lower() for k in ("name", "emp_id", "email", "subject")):
                continue
            rows.append(
                {
                    "Name": t["name"],
                    "Subject": t["subject"],
                    "Employee ID": t["emp_id"],
                    "Age": t["age"],
                    "Email": t["email"],
                }
            )
        if rows:
            st.dataframe(pd.DataFrame(rows), hide_index=True)
        else:
            st.info("No teachers match.")


def page_profiles(data):
    st.title("Profiles")
    st.caption("Full details for one student or teacher.")

    tab_s, tab_t = st.tabs(["Student", "Teacher"])

    with tab_s:
        students = data["students"]
        if not students:
            st.info("No students registered yet.")
        else:
            labels = {s["roll_no"]: f'{s["name"]} (Roll {s["roll_no"]})' for s in students}
            roll_no = st.selectbox("Choose a student", list(labels), format_func=labels.get)
            s = next(x for x in students if x["roll_no"] == roll_no)
            grades = s.get("grades", {})

            st.markdown(
                f'<div class="profile-head"><h2>{s["name"]}</h2>'
                f'<p>Roll {s["roll_no"]}, age {s["age"]}, {s["email"]}</p></div>',
                unsafe_allow_html=True,
            )
            avg = Student.average(s)
            c1, c2, c3 = st.columns(3)
            c1.metric("Average", f"{avg:.1f}" if avg is not None else "-")
            c2.metric("Subjects", len(grades))
            c3.metric("Best subject", max(grades, key=grades.get) if grades else "-")

            if grades:
                st.bar_chart(pd.Series(grades, name="Marks").rename_axis("Subject").to_frame(), color="#0F9D9A")
            else:
                st.info("No grades yet. Add some from the Add grades page.")

    with tab_t:
        teachers = data["teachers"]
        if not teachers:
            st.info("No teachers registered yet.")
        else:
            labels = {t["emp_id"]: f'{t["name"]} (ID {t["emp_id"]})' for t in teachers}
            emp_id = st.selectbox("Choose a teacher", list(labels), format_func=labels.get)
            t = next(x for x in teachers if x["emp_id"] == emp_id)
            st.markdown(
                f'<div class="profile-head"><h2>{t["name"]}</h2>'
                f'<p>{t["subject"]} teacher, ID {t["emp_id"]}</p></div>',
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns(2)
            c1.metric("Subject", t["subject"])
            c2.metric("Age", t["age"])
            st.write(f"Email: {t['email']}")


# --------------------------------------------------------------------------
# App shell
# --------------------------------------------------------------------------
def get_admin_password():
    try:
        return str(st.secrets.get("ADMIN_PASSWORD", ""))
    except Exception:
        return ""


def public_form():
    """What a student sees when opening the link ending in ?form=student.
    Only a form: no student list, no profiles, no sidebar."""
    st.title("Student registration")
    st.caption("Fill in your details and press Register. Your entry goes to the school office.")
    with st.form("public_student_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Full name")
        roll_no = c2.text_input("Roll number")
        email = c1.text_input("Email")
        age = c2.number_input("Age", min_value=3, max_value=100, value=16)
        submitted = st.form_submit_button("Register", type="primary")
    if submitted:
        ok, msg = Student().register(load_data(), name, age, email, roll_no)
        if ok:
            st.success("Thank you. You are registered.")
        else:
            st.error(msg)


def require_admin():
    if st.session_state.get("is_admin"):
        return True
    st.title("School Desk")
    password = get_admin_password()
    if not password:
        st.error("Admin password is not set. Add ADMIN_PASSWORD to the app secrets, then reload.")
        return False
    st.caption("This area is for the school office. Enter the admin password to continue.")
    with st.form("login_form"):
        entered = st.text_input("Admin password", type="password")
        go = st.form_submit_button("Log in", type="primary")
    if go:
        if hmac.compare_digest(entered.encode(), password.encode()):
            st.session_state["is_admin"] = True
            st.rerun()
        else:
            st.error("Wrong password.")
    return False


st.set_page_config(page_title="School Desk", page_icon="🎓", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

# Link ending in ?form=student -> public registration form only
if st.query_params.get("form") == "student":
    public_form()
    st.stop()

# Everything else needs the admin password
if not require_admin():
    st.stop()

PAGES = {
    "Dashboard": page_dashboard,
    "Register": page_register,
    "Add grades": page_grades,
    "Directory": page_directory,
    "Profiles": page_profiles,
}

data = load_data()
st.sidebar.markdown("### School Desk")
st.sidebar.caption("Students, teachers and grades in one place.")
choice = st.sidebar.radio("Navigate", list(PAGES), label_visibility="collapsed")
st.sidebar.download_button(
    "Download backup", json.dumps(data, indent=4), "school_data_backup.json", "application/json"
)
if st.sidebar.button("Log out"):
    st.session_state["is_admin"] = False
    st.rerun()

PAGES[choice](data)