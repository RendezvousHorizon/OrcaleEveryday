from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for,
    current_app, send_file, jsonify
)
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from .utils import recognize, image2base64

from .auth import login_required
from .db import get_db
import os

bp = Blueprint('service', __name__)


@bp.route('/oracle_recognition', methods=['GET'])
def oracle_recognition():
    image = request.files['image']
    image_name = secure_filename(image.filename)
    results = recognize(image)
    rv = []
    db = get_db()
    for name in results:
        tuple = db.execute(
            'SELECT * FROM oracle WHERE name="{}"'.format(name)
        ).fetchone()
        image_path = os.path.join(current_app.config['IMAGE_PATH'], tuple['img'])
        image_base64 = str(image2base64(image_path))
        rv.append((name, image_base64))
    return jsonify(rv)


@bp.route('/oracle_search', methods=['GET'])
def oracle_search():
    query_parameters = request.args
    name = query_parameters.get('name')

    db = get_db()
    result = db.execute(
        'SELECT * FROM oracle WHERE name="{}"'.format(name)
    ).fetchone()
    if result is None:
        abort(404, 'the oracle image of \'{}\' not found'.format(name))
    image_path = os.path.join(current_app.config['IMAGE_PATH'], result['img'])

    return send_file(image_path, mimetype='image/jpeg')


@bp.route('/wrong_question', methods=['POST'])
@login_required
def upload_wrong_question():
    query_parameters = request.args
    question_id = query_parameters.get('question_id')
    user_id = g.user['id']
    db = get_db()
    db.execute('INSERT INTO wrong_question (user_id, question_id) VALUES ({}, {})' \
               .format(user_id, question_id))
    return 'upload success'


@bp.route('/question', methods=['GET'])
@login_required
def get_question():
    db = get_db()
    num_questions = db.execute('SELECT num_questions_per_time FROM user WHERE id = {}'.format(g.user['id'])).fetchone()['num_questions']
    next_question_id = db.execute('SELECT next_question_id FROM user WHERE id = {}'.format(g.user['id'])).fetchone()['next_question_id']
    questions = db.execute('SELECT * FROM question WHERE id >= {} AND id < {}'.format(next_question_id,
                                                                                      next_question_id + num_questions)).fetchall()
    rv = []
    for q in questions:
        image_path = os.path.join(current_app.config['IMAGE_PATH'], q['img'])
        print(image_path)
        image_base64 = str(image2base64(image_path))
        tuple = {
            'id': q['id'],
            'image': image_base64,
            'a': q['a'],
            'b': q['b'],
            'c': q['c'],
            'd': q['d'],
        }
        rv.append(tuple)
    return jsonify(rv)


@bp.route('/num_questions', methods=['GET', 'POST'])
@login_required
def num_questions():
    if request.method == 'POST':
        query_parameters = request.args
        num_questions = query_parameters.get('num_questions')
        db = get_db()
        db.execute('UPDATE user SET num_questions_per_time = {} WHERE id = {}'.format(num_questions, g.user['id']))
        db.commit()
        return 'success'
    else:
        query_parameters = request.args
        db = get_db()
        num_questions = db.execute('SELECT num_questions_per_time FROM user WHERE id = {}'
                                   .format((g.user['id']))).fetchone()['num_questions_per_time']
        return str(num_questions)


@bp.route('/next_question_id', methods=['GET', 'POST'])
@login_required
def next_question_id():
    if request.method == 'POST':
        query_parameters = request.args
        next_question_id = query_parameters.get('next_question_id')
        db = get_db()
        db.execute('UPDATE user SET next_question_id = {} WHERE id = {}'.format(next_question_id, g.user['id']))
        db.commit()
        return 'success'
    else:
        db = get_db()
        next_question_id = db.execute('SELECT next_question_id FROM user WHERE id = {}'
                                      .format((g.user['id']))).fetchone()['next_question_id']
        return str(next_question_id)
