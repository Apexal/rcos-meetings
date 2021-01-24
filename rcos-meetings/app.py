from datetime import date, datetime
import os
from flask import Flask, abort, flash, g, session, request, render_template, redirect, url_for, jsonify
# from whitenoise import WhiteNoise
from flask_cas import CAS, login_required
from dotenv import load_dotenv
from requests.models import HTTPError
from werkzeug.datastructures import Headers
from werkzeug.exceptions import HTTPException
from .utils import emtpy_to_none
from . import TIMESTAMP_FORMAT, generate
from .decorators import admin_required
from .api import api, API_BASE, create_meeting, get_user_and_enrollment, meeting_types, meeting_type_urls, get_meeting, update_meeting

# Loads any variables from the .env file
load_dotenv()

# Initialize Flask application
app = Flask(__name__)

# Serve static files on Heroku
# app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/')

# Initialize CAS authentication on the /cas endpoint
# Adds the /cas/login and /cas/logout routes
cas = CAS(app, '/cas')

# This must be a RANDOM string you generate once and keep secret
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

# Used in templates
app.config['APP_TITLE'] = 'RCOS Meeting Management'

# Must be set to this to use RPI CAS
app.config['CAS_SERVER'] = 'https://cas-auth.rpi.edu/cas'

# What route to go to after logging in
app.config['CAS_AFTER_LOGIN'] = 'index'


@app.template_filter()
def format_datetime(date, format):
    return datetime.strftime(date, format)


@app.before_request
def before_request():
    '''Runs before every request.'''

    # Everything added to g can be accessed during the request
    g.logged_in = cas.username is not None
    user, enrollment = get_user_and_enrollment(cas.username.lower()) if g.logged_in else (None, None)
    g.user = user
    g.enrollment = enrollment
    
    g.is_user_admin = (user and user['role'] == 'faculty_advisor') or (enrollment and enrollment['is_coordinator'])


@app.context_processor
def add_template_locals():
    '''Add values to be available to every rendered template.'''

    # Add keys here
    return {
        'logged_in': g.logged_in,
        'username': cas.username
    }


@app.route('/')
@login_required
@admin_required
def index():
    '''The homepage.'''
    r = api.get(f'{API_BASE}/meetings')
    meetings = r.json()
    return render_template('meetings/index.html', meetings=meetings)

@app.route('/meetings/json')
@login_required
@admin_required
def meetings_json():
    '''Send ALL meetings.'''
    r = api.get(f'{API_BASE}/meetings')
    meetings = r.json()
    return jsonify(meetings)

@app.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_meeting():
    if request.method == 'GET':
        return render_template('meetings/new_meeting.html', meeting={ 'meeting_url': 'https://rensselaer.webex.com/meet/turnew2' }, meeting_types=meeting_types)
    else:
        new_meeting_json = emtpy_to_none(request.form)
        new_meeting_json['agenda'] = request.form['agenda'].split(',')
        new_meeting_json['is_remote'] = True
        new_meeting_json['meeting_url'] = 'https://rensselaer.webex.com/meet/turnew2'
        try:
            new_meeting = create_meeting(new_meeting_json)
        except HTTPError as err:
            print(err.response.json())
            abort(500)

        return redirect(url_for('meeting', meeting_id=new_meeting['meeting_id']))


@app.route('/meetings/<int:meeting_id>')
def meeting(meeting_id: int):
    meeting = get_meeting(meeting_id)
    if meeting is None:
        abort(404, 'Meeting not found')
    start_datetime = datetime.strptime(
        meeting['start_date_time'], TIMESTAMP_FORMAT)
    end_datetime = datetime.strptime(
        meeting['end_date_time'], TIMESTAMP_FORMAT)
    meeting_type_display = generate.meeting_type_display(
        meeting['type'])
    return render_template('meetings/meeting.html',
                           meeting=meeting,
                           meeting_type_display=meeting_type_display,
                           meeting_type_urls=meeting_type_urls,
                           start_datetime=start_datetime,
                           end_datetime=end_datetime
                           )


# @app.route('/meetings/new')
@app.route('/meetings/<int:meeting_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_meeting(meeting_id: int):
    if request.method == 'GET':
        meeting = get_meeting(meeting_id)
        if meeting is None:
            abort(404, 'Meeting not found')

        return render_template('meetings/edit_meeting.html', meeting=meeting, meeting_types=meeting_types)
    elif request.method == 'POST':
        updated_meeting = emtpy_to_none(request.form)
        updated_meeting['is_public'] = 'is_public' in request.form
        updated_meeting['agenda'] = list(map(str.strip, request.form['agenda'].split(',')))
        updated_meeting['is_remote'] = request.form['meeting_url'] is not None
        r = api.patch(f'{API_BASE}/meetings?meeting_id=eq.{meeting_id}',
                      json=updated_meeting)
        r.raise_for_status()
        return redirect(url_for('edit_meeting', meeting_id=meeting_id))


@app.route('/meetings/<int:meeting_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_meeting(meeting_id: int):
    r = api.delete(
        f'{API_BASE}/meetings?meeting_id=eq.{meeting_id}')
    r.raise_for_status()
    return redirect(url_for('index'))


@app.route('/slideshow/<int:meeting_id>')
def slideshow(meeting_id: int):
    meeting = get_meeting(meeting_id)
    if meeting is None:
        abort(404, 'Meeting not found')
    return render_template('slideshow/slideshow.html', **generate.meeting_to_options(meeting))


@app.errorhandler(404)
def page_not_found(e):
    '''Render 404 page.'''
    return render_template('404.html'), 404


@app.errorhandler(Exception)
def handle_exception(e):
    '''Handles all other exceptions.'''

    # Handle HTTP errors
    if isinstance(e, HTTPException):
        return render_template('error.html', error=e), e.code

    # Handle non-HTTP errors
    app.logger.exception(e)

    # Hide error details in production
    if app.env == 'production':
        e = 'Something went wrong... Please try again later.'

    return render_template('error.html', error=e), 500
