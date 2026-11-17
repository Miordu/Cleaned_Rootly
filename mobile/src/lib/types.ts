export type User = { user_id: number; username: string; email: string; region: string | null };

export type Care = {
  watering_frequency: string | null;
  sunlight_requirements: string[];
  soil_preferences: string | null;
  temperature_range: string | null;
  difficulty_level: string | null;
  growth_rate: string | null;
};

export type Plant = {
  plant_id: number;
  scientific_name: string;
  common_name: string;
  image_url: string | null;
  description: string | null;
  indoor: boolean;
  outdoor: boolean;
  poisonous_to_humans: boolean;
  poisonous_to_pets: boolean;
  care?: Care | null;
};

export type TreflePlant = {
  trefle_id: number;
  scientific_name: string;
  common_name: string;
  image_url: string | null;
};

export type Reminder = {
  reminder_id: number;
  user_plant_id: number;
  reminder_type: string;
  frequency: string;
  next_reminder_date: string; // YYYY-MM-DD
  plant_name?: string;
};

export type CareEvent = { event_id: number; event_type: string; date: string; notes: string | null };

export type HealthAssessment = {
  assessment_id: number;
  assessment_date: string;
  symptoms: string[];
  diagnosis: string | null;
  treatment_recommendations: string | null;
  image_url: string | null;
  resolved: boolean;
};

export type MyPlant = {
  user_plant_id: number;
  name: string;
  nickname: string | null;
  location: string | null;
  status: string | null;
  notes: string | null;
  acquisition_date: string | null;
  image_url: string | null;
  has_own_photo: boolean;
  plant: Plant;
  reminders?: Reminder[];
  care_events?: CareEvent[];
  health_assessments?: HealthAssessment[];
};

export type Options = {
  care_types: string[];
  reminder_frequencies: string[];
  plant_statuses: string[];
  regions: { region_id: number; name: string }[];
  min_password_length: number;
};

export type Dashboard = {
  user: User;
  plant_count: number;
  recent_care_count: number;
  upcoming_reminders: Reminder[];
  today: string;
};
