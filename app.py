from flask import Flask, render_template, redirect, session, g, request, jsonify, json, flash
from flask_debugtoolbar import DebugToolbarExtension
import requests
from werkzeug.exceptions import Unauthorized
from sqlalchemy.exc import IntegrityError
import os
from forms import UserAddForm, LoginForm
from models import connect_db, db, User, Location

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///capstone-i'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "weatherly53102")
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
API_key = '384549281a1b886956dff00758e198a3'

toolbar = DebugToolbarExtension(app)

connect_db(app)

db.drop_all()
db.create_all()


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""
    do_logout()
    flash('Logout success!')
    return redirect('/')


@app.route('/')
def home():
    top_locs = Location.query.order_by(
        Location.times_searched.desc()).limit(10).all()
    return render_template('home.html', top_locs=top_locs)


@app.route('/location')
def get_weather():
    zip_code = request.args['search']

    response = requests.get(
        f'http://api.openweathermap.org/data/2.5/weather?zip={zip_code},us&appid=384549281a1b886956dff00758e198a3&units=imperial')
    weather_info = response.json()

    location = weather_info['name']
    exists = Location.query.filter_by(zip_code=zip_code).first()
    if not exists:
        new_loc = Location(name=location, zip_code=zip_code)
        db.session.add(new_loc)
        db.session.commit()
        return redirect(f'/location/{new_loc.zip_code}')
    else:
        ex_loc = Location.query.filter_by(name=location).first()
        return redirect(f'/location/{ex_loc.zip_code}')


@app.route('/location/<int:zip_code>')
def display_loc(zip_code):
    response = requests.get(
        f'http://api.openweathermap.org/data/2.5/weather?zip={zip_code},us&appid=384549281a1b886956dff00758e198a3&units=imperial')
    res = response.json()
    print('*******************************')
    print(res)
    print('*******************************')
    temp = res['main']['temp']
    weath = res['weather'][0]['description']

    existing_loc = Location.query.filter_by(zip_code=zip_code).first()
    existing_loc.times_searched = existing_loc.times_searched + 1
    return render_template('location.html', existing_loc=existing_loc, temp=temp, weath=weath)
