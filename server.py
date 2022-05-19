from flask import Flask, render_template, request, redirect, flash
from forms import LoginForm, RegistryForm
from flask_login import LoginManager, logout_user, current_user, login_user
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

app.config['SECRET_KEY'] = 'you-will-never-guess'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///my_database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

role = ["Пользователь", "Админинстратор"]

bid_user = db.Table('bid_user',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('bid_id', db.Integer, db.ForeignKey('bid.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(120), index=True)
    email = db.Column(db.String(120), index=True, unique=True)
    login = db.Column(db.String(120), index=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default=role[0])

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<user {self.id}>"

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), index=True)
    bid = db.relationship('Bid', backref='Category', lazy=True)

    def __repr__(self):
        return f"<categories {self.id}{self.name}>"

class Bid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), index=True)
    description = db.Column(db.String(120), index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    photo = db.Column(db.String(120), index=True)
    created_on = db.Column(db.Date, default=datetime.date.today())
    user = db.relationship('User', secondary=bid_user, backref=db.backref('bid', lazy='dynamic'))

    def __repr__(self):
        return f"<bid {self.id}>"

login = LoginManager(app)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


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
    record = Bid.query.order_by(Bid.created_on).limit(8).all()
    return render_template('index.html', title="Главная страницы", record=record)

@app.route('/signin')
def signin():
    print(current_user)
    return render_template('signin.html', user=current_user)

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
        print(current_user)
        return redirect('/signin')

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
        print(form.remember_me.data)
        if p == pr and form.remember_me.data:
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