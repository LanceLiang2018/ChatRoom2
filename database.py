import base64
import binascii
import copy
import hashlib
import json
import os
import random
import time


def get_head(email):
    return 'https://s.gravatar.com/avatar/' + hashlib.md5(email.lower().encode()).hexdigest() + '?s=144'


def b64_decode(string: str):
    try:
        result = base64.b64decode(string.encode()).decode()
        return result
    except binascii.Error:
        print("[Error decoding] Can't decode %s!" % string)
        return string


def b64_encode(string: str):
    return base64.b64encode(string.encode()).decode()


# V4 API 新内容：新的加密方式
# 分 token 和 login_token 两种，其中 login_token 含有原来的 md5 密码

def decode_login_token(login_token):
    if len(login_token) != 68:
        return '0' * 32
    auth_mix = login_token[:32]
    order = login_token[32:64]

    orderd = []
    for i in range(0, len(order), 2):
        orderd.append({'num': int(order[i:i + 2], 16), 'key': i // 2})
    orderd.sort(key=lambda x: x['num'])
    auth = ''
    for i in orderd:
        auth = auth + "%02x" % (0xff - int(auth_mix[i['key'] * 2:i['key'] * 2 + 2], 16))
    return auth


def make_token(self):
    salt = '%032x' % random.randint(0, 1 << (4 * 32))
    salted = hashlib.md5(("%s%s" % (self.auth, salt)).encode()).hexdigest()
    token = "%s%s%s" % (salted, salt, self.auth[:4])
    return token


class DataBase:
    def __init__(self):
        self.file_db_init = "db_init.sql"
        self.file_room_init = "room_init.sql"
        self.secret = "This program is owned by Lance."

        self.error_preview = "发生错误："
        self.success = 'Success.'

        self.error = {
            "Success": "%s" % self.success,
            "Error": "%s 服务器内部错误...请提交BUG给管理员。" % self.error_preview,
            "Auth": "%s Auth 错误，请重新登录。" % self.error_preview,
            "RoomNumber": "%s 房间号错误。" % self.error_preview,
            "NotIn": "%s 你不在此房间内。" % self.error_preview,
            "NoUser": "%s 没有这个用户。" % self.error_preview,
            "UserExist": "%s 用户已存在。" % self.error_preview,
            "Password": "%s 密码错误。" % self.error_preview,
            "HaveBeenFriends": "%s 你们已经是好友了。" % self.error_preview,
        }
        self.errors = {
            "Success": str(0),
            "Error": str(1),
            "Auth": str(2),
            "RoomNumber": str(3),
            "NotIn": str(4),
            "NoUser": str(5),
            "UserExist": str(6),
            "Password": str(7),
            "HaveBeenFriends": str(8),
        }
        self.error_messages = {
            str(0): self.error["Success"],
            str(1): self.error["Error"],
            str(2): self.error["Auth"],
            str(3): self.error["RoomNumber"],
            str(4): self.error["NotIn"],
            str(5): self.error["NoUser"],
            str(6): self.error["UserExist"],
            str(7): self.error["Password"],
            str(8): self.error["HaveBeenFriends"]
        }
        self.tables = ['users', 'maintain', 'auth',
                       'message', 'info', 'members',
                       'new_messages', 'files', 'friends']

        # self.sql_type = "PostgreSQL"
        self.sql_types = {"SQLite": 0, "PostgreSQL": 1}
        # self.sql_type = self.sql_types['PostgreSQL']
        # self.sql_type = self.sql_types['SQLite']
        # 用获取的端口号区分本地和远程
        if os.environ.get('PORT', '5000') == '5000':
            # Local
            self.sql_type = self.sql_types['SQLite']
        else:
            # Remote
            self.sql_type = self.sql_types['PostgreSQL']
        self.sql_chars = ["?", "%s"]
        self.sql_char = self.sql_chars[self.sql_type]

        self.connect_init()

    def L(self, string: str):
        return string.replace('%s', self.sql_char)

    def connect_init(self):
        if self.sql_type == self.sql_types['SQLite']:
            import sqlite3 as sql
            self.conn = sql.connect('data_sql.db', check_same_thread=False)
        else:
            import psycopg2 as sql
            self.conn = sql.connect(host='ec2-23-21-244-254.compute-1.amazonaws.com',
                                    database='d2hgdhf6r344jn',
                                    user='ygrsngdiegnvwu',
                                    port='5432',
                                    password='42840ffcad3f92d127108125d9b9bc949f6411a16f8636a179ea4549892bded4')

    def cursor_get(self):
        cursor = self.conn.cursor()
        return cursor

    def cursor_finish(self, cursor):
        self.conn.commit()
        cursor.close()

    def make_result(self, code, **args):
        result = {
            "code": str(code),
            "message": self.error_messages[str(code)],
            "data": args
        }
        return json.dumps(result)

    def get_last_uid(self):
        cursor = self.cursor_get()
        cursor.execute("SELECT last_uid FROM maintain")
        last_uid = cursor.fetchall()[0][0]
        self.cursor_finish(cursor)
        return int(last_uid)

    def get_last_gid(self):
        cursor = self.cursor_get()
        cursor.execute("SELECT last_gid FROM maintain")
        last_gid = cursor.fetchall()[0][0]
        self.cursor_finish(cursor)
        return int(last_gid)

    def get_last_mid(self):
        cursor = self.cursor_get()
        cursor.execute("SELECT last_mid FROM maintain")
        last_mid = cursor.fetchall()[0][0]
        self.cursor_finish(cursor)
        return int(last_mid)

    def update_last_uid(self):
        cursor = self.cursor_get()
        last_uid = self.get_last_uid()
        # 更新last_uid
        last_uid = last_uid + 1
        cursor.execute(self.L("UPDATE maintain SET last_uid = %s WHERE flag = %s"), (last_uid, "FLAG"))
        self.cursor_finish(cursor)
        return last_uid

    def update_last_gid(self):
        cursor = self.cursor_get()
        last_gid = self.get_last_gid()
        # 更新last_gid
        last_gid = last_gid + 1
        cursor.execute(self.L("UPDATE maintain SET last_gid = %s WHERE flag = %s"), (last_gid, "FLAG"))
        self.cursor_finish(cursor)
        return last_gid

    def update_last_mid(self):
        cursor = self.cursor_get()
        last_mid = self.get_last_mid()
        # 更新last_mid
        last_mid = last_mid + 1
        cursor.execute(self.L("UPDATE maintain SET last_mid = %s WHERE flag = %s"), (last_mid, "FLAG"))
        self.cursor_finish(cursor)
        return last_mid

    def check_in(self, table, line, value):
        cursor = self.cursor_get()
        try:
            cursor.execute("SELECT %s FROM %s WHERE %s = \'%s\'" % (line, table, line, value))
        except Exception as e:
            print(e)
            return False
        result = cursor.fetchall()
        self.cursor_finish(cursor)
        if len(result) > 0:
            return True
        return False

    def db_init(self):
        try:
            cursor = self.cursor_get()
            for table in self.tables:
                try:
                    cursor.execute("DROP TABLE IF EXISTS %s" % table)
                except Exception as e:
                    print('Error when dropping:', table, '\nException:\n', e)
                    self.cursor_finish(cursor)
                    cursor = self.cursor_get()
            self.cursor_finish(cursor)
        except Exception as e:
            print(e)
        self.conn.close()
        self.connect_init()
        cursor = self.cursor_get()
        # 一次只能执行一个语句。需要分割。而且中间居然不能有空语句。。
        with open(self.file_db_init, encoding='utf8') as f:
            string = f.read()
            for s in string.split(';'):
                try:
                    if s != '':
                        cursor.execute(s)
                except Exception as e:
                    print('Error:\n', s, 'Exception:\n', e)
        self.cursor_finish(cursor)

    def room_update_number(self, gid):
        cursor = self.cursor_get()
        cursor.execute("SELECT username FROM members")
        member_number = len(cursor.fetchall()[0])
        cursor.execute(self.L("UPDATE info SET member_number = %s WHERE gid = %s"), (member_number, gid))
        self.cursor_finish(cursor)

    def room_init(self, room_type):
        cursor = self.cursor_get()
        last_gid = self.update_last_gid()

        cursor.execute(self.L("INSERT INTO info (gid, name, create_time, member_number, last_post_time, room_type) "
                       "VALUES (%s, %s, %s, %s, %s, %s)"), (last_gid, 'New Group', int(time.time()), 0, int(time.time()), room_type))

        self.cursor_finish(cursor)
        # 返回这次建立的gid
        return last_gid

    # 返回值：创建的房间号。房间号自动递增
    def create_room(self, auth, name='New group', room_type='public', user_head=None):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])

        gid = self.room_init(room_type)
        # 让本人加群
        self.room_join_in(auth, gid)
        if user_head is None:
            user_head = self.get_head(auth)
        # 设置本群基本信息
        cursor = self.cursor_get()
        cursor.execute(self.L('UPDATE info SET name = %s, create_time = %s, last_post_time = %s, head = %s '
                              'WHERE gid = %s'),
                       (name, int(time.time()), int(time.time()), user_head, gid))
        self.cursor_finish(cursor)
        self.room_update_active_time(gid)
        # 返回房间号码
        return gid

    def room_join_in(self, auth, gid):
        # 检查房间存在
        if self.room_check_exist(gid) is False:
            return self.make_result(self.errors["RoomNumber"])
        if self.room_check_in(auth, gid) is True:
            return self.make_result(0)
        if json.loads(self.room_get_info(auth=auth, gid=gid))['data']['info']['room_type'] == "all":
            return self.make_result(0)
        cursor = self.cursor_get()
        username_src = self.auth2username(auth)
        username_b64 = b64_encode(username_src)
        cursor.execute(self.L("INSERT INTO members (gid, username) VALUES (%s, %s)"),
                       (gid, username_b64))
        cursor.execute(self.L("INSERT INTO new_messages (gid, username, latest_mid) VALUES (%s, %s, %s)"),
                       (gid, username_b64, 0))
        cursor.execute(self.L("SELECT rooms FROM users WHERE username = %s"), (username_b64, ))
        rooms = "%s %s" % (cursor.fetchall()[0][0], str(gid))
        cursor.execute(self.L("UPDATE users SET rooms = %s WHERE username = %s"),
                       (rooms, username_b64))
        self.cursor_finish(cursor)
        self.room_update_number(gid)
        return self.make_result(0)

    def room_join_in_friend(self, friend_src, gid):
        friend_b64 = b64_encode(friend_src)
        cursor = self.cursor_get()
        cursor.execute(self.L("INSERT INTO members (gid, username) VALUES (%s, %s)"),
                       (gid, friend_b64))
        cursor.execute(self.L("INSERT INTO new_messages (gid, username, latest_mid) VALUES (%s, %s, %s)"),
                       (gid, friend_b64, 0))
        cursor.execute(self.L("SELECT rooms FROM users WHERE username = %s"), (friend_b64, ))
        rooms = "%s %s" % (cursor.fetchall()[0][0], str(gid))
        cursor.execute(self.L("UPDATE users SET rooms = %s WHERE username = %s"),
                       (rooms, friend_b64))
        self.cursor_finish(cursor)
        self.room_update_number(gid)
        return self.make_result(0)

    # 设置房间基本信息
    def room_set_info(self, auth, gid, name=None, head=None):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])
        if self.room_check_exist(gid) is False:
            return self.make_result(self.errors["RoomNumber"])
        cursor = self.cursor_get()
        if name is not None:
            cursor.execute(self.L("UPDATE info SET name = %s WHERE gid = %s"), (name, gid))
        if head is not None:
            cursor.execute(self.L("UPDATE info SET head = %s WHERE gid = %s"), (head, gid))
        self.cursor_finish(cursor)
        return self.make_result(0)

    def room_get_members(self, auth, gid):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])
        if self.room_check_exist(gid) is False:
            return self.make_result(self.errors["RoomNumber"])
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT username FROM members WHERE gid = %s"), (gid, ))
        data = cursor.fetchall()
        data = list(map(lambda x: x[0], data))
        heads = []
        for username_b64 in data:
            username_src = b64_decode(username_b64)
            heads.append(self.user_get_head(username_src))
        result = []
        for i in range(len(data)):
            username_src = b64_decode(data[i])
            result.append({'username': username_src, 'head': heads[i]})
        cursor.close()
        self.cursor_finish(cursor)
        return self.make_result(0, result=result)

    # 房间号→Name
    def number2name(self, gid):
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT name FROM info WHERE gid = %s"), (gid, ))
        name = cursor.fetchall()[0][0]
        cursor.close()
        self.cursor_finish(cursor)
        return name

    def room_get_gids(self, auth, req='all'):
        if self.check_auth(auth) is False:
            return []
        # 列出所有room
        username_src = self.auth2username(auth)
        username_b64 = b64_encode(username_src)
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT rooms FROM users WHERE username = %s"), (username_b64, ))
        data = cursor.fetchall()
        result = []
        if len(data) != 0:
            rooms = data[0][0].split()
            result = list(map(lambda x: int(x), rooms))
        if req == 'all':
            cursor.execute(self.L("SELECT gid FROM info WHERE room_type = %s"), ('all', ))
            data = cursor.fetchall()
            for d in data:
                result.append(int(d[0]))
        self.cursor_finish(cursor)
        return result

    # 获取房间信息
    def room_get_info(self, auth, gid):
        # if self.check_auth(auth) is False:
        #     return self.make_result(self.errors["Auth"])
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT name, create_time, member_number, last_post_time, room_type, head "
                       "FROM info WHERE gid = %s"), (gid, ))
        data = cursor.fetchall()[0]
        self.cursor_finish(cursor)
        info = {
            'gid': int(gid), 'name': data[0], 'create_time': data[1],
            'member_number': data[2], 'last_post_time': data[3],
            'room_type': data[4], 'head': data[5]
        }
        return self.make_result(0, info=info)

    # 默认：password为空，name和email默认, normal
    def create_user(self, username_src='People', password='',
                    email='', motto='', user_type='normal'):
        username_b64 = b64_encode(username_src)
        if self.check_in("users", "username", username_src):
            return self.make_result(self.errors["UserExist"])

        cursor = self.cursor_get()
        last_uid = self.update_last_uid()

        password = hashlib.md5(password.encode()).hexdigest()
        head = get_head(email)
        cursor.execute(self.L("INSERT INTO users "
                       "(uid, username, password, email, head, motto, rooms, user_type) "
                              "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"),
                       (last_uid, username_b64, password, email, head, motto, "", user_type))

        self.update_last_uid()
        self.cursor_finish(cursor)
        return self.make_result(0)

    # 检查密码是否符合
    def user_check(self, username_src, password):
        username_b64 = b64_encode(username_src)
        if self.check_in("users", "username", username_b64) is False:
            return False
        cursor = self.cursor_get()
        password = hashlib.md5(password.encode()).hexdigest()
        cursor.execute(self.L("SELECT password FROM users WHERE username = %s"), (username_b64, ))
        data = cursor.fetchall()
        if len(data) == 0:
            return False
        storage = data[0][0]
        # print(storage)
        self.cursor_finish(cursor)
        if storage == password:
            return True
        return False

    def user_get_head(self, username_src):
        username_b64 = b64_encode(username_src)
        if self.check_in("users", "username", username_b64) is False:
            # return self.make_result(self.errors["NoUser"])
            return ""
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT head FROM users WHERE username = %s"), (username_b64, ))
        head = cursor.fetchall()[0][0]
        self.cursor_finish(cursor)
        return head

    # 创建鉴权避免麻烦。鉴权格式：MD5(username, secret, time)
    def create_auth(self, username_src, password):
        username_b64 = b64_encode(username_src)
        cursor = self.cursor_get()
        if not self.user_check(username_src, password):
            return self.make_result(self.errors["Password"])
        string = "%s %s %s" % (username_b64, self.secret, str(time.time()))
        auth = hashlib.md5(string.encode()).hexdigest()

        if self.check_in("auth", "username", username_b64):
            cursor.execute(self.L("UPDATE auth SET auth = %s WHERE username = %s"), (auth, username_b64))
        else:
            cursor.execute(self.L("INSERT INTO auth (username, auth) VALUES (%s, %s)"), (username_b64, auth))

        self.cursor_finish(cursor)
        # head = self.get_head(auth)
        # return self.make_result(0, auth=auth, head=head)
        myinfo = json.loads(self.user_get_info(username_src))
        myinfo = myinfo['data']['user_info']
        myinfo.update({'auth': auth})
        return self.make_result(0, user_info=myinfo)

    def check_auth(self, auth):
        result = self.check_in("auth", "auth", auth)
        if result is True:
            return True
        return False

    # 返回的是src码
    def auth2username(self, auth):
        if self.check_auth(auth) is False:
            return 'No_User'
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT username FROM auth WHERE auth = %s"), (auth,))
        username_b64 = cursor.fetchall()[0][0]
        self.cursor_finish(cursor)
        username_src = b64_decode(username_b64)
        return username_src

    def get_head(self, auth):
        if self.check_auth(auth) is False:
            return ""
        username_src = self.auth2username(auth)
        username_b64 = b64_encode(username_src)
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT head FROM users WHERE username = %s"), (username_b64, ))
        head = cursor.fetchall()[0][0]
        self.cursor_finish(cursor)
        return head

    def get_head_public(self, username_src):
        username_b64 = b64_encode(username_src)
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT head FROM users WHERE username = %s"), (username_b64, ))
        data = cursor.fetchall()
        if len(data) == 0:
            return ''
        head = data[0][0]
        self.cursor_finish(cursor)
        return head

    def room_check_in(self, auth, gid):
        # 检验是否在房间内
        username_src = self.auth2username(auth)
        username_b64 = b64_encode(username_src)
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT username FROM members WHERE username = %s AND gid = %s"), (username_b64, gid))
        data = cursor.fetchall()
        self.cursor_finish(cursor)
        if len(data) == 0:
            return False
        return True

    def room_check_exist(self, gid):
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT gid FROM info WHERE gid = %s"), (gid, ))
        data = cursor.fetchall()
        self.cursor_finish(cursor)
        if len(data) == 0:
            return False
        return True

    def room_get_name(self, gid):
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT name FROM info WHERE gid = %s"), (gid,))
        data = cursor.fetchall()
        self.cursor_finish(cursor)
        if len(data) > 0:
            return data[0]
        return ''

    def room_get_all(self, auth):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])
        # 列出所有room
        username_src = self.auth2username(auth)
        username_b64 = b64_encode(username_src)
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT rooms FROM users WHERE username = %s"), (username_b64, ))
        data = cursor.fetchall()
        result = []
        if len(data) != 0:
            rooms = data[0][0].split()
            rooms = list(map(lambda x: int(x), rooms))
            for r in rooms:
                info = json.loads(self.room_get_info(auth, r))['data']['info']
                result.append(info)
        cursor.execute(self.L("SELECT gid FROM info WHERE room_type = %s"), ('all', ))
        data = cursor.fetchall()
        if len(data) != 0:
            rooms = list(map(lambda x: int(x[0]), data))
            for r in rooms:
                info = json.loads(self.room_get_info(auth, r))['data']['info']
                result.append(info)
        self.cursor_finish(cursor)
        return self.make_result(0, room_data=result)

    def room_update_active_time(self, gid):
        cursor = self.cursor_get()
        cursor.execute(self.L("UPDATE info SET last_post_time = %s WHERE gid = %s"), (int(time.time()), gid))
        self.cursor_finish(cursor)

    def send_message(self, auth, gid, text, message_type='text'):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])
        if self.room_check_exist(gid) is False:
            return self.make_result(self.errors["RoomNumber"])
        # if self.room_check_in(auth, gid) is False:
        #     return self.make_result(self.errors["NotIn"])

        username_src = self.auth2username(auth)
        username_b64 = b64_encode(username_src)

        head = self.user_get_head(username_b64)
        last_mid = self.update_last_mid()

        if self.room_check_exist(gid) is False:
            return self.make_result(self.errors["RoomNumber"])
        cursor = self.cursor_get()
        cursor.execute(self.L("INSERT INTO message (mid, gid, username, head, "
                              "type, text, send_time) VALUES (%s, %s, %s, %s, %s, %s, %s)"),
                       (last_mid, gid, username_b64, head, message_type, text, int(time.time())))
        self.cursor_finish(cursor)

        self.room_update_active_time(gid)
        return self.make_result(0)

    # 返回格式：(username, head, type, text, mid)(json)
    def get_message(self, auth, gid, limit=30, offset=0):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])
        if self.room_check_exist(gid) is False:
            return self.make_result(self.errors["RoomNumber"])
        # if self.room_check_in(auth, gid) is False:
        #     return self.make_result(self.errors["NotIn"])

        cursor = self.cursor_get()
        result = []
        unit_ = {}
        cursor.execute(self.L("SELECT mid, username, head, type, text, send_time FROM message "
                       "WHERE gid = %s ORDER BY mid DESC LIMIT %s OFFSET %s"),
                       (gid, limit, offset))
        data = cursor.fetchall()
        for d in data:
            unit_['gid'] = int(gid)
            unit_['mid'], unit_['username'], unit_['head'], unit_['type'], unit_['text'], unit_['send_time'] = d
            unit_['username'] = b64_decode(unit_['username'])
            result.append(copy.deepcopy(unit_))
        self.cursor_finish(cursor)
        return self.make_result(0, message=result)

    # 返回格式：(username, head, type, text, mid)(json)
    def get_new_message(self, auth, gid, limit: int=30, since: int=0):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])
        if self.room_check_exist(gid) is False:
            return self.make_result(self.errors["RoomNumber"])
        # if self.room_check_in(auth, gid) is False:
        #     return self.make_result(self.errors["NotIn"])

        cursor = self.cursor_get()
        result = []
        unit_ = {}
        cursor.execute(self.L("SELECT mid, username, head, type, text, send_time FROM message "
                       "WHERE gid = %s AND mid > %s ORDER BY mid DESC LIMIT %s"),
                       (gid, since, limit))
        data = cursor.fetchall()
        for d in data:
            unit_['gid'] = int(gid)
            unit_['mid'], unit_['username'], unit_['head'], unit_['type'], unit_['text'], unit_['send_time'] = d
            unit_['username'] = b64_decode(unit_['username'])
            result.append(copy.deepcopy(unit_))
        self.cursor_finish(cursor)
        return self.make_result(0, message=result)

    def user_get_latest_mid(self, auth=None):
        if auth is None:
            return ""
        username_src = self.auth2username(auth)
        username_b64 = b64_encode(username_src)
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT gid, latest_mid FROM new_messages "
                       "WHERE username = %s"),
                       (username_b64, ))
        data = cursor.fetchall()
        cursor.close()
        result = []
        for d in data:
            result.append({"gid": d[0], "latest_mid": d[1]})
        return self.make_result(0, new_messages=result)

    def user_set_info(self, auth, head: str=None, motto: str=None, email: str=None):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])
        cursor = self.cursor_get()
        username_src = self.auth2username(auth)
        username_b64 = b64_encode(username_src)
        if head is not None:
            cursor.execute(self.L("UPDATE users SET head = %s WHERE username = %s"), (head, username_b64))
        if motto is not None:
            cursor.execute(self.L("UPDATE users SET motto = %s WHERE username = %s"), (motto, username_b64))
        if email is not None:
            cursor.execute(self.L("UPDATE users SET email = %s WHERE username = %s"), (email, username_b64))
        self.cursor_finish(cursor)
        return self.make_result(0)

    def have_read(self, auth, gid, latest_mid):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])
        username_src = self.auth2username(auth)
        username_b64 = b64_encode(username_src)

        cursor = self.cursor_get()
        cursor.execute(self.L("UPDATE new_messages SET latest_mid = %s WHERE username = %s AND gid = %s"),
                       (int(latest_mid), username_b64, gid))
        self.cursor_finish(cursor)
        return self.make_result(0)

    def file_upload(self, auth, filename: str='FILE', url: str=''):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])
        username_src = self.auth2username(auth)
        username_b64 = b64_encode(username_src)
        cursor = self.cursor_get()
        cursor.execute(self.L("INSERT INTO files (username, filename, url) VALUES (%s, %s, %s)"),
                       (username_b64, filename, url))
        self.cursor_finish(cursor)
        return self.make_result(0)

    def file_get(self, auth, limit: int=30, offset: int=0):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])
        username_src = self.auth2username(auth)
        username_b64 = b64_encode(username_src)
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT DISTINCT username, filename, url FROM files "
                              "WHERE username = %s ORDER BY filename "
                              "LIMIT %s OFFSET %s"),
                       (username_b64, limit, offset))
        data = cursor.fetchall()
        self.cursor_finish(cursor)
        result = []
        for d in data:
            result.append({'username': username_src, 'filename': d[1], 'url': d[2]})
        return self.make_result(0, files=result)

    def make_friends(self, auth, friend_src):
        friend_b64 = b64_encode(friend_src)
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])
        if self.check_in("users", "username", friend_b64) is False:
            return self.make_result(self.errors["NoUser"])
        username_src = self.auth2username(auth)
        username_b64 = b64_encode(username_src)
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT friend FROM friends WHERE username = %s AND friend = %s"),
                       (username_b64, friend_b64))
        data = cursor.fetchall()
        if len(data) != 0:
            return self.make_result(self.errors['HaveBeenFriends'])
        user_info = json.loads(self.user_get_info(friend_src))['data']['user_info']
        my_info = json.loads(self.user_get_info(username_src))['data']['user_info']
        user_head = "%s|%s" % (user_info['head'], my_info['head'])
        if user_info['user_type'] == 'printer':
            gid = self.create_room(auth, '%s|%s' % (username_src, friend_src), room_type='printer', user_head=user_head)
        else:
            gid = self.create_room(auth, '%s|%s' % (username_src, friend_src), room_type='private', user_head=user_head)
        # self.room_set_info(auth, gid, head=self.get_head_public(friend))
        cursor.execute(self.L("INSERT INTO friends (username, friend, gid) VALUES (%s, %s, %s)"),
                       (username_b64, friend_b64, gid))
        cursor.execute(self.L("INSERT INTO friends (username, friend, gid) VALUES (%s, %s, %s)"),
                       (friend_b64, username_b64, gid))
        self.cursor_finish(cursor)
        self.room_join_in_friend(friend_src, gid)
        print("make_friends(): ", user_info)
        print("\troom_info: ", self.room_get_info(auth=auth, gid=gid))
        return self.make_result(0)

    def get_friends(self, auth):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])
        username_src = self.auth2username(auth)
        username_b64 = b64_decode(username_src)
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT friend FROM friends WHERE username = %s"), (username_b64, ))
        data = cursor.fetchall()
        for d in data:
            pass
        # TODO: 啥！？这里还没做完...

    def user_get_info(self, username_src):
        username_b64 = b64_encode(username_src)
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT uid, username, email, head, motto, rooms, user_type "
                              "FROM users WHERE username = %s"),
                       (username_b64, ))
        info = cursor.fetchall()[0]
        self.cursor_finish(cursor)
        rooms = info[5]
        rooms = list(map(lambda x: int(x), rooms.split()))
        result = {
            'uid': info[0], 'username': username_src, 'email': info[2],
            'head': info[3], 'motto': info[4], 'rooms': rooms, "user_type": info[6]
        }
        return self.make_result(0, user_info=result)

    # Token 格式：salted + salt + pre_auth = (68)
    def token_parse(self, token):
        if len(token) != 68:
            return '0' * 32
        salted = token[:32]
        salt = token[32:-4]
        pre_auth = token[-4:]

        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT auth, pre_auth FROM auth WHERE pre_auth = %s"), (pre_auth,))
        data = cursor.fetchall()
        self.cursor_finish(cursor)
        # 没有找到pre_auth
        if len(data) == 0:
            return '0' * 32
        auth_s = data[0][0]
        return auth_s

    # Token 格式：salted + salt + pre_auth = (68)
    def check_token(self, token):
        if len(token) != 68:
            return False
        salted = token[:32]
        salt = token[32:-4]
        pre_auth = token[-4:]

        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT auth, pre_auth FROM auth WHERE pre_auth = %s"), (pre_auth,))
        data = cursor.fetchall()
        self.cursor_finish(cursor)
        # 没有找到pre_auth
        if len(data) == 0:
            return False
        auth_s = data[0][0]
        salted_s = hashlib.md5(("%s%s" % (auth_s, salt)).encode()).hexdigest()
        if salted == salted_s:
            return True
        return False

    # V4: 新的LoginToken: auth_mix(32) + order(32) + noise(4) = (68)
    # 返回login_token
    def create_login_token(self, username_src, password):
        username_b64 = b64_encode(username_src)
        cursor = self.cursor_get()
        if not self.user_check(username_src, password):
            return self.make_result(self.errors["Password"])

        # 独立生成auth
        # string = "%s %s %s" % (username_b64, self.secret, str(time.time()))
        # auth = hashlib.md5(string.encode()).hexdigest()

        # 使用已经有的auth
        auth = json.loads(self.create_auth(username_src, password))['data']['user_info']['auth']

        # 获取token的时候不需要pre_auth。使用随机数。
        # pre_auth = auth[:4]
        pre_auth = "%04x" % random.randint(0, 1 << 16)
        auth_li = []
        for i in range(0, len(auth), 2):
            auth_li.append(auth[i:i + 2])

        # 生成order
        order = random.sample(range(0, 256), 16)
        # 数字→排列
        orderd = []
        for i in range(len(order)):
            # orderd.append({order[i]: i})
            orderd.append({'num': order[i], 'key': i})
        orderd.sort(key=lambda x: x['num'])

        new_orderd = ['00', ] * 16
        index = 0
        for k in orderd:
            # 这里取反了一次
            new_orderd[k['key']] = "%02x" % (0xff - int(auth_li[index], 16))
            index = index + 1

        auth_mix = ''
        for i in new_orderd:
            auth_mix = auth_mix + i

        result = '%s' % auth_mix
        for i in order:
            result = "%s%s" % (result, "%02x" % i)

        login_token = result + pre_auth

        # 这里才需要pre_auth
        cursor.execute(self.L("UPDATE auth SET auth = %s, pre_auth = %s WHERE username = %s"),
                       (auth, auth[:4], username_b64))

        self.cursor_finish(cursor)

        print("DEBUG: auth:", auth)

        myinfo = json.loads(self.user_get_info(username_src))
        myinfo = myinfo['data']['user_info']
        myinfo.update({'login_token': login_token})
        return self.make_result(0, user_info=myinfo)


