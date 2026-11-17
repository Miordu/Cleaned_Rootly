"""Actions shared by the website (server.py) and the mobile app API (mobile_api.py).

Keeping them here means both do exactly the same thing: the same sign-up
rules, the same photo handling, the same way of importing a plant.
"""

import hashlib
import io
import logging
import secrets
from datetime import date, datetime, timedelta

from PIL import Image, ImageOps, UnidentifiedImageError

from model import (db, User, Plant, PlantCareDetails, UserPlant, CareEvent,
                   Reminder, HealthAssessment, IdentificationHistory,
                   UserFavorite, Photo, ApiToken, Region)

logger = logging.getLogger(__name__)

MIN_PASSWORD_LENGTH = 8
MAX_PHOTO_SIDE = 1600  # pixels; bigger photos are shrunk to save space

CARE_TYPES = ['Watering', 'Fertilizing', 'Pruning', 'Repotting', 'Misting', 'Other']
REMINDER_FREQUENCIES = {
    'Daily': 1,
    'Weekly': 7,
    'Biweekly': 14,
    'Monthly': 30,
    'Seasonally': 91,
}
PLANT_STATUSES = ['active', 'dormant', 'struggling', 'deceased']


class ValidationError(Exception):
    """Something the person typed or sent isn't usable. The message is safe to show them."""


def clean(value, max_length=None):
    """Trim a piece of text from a form; empty text becomes None."""
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    if max_length:
        value = value[:max_length]
    return value


# ----------------------------------------
# Accounts
# ----------------------------------------

def register_user(username, email, password, region_id=None):
    """Create an account, or raise ValidationError saying what's wrong."""
    username = clean(username)
    email = (clean(email) or '').lower()
    password = password or ''

    if not username:
        raise ValidationError('Please enter a username.')
    if len(username) > 50:
        raise ValidationError('Usernames can be up to 50 characters.')
    if '@' not in email or '.' not in email.split('@')[-1] or len(email) > 100:
        raise ValidationError('Please enter a valid email address.')
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f'Passwords need at least {MIN_PASSWORD_LENGTH} characters.')
    if db.session.query(User).filter(db.func.lower(User.email) == email).first():
        raise ValidationError('An account with this email already exists.')

    if region_id in ('', None):
        region_id = None
    else:
        try:
            region_id = int(region_id)
        except (TypeError, ValueError):
            region_id = None
        if region_id is not None and db.session.get(Region, region_id) is None:
            region_id = None

    user = User(username=username, email=email, region_id=region_id)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


# Wrong-password attempts per email, to slow down password guessing.
# Kept in memory, so it resets when the server restarts.
MAX_FAILED_LOGINS = 10
FAILED_LOGIN_WINDOW = timedelta(minutes=15)
_failed_logins = {}


def check_login(email, password):
    """Return the user if the email and password match, otherwise None.

    Raises ValidationError after too many wrong passwords for one email.
    """
    email = (clean(email) or '').lower()
    now = datetime.utcnow()
    recent = [t for t in _failed_logins.get(email, []) if now - t < FAILED_LOGIN_WINDOW]
    if len(recent) >= MAX_FAILED_LOGINS:
        raise ValidationError('Too many wrong passwords. Please wait 15 minutes and try again.')

    user = db.session.query(User).filter(db.func.lower(User.email) == email).first()
    if user and password and user.check_password(password):
        _failed_logins.pop(email, None)
        return user

    if email:
        _failed_logins[email] = recent + [now]
        if len(_failed_logins) > 10000:  # don't let the list grow forever
            _failed_logins.clear()
    return None


def _hash_token(token):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def create_api_token(user):
    """Make a new mobile login for this user and return the secret token."""
    token = secrets.token_urlsafe(32)
    db.session.add(ApiToken(user_id=user.user_id, token_hash=_hash_token(token)))
    db.session.commit()
    return token


def user_for_api_token(token):
    """Return the user a mobile token belongs to, or None."""
    if not token:
        return None
    record = db.session.query(ApiToken).filter_by(token_hash=_hash_token(token)).first()
    if record is None:
        return None
    # Note when it was last used, at most once an hour to avoid a write per request
    now = datetime.utcnow()
    if record.last_used_at is None or now - record.last_used_at > timedelta(hours=1):
        record.last_used_at = now
        db.session.commit()
    return record.user


def revoke_api_token(token):
    """Log one phone out."""
    db.session.query(ApiToken).filter_by(token_hash=_hash_token(token or '')).delete()
    db.session.commit()


