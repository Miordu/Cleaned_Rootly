"""JSON API for the Rootly mobile app. Every address starts with /api/v1.

The phone logs in once with an email and password and gets back a token.
It then sends that token with every request in a header:

    Authorization: Bearer <token>

Answers are JSON. Errors look like {"error": "A message that can be shown to the person"}.
"""

from datetime import date
from functools import wraps

from flask import Blueprint, g, jsonify, request

import crud
import services
from services import ValidationError
from model import (db, Plant, UserPlant, CareEvent, Reminder, HealthAssessment, Region)

mobile_api = Blueprint('mobile_api', __name__, url_prefix='/api/v1')


# ----------------------------------------
# Plumbing
# ----------------------------------------

def error(message, status=400):
    return jsonify({'error': message}), status


@mobile_api.errorhandler(ValidationError)
def validation_error(e):
    db.session.rollback()
    return error(str(e), 400)


@mobile_api.after_request
def allow_browser_clients(response):
    """Lets the app also run in a web browser during development.

    Safe because the API never uses cookies: a caller needs the token.
    """
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, DELETE, OPTIONS'
    return response


def bearer_token():
    header = request.headers.get('Authorization', '')
    return header[7:].strip() if header.lower().startswith('bearer ') else None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = services.user_for_api_token(bearer_token())
        if user is None:
            return error('Please log in again.', 401)
        g.user = user
        return view(*args, **kwargs)
    return wrapped


def body():
    """The values sent with the request, whether as JSON or as a form (photo uploads)."""
    if request.is_json:
        data = request.get_json(silent=True)
        return data if isinstance(data, dict) else {}
    return request.form.to_dict()


def my_plant_or_404(user_plant_id):
    user_plant = db.session.get(UserPlant, user_plant_id)
    if user_plant is None or user_plant.user_id != g.user.user_id:
        return None
    return user_plant


# ----------------------------------------
# Turning database rows into JSON
# ----------------------------------------

def iso(value):
    """Dates as text. Times in the database are UTC, so they end in Z."""
    if value is None:
        return None
    if isinstance(value, date) and not hasattr(value, 'hour'):
        return value.isoformat()
    return value.isoformat(timespec='seconds') + 'Z'


def care_json(care):
    if care is None:
        return None
    return {
        'watering_frequency': care.watering_frequency,
        'sunlight_requirements': care.sunlight_requirements or [],
        'soil_preferences': care.soil_preferences,
        'temperature_range': care.temperature_range,
        'difficulty_level': care.difficulty_level,
        'growth_rate': care.growth_rate,
    }


def plant_json(plant, with_care=True):
    data = {
        'plant_id': plant.plant_id,
        'scientific_name': plant.scientific_name,
        'common_name': plant.common_name or plant.scientific_name,
        'image_url': plant.image_url,
        'description': plant.description,
        'indoor': bool(plant.indoor),
        'outdoor': bool(plant.outdoor),
        'poisonous_to_humans': bool(plant.poisonous_to_humans),
        'poisonous_to_pets': bool(plant.poisonous_to_pets),
    }
    if with_care:
        data['care'] = care_json(plant.care_details)
    return data


def reminder_json(reminder, with_plant=False):
    data = {
        'reminder_id': reminder.reminder_id,
        'user_plant_id': reminder.user_plant_id,
        'reminder_type': reminder.reminder_type,
        'frequency': reminder.frequency,
        'next_reminder_date': iso(reminder.next_reminder_date),
    }
    if with_plant:
        up = reminder.user_plant
        data['plant_name'] = up.nickname or up.plant.common_name or up.plant.scientific_name
    return data


def care_event_json(event):
    return {
        'event_id': event.event_id,
        'event_type': event.event_type,
        'date': iso(event.date),
        'notes': event.notes,
    }


def health_json(assessment):
    return {
        'assessment_id': assessment.assessment_id,
        'assessment_date': iso(assessment.assessment_date),
        'symptoms': assessment.symptoms or [],
        'diagnosis': assessment.diagnosis,
        'treatment_recommendations': assessment.treatment_recommendations,
        'image_url': assessment.image_url,
        'resolved': bool(assessment.resolved),
    }


def user_plant_json(user_plant, full=False):
    plant = user_plant.plant
    data = {
        'user_plant_id': user_plant.user_plant_id,
        'name': user_plant.nickname or plant.common_name or plant.scientific_name,
        'nickname': user_plant.nickname,
        'location': user_plant.location_in_home,
        'status': user_plant.status,
        'notes': user_plant.notes,
        'acquisition_date': iso(user_plant.acquisition_date),
        'image_url': user_plant.image_url or plant.image_url,
        'has_own_photo': bool(user_plant.image_url),
        'plant': plant_json(plant, with_care=full),
    }
    if full:
        upid = user_plant.user_plant_id
        data['reminders'] = [reminder_json(r) for r in Reminder.query.filter_by(
            user_plant_id=upid, is_active=True).order_by(Reminder.next_reminder_date)]
        data['care_events'] = [care_event_json(e) for e in CareEvent.query.filter_by(
            user_plant_id=upid).order_by(CareEvent.date.desc()).limit(50)]
        data['health_assessments'] = [health_json(a) for a in HealthAssessment.query.filter_by(
            user_plant_id=upid).order_by(HealthAssessment.assessment_date.desc())]
    return data


