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
import crud

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

# Initialize database connection
from model import connect_to_db
connect_to_db(app)

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
    
    user = db.session.get(User, session['user_id'])
    
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
            user_filename = f"{session['user_id']}_{datetime.utcnow().timestamp()}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], user_filename)
            file.save(file_path)
            
            # Call the Plant.id API
            from api.plant_id import identify_plant, map_identification_result
            
            try:
                # Identify the plant
                identification_result = identify_plant(file_path)
                
                if 'error' in identification_result:
                    flash(f"Error identifying plant: {identification_result['error']}")
                    return redirect('/identify')
                
                # Map the result to our model structure
                plant_data = map_identification_result(identification_result)
                
                if not plant_data:
                    flash("Could not identify the plant. Please try with a clearer image.")
                    return redirect('/identify')
                
                # Look for matching plant in database
                plant = crud.get_plant_by_scientific_name(plant_data['scientific_name'])
                
                # If not found, create a new plant entry
                if not plant:
                    # Import the data merger
                    from data_merger import find_or_create_plant
                    plant = find_or_create_plant(scientific_name=plant_data['scientific_name'])
                
                # Create identification history record
                identification = crud.create_identification(
                    user_id=session['user_id'],
                    image_url=f"/static/uploads/{user_filename}",
                    identified_plant_id=plant.plant_id,
                    confidence_score=plant_data.get('confidence_score', 0.0)
                )
                
                return render_template('identification_results.html', 
                                      plant=plant, 
                                      image_url=f"/static/uploads/{user_filename}",
                                      confidence=plant_data.get('confidence_score', 0.0),
                                      plant_data=plant_data)
            
            except Exception as e:
                app.logger.error(f"Error in plant identification: {str(e)}")
                flash("An error occurred during identification. Please try again.")
                return redirect('/identify')
    
    return render_template('identify.html')

@app.route('/my-plants')
def my_plants():
    """Show user's plant collection."""
    if 'user_id' not in session:
        flash('Please log in to view your plants.')
        return redirect('/login')
    
    user = db.session.get(User, session['user_id'])
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
    """Browse plants from APIs and database."""
    # Get search parameter
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    
    try:
        if search:
            # Search local database first
            local_plants = Plant.query.filter(
                (Plant.common_name.ilike(f'%{search}%')) | 
                (Plant.scientific_name.ilike(f'%{search}%'))
            ).limit(20).all()
            
            # If few results, supplement with API search
            if len(local_plants) < 10:
                try:
                    from api.perenual import search_plants as perenual_search
                    api_plants = perenual_search(search)
                    if api_plants and 'data' in api_plants:
                        # Convert API plants to display format
                        for plant_data in api_plants['data'][:10]:
                            # Create temporary plant objects for display
                            api_plant = {
                                'plant_id': f"api_{plant_data.get('id', 0)}",
                                'scientific_name': plant_data.get('scientific_name', ['Unknown'])[0] if plant_data.get('scientific_name') else 'Unknown',
                                'common_name': plant_data.get('common_name', 'Unknown'),
                                'image_url': plant_data.get('default_image', {}).get('small_url') if plant_data.get('default_image') else None,
                                'description': f"A {plant_data.get('type', 'plant')} from our plant database.",
                                'is_api_result': True
                            }
                            local_plants.append(type('Plant', (), api_plant)())
                except Exception as e:
                    logger.warning(f"API search failed: {e}")
            
            plants = local_plants
        else:
            # Load popular plants from API
            try:
                from api.perenual import get_plant_list
                api_response = get_plant_list(page=page)
                plants = []
                
                if api_response and 'data' in api_response:
                    for plant_data in api_response['data']:
                        # Create plant objects for display
                        api_plant = {
                            'plant_id': f"api_{plant_data.get('id', 0)}",
                            'scientific_name': plant_data.get('scientific_name', ['Unknown'])[0] if plant_data.get('scientific_name') else 'Unknown',
                            'common_name': plant_data.get('common_name', 'Unknown'),
                            'image_url': plant_data.get('default_image', {}).get('small_url') if plant_data.get('default_image') else None,
                            'description': f"A {plant_data.get('type', 'plant')} from our plant database.",
                            'is_api_result': True
                        }
                        plants.append(type('Plant', (), api_plant)())
                else:
                    # Fall back to local database
                    plants = Plant.query.limit(20).all()
            except Exception as e:
                logger.error(f"API request failed: {e}")
                # Fall back to local database
                plants = Plant.query.limit(20).all()
                
    except Exception as e:
        logger.error(f"Error in browse_plants: {e}")
        plants = Plant.query.limit(20).all()
    
    return render_template('browse_plants.html', plants=plants, search=search, page=page)

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
    
    # Verify the plant belongs to the user
    user_plant = UserPlant.query.get_or_404(user_plant_id)
    if user_plant.user_id != session['user_id']:
        flash('You do not have access to this plant.')
        return redirect('/my-plants')
    
    # Process image upload if provided
    image_url = None
    assessment_result = None
    
    if 'image' in request.files and request.files['image'].filename:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add user_id and timestamp to filename to avoid conflicts
            user_filename = f"{session['user_id']}_{int(datetime.utcnow().timestamp())}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], user_filename)
            file.save(file_path)
            image_url = f"/static/uploads/{user_filename}"
            
            # Use Plant.health API for automated assessment
            try:
                from api.plant_health import assess_health, map_health_assessment
                
                # Assess plant health
                health_result = assess_health(file_path)
                
                if 'error' not in health_result:
                    # Map health assessment to our model structure
                    assessment_result = map_health_assessment(health_result)
                else:
                    app.logger.warning(f"Health assessment API error: {health_result.get('error')}")
            except Exception as e:
                app.logger.error(f"Error in health assessment: {str(e)}")
    
    # Get form data
    symptoms = request.form.getlist('symptoms')
    diagnosis = request.form.get('diagnosis')
    treatment_recommendations = request.form.get('treatment_recommendations')
    
    # If we have an API assessment result, use it to supplement user input
    if assessment_result:
        # Only use API diagnosis if user didn't provide one
        if not diagnosis and assessment_result.get('diagnosis'):
            diagnosis = assessment_result.get('diagnosis')
        
        # Combine symptoms from user and API
        if assessment_result.get('symptoms'):
            symptoms = list(set(symptoms + assessment_result.get('symptoms', [])))
        
        # Enhance treatment recommendations
        if assessment_result.get('treatment_recommendations'):
            if treatment_recommendations:
                treatment_recommendations += "\n\nAPI Suggestions: " + assessment_result.get('treatment_recommendations')
            else:
                treatment_recommendations = assessment_result.get('treatment_recommendations')
    
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

