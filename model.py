"""Models for Rootly plant care app."""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    """User of Rootly website."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    region_id = db.Column(db.Integer, db.ForeignKey('regions.region_id'), nullable=True)
    preferences = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    region = db.relationship('Region', backref='users')
    plants = db.relationship('UserPlant', backref='user')
    favorites = db.relationship('UserFavorite', backref='user')
    identifications = db.relationship('IdentificationHistory', backref='user')

    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """Check password."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User user_id={self.user_id} username={self.username}>"


class Plant(db.Model):
    """Plant in the database."""

    __tablename__ = "plants"

    plant_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    scientific_name = db.Column(db.String(255), nullable=False, unique=True)
    common_name = db.Column(db.String(255))
    plant_type = db.Column(db.String(100))
    image_url = db.Column(db.String(500))
    origin = db.Column(db.String(255))
    description = db.Column(db.Text)
    poisonous_to_humans = db.Column(db.Boolean, default=False)
    poisonous_to_pets = db.Column(db.Boolean, default=False)
    invasive = db.Column(db.Boolean, default=False)
    rare = db.Column(db.Boolean, default=False)
    tropical = db.Column(db.Boolean, default=False)
    indoor = db.Column(db.Boolean, default=False)
    outdoor = db.Column(db.Boolean, default=False)
    data_sources = db.Column(db.ARRAY(db.String(50)))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    care_details = db.relationship('PlantCareDetails', backref='plant', uselist=False)
    user_plants = db.relationship('UserPlant', backref='plant')
    health_issues = db.relationship('PlantHealthIssue', backref='plant')
    favorites = db.relationship('UserFavorite', backref='plant')
    region_care = db.relationship('PlantRegionCare', backref='plant')
    identifications = db.relationship('IdentificationHistory', backref='identified_plant')

    def __repr__(self):
        return f"<Plant plant_id={self.plant_id} name={self.common_name or self.scientific_name}>"


class PlantCareDetails(db.Model):
    """Care details for a plant."""

    __tablename__ = "plant_care_details"

    care_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plants.plant_id'), nullable=False)
    watering_frequency = db.Column(db.String(100))
    watering_interval_days = db.Column(db.Integer)
    sunlight_requirements = db.Column(db.ARRAY(db.String(50)))
    sunlight_duration_min = db.Column(db.Integer)
    sunlight_duration_max = db.Column(db.Integer)
    sunlight_duration_unit = db.Column(db.String(20), default='hours')
    soil_preferences = db.Column(db.Text)
    temperature_range = db.Column(db.String(100))
    fertilizing_schedule = db.Column(db.Text)
    pruning_months = db.Column(db.ARRAY(db.String(20)))
    difficulty_level = db.Column(db.String(20))
    growth_rate = db.Column(db.String(20))
    propagation_methods = db.Column(db.ARRAY(db.String(50)))
    companion_plants = db.Column(db.Text)

    def __repr__(self):
        return f"<PlantCareDetails care_id={self.care_id} plant_id={self.plant_id}>"

class UserPlant(db.Model):
    """A plant in a user's collection."""

    __tablename__ = "user_plants"

    user_plant_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    plant_id = db.Column(db.Integer, db.ForeignKey('plants.plant_id'), nullable=False)
    nickname = db.Column(db.String(100))
    location_in_home = db.Column(db.String(100))
    acquisition_date = db.Column(db.Date)
    image_url = db.Column(db.String(500))
    notes = db.Column(db.Text)
    status = db.Column(db.String(50))

    # Relationships
    care_events = db.relationship('CareEvent', backref='user_plant')
    reminders = db.relationship('Reminder', backref='user_plant')
    health_assessments = db.relationship('HealthAssessment', backref='user_plant')
    identifications = db.relationship('IdentificationHistory', backref='user_plant')

    def __repr__(self):
        return f"<UserPlant user_plant_id={self.user_plant_id} nickname={self.nickname}>"


class CareEvent(db.Model):
    """A care event for a user's plant."""

    __tablename__ = "care_events"

    event_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_plant_id = db.Column(db.Integer, db.ForeignKey('user_plants.user_plant_id'), nullable=False)
    event_type = db.Column(db.String(50))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

    def __repr__(self):
        return f"<CareEvent event_id={self.event_id} type={self.event_type}>"