def user_json(user):
    return {
        'user_id': user.user_id,
        'username': user.username,
        'email': user.email,
        'region': user.region.name if user.region else None,
    }


# ----------------------------------------
# Accounts
# ----------------------------------------

@mobile_api.route('/options')
def options():
    """The fixed lists the app shows in its pickers."""
    return jsonify({
        'care_types': services.CARE_TYPES,
        'reminder_frequencies': list(services.REMINDER_FREQUENCIES),
        'plant_statuses': services.PLANT_STATUSES,
        'regions': [{'region_id': r.region_id, 'name': r.name}
                    for r in Region.query.order_by(Region.name)],
        'min_password_length': services.MIN_PASSWORD_LENGTH,
    })


@mobile_api.route('/auth/register', methods=['POST'])
def register():
    data = body()
    user = services.register_user(data.get('username'), data.get('email'),
                                  data.get('password'), data.get('region_id'))
    return jsonify({'token': services.create_api_token(user), 'user': user_json(user)}), 201


@mobile_api.route('/auth/login', methods=['POST'])
def login():
    data = body()
    user = services.check_login(data.get('email'), data.get('password'))
    if user is None:
        return error('Invalid email or password.', 401)
    return jsonify({'token': services.create_api_token(user), 'user': user_json(user)})


@mobile_api.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    services.revoke_api_token(bearer_token())
    return jsonify({'ok': True})


@mobile_api.route('/me')
@login_required
def me():
    return jsonify({'user': user_json(g.user)})


@mobile_api.route('/me', methods=['DELETE'])
@login_required
def delete_me():
    """Delete the account for good. The password is asked for again to be sure."""
    if not g.user.check_password(body().get('password') or ''):
        return error('That password is not right, so the account was not deleted.', 403)
    services.delete_account(g.user)
    return jsonify({'ok': True})


# ----------------------------------------
# Home screen
# ----------------------------------------

@mobile_api.route('/dashboard')
@login_required
def dashboard():
    uid = g.user.user_id
    upcoming = crud.get_upcoming_reminders(uid)
    return jsonify({
        'user': user_json(g.user),
        'plant_count': UserPlant.query.filter_by(user_id=uid).count(),
        'recent_care_count': len(crud.get_recent_care_events(uid)),
        'upcoming_reminders': [reminder_json(r, with_plant=True) for r in upcoming],
        'today': date.today().isoformat(),
    })


@mobile_api.route('/reminders')
@login_required
def all_reminders():
    """Every active reminder, so the phone can schedule its notifications."""
    reminders = (Reminder.query.join(UserPlant)
                 .filter(UserPlant.user_id == g.user.user_id, Reminder.is_active.is_(True))
                 .order_by(Reminder.next_reminder_date).all())
    return jsonify({'reminders': [reminder_json(r, with_plant=True) for r in reminders]})


# ----------------------------------------
# Plant catalogue
# ----------------------------------------

@mobile_api.route('/plants')
@login_required
def plants():
    """Search the catalogue. Results from our database come first, then Trefle's."""
    import api.quantitative_plant as trefle

    search = (request.args.get('search') or '').strip()
    if not search:
        found = Plant.query.order_by(Plant.common_name).limit(50).all()
        return jsonify({'plants': [plant_json(p, with_care=False) for p in found],
                        'more': []})

    found = crud.search_plants(search, limit=30)
    more = []
    if len(found) < 10:
        known = {p.scientific_name for p in found}
        for item in (trefle.search_plants(search).get('data') or [])[:15]:
            name = item.get('scientific_name')
            if name and name not in known and item.get('id'):
                more.append({
                    'trefle_id': item['id'],
                    'scientific_name': name,
                    'common_name': item.get('common_name') or name,
                    'image_url': item.get('image_url'),
                })
    return jsonify({'plants': [plant_json(p, with_care=False) for p in found], 'more': more})


@mobile_api.route('/plants/<int:plant_id>')
@login_required
def plant(plant_id):
    found = db.session.get(Plant, plant_id)
    if found is None:
        return error('That plant could not be found.', 404)
    return jsonify({'plant': plant_json(found)})


# ----------------------------------------
# My plants
# ----------------------------------------

@mobile_api.route('/my-plants')
@login_required
def my_plants():
    mine = (UserPlant.query.filter_by(user_id=g.user.user_id)
            .order_by(UserPlant.user_plant_id.desc()).all())
    return jsonify({'plants': [user_plant_json(up) for up in mine]})