@app.route('/search-plants')
def search_plants():
    """Search for plants using Trefle API with fallback to database."""
    if 'user_id' not in session:
        flash('Please log in to search plants.')
        return redirect('/login')
    
    query = request.args.get('query', '')
    
    if not query:
        return render_template('search_plants.html', plants=None, query=None)
    
    # First search the local database (limit to 100 plants)
    db_plants = crud.search_plants(query, limit=100)
    
    # Format database plants for display
    formatted_plants = []
    for plant in db_plants:
        # Get care details if they exist
        care_details = PlantCareDetails.query.filter_by(plant_id=plant.plant_id).first()
        
        formatted_plants.append({
            'in_database': True,
            'plant_id': plant.plant_id,
            'scientific_name': plant.scientific_name,
            'common_name': plant.common_name,
            'image_url': plant.image_url,
            'care_details': {
                'sunlight_requirements': care_details.sunlight_requirements if care_details else None,
                'watering_frequency': care_details.watering_frequency if care_details else None,
                'difficulty_level': care_details.difficulty_level if care_details else None
            } if care_details else None
        })
    
    # If we have fewer than 50 results from the database, supplement with Trefle API
    if len(formatted_plants) < 50:
        try:
            # Import Trefle API search function
            from api.quantitative_plant import search_plants as search_trefle_plants
            
            # Search Trefle API
            logger.info(f"Searching Trefle API for: {query}")
            trefle_results = search_trefle_plants(query)
            
            if trefle_results and 'data' in trefle_results:
                # Process the first 10 results from Trefle
                for plant_data in trefle_results['data'][:10]:
                    # Check if this plant is already in our formatted results (avoid duplicates)
                    scientific_name = plant_data.get('scientific_name')
                    if scientific_name and not any(p['scientific_name'] == scientific_name for p in formatted_plants):
                        # Extract image URL if available
                        image_url = None
                        if 'image_url' in plant_data and plant_data['image_url']:
                            image_url = plant_data['image_url']
                        
                        # Add to formatted plants
                        formatted_plants.append({
                            'in_database': False,
                            'plant_id': plant_data.get('id'),
                            'scientific_name': scientific_name,
                            'common_name': plant_data.get('common_name', 'Unknown'),
                            'image_url': image_url,
                            'care_details': None,  # We'll fetch this only when importing to save API calls
                            'api_source': 'trefle'
                        })
            
        except Exception as e:
            logger.error(f"Error searching Trefle API: {str(e)}")
            # If Trefle API fails, we still have the database results
    
    return render_template('search_plants.html', plants=formatted_plants, query=query)

