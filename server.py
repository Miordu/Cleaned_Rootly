"""Server for Rootly app: the website pages. The mobile app's API is in mobile_api.py."""

from flask import (Flask, render_template, request, flash, redirect,
                   session, abort, Response)
from flask_wtf.csrf import CSRFProtect, CSRFError
from model import connect_to_db, db, User, Plant, PlantCareDetails, UserPlant
from model import CareEvent, Reminder, HealthAssessment, Region, Photo
import os
from types import SimpleNamespace
from jinja2 import StrictUndefined
import logging
from dotenv import load_dotenv
import crud
import services
from services import ValidationError
import api.quantitative_plant as trefle

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.jinja_env.undefined = StrictUndefined


def env_flag(name, default=False):
    """Read a true/false setting such as DEBUG=True from the environment."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


# APP_ENV=production is set on the hosting service (see render.yaml)
IS_PRODUCTION = os.environ.get('APP_ENV', '').strip().lower() == 'production'

# Set up secret key for sessions
app.secret_key = os.environ.get('FLASK_SECRET_KEY')
if not app.secret_key:
    if IS_PRODUCTION:
        raise RuntimeError("FLASK_SECRET_KEY must be set when APP_ENV=production.")
    app.secret_key = 'dev-secret-key'
    print("WARNING: FLASK_SECRET_KEY is not set, using an insecure development key.")

app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = IS_PRODUCTION  # https only on the live site
# Reject uploads bigger than 16 MB instead of filling the disk
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
# Form tokens last as long as the login session, so a form left open overnight still works
app.config['WTF_CSRF_TIME_LIMIT'] = None

# Every form on the website carries a hidden token, so other websites can't
# submit forms on behalf of someone who is logged in.
csrf = CSRFProtect(app)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# A web page should never hang waiting for Trefle's rate limit
trefle.MAX_BLOCKING_WAIT = 3

# Initialize database connection (uses DATABASE_URI from .env if set)
connect_to_db(app, echo=env_flag('SQLALCHEMY_ECHO'))

# The mobile app talks to /api/v1/... It logs in with a token instead of a
# cookie, so the form-token check doesn't apply to it.
from mobile_api import mobile_api  # noqa: E402
csrf.exempt(mobile_api)
app.register_blueprint(mobile_api)

PLANTS_PER_PAGE = 21  # three across on the browse page


# Helper functions
def stale_session_redirect():
    """Log out a browser whose saved user no longer exists in the database."""
    session.pop('user_id', None)
    flash('Please log in again.')
    return redirect('/login')


def current_user():
    """The logged-in user, or None."""
    user_id = session.get('user_id')
    if user_id is None:
        return None
    user = db.session.get(User, user_id)
    if user is None:
        session.pop('user_id', None)
    return user


def owned_user_plant(user_plant_id):
    """The logged-in user's plant with this id, or a 404 page.

    Someone else's plant looks exactly like one that doesn't exist.
    """
    user_plant = db.session.get(UserPlant, user_plant_id) if user_plant_id else None
    if user_plant is None or user_plant.user_id != session.get('user_id'):
        abort(404)
    return user_plant


@app.errorhandler(CSRFError)
def csrf_error(e):
    """The hidden form token was missing or too old."""
    flash('That page had been open too long. Please try again.')
    return redirect(request.referrer or '/')


# Routes
@app.route('/')
def homepage():
    """Show homepage."""
    return render_template('homepage.html')


@app.route('/healthz')
def healthz():
    """Used by the hosting service to check the app is running."""
    return {'status': 'ok'}


@app.route('/privacy')
def privacy():
    """Privacy policy (the app stores require a link to one)."""
    return render_template('privacy.html',
                           contact_email=os.environ.get('CONTACT_EMAIL', ''))


@app.route('/photos/<token>.jpg')
def photo(token):
    """Send back a photo someone uploaded."""
    record = Photo.query.filter_by(token=token).first()
    if record is None:
        abort(404)
    response = Response(record.data, mimetype=record.content_type)
    response.headers['Cache-Control'] = 'private, max-age=31536000, immutable'
    return response


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user."""
    if request.method == 'POST':
        try:
            new_user = services.register_user(
                request.form.get('username'),
                request.form.get('email'),
                request.form.get('password'),
                request.form.get('region_id'),
            )
        except ValidationError as e:
            flash(str(e))
            return redirect('/register')

        # Log in the user
        session['user_id'] = new_user.user_id
        flash(f'Account created for {new_user.username}!')
        return redirect('/dashboard')

    # Get regions for the dropdown
    regions = Region.query.all()
    return render_template('register.html', regions=regions)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Log in a user."""
    if request.method == 'POST':
        try:
            user = services.check_login(request.form.get('email'), request.form.get('password'))
        except ValidationError as e:
            flash(str(e))
            return render_template('login.html')

        if user:
            session['user_id'] = user.user_id
            flash(f'Welcome back, {user.username}!')
            return redirect('/dashboard')
        flash('Invalid email or password.')

    return render_template('login.html')


@app.route('/logout', methods=['POST'])
def logout():
    """Log out a user."""
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect('/')


@app.route('/account')
def account():
    """Account page: shows who is logged in and lets them delete their account."""
    user = current_user()
    if user is None:
        flash('Please log in to manage your account.')
        return redirect('/login')
    return render_template('account.html', user=user)


@app.route('/account/delete', methods=['POST'])
def delete_account():
    """Permanently delete the logged-in account after checking the password."""
    user = current_user()
    if user is None:
        return redirect('/login')
    if not user.check_password(request.form.get('password') or ''):
        flash('That password is not right, so the account was not deleted.')
        return redirect('/account')
    services.delete_account(user)
    session.pop('user_id', None)
    flash('Your account and everything in it has been deleted.')
    return redirect('/')


@app.route('/dashboard')
def dashboard():
    """Show user dashboard."""
    if 'user_id' not in session:
        flash('Please log in to view your dashboard.')
        return redirect('/login')

    user = db.session.get(User, session['user_id'])
    if user is None:
        return stale_session_redirect()

    return render_template(
        'dashboard.html',
        user=user,
        upcoming_reminders=len(crud.get_upcoming_reminders(user.user_id)),
        recent_care_events=len(crud.get_recent_care_events(user.user_id)),
    )


@app.route('/identify')
def identify_plant():
    """Photo identification was removed with the paid Plant.id API.

    Old links and bookmarks land on plant search instead.
    """
    flash('Photo identification is no longer available. Search for your plant by name instead.')
    return redirect('/search-plants')


@app.route('/my-plants')
def my_plants():
    """Show user's plant collection."""
    if 'user_id' not in session:
        flash('Please log in to view your plants.')
        return redirect('/login')

    user = db.session.get(User, session['user_id'])
    if user is None:
        return stale_session_redirect()
    user_plants = UserPlant.query.filter_by(user_id=user.user_id).all()

    return render_template('my_plants.html', user=user, user_plants=user_plants)


