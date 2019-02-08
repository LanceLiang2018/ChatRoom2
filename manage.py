import base64
import hashlib
# import json
import os

from flask import *
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client

from database import DataBase

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


@app.route('/get_head_public', methods=["POST"])
def get_head_public():
    form = request.form
    try:
        username = form['username']
    except Exception as e:
        return db.make_result(1, message=str(e))
    head = db.get_head_public(username)
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
        username, password, email = form['username'], form['password'], form['email']
        name = username
        if 'name' in form:
            name = form['name']
    except Exception as e:
        return db.make_result(1, message=str(e))
    return db.create_user(username, password, name, email)


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
        name = None
        head = None
        if 'name' in form:
            name = form['name']
        if 'head' in form:
            head = form['head']
    except Exception as e:
        return db.make_result(1, message=str(e))
    res = db.room_set_info(auth, gid, name=name, head=head)
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


@app.route('/get_user_info', methods=['POST'])
def get_user_info():
    form = request.form
    try:
        username, auth = None, None
        if 'username' in form:
            username = form['username']
        else:
            auth = form['auth']
    except Exception as e:
        return db.make_result(1, message=str(e))
    if username is None:
        username = db.auth2username(auth)
    res = db.user_get_info(username)
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


@app.route('/make_friends', methods=['POST'])
def make_friends():
    form = request.form
    try:
        auth = form['auth']
        friend = form['friend']
    except Exception as e:
        return db.make_result(1, message=str(e))
    data = db.make_friends(auth, friend)
    return data


def get_if_in(key: str, form: dict, default=None):
    if key in form:
        return form[key]
    return default


@app.route('/v3/api/clear_all', methods=["POST", "GET"])
def v3_clear_all():
    try:
        db.db_init()
    except Exception as e:
        return db.make_result(1, message=str(e))
    return db.make_result(0)


@app.route('/update', methods=["GET"])
def update():
    return redirect("https://%s.cos.ap-chengdu.myqcloud.com/release.apk" % bucket)


@app.route('/device', methods=["GET"])
def device():
    return redirect("https://%s.cos.ap-chengdu.myqcloud.com/device.exe" % bucket)


@app.route('/license', methods=["GET"])
def license_help():
    return redirect("https://static-1254016670.cos.ap-chengdu.myqcloud.com/license.html")


@app.route('/device_help', methods=["GET"])
def device_help():
    return redirect("https://static-1254016670.cos.ap-chengdu.myqcloud.com/device_part.html")