@app.route('/import-plant', methods=['POST'])
def import_plant():
    """Import a plant from Trefle API or database."""
    if 'user_id' not in session:
        flash('Please log in to import plants.')
        return redirect('/login')
    
    scientific_name = request.form.get('scientific_name')
    api_source = request.form.get('api_source', '')
    external_id = request.form.get('external_id')
    
    if not scientific_name:
        flash('Missing required information to import plant.')
        return redirect('/search-plants')
    
    try:
        # First check if plant already exists in database
        existing_plant = Plant.query.filter_by(scientific_name=scientific_name).first()
        
        if existing_plant:
            flash(f'{existing_plant.common_name or existing_plant.scientific_name} is already in the database!')
            return redirect(f'/plant/{existing_plant.plant_id}')
        
        # Import the plant based on the API source
        if api_source == 'trefle' and external_id:
            # Import from Trefle API
            from api.quantitative_plant import get_plant_details, get_growth_data, map_growth_data_to_model
            
            # Get plant details from Trefle
            logger.info(f"Fetching plant details from Trefle API for ID: {external_id}")
            plant_details = get_plant_details(external_id)
            
            if not plant_details or 'data' not in plant_details:
                flash('Error importing plant: Could not retrieve plant details.')
                return redirect('/search-plants')
            
            # Extract plant data
            plant_data = plant_details['data']
            
            # Create plant record
            new_plant = Plant(
                scientific_name=plant_data.get('scientific_name', scientific_name),
                common_name=plant_data.get('common_name', 'Unknown'),
                description=plant_data.get('family_common_name', '') or f"A plant in the {plant_data.get('family', 'plant')} family.",
                indoor=True,  # Default to indoor for now
                data_sources=['trefle']
            )
            
            # Add image URL if available
            if 'image_url' in plant_data and plant_data['image_url']:
                new_plant.image_url = plant_data['image_url']
            
            db.session.add(new_plant)
            db.session.flush()  # Get ID without committing
            
            # Try to get care details
            try:
                growth_data = get_growth_data(external_id)
                if growth_data and 'error' not in growth_data:
                    care_model = map_growth_data_to_model(growth_data)
                    
                    # Create care details
                    care_details = PlantCareDetails(
                        plant_id=new_plant.plant_id,
                        watering_frequency='Weekly',  # Default
                        sunlight_requirements=care_model.get('sunlight_requirements', []),
                        soil_preferences=care_model.get('soil_preferences', 'Well-draining potting mix'),
                        temperature_range=care_model.get('temperature_range'),
                        pruning_frequency='As needed',
                        propagation_methods=['Division', 'Cuttings'],
                        difficulty_level=care_model.get('difficulty_level', 'Moderate')
                    )
                    db.session.add(care_details)
            except Exception as e:
                logger.error(f"Error importing care details: {str(e)}")
                # Continue with import even if care details fail
            
            db.session.commit()
            flash(f'Successfully imported {new_plant.common_name or new_plant.scientific_name}!')
            return redirect(f'/plant/{new_plant.plant_id}')
            
        else:
            # Fall back to the existing method using data_merger
            from data_merger import find_or_create_plant
            plant = find_or_create_plant(scientific_name=scientific_name)
            
            if plant:
                flash(f'Successfully imported {plant.common_name or plant.scientific_name}!')
                return redirect(f'/plant/{plant.plant_id}')
            else:
                flash('Error importing plant.')
                return redirect('/search-plants')
                
    except Exception as e:
        logger.error(f"Error in plant import: {str(e)}")
        db.session.rollback()
        flash(f'Error importing plant: {str(e)}')
        return redirect('/search-plants')

@app.route('/search-plants-template')
def search_plants_template():
    """Display the search plants template."""
    return render_template('search_plants.html', plants=None, query=None)

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return render_template('500.html'), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5001)
