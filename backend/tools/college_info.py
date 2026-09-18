"""
tools/college_info.py
------------------------
TOOL 2: College Information Tool.

This holds simple structured information about the college (working
hours, office contacts, etc.) as a plain Python dictionary, so it is easy
for a beginner to edit later without touching any other code.

*** IMPORTANT ***
Everything below is SAMPLE DATA for demonstration purposes only.
Replace it with your own college's real information before using this
project for real.
"""

# SAMPLE DATA — Replace with official college information.
COLLEGE_INFO = {
    "college_name": "SAMPLE DATA — Replace with your college's name",
    "working_hours": {
        "days": "Monday to Friday",
        "hours": "9:00 AM to 4:30 PM",
        "note": "SAMPLE DATA — confirm with your college administration.",
    },
    "office_hours": {
        "student_office": "9:30 AM to 4:00 PM (Monday to Saturday)",
        "note": "SAMPLE DATA — confirm with your college administration.",
    },
    "departments": {
        "CSE": {
            "full_name": "Computer Science and Engineering",
            "contact_email": "cse.dept@sample-college.edu (SAMPLE DATA)",
            "contact_phone": "0000-000000 (SAMPLE DATA)",
        },
        "ECE": {
            "full_name": "Electronics and Communication Engineering",
            "contact_email": "ece.dept@sample-college.edu (SAMPLE DATA)",
            "contact_phone": "0000-000000 (SAMPLE DATA)",
        },
        "MECH": {
            "full_name": "Mechanical Engineering",
            "contact_email": "mech.dept@sample-college.edu (SAMPLE DATA)",
            "contact_phone": "0000-000000 (SAMPLE DATA)",
        },
    },
    "exam_cell": {
        "contact_email": "examcell@sample-college.edu (SAMPLE DATA)",
        "contact_phone": "0000-000000 (SAMPLE DATA)",
        "location": "Admin Block, Ground Floor (SAMPLE DATA)",
    },
    "general_student_office": {
        "contact_email": "studentoffice@sample-college.edu (SAMPLE DATA)",
        "contact_phone": "0000-000000 (SAMPLE DATA)",
        "location": "Main Building, Room 101 (SAMPLE DATA)",
    },
}


def get_college_info(topic: str = ""):
    """Looks up a piece of college information.

    `topic` can be things like: "working hours", "CSE", "exam cell",
    "student office". Matching is simple and case-insensitive so it is
    easy to understand and extend.

    Returns a dict describing what was found, always noting that this is
    sample data (since, by default, it is).
    """
    topic = (topic or "").strip().lower()

    if not topic:
        return {
            "found": True,
            "data": COLLEGE_INFO,
            "note": "SAMPLE DATA — Replace with real college information "
                    "in backend/tools/college_info.py",
        }

    # Check departments first (e.g. "CSE", "computer science").
    for dept_code, dept_info in COLLEGE_INFO["departments"].items():
        if topic == dept_code.lower() or topic in dept_info["full_name"].lower():
            return {
                "found": True,
                "data": {dept_code: dept_info},
                "note": "SAMPLE DATA — Replace with real college "
                        "information in backend/tools/college_info.py",
            }

    # Check other top-level keys (working_hours, office_hours, exam_cell,
    # general_student_office).
    for key, value in COLLEGE_INFO.items():
        if key == "departments":
            continue
        readable_key = key.replace("_", " ")
        if topic in readable_key or topic in key:
            return {
                "found": True,
                "data": {key: value},
                "note": "SAMPLE DATA — Replace with real college "
                        "information in backend/tools/college_info.py",
            }

    return {
        "found": False,
        "data": None,
        "note": "SAMPLE DATA — Replace with real college information "
                "in backend/tools/college_info.py",
    }