@app.route('/add-plant', methods=['GET', 'POST'])
def add_plant():
    """Add a plant to user's collection."""
    if 'user_id' not in session:
        flash('Please log in to add plants to your collection.')
        return redirect('/login')
    if current_user() is None:
        return stale_session_redirect()

    if request.method == 'POST':
        try:
            services.add_to_collection(
                session['user_id'],
                request.form.get('plant_id'),
                request.form.get('nickname'),
                request.form.get('location'),
            )
        except ValidationError as e:
            flash(str(e))
            return redirect('/add-plant')

        flash('Plant added to your collection!')
        return redirect('/my-plants')

    # Get all plants to display in a dropdown
    plants = Plant.query.order_by(Plant.common_name).all()
    return render_template('add_plant.html', plants=plants)


def trefle_plant_for_display(plant_data):
    """Turn one plant from a Trefle list or search into something the
    browse page can show next to the plants from our own database."""
    family = plant_data.get('family')
    return SimpleNamespace(
        plant_id=None,
        external_id=plant_data.get('id'),
        scientific_name=plant_data.get('scientific_name') or 'Unknown',
        common_name=plant_data.get('common_name') or plant_data.get('scientific_name') or 'Unknown',
        image_url=plant_data.get('image_url'),
        description=f"A plant in the {family} family." if family else "A plant from the Trefle database.",
        is_api_result=True,
    )


BROWSE_FILTERS = {
    'indoor': lambda q: q.filter(Plant.indoor.is_(True)),
    'outdoor': lambda q: q.filter(Plant.outdoor.is_(True)),
    'easy': lambda q: q.join(PlantCareDetails).filter(PlantCareDetails.difficulty_level == 'Easy'),
}


