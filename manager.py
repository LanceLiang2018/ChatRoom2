from flask import *
from database import DataBase
import json

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
    return 'Success'


if __name__ == '__main__':
    app.run("0.0.0.0", port=8080, debug=True)
