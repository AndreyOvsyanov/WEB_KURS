from flask import Flask, render_template, request, redirect, flash, url_for
from forms import *
from flask_login import LoginManager, logout_user, current_user, login_user
import datetime
import os
import shutil
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from plugins import *

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

mark_announce = db.Table('marks_announce',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('announce_id', db.Integer, db.ForeignKey('announce.id'), nullable=False),
    db.Column('mark', db.Integer, nullable=False)
)


def index_filter(name_category=None):
    record = Announce.query.filter_by(status=Status.CURRENT).all()
    if name_category:
        id = Category.query.filter_by(name=name_category).first().id
        record = Announce.query.filter(Announce.category_id==id).all()

    print(record)

    fltr = Category().get_all_name()
    pathes = Announce().get_photo_announce(['announce' + str(ann.id) for ann in record])

    data = {}
    for rec, value in zip(record, pathes.values()):
        data[rec] = value

    return render_template('index.html', title="Главная страницы", record=data, filters=fltr)


def profile_filter(id=None):
    id = current_user.id if not id else id
    user = User.query.filter_by(id=id).first()
    profile = user.get_photo_user(['user' + str(user.id)])

    sql = """
            SELECT AVG(m_a.mark) FROM marks_announce m_a
            INNER JOIN announce a on a.id = m_a.announce_id
            WHERE a.user_id = {}
        """.format(id)

    mark = db.session.execute(sql).fetchone()[0]
    mark = get_rating(mark) if mark else [0.0, 0, 0, 5]

    for _, value in profile.items():
        profile_path = value

    return render_template('profile.html', profile={user: profile_path}, mark=mark)


