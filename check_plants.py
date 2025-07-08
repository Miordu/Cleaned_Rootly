#!/usr/bin/env python3
import psycopg2

# Connect to database
conn = psycopg2.connect('postgresql:///rootly')
cur = conn.cursor()

# Check plants with missing images
print('=== Plants with missing images ===')
cur.execute('SELECT plant_id, common_name, scientific_name, image_url, data_sources FROM plants WHERE image_url IS NULL OR image_url = \'\' ORDER BY common_name')
missing_images = cur.fetchall()
for plant in missing_images:
    print(f'ID: {plant[0]}, Common: {plant[1]}, Scientific: {plant[2]}, Image: {plant[3]}, Sources: {plant[4]}')

print(f'\nTotal plants with missing images: {len(missing_images)}')

# Check total plants
cur.execute('SELECT COUNT(*) FROM plants')
total = cur.fetchone()[0]
print(f'Total plants in database: {total}')

# Check for plants containing 'lemon'
print('\n=== Plants containing "lemon" ===')
cur.execute('SELECT plant_id, common_name, scientific_name, image_url FROM plants WHERE common_name ILIKE \'%lemon%\' OR scientific_name ILIKE \'%lemon%\'')
lemon_plants = cur.fetchall()
for plant in lemon_plants:
    print(f'ID: {plant[0]}, Common: {plant[1]}, Scientific: {plant[2]}, Image: {plant[3]}')

print(f'\nFound {len(lemon_plants)} plants containing "lemon"')

# Show sample of all plants for search reference
print('\n=== Sample of all plants (first 30) ===')
cur.execute('SELECT plant_id, common_name, scientific_name FROM plants ORDER BY common_name LIMIT 30')
sample_plants = cur.fetchall()
for plant in sample_plants:
    print(f'ID: {plant[0]}, Common: {plant[1]}, Scientific: {plant[2]}')

# Check for specific plants mentioned by user
print('\n=== Checking specific plants (Rosa, Swiss Cheese Plant) ===')
cur.execute('SELECT plant_id, common_name, scientific_name, image_url FROM plants WHERE common_name ILIKE \'%rosa%\' OR common_name ILIKE \'%swiss%\' OR common_name ILIKE \'%cheese%\' OR scientific_name ILIKE \'%rosa%\'')
specific_plants = cur.fetchall()
for plant in specific_plants:
    print(f'ID: {plant[0]}, Common: {plant[1]}, Scientific: {plant[2]}, Image: {plant[3]}')

cur.close()
conn.close()
