from flask import *
from database import DataBase
import json
import os

app = Flask(__name__)

db = DataBase()


@app.route('/', methods=["GET"])
def index():
    return "This is a server for Chat Room 2."


@app.route('/get_message', methods=["POST"])
def get_message():
    form = request.form
    try:
        auth = form['auth']
        gid = int(form['gid'])
        limit = 30
        if 'limit' in form:
            limit = int(form['limit'])
    except Exception as e:
        return "Error %s" % str(e)
    # au = db.create_auth("Lance", "")
    data = db.get_message(auth, gid, limit=limit)
    return json.dumps(data)


@app.route('/login', methods=["POST"])
def login():
    form = request.form
    try:
        username, password = form['username'], form['password']
    except Exception as e:
        return "Error %s" % str(e)
    return db.create_auth(username, password)


@app.route('/send_message', methods=["POST"])
def send_message():
    form = request.form
    try:
        auth, gid, text = form['auth'], int(form['gid']), form['text']
        message_type = 'text'
        if 'message_type' in form:
            message_type = form['message_type']
    except Exception as e:
        return "Error %s" % str(e)
    return db.send_message(auth, gid, text, message_type)


@app.route('/signup', methods=["POST"])
def signup():
    form = request.form
    try:
        username, password, name, email = form['username'], form['password'], form['name'], form['email']
    except Exception as e:
        return "Error %s" % str(e)
    return str(db.create_user(username, password, name, email))


@app.route('/beat', methods=["POST"])
def beat():
    form = request.form
    try:
        auth = form['auth']
    except Exception as e:
        return "Error. " + str(e)
    if db.check_auth(auth) is False:
        return "Error. Auth Error."
    return 'Success'


@app.route('/create_room', methods=["PUSH"])
def create_room():
    form = request.form
    try:
        auth = form['auth']
        name = 'New group'
        if 'name' in form:
            name = form['name']
    except Exception as e:
        return "Error. " + str(e)
    if db.check_auth(auth) is False:
        return "Error. Auth Error."
    gid = db.create_room(auth, name)
    return 'Success. gid = %d' % gid


@app.route('/join_in', methods=["POST"])
def join_in():
    form = request.form
    try:
        auth = form['auth']
        gid = int(form['gid'])
    except Exception as e:
        return "Error. " + str(e)
    res = db.room_join_in(auth, gid)
    return res


if __name__ == '__main__':
    app.run("0.0.0.0", port=os.environ.get('PORT', '5000'), debug=True)
