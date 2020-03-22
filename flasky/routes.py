import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request
from flasky import app, db, bcrypt
from flasky.forms import RegistrationForm, LoginForm, UpdateAccForm
from flasky.models import User
from flask_login import login_user, current_user, logout_user, login_required

posts = [
    {
        'author': 'Harry Ellerm',
        'title': 'Blog Post 1',
        'content': 'First post content',
        'date_posted': 'April 20, 2018'
    },
    {
        'author': 'Jane Doe',
        'title': 'Blog Post 2',
        'content': 'Second post content',
        'date_posted': 'April 22, 2018'
    }
]


@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', posts=posts)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    # If form validated create user then flash message
    if form.validate_on_submit():
        # noinspection PyArgumentList
        user = User(username=form.username.data, email=form.email.data,
                    password=bcrypt.generate_password_hash(form.password.data).decode('utf-8'))
        db.session.add(user)
        db.session.commit()
        flash(f'Account created! You can now login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, form.remember.data)
            page_requested = request.args.get('next')
            flash('Welcome back!', 'success')
            return redirect(page_requested) if page_requested else redirect(url_for('home'))
        else:
            flash('Log in unsuccessful, please check email & password', 'danger')

    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


# Saves new account image and if successful deletes old image
def save_acct_image_and_clean_up(new_image, old_image):
    # To avoid potential collisions
    rnd = secrets.token_hex(8)
    _, file_ext = os.path.splitext(new_image.filename)
    new_pth = os.path.join(app.root_path, 'static/images', rnd + file_ext)
    old_pth = os.path.join(app.root_path, 'static/images', old_image)

    try:
        # Resize image to save space
        output_size = (125, 125)
        i = Image.open(new_image)
        i.thumbnail(output_size)
        i.save(new_pth)
        os.remove(old_pth)
        return rnd + file_ext
    except (KeyError, IOError) as e:
        print(f'An exception occurred when saving file: {e}, rolling back changes...')
        return old_image


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccForm()
    if form.validate_on_submit():
        if form.acct_image.data:
            new_image = form.acct_image.data
            old_image = current_user.image_file
            current_user.image_file = save_acct_image_and_clean_up(new_image, old_image)
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    image = url_for('static', filename=f'images/{current_user.image_file}')
    return render_template('account.html', title='Account', image=image, form=form)