def module_test():
    db = DataBase()
    db.db_init()
    # exit()
    db.create_user("Lance", "1352040930lxr")
    db.create_user("中文", "1352040930lxr")
    # print(db.check_in("users", "username", "Lance"))
    # _au = json.loads(db.create_auth("Lance", "1352040930lxr"))['data']['user_info']['auth']
    # _au2 = json.loads(db.create_auth("中文", "1352040930lxr"))['data']['user_info']['auth']
    _to = json.loads(db.create_login_token("Lance", "1352040930lxr"))['data']['user_info']['login_token']
    _to2 = json.loads(db.create_login_token("中文", "1352040930lxr"))['data']['user_info']['login_token']
    _au = decode_login_token(_to)
    _au2 = decode_login_token(_to2)
    print(_au, _au2)
    name = db.auth2username(_au), db.auth2username(_au2)
    print(name)
    print(_au, _au2)
    _gid = db.create_room(_au, "TEST GROUP")
    print(db.room_join_in(_au, _gid))
    print(db.room_join_in(_au2, _gid))
    print(type(_gid), _gid)
    print(db.send_message(_au, _gid, "Test message"))
    print(db.send_message(_au, _gid, "Sent by Lance"))
    print(db.get_message(_au, _gid))
    print(db.send_message(_au2, _gid, "Sent by 中文"))
    print(db.send_message(_au2, _gid, "Sent by 中文"))
    print(db.get_message(_au, _gid))
    print(db.room_get_all(_au))
    print(db.room_get_members(_au, _gid))