class Reviews(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    text = db.Column(db.String)
    date = db.Column(db.DateTime)
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

    announce_marked = db.relationship('Announce', secondary=mark_announce, backref=db.backref('mark_announce', lazy='dynamic'))

    announces = db.relationship('Announce', secondary=featured_announce, backref=db.backref('announces', lazy='dynamic'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_photo_user(self, ids=os.listdir(MAIN_PATH + '/static/img/users/')):
        list_dirs = []
        local_path = '/static/img/users/'
        path = MAIN_PATH + local_path
        for element in ids:
            list_dirs.append(os.listdir(path + element))
            for idx in range(len(list_dirs[-1])):
                list_dirs[-1][idx] =  local_path + element + '/' + list_dirs[-1][idx]

        rec = {}
        for a, b in zip(list_dirs, User.query.all()):
            rec[b] = a

        return rec

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

    users = db.relationship('User', secondary=featured_announce, backref=db.backref('users', lazy='dynamic'))

    reviews = db.relationship('Reviews', secondary=reviews_announce, backref=db.backref('Announce', lazy='dynamic'))

    def __repr__(self):
        return f"<annonce {self.id}>"


    def get_photo_announce(self, ids=os.listdir(MAIN_PATH + '/static/img/announces/')):
        list_dirs = []
        local_path = '/static/img/announces/'
        path = MAIN_PATH + local_path
        for element in ids:
            list_dirs.append(os.listdir(path + element))
            for idx in range(len(list_dirs[-1])):
                list_dirs[-1][idx] =  local_path + element + '/' + list_dirs[-1][idx]

        rec = {}
        for a, b in zip(list_dirs, Announce.query.all()):
            rec[b] = a

        return rec


login = LoginManager(app)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/admin')
def admin_panel():
    return render_template('panel.html')

@app.route('/complete/<int:id>')
def complete(id):
    announce = Announce.query.filter_by(id=id).first()
    announce.status = Status.ACCEPTED
    db.session.commit()
    return redirect('/on_accepted')


@app.route('/deystvo/<int:id>')
def deystvo(id):
    announce = Announce.query.filter_by(id=id).first()
    announce.status = Status.CURRENT
    db.session.commit()
    return redirect('/on_accepted')


@app.route('/on_accepted')
def acc():
    rec = Announce.query.filter_by(status=Status.ON_ACCEPTED).all()
    pathes = Announce().get_photo_announce(['announce' + str(ann.id) for ann in rec])

    data = {}
    for ann_acc, path in zip(rec, pathes.values()):
        data[ann_acc] = path

    return render_template(
        'accepting.html',
        rec=data
    )


@app.route('/on_accepted/<int:id>', methods=['POST', 'GET'])
def on_accept(id):
    announce = Announce.query.filter_by(id=id).first()

    if request.method == 'POST':
        announce.status = Status.ON_ACCEPTED
        db.session.commit()

        print("test")

        return redirect('/index')

    rec = Announce().get_photo_announce(['announce' + str(id)])

    for path in rec.values():

        return render_template('on_accepted.html', data=announce, path=path)


@app.route('/on_deleted/<int:id>')
def on_deleted(id):

    announce = Announce.query.filter_by(id=id).first()
    if announce.status == Status.ON_DELETED:
        db.session.delete(announce)
        shutil.rmtree(MAIN_PATH + '/static/img/announces/announce{}'.format(announce.id))
        queryset = db.session.query(reviews_announce).filter_by(
            announce_id=announce.id
        ).all()

        for q_s in queryset:
            review = Reviews.query.filter_by(id=q_s[0]).first()
            announce.reviews.remove(review)

    else:
        announce.status = Status.ON_DELETED

    db.session.commit()

    return redirect('/index')


@app.route('/deleted/<int:id>', methods=['POST', 'GET'])
def delete(id):
    announce = Announce.query.filter_by(id=id).first()
    db.session.delete(announce)

    queryset = db.session.query(reviews_announce).filter_by(
        announce_id=announce.id
    ).all()

    for q_s in queryset:
        review = Reviews.query.filter_by(id=q_s[1]).first()
        announce.reviews.remove(review)



    db.session.commit()

    shutil.rmtree(MAIN_PATH + '/static/img/announces/announce{}'.format(announce.id))

    return redirect('/deleted')


@app.route('/deleted', methods=['POST', 'GET'])
def deleted():
    rec = Announce.query.filter_by(status=Status.ON_DELETED).all()
    data = Announce().get_photo_announce(['announce' + str(ann.id) for ann in rec])

    return render_template(
        'deleted.html',
        deleted=data
    )


@app.route('/dismiccing')
def dismicced():
    return render_template('dismicc.html')


@app.route('/dismiccing/<int:id>')
def dismiccing(id):
    announce = Announce.query.filter_by(id=id).first()
    announce.status = Status.DISMISSED
    db.session.commit()

    return redirect('/accepted')


@app.route('/accepted/<int:id>')
def accept(id):

    announce = Announce.query.filter_by(id=id).first()
    announce.status = Status.CURRENT
    announce.data_success = datetime.datetime.utcnow()
    db.session.commit()

    return redirect('/accepted')


@app.route('/accepted')
def accepted():
    rec = Announce.query.filter_by(status=Status.UNDER_CONSIDERATION).all()
    pathes = Announce().get_photo_announce(['announce' + str(ann.id) for ann in rec])

    data = {}
    for ann_acc, path in zip(rec, pathes.values()):
        data[ann_acc] = path

    return render_template(
        'accepted.html',
        rec=data
    )


@app.route('/marked/<int:ann_id>', methods=['GET', 'POST'])
def marked(ann_id):
    announce = Announce.query.filter_by(id=ann_id).first()

    if request.method == 'POST':
        cur, mark = current_user.id, request.form['number']
        sql = "SELECT * FROM marks_announce WHERE user_id={} AND announce_id={}".format(cur, announce.id)
        select = []
        [select.append(row) for row in db.session.execute(sql)]
        if select:
            db.session.execute("""
                UPDATE marks_announce SET mark={} WHERE user_id={} AND announce_id={}""".format(mark, cur, announce.id)
            )
        else:
            db.session.execute("""INSERT INTO marks_announce VALUES({},{},{})""".format(cur, announce.id, mark))

        db.session.commit()

    rec = Announce().get_photo_announce(['announce' + str(announce.id)])

    for path in rec.values():

        rvs = announce.reviews
        return render_template('marked.html', data=announce, pathe=path , rvs=rvs)


@app.route('/profile/<int:id>')
def profile_user(id):
    return profile_filter(id)


@app.route('/profile')
def profile():
    return profile_filter()


@app.route('/card<int:id>', methods=['POST', 'GET'])
def card(id):

    form = ReviewForm()
    announce = Announce.query.filter_by(id=id).first()

    if request.method == 'POST':
        if not form.text.data == "":
            reviews = Reviews()
            reviews.text = form.text.data
            reviews.date = datetime.datetime.utcnow()
            reviews.user_id = current_user.id

            announce.reviews.append(reviews)
            db.session.add(announce)
            db.session.commit()

    rec = Announce().get_photo_announce(['announce' + str(id)])

    for path in rec.values():

        rvs = announce.reviews

        return render_template('card.html', data=announce, path=path, form=form, rvs=rvs)


@app.route('/logout')
def logout():
    logout_user()
    return redirect('index')


@app.route('/signup')
def signup():
    redirect('/index')


@app.route('/index/<string:name>')
def indexes(name):
    return index_filter(name)


@app.route('/')
@app.route('/index')
def index():
    return index_filter()


@app.route('/signin')
def signin():
    print(current_user)
    return render_template('signin.html', user=current_user)


@app.route('/announce', methods=['POST', 'GET'])
def announce():
    if not current_user.is_authenticated:
        return redirect('/login')
    else:
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

            db.session.add(announce)
            db.session.commit()

            print(announce.id, announce.name, announce.description, announce.contact_data)
            file = request.files['file']
            if not file:
                return render_template(
                    'announce.html',
                    form=form,
                    message="Обязательно выберите изображение!"
                )
            set_photo_announce(announce.id, file)

            return redirect('/profile')

        return render_template('announce.html', form=form)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if not current_user.is_authenticated:
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
    else:
        return redirect('/index')


@app.route('/registry', methods=['POST', 'GET'])
def registry():
    if not current_user.is_authenticated:
        form = RegistryForm()
        message = ""
        if request.method == 'POST':

            user = User()
            username = [form.firstname.data, form.surname.data, form.lastname.data]
            user.username = " ".join(username)
            user.email = form.email.data
            user.login = form.login.data

            if form.password.data == form.password_repeat.data:
                user.set_password(form.password.data)

                db.session.add(user)
                db.session.commit()

                file = request.files['file']
                if not file:
                    return render_template(
                        'registry.html',
                        title='Registration',
                        message="Please select to image!",
                        form=form
                    )
                set_photo_user(user.id, file)

                #flash('Login requested for user {}, '
                      #'remember_me = {}'
                      #.format(username, form.remember_me.data))

                login_user(user, remember=form.remember_me.data)

                return redirect('/index')

            else:
                message = "Неверно введённые данные"

        return render_template('registry.html', title='Registration', message=message, form=form)
    else:
        return redirect('/index')

@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == "__main__":
    app.run(debug=True, port=8080)