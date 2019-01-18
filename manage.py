from flask import *
from database import DataBase
import base64
import time
# import json
import os
import hashlib
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client

secret_id = 'AKIDcq7HVrj0nlAWUYvPoslyMKKI2GNJ478z'
secret_key = '70xZrtGAwmf6WdXGhcch3gRt7hV4SJGx'
region = 'ap-chengdu'
config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
# 2. 获取客户端对象
client = CosS3Client(config)

bucket = 'chatroom-1254016670'

app = Flask(__name__)

db = DataBase()


def delete_dir(_dir):
    for name in os.listdir(_dir):
        file = _dir + "/" + name
        if not os.path.isfile(file) and os.path.isdir(file):
            delete_dir(file)  # It's another directory - recurse in to it...
        else:
            os.remove(file)  # It's a file - remove it...
    os.rmdir(_dir)


@app.route('/', methods=["GET", "POST"])
def index():
    """
        res = '###### manage.py:\n'
        with open('manage.py', 'r', encoding='utf8') as f:
            res = res + f.read()
        res = res + "###### database.py\n"
        with open('database.py', 'r', encoding='utf8') as f:
            res = res + f.read()
        res = res + '\n\n##### End of files.\n'
        return res
    """
    return \
        "<title>Chat 2 Server</title>" \
        "<h1>It is a server for Chat 2! <br>@LanceLiang2018</h1><br>" \
        "<a href=\"http://github.com/LanceLiang2018/ChatRoom2/\">About (Server)</a><br>" \
        "<a href=\"http://github.com/LanceLiang2018/Chat2-Android/\">About (Client)</a>"


@app.route('/get_head', methods=["POST"])
def get_head():
    form = request.form
    try:
        auth = form['auth']
    except Exception as e:
        return db.make_result(1, message=str(e))
    if db.check_auth(auth) is False:
        return db.make_result(2)
    username = db.auth2username(auth)
    head = db.get_head(auth)
    return db.make_result(0, username=username, head=head)


@app.route('/login', methods=["POST"])
def login():
    form = request.form
    try:
        username, password = form['username'], form['password']
    except Exception as e:
        return db.make_result(1, message=str(e))
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
        return db.make_result(1, message=str(e))
    return db.send_message(auth, gid, text, message_type)


@app.route('/signup', methods=["POST"])
def signup():
    form = request.form
    try:
        username, password, name, email = form['username'], form['password'], form['name'], form['email']
    except Exception as e:
        return db.make_result(1, message=str(e))
    return str(db.create_user(username, password, name, email))


@app.route('/beat', methods=["POST"])
def beat():
    form = request.form
    try:
        auth = form['auth']
    except Exception as e:
        return db.make_result(1, message=str(e))
    if db.check_auth(auth) is False:
        return db.make_result(2)
    return db.make_result(0)


@app.route('/create_room', methods=["POST"])
def create_room():
    form = request.form
    try:
        auth = form['auth']
        name = 'New group'
        if 'name' in form:
            name = form['name']
    except Exception as e:
        return db.make_result(1, message=str(e))
    if db.check_auth(auth) is False:
        return db.make_result(2)
    gid = db.create_room(auth, name)
    return db.room_get_info(auth, gid)


@app.route('/set_room_info', methods=["POST"])
def set_room_info():
    form = request.form
    try:
        auth = form['auth']
        gid = int(form['gid'])
        name = 'New group'
        if 'name' in form:
            name = form['name']
    except Exception as e:
        return db.make_result(1, message=str(e))
    res = db.room_set_info(auth, gid, name)
    return res


@app.route('/join_in', methods=["POST"])
def join_in():
    form = request.form
    try:
        auth = form['auth']
        gid = int(form['gid'])
    except Exception as e:
        return db.make_result(1, message=str(e))
    res = db.room_join_in(auth, gid)
    return res


@app.route('/get_room_info', methods=["POST"])
def get_room_info():
    form = request.form
    try:
        auth = form['auth']
        gid = int(form['gid'])
    except Exception as e:
        return db.make_result(1, message=str(e))
    res = db.room_get_info(auth, gid)
    return res


@app.route('/get_room_all', methods=["POST"])
def get_room_all():
    form = request.form
    try:
        auth = form['auth']
    except Exception as e:
        return db.make_result(1, message=str(e))
    res = db.room_get_all(auth)
    return res


@app.route('/get_room_members', methods=["POST"])
def get_room_numbers():
    form = request.form
    try:
        auth = form['auth']
        gid = int(form['gid'])
    except Exception as e:
        return db.make_result(1, message=str(e))
    res = db.room_get_members(auth, gid)
    return res


@app.route('/clear_all', methods=["POST", "GET"])
def clear_all():
    try:
        db.db_init()
    except Exception as e:
        return db.make_result(1, message=str(e))
    return db.make_result(0)


@app.route('/upload', methods=["POST"])
def upload():
    try:
        auth = request.form['auth']
        filename = request.form['filename']
        if db.check_auth(auth) is False:
            return db.make_result(2)
        data = request.form['data']
        data = base64.b64decode(data)
        md5 = hashlib.md5(data).hexdigest()
        filename_md5 = "%s" % md5
        response = client.put_object(
            Bucket=bucket,
            Body=data,
            Key=filename_md5,
            StorageClass='STANDARD',
            EnableMD5=False
            # 我自己算吧......
        )
        print(response)
        url = 'https://%s.cos.ap-chengdu.myqcloud.com/%s' % (bucket, filename_md5)
        result = {
            'filename': filename, 'etag': response['ETag'][1:-1],
            "url": url
        }
        print(result)
    except Exception as e:
        print(e)
        return db.make_result(1, message=str(e))
    db.file_upload(auth, filename, url)
    # return db.make_result(0, upload_result=result)
    res = db.make_result(0, upload_result=result)
    print(res)
    return res


@app.route('/file_get', methods=["POST"])
def file_get():
    form = request.form
    try:
        auth = form['auth']
        limit = 30
        offset = 0
        if 'limit' in form:
            limit = int(form['limit'])
        if 'offset' in form:
            offset = int(form['offset'])
    except Exception as e:
        return db.make_result(1, message=str(e))
    res = db.file_get(auth, limit, offset)
    return res


@app.route('/get_message', methods=["POST", "GET"])
def get_message():
    form = request.form
    try:
        auth = form['auth']
        gid = int(form['gid'])
        limit = 30
        offset = 0
        # print(auth, gid, limit)
        if 'limit' in form:
            limit = int(form['limit'])
        if 'offset' in form:
            offset = int(form['offset'])
    except Exception as e:
        return db.make_result(1, message=str(e))
    data = db.get_message(auth, gid, limit=limit, offset=offset)
    print('get_message():', data)
    return data


@app.route('/get_new_message', methods=["POST", "GET"])
def get_new_message():
    form = request.form
    try:
        auth = form['auth']
        gid = int(form['gid'])
        since = 0
        limit = 30
        if 'limit' in form:
            limit = int(form['limit'])
        if 'since' in form:
            since = int(form['since'])
    except Exception as e:
        return db.make_result(1, message=str(e))
    data = db.get_new_message(auth, gid, limit=limit, since=since)
    print('get_new_message():', data)
    return data


if __name__ == '__main__':
    app.run("0.0.0.0", port=os.environ.get('PORT', '5000'), debug=False)