def delete_account(user):
    """Permanently delete someone's account and everything they added."""
    for user_plant in list(user.plants):
        _delete_user_plant_rows(user_plant)
    db.session.query(IdentificationHistory).filter_by(user_id=user.user_id).delete()
    db.session.query(UserFavorite).filter_by(user_id=user.user_id).delete()
    db.session.query(ApiToken).filter_by(user_id=user.user_id).delete()
    db.session.query(Photo).filter_by(user_id=user.user_id).delete()
    db.session.delete(user)
    db.session.commit()


# ----------------------------------------
# Photos
# ----------------------------------------

def save_photo(file_storage, user_id):
    """Store an uploaded photo and return its web address (e.g. /photos/abc.jpg).

    Returns None when no file was sent. Raises ValidationError when the file
    isn't a photo. Every photo is re-saved as a JPEG no bigger than
    1600 pixels, which also strips anything hidden inside the file.
    """
    if file_storage is None or not getattr(file_storage, 'filename', None):
        return None
    try:
        image = Image.open(file_storage.stream)
        image = ImageOps.exif_transpose(image)  # phone photos: fix sideways pictures
        image = image.convert('RGB')
        image.thumbnail((MAX_PHOTO_SIDE, MAX_PHOTO_SIDE))
        out = io.BytesIO()
        image.save(out, format='JPEG', quality=85)
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise ValidationError('That file is not a photo we can read. Please use a JPG or PNG.')

    photo = Photo(token=secrets.token_urlsafe(16), user_id=user_id,
                  content_type='image/jpeg', data=out.getvalue())
    db.session.add(photo)
    db.session.flush()
    return f"/photos/{photo.token}.jpg"


def delete_photo_by_url(image_url):
    """Remove a stored photo given the address save_photo returned."""
    if image_url and image_url.startswith('/photos/'):
        token = image_url[len('/photos/'):].rsplit('.', 1)[0]
        db.session.query(Photo).filter_by(token=token).delete()


# ----------------------------------------
# Plants
# ----------------------------------------

def import_trefle_plant(trefle_id):
    """Copy one plant from Trefle into our database and return it.

    If we already have that plant, the existing one is returned. Raises
    ValidationError when Trefle can't give us the plant.
    """
    from api.quantitative_plant import (get_plant_details, get_growth_data,
                                        map_growth_data_to_model)

    try:
        trefle_id = int(trefle_id)
    except (TypeError, ValueError):
        raise ValidationError('That plant could not be found.')

    details = get_plant_details(str(trefle_id))
    data = (details or {}).get('data')
    if not data or not data.get('scientific_name'):
        raise ValidationError('Could not get that plant from the plant database right now. '
                              'Please try again in a minute.')

    scientific_name = data['scientific_name'][:255]
    existing = db.session.query(Plant).filter_by(scientific_name=scientific_name).first()
    if existing:
        return existing

    family = data.get('family_common_name') or (data.get('family') or {})
    if isinstance(family, dict):
        family = family.get('name')
    plant = Plant(
        scientific_name=scientific_name,
        common_name=(data.get('common_name') or scientific_name)[:255],
        description=f"A plant in the {family} family." if family else None,
        image_url=(data.get('image_url') or None),
        indoor=True,
        data_sources=['trefle'],
    )
    if plant.image_url and len(plant.image_url) > 500:
        plant.image_url = None
    db.session.add(plant)
    db.session.flush()

    care = map_growth_data_to_model(get_growth_data(trefle_id, plant_details=details))
    db.session.add(PlantCareDetails(
        plant_id=plant.plant_id,
        sunlight_requirements=care.get('sunlight_requirements') or [],
        soil_preferences=care.get('soil_preferences'),
        temperature_range=care.get('temperature_range'),
        difficulty_level=care.get('difficulty_level'),
        growth_rate=care.get('growth_rate'),
    ))
    db.session.commit()
    return plant


def add_to_collection(user_id, plant_id, nickname=None, location=None):
    """Add a plant from the catalogue to someone's collection."""
    try:
        plant_id = int(plant_id)
    except (TypeError, ValueError):
        plant_id = None
    if not plant_id or db.session.get(Plant, plant_id) is None:
        raise ValidationError('Please choose a plant from the list.')
    user_plant = UserPlant(
        user_id=user_id,
        plant_id=plant_id,
        nickname=clean(nickname, 100),
        location_in_home=clean(location, 100),
        acquisition_date=date.today(),
        status='active',
    )
    db.session.add(user_plant)
    db.session.commit()
    return user_plant