def jsonify(string: str):
    return json.loads(string)


def mini_test():
    db = DataBase()
    db.db_init()
    db.create_user("Lance", "")
    _au = json.loads(db.create_auth("Lance", ""))['data']['auth']

    _gid = db.create_room(_au, "TEST GROUP")
    print('join in', db.room_join_in(_au, _gid))

    '''

    print('send message', db.send_message(_au, _gid, "TEXT", "text"))

    res = jsonify(db.get_message(_au, _gid))
    print('get message', res)
    length = len(res['data']['message'])
    print('got', length, 'message(s)')

    res = jsonify(db.user_get_latest_mid(auth=_au))
    print('get latest mid', res)
    latest = 0
    for r in res['data']['new_messages']:
        rdata = jsonify(db.get_message(_au, _gid))
        for rd in rdata['data']['message']:
            latest = max(latest, rd['mid'])
        print('gid:', r['gid'], rdata['data']['message'])

    print('have read', db.have_read(_au, _gid, latest))
    print('now get latest mid', db.user_get_latest_mid(auth=_au))

    print('#' * 30)
    print('send new message', db.send_message(_au, _gid, "T2", "text"))

    res = jsonify(db.get_message(_au, _gid))
    print('get message', res)
    length = len(res['data']['message'])
    print('got', length, 'message(s)')

    res = jsonify(db.user_get_latest_mid(auth=_au))
    print('get latest mid', res)

    for r in res['data']['new_messages']:
        rdata = jsonify(db.get_new_message(_au, _gid, since=latest))
        for rd in rdata['data']['message']:
            latest = max(latest, rd['mid'])
        print('gid:', r['gid'], rdata['data']['message'])

    print('have read', db.have_read(_au, _gid, latest))
    print('now get latest mid', db.user_get_latest_mid(auth=_au))
    
    '''

    print('put file', db.file_upload(_au, filename='NAME', url='NONE'))
    print('get file', db.file_get(_au))


