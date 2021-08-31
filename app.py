from flask import Flask, render_template, redirect, session
from flask_debugtoolbar import DebugToolbarExtension
import requests
from werkzeug.exceptions import Unauthorized

from models import connect_db, db

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///capstone-i"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = "shhhhh"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

toolbar = DebugToolbarExtension(app)

connect_db(app)

db.create_all()


@app.route('/')
def home():
    return render_template('home.html')