@mobile_api.route('/my-plants', methods=['POST'])
@login_required
def add_my_plant():
    """Add a plant to my collection.

    Send plant_id for a plant already in our catalogue, or trefle_id for a
    Trefle search result (it is copied into our catalogue first).
    """
    data = body()
    plant_id = data.get('plant_id')
    if not plant_id and data.get('trefle_id'):
        plant_id = services.import_trefle_plant(data.get('trefle_id')).plant_id
    user_plant = services.add_to_collection(g.user.user_id, plant_id,
                                            data.get('nickname'), data.get('location'))
    return jsonify({'plant': user_plant_json(user_plant, full=True)}), 201


@mobile_api.route('/my-plants/<int:user_plant_id>')
@login_required
def my_plant(user_plant_id):
    user_plant = my_plant_or_404(user_plant_id)
    if user_plant is None:
        return error('That plant could not be found.', 404)
    return jsonify({'plant': user_plant_json(user_plant, full=True)})


@mobile_api.route('/my-plants/<int:user_plant_id>', methods=['PATCH', 'POST'])
@login_required
def update_my_plant(user_plant_id):
    """Change nickname, location, status, notes and/or photo (form field "image")."""
    user_plant = my_plant_or_404(user_plant_id)
    if user_plant is None:
        return error('That plant could not be found.', 404)
    data = body()
    services.update_user_plant(
        user_plant,
        nickname=data.get('nickname'),
        location=data.get('location'),
        status=data.get('status'),
        notes=data.get('notes'),
        photo=request.files.get('image'),
    )
    return jsonify({'plant': user_plant_json(user_plant, full=True)})


@mobile_api.route('/my-plants/<int:user_plant_id>', methods=['DELETE'])
@login_required
def delete_my_plant(user_plant_id):
    user_plant = my_plant_or_404(user_plant_id)
    if user_plant is None:
        return error('That plant could not be found.', 404)
    services.delete_user_plant(user_plant)
    return jsonify({'ok': True})


@mobile_api.route('/my-plants/<int:user_plant_id>/care-events', methods=['POST'])
@login_required
def add_care_event(user_plant_id):
    user_plant = my_plant_or_404(user_plant_id)
    if user_plant is None:
        return error('That plant could not be found.', 404)
    data = body()
    event = services.log_care(user_plant, data.get('event_type'), data.get('notes'))
    return jsonify({'care_event': care_event_json(event)}), 201


@mobile_api.route('/my-plants/<int:user_plant_id>/reminders', methods=['POST'])
@login_required
def add_reminder(user_plant_id):
    user_plant = my_plant_or_404(user_plant_id)
    if user_plant is None:
        return error('That plant could not be found.', 404)
    data = body()
    reminder = services.add_reminder(user_plant, data.get('reminder_type'),
                                     data.get('frequency'), data.get('next_reminder_date'))
    return jsonify({'reminder': reminder_json(reminder, with_plant=True)}), 201


def my_reminder_or_404(reminder_id):
    reminder = db.session.get(Reminder, reminder_id)
    if reminder is None or reminder.user_plant.user_id != g.user.user_id:
        return None
    return reminder


@mobile_api.route('/reminders/<int:reminder_id>/done', methods=['POST'])
@login_required
def reminder_done(reminder_id):
    """Mark as done: logs the care and moves the reminder to its next date."""
    reminder = my_reminder_or_404(reminder_id)
    if reminder is None:
        return error('That reminder could not be found.', 404)
    services.complete_reminder(reminder)
    return jsonify({'reminder': reminder_json(reminder, with_plant=True)})


@mobile_api.route('/reminders/<int:reminder_id>', methods=['DELETE'])
@login_required
def reminder_delete(reminder_id):
    reminder = my_reminder_or_404(reminder_id)
    if reminder is None:
        return error('That reminder could not be found.', 404)
    services.delete_reminder(reminder)
    return jsonify({'ok': True})


@mobile_api.route('/my-plants/<int:user_plant_id>/health', methods=['POST'])
@login_required
def add_health(user_plant_id):
    """Record a health problem. Send as a form; "symptoms" may repeat; photo field is "image"."""
    user_plant = my_plant_or_404(user_plant_id)
    if user_plant is None:
        return error('That plant could not be found.', 404)
    if request.is_json:
        data = body()
        symptoms = data.get('symptoms') or []
        if not isinstance(symptoms, list):
            symptoms = [str(symptoms)]
        symptoms = [str(s) for s in symptoms]
    else:
        data = request.form
        symptoms = request.form.getlist('symptoms')
    assessment = services.add_health_assessment(
        user_plant, symptoms=symptoms, diagnosis=data.get('diagnosis'),
        treatment=data.get('treatment_recommendations'), photo=request.files.get('image'))
    return jsonify({'health_assessment': health_json(assessment)}), 201


@mobile_api.route('/health/<int:assessment_id>/resolve', methods=['POST'])
@login_required
def resolve_health(assessment_id):
    assessment = db.session.get(HealthAssessment, assessment_id)
    if assessment is None or assessment.user_plant.user_id != g.user.user_id:
        return error('That health record could not be found.', 404)
    assessment.resolved = True
    db.session.commit()
    return jsonify({'health_assessment': health_json(assessment)})
