# Rootly Data Model Explanation

## Overview

Rootly is a comprehensive plant care management application that combines data from multiple specialized plant APIs to help users identify plants, track care schedules, diagnose health issues, and receive customized care recommendations.

Our data model is designed to:
1. Store plant information from multiple authoritative sources
2. Track users' personal plant collections
3. Manage care schedules and history
4. Provide health assessments and diagnostics
5. Offer region-specific care recommendations

## Core Tables

### Users
The Users table stores authentication information and preferences:
- **user_id**: Primary identifier for each user
- **username, email, password_hash**: Authentication credentials
- **region_id**: Links to the Regions table for location-specific recommendations
- **preferences**: Stores user preferences as JSON

### Plants
The Plants table serves as our master plant database with comprehensive information:
- **plant_id**: Primary identifier for each plant species
- **scientific_name, common_name**: Plant identification
- **plant_type, origin, description**: General information
- **Characteristic flags**: Boolean fields for poisonous_to_humans, poisonous_to_pets, invasive, rare, tropical, indoor, outdoor
- **data_sources**: Tracks which APIs provided data for each plant
- **last_updated**: Timestamp for data freshness

### PlantCareDetails
This table stores detailed care requirements for each plant species:
- **care_id, plant_id**: Primary and foreign keys
- **Watering needs**: Frequency and interval information
- **Sunlight requirements**: Including duration minimums and maximums
- **soil_preferences, temperature_range**: Environmental needs
- **fertilizing_schedule, pruning_months**: Maintenance information
- **growth_rate, propagation_methods**: Growth characteristics
- **companion_plants**: Plants that grow well together

## User Plant Management

### UserPlants
Tracks the specific plants owned by each user:
- **user_plant_id**: Primary identifier for each user's plant
- **user_id, plant_id**: Links to Users and Plants tables
- **nickname, location_in_home**: Personalization information
- **acquisition_date**: When the plant was obtained
- **image_url**: User's own photo of their plant
- **notes, status**: User-provided information and plant health status

### CareEvents
Records maintenance activities performed on each plant:
- **event_id, user_plant_id**: Primary and foreign keys
- **event_type**: Type of care (watering, fertilizing, etc.)
- **date, notes**: When and what was done

### Reminders
Manages upcoming care tasks:
- **reminder_id, user_plant_id**: Primary and foreign keys
- **reminder_type, frequency**: What needs to be done and how often
- **next_reminder_date**: When the next task is due
- **is_active**: Whether the reminder is currently enabled

## Plant Health and Identification

### HealthAssessments
Stores plant health issues diagnosed for specific plants:
- **assessment_id, user_plant_id**: Primary and foreign keys
- **assessment_date**: When the diagnosis was made
- **symptoms, diagnosis**: Health issue information
- **treatment_recommendations**: How to address the problem
- **image_url**: Photo of the unhealthy plant
- **resolved**: Whether the issue has been addressed

### IdentificationHistory
Tracks plant identification events:
- **identification_id, user_id**: Primary and foreign keys
- **user_plant_id**: Optional link to UserPlants (can be null for plants not yet added to collection)
- **image_url**: Photo used for identification
- **identified_plant_id**: Link to the identified plant in Plants table
- **confidence_score**: How confident the identification is
- **added_to_collection**: Whether the user added this plant to their collection

### PlantHealthIssues
A knowledge base of common health problems for each plant species:
- **issue_id, plant_id**: Primary and foreign keys
- **issue_name, symptoms, treatment, prevention**: Health issue information
- **severity**: How serious the issue is

## Enhanced Features

### UserFavorites
Allows users to bookmark plants they're interested in:
- **favorite_id, user_id, plant_id**: Primary and foreign keys
- **favorited_at**: When the plant was bookmarked

### Regions
Stores geographical/climate information:
- **region_id**: Primary identifier for each region
- **name, climate_zone**: Location information
- **avg_temperature, humidity_level**: Climate characteristics

### PlantRegionCare
Provides region-specific care adjustments:
- **plant_region_id, plant_id, region_id**: Primary and foreign keys
- **watering_frequency, sunlight_adjustments**: Regional care modifications
- **seasonal_notes**: Season-specific information for the region

### RelatedPlants
Establishes relationships between different plant species:
- **related_id, plant_id_1, plant_id_2**: Primary and foreign keys
- **relationship_type**: How the plants are related (same family, companions, etc.)
- **notes**: Additional information about the relationship

## API Integration

Our data model is designed to store information retrieved from multiple plant APIs:

1. **Perenual API**: Populates the Plants and PlantCareDetails tables with comprehensive plant information
2. **Plant.id API**: Powers our identification functionality, storing results in IdentificationHistory
3. **Plant.health API**: Provides diagnostics for HealthAssessments and populates PlantHealthIssues
4. **Quantitative Plant API**: Supplies technical growth data to enhance PlantCareDetails

The application integrates these APIs to create a unified plant database while maintaining data provenance through the data_sources field, allowing us to track which information came from which source.

## Conclusion

This comprehensive data model provides a solid foundation for Rootly's functionality while allowing for future expansion. It supports all our planned features from basic plant identification to advanced region-specific care recommendations and plant relationship management.
