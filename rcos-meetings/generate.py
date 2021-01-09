import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(["html"])
)

def meeting_to_options(meeting):
    date = datetime.datetime.strptime(meeting["start_date_time"], "%Y-%m-%dT%H:%M:%S.%f")
    capitalized_meeting_type = " ".join(map(str.capitalize, meeting["meeting_type"].split("_")))
    return {
        "title": meeting["title"] if meeting["title"] is not None else datetime.datetime.strftime(date, "%A, %B %-d %Y"),
        "subtitle": capitalized_meeting_type + (" | " + meeting["location"] if meeting["location"] else ""),
        "announcements": ["Announcement 1", "Announcement 2", "Announcement 3"],
        "agenda": meeting["agenda"],
        "venue_qr_code": meeting["venue_qr_code"] if "venue_qr_code" in meeting else None,
        "attendance_code": meeting["attendance_code"],
        "markdown": meeting["presentation_markdown"]
    }

def render_slideshow_from_meeting(meeting):
    t = env.get_template("slideshow.html")
    return t.render(meeting_to_options(meeting))
