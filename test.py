import os
import math
from flask import url_for
from plugins import MAIN_PATH, get_rating
from server import User, Announce, Reviews, db, reviews_announce, mark_announce, Category


print(Category.query.filter_by(name="Покупка").first().id)


#print(os.listdir(MAIN_PATH + '/static/img/announces/'))
#from server import db
#db.create_all()