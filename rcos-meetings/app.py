from datetime import date, datetime
import os
from flask import Flask, abort, flash, g, session, request, render_template, redirect, url_for
# from whitenoise import WhiteNoise
from flask_cas import CAS, login_required
from dotenv import load_dotenv
from werkzeug.datastructures import Headers
from werkzeug.exceptions import HTTPException
from .utils import emtpy_to_none
from . import generate
from .api import api, API_BASE

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
app.config['APP_TITLE'] = 'RCOS Meetings'

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


@app.context_processor
def add_template_locals():
    '''Add values to be available to every rendered template.'''

    # Add keys here
    return {
        'logged_in': g.logged_in,
        'username': cas.username
    }


@app.route('/')
def index():
    '''The homepage.'''
    r = api.get(f'{API_BASE}/meetings')
    meetings = r.json()
    return render_template('meetings/index.html', meetings=meetings)


@app.route('/meetings/<int:meeting_id>')
def meeting(meeting_id: int):
    r = api.get(f'{API_BASE}/meetings?meeting_id=eq.{meeting_id}')
    r.raise_for_status()
    meeting = r.json()[0]
    start_datetime = datetime.strptime(
        meeting['start_date_time'], '%Y-%m-%dT%H:%M:%S')
    end_datetime = datetime.strptime(
        meeting['end_date_time'], '%Y-%m-%dT%H:%M:%S')
    meeting_type_display = generate.meeting_type_display(
        meeting['meeting_type'])
    return render_template('meetings/meeting.html',
                           meeting=meeting,
                           meeting_type_display=meeting_type_display,
                           start_datetime=start_datetime,
                           end_datetime=end_datetime
                           )


# @app.route('/meetings/new')
@app.route('/meetings/<int:meeting_id>/edit', methods=['GET', 'POST'])
def edit_meeting(meeting_id: int):
    if request.method == 'GET':
        r = api.get(f'{API_BASE}/meetings?meeting_id=eq.{meeting_id}')
        r.raise_for_status()
        meeting = r.json()[0]

        meeting_types = {
            'large_group': 'Large Group',
            'small_group': 'Small Group',
            'mentors': 'Mentors',
            'coordinators': 'Coordinators'
        }
        return render_template('meetings/edit_meeting.html', meeting=meeting, meeting_types=meeting_types)
    elif request.method == 'POST':
        updated_meeting = emtpy_to_none(request.form)
        updated_meeting['agenda'] = request.form['agenda'].split(',')
        r = api.patch(f'{API_BASE}/meetings?meeting_id=eq.{meeting_id}',
                      json=updated_meeting)
        r.raise_for_status()
        return redirect(url_for('edit_meeting', meeting_id=meeting_id))


@app.route('/meetings/<int:meeting_id>/delete', methods=['POST'])
def delete_meeting(meeting_id: int):
    r = api.delete(
        f'{API_BASE}/meetings?meeting_id=eq.{meeting_id}')
    r.raise_for_status()
    return redirect(url_for('index'))


@app.route('/slideshow/<int:meeting_id>')
def slideshow(meeting_id: int):
    r = api.get(f'{API_BASE}/meetings?meeting_id=eq.{meeting_id}')
    r.raise_for_status()
    try:
        meeting = r.json()[0]
    except IndexError:
        abort(404)
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