@app.route('/browse-plants')
def browse_plants():
    """Browse plants from our database and the Trefle API."""
    search = (request.args.get('search') or '').strip()
    # type=int returns the default instead of crashing on ?page=abc
    page = max(request.args.get('page', 1, type=int), 1)
    plant_filter = request.args.get('filter', '')
    if plant_filter not in BROWSE_FILTERS:
        plant_filter = ''
    has_next = False

    if search:
        # Search our own database first
        plants = crud.search_plants(search, limit=20)

        # Only call Trefle when our database has few matches, to save requests
        if len(plants) < 10:
            known = {p.scientific_name for p in plants}
            for plant_data in (trefle.search_plants(search).get('data') or [])[:10]:
                if plant_data.get('scientific_name') not in known:
                    plants.append(trefle_plant_for_display(plant_data))
    elif plant_filter:
        # Indoor / Outdoor / Easy Care only exist for plants in our own database
        query = BROWSE_FILTERS[plant_filter](Plant.query).order_by(Plant.common_name)
        found = query.offset((page - 1) * PLANTS_PER_PAGE).limit(PLANTS_PER_PAGE + 1).all()
        plants, has_next = found[:PLANTS_PER_PAGE], len(found) > PLANTS_PER_PAGE
    else:
        api_response = trefle.get_plant_list(page=page, limit=PLANTS_PER_PAGE)
        # Plants we already have link to our own page for them
        api_plants = api_response.get('data') or []
        ours = {p.scientific_name: p for p in Plant.query.filter(
            Plant.scientific_name.in_([p.get('scientific_name') for p in api_plants])).all()}
        plants = [ours.get(p.get('scientific_name')) or trefle_plant_for_display(p)
                  for p in api_plants]
        has_next = bool((api_response.get('links') or {}).get('next'))

        if not plants:
            # Trefle sent nothing back (no key, API down, or past the last
            # page), so show the plants already in our database.
            found = (Plant.query.order_by(Plant.common_name)
                     .offset((page - 1) * PLANTS_PER_PAGE).limit(PLANTS_PER_PAGE + 1).all())
            plants, has_next = found[:PLANTS_PER_PAGE], len(found) > PLANTS_PER_PAGE

    return render_template('browse_plants.html', plants=plants, search=search, page=page,
                           plant_filter=plant_filter, has_next=has_next)


@app.route('/plant/<int:plant_id>')
def plant_details(plant_id):
    """Show details for a specific plant."""
    plant = db.get_or_404(Plant, plant_id)
    care_details = PlantCareDetails.query.filter_by(plant_id=plant_id).first()

    return render_template('plant_details.html', plant=plant, care_details=care_details)


@app.route('/user-plant/<int:user_plant_id>')
def user_plant_details(user_plant_id):
    """Show details for a specific user plant."""
    if 'user_id' not in session:
        flash('Please log in to view your plants.')
        return redirect('/login')

    user_plant = db.get_or_404(UserPlant, user_plant_id)

    # Ensure the plant belongs to the logged-in user
    if user_plant.user_id != session['user_id']:
        flash('You do not have access to this plant.')
        return redirect('/my-plants')

    care_details = PlantCareDetails.query.filter_by(plant_id=user_plant.plant_id).first()
    care_events = CareEvent.query.filter_by(user_plant_id=user_plant_id).order_by(CareEvent.date.desc()).all()
    reminders = Reminder.query.filter_by(user_plant_id=user_plant_id, is_active=True).order_by(Reminder.next_reminder_date).all()
    health_assessments = HealthAssessment.query.filter_by(user_plant_id=user_plant_id).order_by(HealthAssessment.assessment_date.desc()).all()

    return render_template('user_plant_details.html',
                          user_plant=user_plant,
                          care_details=care_details,
                          care_events=care_events,
                          reminders=reminders,
                          health_assessments=health_assessments)


def user_plant_from_form():
    """The logged-in user's plant named by the form's user_plant_id.

    Returns (user_plant, None), or (None, a redirect) when it isn't theirs.
    """
    user_plant = db.get_or_404(UserPlant, request.form.get('user_plant_id', type=int) or 0)
    if user_plant.user_id != session['user_id']:
        flash('You do not have access to this plant.')
        return None, redirect('/my-plants')
    return user_plant, None


@app.route('/log-care', methods=['POST'])
def log_care():
    """Log a care event for a plant."""
    if 'user_id' not in session:
        flash('Please log in to log care events.')
        return redirect('/login')

    user_plant, denied = user_plant_from_form()
    if denied:
        return denied

    try:
        event = services.log_care(user_plant, request.form.get('event_type'),
                                  request.form.get('notes'))
        flash(f'{event.event_type} event logged successfully!')
    except ValidationError as e:
        flash(str(e))
    return redirect(f'/user-plant/{user_plant.user_plant_id}')


