import os
from flask import Flask
from models import db
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
app.config['MONGO_DBNAME'] = os.getenv('MONGO_DBNAME', 'timetable')

db.init_app(app)

with app.app_context():
    print("Creating MongoDB indexes...")
    db.create_all()
    print("Done.")
