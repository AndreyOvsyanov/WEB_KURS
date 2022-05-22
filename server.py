from flask import Flask, render_template, request, redirect, flash
from forms import *
from flask_login import LoginManager, logout_user, current_user, login_user
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from plugins import Status

app = Flask(__name__)

app.config['SECRET_KEY'] = 'you-will-never-guess'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

role = ["Пользователь", "Админинстратор"]

featured_announce = db.Table('featured_announce',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('announce_id', db.Integer, db.ForeignKey('announce.id'), nullable=False)
)

reviews_announce = db.Table('reviews_announce',
    db.Column('announce_id', db.Integer, db.ForeignKey('announce.id')),
    db.Column('reviews_id', db.Integer, db.ForeignKey('reviews.id'), nullable=False)
)

class Reviews(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    text = db.Column(db.String)
    date = db.Column(db.Date)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"<review {self.id}>"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(120), index=True)
    email = db.Column(db.String(120), index=True, unique=True)
    login = db.Column(db.String(120), index=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default=role[0])
    photo = db.Column(db.String, default=None)
    announce = db.relationship('Announce', backref='User', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<user {self.id}>"

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), index=True)
    announce = db.relationship('Announce', backref='Category', lazy=True)

    def get_all_name(self):
        return [element.name for element in Category.query.all()]

    def __repr__(self):
        return f"<category {self.id}>"

class Announce(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    description = db.Column(db.String)
    contact_data = db.Column(db.String(120))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    status = db.Column(db.String(20), default=Status.UNDER_CONSIDERATION)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_on = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    data_success = db.Column(db.DateTime, default=None)

    user = db.relationship('User', secondary=featured_announce, backref=db.backref('Announce', lazy='dynamic'))

    reviews = db.relationship('Reviews', secondary=reviews_announce, backref=db.backref('Announce', lazy='dynamic'))

    def __repr__(self):
        return f"<annonce {self.id}>"

login = LoginManager(app)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/admin')
def admin_panel():
    return render_template('panel.html')


@app.route('/on_deleted/<int:id>')
def on_deleted(id):

    announce = Announce.query.filter_by(id=id).first()
    if announce.status == Status.ON_DELETED:
        db.session.delete(announce)
    else:
        announce.status = Status.ON_DELETED

    db.session.commit()

    return redirect('/index')


@app.route('/deleted/<int:id>', methods=['POST', 'GET'])
def delete(id):

    announce = Announce.query.filter_by(id=id).first()
    db.session.delete(announce)
    db.session.commit()

    return redirect('/deleted')


@app.route('/deleted', methods=['POST', 'GET'])
def deleted():
    return render_template(
        'deleted.html',
        deleted=Announce.query.filter_by(status=Status.ON_DELETED)
    )


@app.route('/accepted/<int:id>')
def accept(id):

    announce = Announce.query.filter_by(id=id).first()
    announce.status = Status.CURRENT
    announce.data_success = datetime.datetime.utcnow()
    db.session.commit()

    return redirect('/accepted')


@app.route('/accepted')
def accepted():
    return render_template(
        'accepted.html',
        on_acceptance=Announce.query.filter_by(status=Status.UNDER_CONSIDERATION)
    )


@app.route('/profile')
def profile():
    return render_template('profile.html', data=User.query.filter_by(id=current_user.id).first())


@app.route('/card<int:id>')
def card(id):
    data = Announce.query.filter_by(id=id).first()
    return render_template('card.html', data=data)


@app.route('/logout')
def logout():
    logout_user()
    return redirect('index')



@app.route('/signup')
def signup():
    redirect('/index')


@app.route('/')
@app.route('/index')
def index():
    record = Announce.query.filter_by(status=Status.CURRENT).all()
    return render_template('index.html', title="Главная страницы", record=record)


@app.route('/signin')
def signin():
    print(current_user)
    return render_template('signin.html', user=current_user)


@app.route('/announce', methods=['POST', 'GET'])
def announce():
    form = AnnounceForm()
    form.category.choices = Category().get_all_name()
    if request.method == 'POST':
        announce = Announce()
        announce.name = form.name.data
        announce.description = form.description.data
        announce.contact_data = form.contact_data.data
        announce.category_id = Category.query.filter_by(name=form.category.data).first().id
        announce.created_on = datetime.datetime.utcnow()
        announce.user_id = current_user.id

        print(announce.contact_data)
        print(form.contact_data.data)

        db.session.add(announce)
        db.session.commit()

        return redirect('/profile')

    return render_template('announce.html', form=form)


@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        user = User.query.filter_by(login=form.login.data).first()
        if user is None or not user.check_password(form.password.data):
            message = 'Invalid username or password'
            flash(message)
            return render_template('login.html', message=message, title='Sign In', form=form)

        login_user(user, remember=form.remember_me.data)
        return redirect('/index')

    return render_template('login.html', title='Sign In', form=form)


@app.route('/registry', methods=['POST', 'GET'])
def registry():
    form = RegistryForm()
    message = ""
    user: User
    if request.method == 'POST':
        print("test")
        user = User()
        username = [form.firstname.data, form.surname.data, form.lastname.data]
        user.username = " ".join(username)
        user.email = form.email.data
        user.login = form.login.data

        p = form.password.data
        pr = form.password_repeat.data
        if p == pr:
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            print(user.username, user.email, user.login, user.password_hash)

            flash('Login requested for user {}, '
                  'remember_me = {}'
                  .format(username, form.remember_me.data))

            return redirect('/login')

        else:
            message = "Неверно введённые данные"

    return render_template('registry.html', title='Registration', message=message, form=form)


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == "__main__":
    app.run(debug=True)