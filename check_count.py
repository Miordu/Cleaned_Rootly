from server import app
from model import Plant

with app.app_context():
    count = Plant.query.count()
    print(f"Current plants in database: {count}")
