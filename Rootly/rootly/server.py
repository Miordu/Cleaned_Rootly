"""Server for Rootly app."""

from flask import (Flask, render_template, request, flash, redirect, 
                   session, jsonify, url_for)
from model import connect_to_db, db, User, Plant, PlantCareDetails, UserPlant
from model import CareEvent, Reminder, HealthAssessment, Region
import os
from datetime import datetime, date, timedelta
from jinja2 import StrictUndefined
from werkzeug.utils import secure_filename
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.jinja_env.undefined = StrictUndefined

# Set up secret key for sessions and debug
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')

# Configure upload folder for plant images
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Helper functions
def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def homepage():
    """Show homepage."""
    return render_template('homepage.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user."""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        region_id = request.form.get('region_id') or None  # Handle empty string
        
        # Check if user already exists
        existing_user = User.query.filter(User.email == email).first()
        if existing_user:
            flash('An account with this email already exists.')
            return redirect('/register')
        
        # Create new user
        new_user = User(username=username, email=email, region_id=region_id)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        # Log in the user
        session['user_id'] = new_user.user_id
        flash(f'Account created for {username}!')
        return redirect('/dashboard')
    
    # Get regions for the dropdown
    regions = Region.query.all()
    return render_template('register.html', regions=regions)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Log in a user."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter(User.email == email).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.user_id
            flash(f'Welcome back, {user.username}!')
            return redirect('/dashboard')
        else:
            flash('Invalid email or password.')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Log out a user."""
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    """Show user dashboard."""
    if 'user_id' not in session:
        flash('Please log in to view your dashboard.')
        return redirect('/login')
    
    user = User.query.get(session['user_id'])
    
    return render_template('dashboard.html', user=user)

@app.route('/identify', methods=['GET', 'POST'])
def identify_plant():
    """Identify a plant from an image."""
    if 'user_id' not in session:
        flash('Please log in to identify plants.')
        return redirect('/login')
    
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'plant_image' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['plant_image']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add user_id to filename to avoid conflicts
            user_filename = f"{session['user_id']}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], user_filename)
            file.save(file_path)
            
            # In a real app, you would call the Plant.id API here
            # For now, we'll just simulate a successful identification
            
            # For demo purposes, just use the first plant in the database
            plant = Plant.query.first()
            
            if plant:
                return render_template('identification_results.html', 
                                      plant=plant, 
                                      image_url=f"/static/uploads/{user_filename}",
                                      confidence=0.95)
            else:
                flash('No plants in database to match against.')
                return redirect('/identify')
    
    return render_template('identify.html')

@app.route('/my-plants')
def my_plants():
    """Show user's plant collection."""
    if 'user_id' not in session:
        flash('Please log in to view your plants.')
        return redirect('/login')
    
    user = User.query.get(session['user_id'])
    user_plants = UserPlant.query.filter_by(user_id=user.user_id).all()
    
    return render_template('my_plants.html', user=user, user_plants=user_plants)

@app.route('/add-plant', methods=['GET', 'POST'])
def add_plant():
    """Add a plant to user's collection."""
    if 'user_id' not in session:
        flash('Please log in to add plants to your collection.')
        return redirect('/login')
    
    if request.method == 'POST':
        plant_id = request.form.get('plant_id')
        nickname = request.form.get('nickname')
        location = request.form.get('location')
        
        new_user_plant = UserPlant(
            user_id=session['user_id'],
            plant_id=plant_id,
            nickname=nickname,
            location_in_home=location,
            acquisition_date=date.today(),
            status='active'
        )
        
        db.session.add(new_user_plant)
        db.session.commit()
        
        flash('Plant added to your collection!')
        return redirect('/my-plants')
    
    # Get all plants to display in a dropdown
    plants = Plant.query.all()
    return render_template('add_plant.html', plants=plants)

@app.route('/browse-plants')
def browse_plants():
    """Browse all plants in the database."""
    # Get search parameter
    search = request.args.get('search', '')
    
    # Filter plants if search parameter is provided
    if search:
        plants = Plant.query.filter(
            (Plant.common_name.ilike(f'%{search}%')) | 
            (Plant.scientific_name.ilike(f'%{search}%'))
        ).all()
    else:
        plants = Plant.query.all()
    
    return render_template('browse_plants.html', plants=plants, search=search)

@app.route('/plant/<int:plant_id>')
def plant_details(plant_id):
    """Show details for a specific plant."""
    plant = Plant.query.get_or_404(plant_id)
    care_details = PlantCareDetails.query.filter_by(plant_id=plant_id).first()
    
    return render_template('plant_details.html', plant=plant, care_details=care_details)

@app.route('/user-plant/<int:user_plant_id>')
def user_plant_details(user_plant_id):
    """Show details for a specific user plant."""
    if 'user_id' not in session:
        flash('Please log in to view your plants.')
        return redirect('/login')
    
    user_plant = UserPlant.query.get_or_404(user_plant_id)
    
    # Ensure the plant belongs to the logged-in user
    if user_plant.user_id != session['user_id']:
        flash('You do not have access to this plant.')
        return redirect('/my-plants')
    
    # Get plant care details
    care_details = PlantCareDetails.query.filter_by(plant_id=user_plant.plant_id).first()
    
    # Get care events
    care_events = CareEvent.query.filter_by(user_plant_id=user_plant_id).order_by(CareEvent.date.desc()).all()
    
    # Get reminders
    reminders = Reminder.query.filter_by(user_plant_id=user_plant_id, is_active=True).order_by(Reminder.next_reminder_date).all()
    
    # Get health assessments
    health_assessments = HealthAssessment.query.filter_by(user_plant_id=user_plant_id).order_by(HealthAssessment.assessment_date.desc()).all()
    
    return render_template('user_plant_details.html', 
                          user_plant=user_plant,
                          care_details=care_details,
                          care_events=care_events,
                          reminders=reminders,
                          health_assessments=health_assessments)

@app.route('/log-care', methods=['POST'])
def log_care():
    """Log a care event for a plant."""
    if 'user_id' not in session:
        flash('Please log in to log care events.')
        return redirect('/login')
    
    user_plant_id = request.form.get('user_plant_id')
    event_type = request.form.get('event_type')
    notes = request.form.get('notes')
    
    # Verify the plant belongs to the user
    user_plant = UserPlant.query.get_or_404(user_plant_id)
    if user_plant.user_id != session['user_id']:
        flash('You do not have access to this plant.')
        return redirect('/my-plants')
    
    # Create the care event
    new_event = CareEvent(
        user_plant_id=user_plant_id,
        event_type=event_type,
        date=datetime.utcnow(),
        notes=notes
    )
    
    db.session.add(new_event)
    db.session.commit()
    
    flash(f'{event_type} event logged successfully!')
    return redirect(f'/user-plant/{user_plant_id}')

@app.route('/add-reminder', methods=['POST'])
def add_reminder():
    """Add a care reminder for a plant."""
    if 'user_id' not in session:
        flash('Please log in to add reminders.')
        return redirect('/login')
    
    user_plant_id = request.form.get('user_plant_id')
    reminder_type = request.form.get('reminder_type')
    frequency = request.form.get('frequency')
    next_reminder_date = request.form.get('next_reminder_date')
    
    # Verify the plant belongs to the user
    user_plant = UserPlant.query.get_or_404(user_plant_id)
    if user_plant.user_id != session['user_id']:
        flash('You do not have access to this plant.')
        return redirect('/my-plants')
    
    # Create the reminder
    new_reminder = Reminder(
        user_plant_id=user_plant_id,
        reminder_type=reminder_type,
        frequency=frequency,
        next_reminder_date=next_reminder_date,
        is_active=True
    )
    
    db.session.add(new_reminder)
    db.session.commit()
    
    flash(f'{reminder_type} reminder added successfully!')
    return redirect(f'/user-plant/{user_plant_id}')

@app.route('/add-health-assessment', methods=['POST'])
def add_health_assessment():
    """Add a health assessment for a plant."""
    if 'user_id' not in session:
        flash('Please log in to add health assessments.')
        return redirect('/login')
    
    user_plant_id = request.form.get('user_plant_id')
    symptoms = request.form.getlist('symptoms')
    diagnosis = request.form.get('diagnosis')
    treatment_recommendations = request.form.get('treatment_recommendations')
    
    # Verify the plant belongs to the user
    user_plant = UserPlant.query.get_or_404(user_plant_id)
    if user_plant.user_id != session['user_id']:
        flash('You do not have access to this plant.')
        return redirect('/my-plants')
    
    # Process image upload if provided
    image_url = None
    if 'image' in request.files and request.files['image'].filename:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add user_id and timestamp to filename to avoid conflicts
            user_filename = f"{session['user_id']}_{int(datetime.utcnow().timestamp())}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], user_filename)
            file.save(file_path)
            image_url = f"/static/uploads/{user_filename}"
    
    # Create the health assessment
    new_assessment = HealthAssessment(
        user_plant_id=user_plant_id,
        assessment_date=datetime.utcnow(),
        symptoms=symptoms,
        diagnosis=diagnosis,
        treatment_recommendations=treatment_recommendations,
        image_url=image_url,
        resolved=False
    )
    
    db.session.add(new_assessment)
    db.session.commit()
    
    flash('Health assessment added successfully!')
    return redirect(f'/user-plant/{user_plant_id}')

@app.route('/resolve-health-issue/<int:assessment_id>', methods=['POST'])
def resolve_health_issue(assessment_id):
    """Mark a health issue as resolved."""
    if 'user_id' not in session:
        flash('Please log in to update health assessments.')
        return redirect('/login')
    
    # Get the assessment
    assessment = HealthAssessment.query.get_or_404(assessment_id)
    
    # Verify the assessment belongs to a plant owned by the user
    user_plant = UserPlant.query.get(assessment.user_plant_id)
    if user_plant.user_id != session['user_id']:
        flash('You do not have access to this assessment.')
        return redirect('/my-plants')
    
    # Mark as resolved
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
    
    user_plant = UserPlant.query.get_or_404(user_plant_id)
    
    # Ensure the plant belongs to the logged-in user
    if user_plant.user_id != session['user_id']:
        flash('You do not have access to this plant.')
        return redirect('/my-plants')
    
    if request.method == 'POST':
        # Update user plant details
        user_plant.nickname = request.form.get('nickname')
        user_plant.location_in_home = request.form.get('location')
        user_plant.status = request.form.get('status')
        user_plant.notes = request.form.get('notes')
        
        # Process image upload if provided
        if 'image' in request.files and request.files['image'].filename:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add user_id and timestamp to filename to avoid conflicts
                user_filename = f"{session['user_id']}_{int(datetime.utcnow().timestamp())}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], user_filename)
                file.save(file_path)
                user_plant.image_url = f"/static/uploads/{user_filename}"
        
        db.session.commit()
        flash('Plant details updated successfully!')
        return redirect(f'/user-plant/{user_plant_id}')
    
    return render_template('edit_user_plant.html', user_plant=user_plant)

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return render_template('500.html'), 500

if __name__ == "__main__":
    connect_to_db(app)
    app.run(host="0.0.0.0", debug=True)