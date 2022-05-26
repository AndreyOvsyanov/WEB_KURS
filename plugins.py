"""
    Здесь будут содержаться необходимые плагины для поддержки бизнес-логики
"""

import os
import math
from werkzeug.utils import secure_filename


MAIN_PATH = 'C:/Users/Acer/Desktop/Учёба/WEB_LR_commit_fifth/WEB_LR'


class Status:
    """
        Статус заявки, который может быть
    """
    ACCEPTED = "Завершён"
    ON_ACCEPTED = "На завершении"
    DISMISSED = "Отклонён"
    DELETED = "Удалён"
    ON_DELETED = "На удалении"
    CURRENT = "Действующий"
    UNDER_CONSIDERATION = "На рассмотрении"


def set_photo_announce(id, file):
    path = MAIN_PATH + '/static/img/announces/announce{}/'.format(id)
    os.mkdir(path)

    filename = secure_filename(file.filename)
    file.save(path + filename)


def set_photo_user(id, file):
    path = MAIN_PATH + '/static/img/users/user{}/'.format(id)
    os.mkdir(path)

    filename = secure_filename(file.filename)
    file.save(path + filename)


def get_rating(mark) -> list:
    m_t = math.trunc(mark)
    c_g, c_h = m_t, 1 if mark - m_t >= 0.5 else 0
    c_e = 5 - m_t - 1 if mark - m_t >= 0.5 else 5 - m_t

    return [mark, c_g, c_h, c_e]