@app.route('/add-reminder', methods=['POST'])
def add_reminder():
    """Add a care reminder for a plant."""
    if 'user_id' not in session:
        flash('Please log in to add reminders.')
        return redirect('/login')

    user_plant, denied = user_plant_from_form()
    if denied:
        return denied

    try:
        reminder = services.add_reminder(user_plant, request.form.get('reminder_type'),
                                         request.form.get('frequency'),
                                         request.form.get('next_reminder_date'))
        flash(f'{reminder.reminder_type} reminder added successfully!')
    except ValidationError as e:
        flash(str(e))
    return redirect(f'/user-plant/{user_plant.user_plant_id}')


def owned_reminder(reminder_id):
    reminder = db.session.get(Reminder, reminder_id)
    if reminder is None or reminder.user_plant.user_id != session.get('user_id'):
        abort(404)
    return reminder


@app.route('/reminder/<int:reminder_id>/done', methods=['POST'])
def reminder_done(reminder_id):
    """Mark a reminder as done: logs the care and moves it to the next date."""
    if 'user_id' not in session:
        return redirect('/login')
    reminder = services.complete_reminder(owned_reminder(reminder_id))
    flash(f"{reminder.reminder_type} logged. Next reminder: "
          f"{reminder.next_reminder_date.strftime('%b %d')}.")
    return redirect(f'/user-plant/{reminder.user_plant_id}')


@app.route('/reminder/<int:reminder_id>/delete', methods=['POST'])
def reminder_delete(reminder_id):
    """Delete a reminder."""
    if 'user_id' not in session:
        return redirect('/login')
    reminder = owned_reminder(reminder_id)
    user_plant_id = reminder.user_plant_id
    services.delete_reminder(reminder)
    flash('Reminder deleted.')
    return redirect(f'/user-plant/{user_plant_id}')


@app.route('/add-health-assessment', methods=['POST'])
def add_health_assessment():
    """Add a health assessment for a plant."""
    if 'user_id' not in session:
        flash('Please log in to add health assessments.')
        return redirect('/login')

    user_plant, denied = user_plant_from_form()
    if denied:
        return denied

    try:
        services.add_health_assessment(
            user_plant,
            symptoms=request.form.getlist('symptoms'),
            diagnosis=request.form.get('diagnosis'),
            treatment=request.form.get('treatment_recommendations'),
            photo=request.files.get('image'),
        )
        flash('Health assessment added successfully!')
    except ValidationError as e:
        db.session.rollback()
        flash(str(e))
    return redirect(f'/user-plant/{user_plant.user_plant_id}')


@app.route('/resolve-health-issue/<int:assessment_id>', methods=['POST'])
def resolve_health_issue(assessment_id):
    """Mark a health issue as resolved."""
    if 'user_id' not in session:
        flash('Please log in to update health assessments.')
        return redirect('/login')

    assessment = db.get_or_404(HealthAssessment, assessment_id)

    # Verify the assessment belongs to a plant owned by the user
    user_plant = db.session.get(UserPlant, assessment.user_plant_id)
    if user_plant.user_id != session['user_id']:
        flash('You do not have access to this assessment.')
        return redirect('/my-plants')

    assessment.resolved = True
    db.session.commit()

    flash('Health issue marked as resolved!')
    return redirect(f'/user-plant/{assessment.user_plant_id}')


@app.route('/edit-user-plant/<int:user_plant_id>', methods=['GET', 'POST'])
def edit_user_plant(user_plant_id):
    """Edit a user's plant."""
    if 'user_id' not in session:
        flash('Please log in to edit your plants.')
        return redirect('/login')

    user_plant = db.get_or_404(UserPlant, user_plant_id)

    # Ensure the plant belongs to the logged-in user
    if user_plant.user_id != session['user_id']:
        flash('You do not have access to this plant.')
        return redirect('/my-plants')

    if request.method == 'POST':
        try:
            services.update_user_plant(
                user_plant,
                nickname=request.form.get('nickname', ''),
                location=request.form.get('location', ''),
                status=request.form.get('status'),
                notes=request.form.get('notes', ''),
                photo=request.files.get('image'),
            )
            flash('Plant details updated successfully!')
        except ValidationError as e:
            # The text changes are kept; only the photo was refused
            db.session.commit()
            flash(str(e))
        return redirect(f'/user-plant/{user_plant_id}')

    return render_template('edit_user_plant.html', user_plant=user_plant)


@app.route('/delete-user-plant/<int:user_plant_id>', methods=['POST'])
def delete_user_plant(user_plant_id):
    """Remove a plant from the user's collection."""
    if 'user_id' not in session:
        return redirect('/login')
    user_plant = owned_user_plant(user_plant_id)
    name = user_plant.nickname or user_plant.plant.common_name or 'Plant'
    services.delete_user_plant(user_plant)
    flash(f'{name} was removed from your collection.')
    return redirect('/my-plants')