class Reminder(db.Model):
    """A reminder for plant care."""

    __tablename__ = "reminders"

    reminder_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_plant_id = db.Column(db.Integer, db.ForeignKey('user_plants.user_plant_id'), nullable=False)
    reminder_type = db.Column(db.String(50))
    frequency = db.Column(db.String(50))
    next_reminder_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Reminder reminder_id={self.reminder_id} type={self.reminder_type}>"


class HealthAssessment(db.Model):
    """A health assessment for a user's plant."""

    __tablename__ = "health_assessments"

    assessment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_plant_id = db.Column(db.Integer, db.ForeignKey('user_plants.user_plant_id'), nullable=False)
    assessment_date = db.Column(db.DateTime, default=datetime.utcnow)
    symptoms = db.Column(db.ARRAY(db.String(100)))
    diagnosis = db.Column(db.String(255))
    treatment_recommendations = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    resolved = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<HealthAssessment assessment_id={self.assessment_id} diagnosis={self.diagnosis}>"


class IdentificationHistory(db.Model):
    """History of plant identifications."""

    __tablename__ = "identification_history"

    identification_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    user_plant_id = db.Column(db.Integer, db.ForeignKey('user_plants.user_plant_id'), nullable=True)
    image_url = db.Column(db.String(500))
    identified_plant_id = db.Column(db.Integer, db.ForeignKey('plants.plant_id'), nullable=False)
    confidence_score = db.Column(db.Float)
    identified_at = db.Column(db.DateTime, default=datetime.utcnow)
    added_to_collection = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<IdentificationHistory id={self.identification_id} user_id={self.user_id}>"


class PlantHealthIssue(db.Model):
    """Common health issues for a plant species."""

    __tablename__ = "plant_health_issues"

    issue_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plants.plant_id'), nullable=False)
    issue_name = db.Column(db.String(255), nullable=False)
    symptoms = db.Column(db.Text)
    treatment = db.Column(db.Text)
    prevention = db.Column(db.Text)
    severity = db.Column(db.String(50))

    def __repr__(self):
        return f"<PlantHealthIssue issue_id={self.issue_id} name={self.issue_name}>"


class UserFavorite(db.Model):
    """Plant favorites for users."""

    __tablename__ = "user_favorites"

    favorite_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    plant_id = db.Column(db.Integer, db.ForeignKey('plants.plant_id'), nullable=False)
    favorited_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<UserFavorite favorite_id={self.favorite_id} user_id={self.user_id}>"


class Region(db.Model):
    """Geographic regions."""

    __tablename__ = "regions"

    region_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    climate_zone = db.Column(db.String(50))
    avg_temperature = db.Column(db.Float)
    humidity_level = db.Column(db.String(50))

    # Relationships
    plant_region_care = db.relationship('PlantRegionCare', backref='region')

    def __repr__(self):
        return f"<Region region_id={self.region_id} name={self.name}>"


class PlantRegionCare(db.Model):
    """Region-specific plant care."""

    __tablename__ = "plant_region_care"

    plant_region_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plants.plant_id'), nullable=False)
    region_id = db.Column(db.Integer, db.ForeignKey('regions.region_id'), nullable=False)
    watering_frequency = db.Column(db.String(100))
    sunlight_adjustments = db.Column(db.Text)
    seasonal_notes = db.Column(db.Text)

    def __repr__(self):
        return f"<PlantRegionCare id={self.plant_region_id} plant_id={self.plant_id}>"


class RelatedPlant(db.Model):
    """Relationships between plant species."""

    __tablename__ = "related_plants"

    related_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plant_id_1 = db.Column(db.Integer, db.ForeignKey('plants.plant_id'), nullable=False)
    plant_id_2 = db.Column(db.Integer, db.ForeignKey('plants.plant_id'), nullable=False)
    relationship_type = db.Column(db.String(100))
    notes = db.Column(db.Text)

    # Relationships
    plant_1 = db.relationship('Plant', foreign_keys=[plant_id_1], backref=db.backref('related_as_1', lazy='dynamic'))
    plant_2 = db.relationship('Plant', foreign_keys=[plant_id_2], backref=db.backref('related_as_2', lazy='dynamic'))

    def __repr__(self):
        return f"<RelatedPlant related_id={self.related_id} type={self.relationship_type}>"


def connect_to_db(flask_app, db_uri="postgresql:///rootly", echo=True):
    """Connect the database to our Flask app."""

    # Configure to use our database
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    flask_app.config["SQLALCHEMY_ECHO"] = echo
    flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = flask_app
    db.init_app(flask_app)

    print("Connected to the db!")


if __name__ == "__main__":
    from server import app
    connect_to_db(app)
    print("Connected to DB.")

