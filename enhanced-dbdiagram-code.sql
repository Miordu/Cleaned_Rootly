// Rootly - Plant Care Tracker Data Model

Table Users {
  user_id integer [primary key, increment]
  username varchar [not null]
  email varchar [unique, not null]
  password_hash varchar [not null]
  created_at timestamp [default: `now()`]
}

Table Plants {
  plant_id integer [primary key, increment]
  scientific_name varchar [not null, unique]
  common_name varchar
  plant_type varchar
  image_url varchar
  origin varchar
  description text
  poisonous_to_humans boolean [default: false]
  poisonous_to_pets boolean [default: false]
  invasive boolean [default: false]
  rare boolean [default: false]
  tropical boolean [default: false]
  indoor boolean [default: false]
  outdoor boolean [default: false]
  data_sources varchar[]
  last_updated timestamp [default: `now()`]
}

Table PlantCareDetails {
  care_id integer [primary key, increment]
  plant_id integer [ref: > Plants.plant_id]
  watering_frequency varchar
  watering_interval_days integer
  sunlight_requirements varchar[]
  sunlight_duration_min integer
  sunlight_duration_max integer
  sunlight_duration_unit varchar [default: 'hours']
  soil_preferences text
  temperature_range varchar
  fertilizing_schedule text
  pruning_months varchar[]
  difficulty_level varchar
}

Table UserPlants {
  user_plant_id integer [primary key, increment]
  user_id integer [ref: > Users.user_id]
  plant_id integer [ref: > Plants.plant_id]
  nickname varchar
  location_in_home varchar
  acquisition_date date
  image_url varchar
  notes text
  status varchar
}

Table CareEvents {
  event_id integer [primary key, increment]
  user_plant_id integer [ref: > UserPlants.user_plant_id]
  event_type varchar
  date timestamp
  notes text
}

Table Reminders {
  reminder_id integer [primary key, increment]
  user_plant_id integer [ref: > UserPlants.user_plant_id]
  reminder_type varchar
  frequency varchar
  next_reminder_date date
  is_active boolean [default: true]
}

Table HealthAssessments {
  assessment_id integer [primary key, increment]
  user_plant_id integer [ref: > UserPlants.user_plant_id]
  assessment_date timestamp [default: `now()`]
  symptoms varchar[]
  diagnosis varchar
  treatment_recommendations text
  image_url varchar
  resolved boolean [default: false]
}

Table IdentificationHistory {
  identification_id integer [primary key, increment]
  user_id integer [ref: > Users.user_id]
  image_url varchar
  identified_plant_id integer [ref: > Plants.plant_id]
  confidence_score float
  identified_at timestamp [default: `now()`]
  added_to_collection boolean [default: false]
}