@app.route('/search-plants')
def search_plants():
    """Search for plants using Trefle API with fallback to database."""
    if 'user_id' not in session:
        flash('Please log in to search plants.')
        return redirect('/login')

    query = (request.args.get('query') or '').strip()

    if not query:
        return render_template('search_plants.html', plants=None, query=None)

    # First search the local database (limit to 100 plants)
    db_plants = crud.search_plants(query, limit=100)

    # Format database plants for display
    formatted_plants = []
    for plant in db_plants:
        care_details = plant.care_details

        formatted_plants.append({
            'in_database': True,
            'plant_id': plant.plant_id,
            'scientific_name': plant.scientific_name,
            'common_name': plant.common_name,
            'image_url': plant.image_url,
            'care_details': {
                'sunlight_requirements': care_details.sunlight_requirements,
                'watering_frequency': care_details.watering_frequency,
                'difficulty_level': care_details.difficulty_level,
            } if care_details else None
        })

    # If we have fewer than 50 results from the database, supplement with Trefle API
    if len(formatted_plants) < 50:
        logger.info("Searching Trefle API")
        trefle_results = trefle.search_plants(query)
        known = {p['scientific_name'] for p in formatted_plants}

        for plant_data in (trefle_results.get('data') or [])[:10]:
            scientific_name = plant_data.get('scientific_name')
            if scientific_name and scientific_name not in known:
                formatted_plants.append({
                    'in_database': False,
                    'plant_id': plant_data.get('id'),
                    'scientific_name': scientific_name,
                    'common_name': plant_data.get('common_name') or scientific_name,
                    'image_url': plant_data.get('image_url') or None,
                    'care_details': None,  # fetched only when importing, to save API calls
                    'api_source': 'trefle'
                })

    return render_template('search_plants.html', plants=formatted_plants, query=query)


@app.route('/import-plant', methods=['POST'])
def import_plant():
    """Copy a plant from Trefle into our database."""
    if 'user_id' not in session:
        flash('Please log in to import plants.')
        return redirect('/login')

    # A plant we already have doesn't need Trefle at all
    scientific_name = (request.form.get('scientific_name') or '').strip()
    if scientific_name:
        existing_plant = Plant.query.filter_by(scientific_name=scientific_name).first()
        if existing_plant:
            flash(f'{existing_plant.common_name or existing_plant.scientific_name} is already in the database!')
            return redirect(f'/plant/{existing_plant.plant_id}')

    # Plants can only come from Trefle. (This used to create a made-up
    # placeholder plant from whatever name was sent.)
    if request.form.get('api_source') != 'trefle' or not request.form.get('external_id'):
        flash('Please pick a plant from the search results to import it.')
        return redirect('/search-plants')

    try:
        plant = services.import_trefle_plant(request.form.get('external_id'))
    except ValidationError as e:
        db.session.rollback()
        flash(str(e))
        return redirect('/search-plants')
    except Exception:
        # Log the details for us; show the visitor a plain message
        logger.exception("Error in plant import")
        db.session.rollback()
        flash('Sorry, something went wrong importing that plant. Please try again.')
        return redirect('/search-plants')

    flash(f'Successfully imported {plant.common_name or plant.scientific_name}!')
    return redirect(f'/plant/{plant.plant_id}')


@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    if request.path.startswith('/api/'):
        return {'error': 'Not found.'}, 404
    return render_template('404.html'), 404


@app.errorhandler(413)
def too_large(e):
    """An upload was over the size limit."""
    if request.path.startswith('/api/'):
        return {'error': 'That photo is too large (the limit is 16 MB).'}, 413
    return ('That file is too large (the limit is 16 MB). '
            'Go back and choose a smaller photo.'), 413


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    db.session.rollback()
    if request.path.startswith('/api/'):
        return {'error': 'Something went wrong on the server. Please try again.'}, 500
    return render_template('500.html'), 500


if __name__ == "__main__":
    # Debug mode turns on Flask's interactive debugger, which lets anyone who
    # can reach the page run Python code. Only turn it on with DEBUG=True in
    # your local .env, and keep the app on 127.0.0.1 unless you set HOST.
    app.run(host=os.environ.get('HOST', '127.0.0.1'),
            port=int(os.environ.get('PORT', 5001)),
            debug=env_flag('DEBUG') and not IS_PRODUCTION)