@app.route('/v3/api', methods=["POST"])
def main_api():
    form = request.form
    print("DEBUG:", form)
    # 一定需要action
    if 'action' not in form:
        return db.make_result(1, error="No action selected")
    action = form['action']

    # print("Action...")

    # 这三个api不需要auth
    if action == 'clear_all':
        # 访问/v3/api/clear_all
        pass

    if action == 'get_user':
        if 'username' not in form:
            return db.make_result(1, error=form)
        username = get_if_in('username', form, default='Lance')
        return db.user_get_info(username=username)

    if action == 'get_room':
        if 'gid' not in form:
            return db.make_result(1, error=form)
        gid = int(get_if_in('gid', form, default='0'))
        return db.room_get_info(gid=gid, auth='')

    if action == 'login':
        if 'username' not in form \
                or 'password' not in form:
            return db.make_result(1, error=form)
        username = get_if_in('username', form)
        password = get_if_in('password', form)
        return db.create_auth(username=username, password=password)

    if action == 'signup':
        if 'username' not in form \
                or 'password' not in form:
            return db.make_result(1, error=form)
        username = get_if_in('username', form)
        password = get_if_in('password', form)
        user_type = get_if_in('user_type', form, default='normal')
        email = get_if_in('email', form, default='')
        return db.create_user(username=username, password=password, email=email, user_type=user_type)

    # 需要auth
    if 'auth' not in form:
        return db.make_result(1, error="No auth")
    auth = form['auth']

    # print("Auth...")

    if action == 'beat':
        if db.check_auth(auth) is False:
            return db.make_result(2)
        return db.make_result(0)

    if action == 'create_room':
        name = get_if_in('name', form, default='New group')
        room_type = get_if_in('room_type', form, default='public')
        if db.check_auth(auth) is False:
            return db.make_result(2)
        gid = db.create_room(auth=auth, name=name, room_type=room_type)
        return db.room_get_info(auth=auth, gid=gid)

    if action == 'get_room_all':
        # print("Your request:", form)
        return db.room_get_all(auth=auth)

    if action == 'join_in':
        if 'gid' not in form:
            return db.make_result(1, error=form)
        gid = int(get_if_in('gid', form, default="0"))
        return db.room_join_in(auth=auth, gid=gid)

    if action == 'set_room':
        if 'gid' not in form:
            return db.make_result(1, error=form)
        gid = int(get_if_in('gid', form, default=None))
        name = get_if_in('name', form, default=None)
        head = get_if_in('head', form, default=None)
        return db.room_set_info(auth=auth, gid=gid, name=name, head=head)

    # New Action
    if action == 'pre_upload':
        return db.make_result(0, pre_upload={'pre_url': 'https://%s.cos.ap-chengdu.myqcloud.com/' % bucket})

    if action == 'upload':
        if 'data' not in form:
            return db.make_result(1, error=form)
        filename = get_if_in('filename', form, default='filename')
        data = get_if_in('data', form, default=None)
        data = base64.b64decode(data)
        username = db.auth2username(auth)
        # md5 = hashlib.md5(data).hexdigest()
        # filename_md5 = "%s" % md5
        response = client.put_object(
            Bucket=bucket,
            Body=data,
            # Key=filename_md5,
            Key="%s/%s" % (username, filename),
            StorageClass='STANDARD',
            EnableMD5=False
            # 我自己算吧......
        #     不算了
        )
        print(response)
        # url = 'https://%s.cos.ap-chengdu.myqcloud.com/%s' % (bucket, filename_md5)
        url = 'https://%s.cos.ap-chengdu.myqcloud.com/%s/%s' % (bucket, username, filename)
        result = {
            'filename': filename, 'etag': response['ETag'][1:-1],
            "url": url
        }
        db.file_upload(auth, filename, url)
        res = db.make_result(0, upload_result=result)
        return res

    if action == 'get_files':
        limit = int(get_if_in('limit', form, default='30'))
        offset = int(get_if_in('limit', form, default='0'))
        return db.file_get(auth=auth, limit=limit, offset=offset)

    if action == 'get_messages':
        if db.check_auth(auth) is False:
            return db.make_result(2)
        gid = int(get_if_in('gid', form, default='0'))
        limit = int(get_if_in('limit', form, default='30'))
        since = int(get_if_in('since', form, default='0'))
        req = get_if_in('request', form, default='all')
        # print("req: ", req)

        if req == 'all' and gid == 0:
            print("req: all")
            gids = db.room_get_gids(auth=auth, req='all')
            messages = []
            for g in gids:
                result = json.loads(db.get_new_message(auth=auth, gid=g, limit=limit, since=since))
                if result['code'] != 0:
                    return jsonify(result)
                messages.extend(result['data']['message'])
            return db.make_result(0, message=messages)
        elif req == 'private':
            print("req: private")
            gids = db.room_get_gids(auth=auth, req='private')
            messages = []
            for g in gids:
                result = json.loads(db.get_new_message(auth=auth, gid=g, limit=limit, since=since))
                if result['code'] != 0:
                    return jsonify(result)
                messages.extend(result['data']['message'])
            return db.make_result(0, message=messages)
        elif gid != 0:
            print("req: single room...")
            return db.get_new_message(auth=auth, gid=gid, limit=limit, since=since)
        return db.make_result(1)

    if action == 'send_message':
        if 'gid' not in form \
                or 'text' not in form:
            return db.make_result(1, error=form)
        gid = int(get_if_in('gid', form, default='0'))
        text = get_if_in('text', form, default='text')
        message_type = get_if_in('message_type', form, default='text')
        return db.send_message(auth=auth, gid=gid, text=text, message_type=message_type)

    if action == 'make_friends':
        if 'friend' not in form:
            return db.make_result(1, error=form)
        friend = get_if_in('friend', form, default='Lance')
        return db.make_friends(auth=auth, friend=friend)

    if action == "set_user":
        head = get_if_in('head', form, default=None)
        motto = get_if_in('motto', form, default=None)
        email = get_if_in("email", form, default=None)
        return db.user_set_info(auth=auth, head=head, motto=motto, email=email)

    if action == "get_version":
        return db.make_result(0, version="2.0")

    return db.make_result(1, error='Not support method')


if __name__ == '__main__':
    app.run("0.0.0.0", port=int(os.environ.get('PORT', '5000')), debug=False)

