# Rootly Database Table Relationships

## Core Relationships

### User-Centered Relationships
- **Users → UserPlants**: One-to-many relationship where one user can have many plants in their collection
  - Connected via `user_id` in UserPlants referencing Users
- **Users → UserFavorites**: One-to-many relationship where one user can bookmark many plants
  - Connected via `user_id` in UserFavorites referencing Users
- **Users → IdentificationHistory**: One-to-many relationship tracking plant identifications initiated by a user
  - Connected via `user_id` in IdentificationHistory referencing Users
- **Users → Regions**: Many-to-one relationship connecting users to their geographic region
  - Connected via `region_id` in Users referencing Regions

### Plant-Centered Relationships
- **Plants → PlantCareDetails**: One-to-one relationship providing care information for each plant species
  - Connected via `plant_id` in PlantCareDetails referencing Plants
- **Plants → UserPlants**: One-to-many relationship where a plant species can be in many users' collections
  - Connected via `plant_id` in UserPlants referencing Plants
- **Plants → PlantHealthIssues**: One-to-many relationship where a plant species can have many common health issues
  - Connected via `plant_id` in PlantHealthIssues referencing Plants
- **Plants → UserFavorites**: One-to-many relationship where a plant can be favorited by many users
  - Connected via `plant_id` in UserFavorites referencing Plants
- **Plants → PlantRegionCare**: One-to-many relationship providing region-specific care for each plant
  - Connected via `plant_id` in PlantRegionCare referencing Plants
- **Plants → RelatedPlants**: Many-to-many relationship connecting plants to other related plants
  - Connected via `plant_id_1` and `plant_id_2` in RelatedPlants, both referencing Plants

### UserPlant-Centered Relationships
- **UserPlants → CareEvents**: One-to-many relationship tracking care activities for each plant
  - Connected via `user_plant_id` in CareEvents referencing UserPlants
- **UserPlants → Reminders**: One-to-many relationship managing care reminders for each plant
  - Connected via `user_plant_id` in Reminders referencing UserPlants
- **UserPlants → HealthAssessments**: One-to-many relationship tracking health issues for each plant
  - Connected via `user_plant_id` in HealthAssessments referencing UserPlants
- **UserPlants → IdentificationHistory**: One-to-many relationship linking identification records to specific plants
  - Connected via `user_plant_id` in IdentificationHistory referencing UserPlants (optional link)

### Region-Centered Relationships
- **Regions → Users**: One-to-many relationship where one region can have many users
  - Connected via `region_id` in Users referencing Regions
- **Regions → PlantRegionCare**: One-to-many relationship providing regional care adjustments
  - Connected via `region_id` in PlantRegionCare referencing Regions

## Visual Reference of Key Relationships

```
Users
 ├── UserPlants (user_id)
 │    ├── CareEvents (user_plant_id)
 │    ├── Reminders (user_plant_id)
 │    └── HealthAssessments (user_plant_id)
 ├── UserFavorites (user_id)
 ├── IdentificationHistory (user_id)
 └── connected to → Regions (region_id)

Plants
 ├── PlantCareDetails (plant_id)
 ├── UserPlants (plant_id)
 ├── PlantHealthIssues (plant_id)
 ├── UserFavorites (plant_id)
 ├── PlantRegionCare (plant_id)
 ├── IdentificationHistory (identified_plant_id)
 └── RelatedPlants (plant_id_1, plant_id_2)
```

## Relationship Types Explained

### One-to-One Relationships
- **Plants → PlantCareDetails**: Each plant species has exactly one set of care details

### One-to-Many Relationships
- **Users → UserPlants**: One user can have many plants
- **Plants → UserPlants**: One plant species can be in many users' collections
- **UserPlants → CareEvents**: One plant can have many care events
- **UserPlants → Reminders**: One plant can have many reminders
- **Plants → PlantHealthIssues**: One plant species can have many health issues

### Many-to-Many Relationships
- **Plants ↔ Plants** (via RelatedPlants): Plants can have relationships with multiple other plants
- **Plants ↔ Regions** (via PlantRegionCare): Plants can have different care needs in different regions

## Foreign Key Structure

The relationships are implemented through foreign keys:

1. **Primary Keys**: Each table has its own primary key (e.g., `user_id`, `plant_id`, etc.)

2. **Foreign Keys**: Tables reference other tables through foreign keys:
   - `user_id` in UserPlants references Users
   - `plant_id` in UserPlants references Plants
   - `user_plant_id` in CareEvents references UserPlants

3. **Nullable Foreign Keys**: Some relationships are optional:
   - `user_plant_id` in IdentificationHistory can be null (for plants not yet added to collection)
   - `region_id` in Users can be null (for users who haven't specified their region)

These relationships create a network of connected data that allows the application to:
- Track which plants belong to which users
- Associate care events with specific plants
- Provide care recommendations based on plant species and region
- Link identification results to users and their plants
- Show relationships between different plant species