def _delete_user_plant_rows(user_plant):
    upid = user_plant.user_plant_id
    for assessment in user_plant.health_assessments:
        delete_photo_by_url(assessment.image_url)
    delete_photo_by_url(user_plant.image_url)
    db.session.query(CareEvent).filter_by(user_plant_id=upid).delete()
    db.session.query(Reminder).filter_by(user_plant_id=upid).delete()
    db.session.query(HealthAssessment).filter_by(user_plant_id=upid).delete()
    db.session.query(IdentificationHistory).filter_by(user_plant_id=upid).update(
        {'user_plant_id': None})
    db.session.delete(user_plant)


def delete_user_plant(user_plant):
    """Remove a plant from someone's collection, with its care log, reminders and health records."""
    _delete_user_plant_rows(user_plant)
    db.session.commit()


# ----------------------------------------
# Care, reminders, health
# ----------------------------------------

def log_care(user_plant, event_type, notes=None):
    event_type = clean(event_type, 50)
    if not event_type:
        raise ValidationError('Please choose the type of care.')
    event = CareEvent(user_plant_id=user_plant.user_plant_id, event_type=event_type,
                      date=datetime.utcnow(), notes=clean(notes))
    db.session.add(event)
    db.session.commit()
    return event


def parse_date(value):
    """Read a YYYY-MM-DD date or raise ValidationError."""
    try:
        return date.fromisoformat((value or '').strip())
    except (ValueError, AttributeError):
        raise ValidationError('Please pick a date for the reminder.')


def add_reminder(user_plant, reminder_type, frequency, next_date):
    reminder_type = clean(reminder_type, 50)
    frequency = clean(frequency, 50)
    if not reminder_type:
        raise ValidationError('Please choose what the reminder is for.')
    if frequency not in REMINDER_FREQUENCIES:
        raise ValidationError('Please choose how often to be reminded.')
    reminder = Reminder(user_plant_id=user_plant.user_plant_id, reminder_type=reminder_type,
                        frequency=frequency, next_reminder_date=parse_date(next_date),
                        is_active=True)
    db.session.add(reminder)
    db.session.commit()
    return reminder


def complete_reminder(reminder, today=None):
    """Mark a reminder as done: log the care and move it to its next date.

    `today` is the date on the person's phone ("YYYY-MM-DD"), which can be a
    day ahead of or behind the server's. It's ignored unless it is within a
    day of the server's date.
    """
    try:
        client_today = date.fromisoformat(today) if today else None
    except (TypeError, ValueError):
        client_today = None
    if client_today is None or abs((client_today - date.today()).days) > 1:
        client_today = date.today()
    days = REMINDER_FREQUENCIES.get(reminder.frequency, 7)
    db.session.add(CareEvent(user_plant_id=reminder.user_plant_id,
                             event_type=reminder.reminder_type,
                             date=datetime.utcnow(),
                             notes='Logged from a reminder'))
    reminder.next_reminder_date = client_today + timedelta(days=days)
    db.session.commit()
    return reminder


def delete_reminder(reminder):
    db.session.delete(reminder)
    db.session.commit()


def add_health_assessment(user_plant, symptoms=None, diagnosis=None, treatment=None, photo=None):
    image_url = save_photo(photo, user_plant.user_id)
    assessment = HealthAssessment(
        user_plant_id=user_plant.user_plant_id,
        assessment_date=datetime.utcnow(),
        symptoms=[s[:100] for s in (symptoms or []) if s and s.strip()],
        diagnosis=clean(diagnosis, 255),
        treatment_recommendations=clean(treatment),
        image_url=image_url,
        resolved=False,
    )
    db.session.add(assessment)
    db.session.commit()
    return assessment


def update_user_plant(user_plant, nickname=None, location=None, status=None, notes=None, photo=None):
    """Change a plant's details. Only the values that are passed (not None) change."""
    if nickname is not None:
        user_plant.nickname = clean(nickname, 100)
    if location is not None:
        user_plant.location_in_home = clean(location, 100)
    if status is not None and clean(status) in PLANT_STATUSES:
        user_plant.status = clean(status)
    if notes is not None:
        user_plant.notes = clean(notes)
    new_url = save_photo(photo, user_plant.user_id)
    if new_url:
        delete_photo_by_url(user_plant.image_url)
        user_plant.image_url = new_url
    db.session.commit()
    return user_plant