def friend_test():
    db = DataBase()
    db.db_init()
    db.create_user('Lance', "", email='LanceLiang2018@163.com')
    db.create_user('Tony', "", email='TonyLiang2018@163.com')
    au1, au2 = jsonify(db.create_auth('Lance', ''))['data']['auth'], jsonify(db.create_auth('Tony', ''))['data']['auth']
    print(au1, au2)
    gid1 = db.create_room(au1, 'Lance\'s Room')
    gid2 = db.create_room(au2, 'Tony\'s Room')
    print('Lance | gid1=%d: room_get_all():' % gid1, db.room_get_all(au1))
    print('Tony  | gid2=%d: room_get_all():' % gid2, db.room_get_all(au2))
    print('make_friends(): ', db.make_friends(au1, 'Tony'))
    print('make_friends(): ', db.make_friends(au2, 'Lance'))
    print('Lance | gid1=%d: room_get_all():' % gid1, db.room_get_all(au1))
    print('Tony  | gid2=%d: room_get_all():' % gid2, db.room_get_all(au2))


def base64_username_test():
    db = DataBase()
    db.db_init()

    print(db.create_user('Lance', ''))
    print(jsonify(db.create_auth('Lance', '')))


if __name__ == '__main__':
    # db = DataBase()
    # db.db_init()
    # print(db.update_last_mid())
    # print(db.make_result(0, messages={"s": "a"}))

    module_test()
    # MiniTest()
    # friend_test()
    # base64_username_test()
