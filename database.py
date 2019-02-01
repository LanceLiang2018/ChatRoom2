import copy
import hashlib
import json
import os
import time


def get_head(email):
    return 'https://s.gravatar.com/avatar/' + hashlib.md5(email.lower().encode()).hexdigest() + '?s=144'


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
            self.conn = sql.connect(host='ec2-54-235-156-60.compute-1.amazonaws.com',
                                    database='d90dv1hptfo8l9',
                                    user='tagnipsifgbhic',
                                    port='5432',
                                    password='c26e906de3e7d5f7f54872432bcab7cbbcee3ab24b530964dfe4480fa4fef9e2')

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
#        cursor.execute(self.L("INSERT INTO message (gid, mid, uid, username, head, type, text, send_time) VALUES "
#                       "(%s, 0, 0, 'Administrator', 'https://s.gravatar.com/avatar/544b5009873b27f5e0aa6dd8ffc1d3d8?s") +
#                       self.L("=512', 'text',  %s, %s)"), (last_gid, "Welcome to this room!", int(time.time())))

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
        username = self.auth2username(auth)
        cursor.execute(self.L("INSERT INTO members (gid, username) VALUES (%s, %s)"),
                       (gid, username))
        cursor.execute(self.L("INSERT INTO new_messages (gid, username, latest_mid) VALUES (%s, %s, %s)"),
                       (gid, username, 0))
        cursor.execute(self.L("SELECT rooms FROM users WHERE username = %s"), (username, ))
        rooms = "%s %s" % (cursor.fetchall()[0][0], str(gid))
        cursor.execute(self.L("UPDATE users SET rooms = %s WHERE username = %s"),
                       (rooms, username))
        self.cursor_finish(cursor)
        self.room_update_number(gid)
        return self.make_result(0)

    def room_join_in_friend(self, friend, gid):
        cursor = self.cursor_get()
        cursor.execute(self.L("INSERT INTO members (gid, username) VALUES (%s, %s)"),
                       (gid, friend))
        cursor.execute(self.L("INSERT INTO new_messages (gid, username, latest_mid) VALUES (%s, %s, %s)"),
                       (gid, friend, 0))
        cursor.execute(self.L("SELECT rooms FROM users WHERE username = %s"), (friend, ))
        rooms = "%s %s" % (cursor.fetchall()[0][0], str(gid))
        cursor.execute(self.L("UPDATE users SET rooms = %s WHERE username = %s"),
                       (rooms, friend))
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
        for username in data:
            heads.append(self.user_get_head(username))
        result = []
        for i in range(len(data)):
            result.append({'username': data[i], 'head': heads[i]})
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
        username = self.auth2username(auth)
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT rooms FROM users WHERE username = %s"), (username, ))
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
    def create_user(self, username='Lance', password='',
                    email='lanceliang2018@163.com', motto='', user_type='normal'):
        if self.check_in("users", "username", username):
            return self.make_result(self.errors["UserExist"])

        cursor = self.cursor_get()
        last_uid = self.update_last_uid()

        password = hashlib.md5(password.encode()).hexdigest()
        head = get_head(email)
        cursor.execute(self.L("INSERT INTO users "
                       "(uid, username, password, email, head, motto, rooms, user_type) "
                              "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"),
                       (last_uid, username, password, email, head, motto, "", user_type))

        self.update_last_uid()
        self.cursor_finish(cursor)
        return self.make_result(0)

    # 检查密码是否符合
    def user_check(self, username, password):
        if self.check_in("users", "username", username) is False:
            return False
        cursor = self.cursor_get()
        password = hashlib.md5(password.encode()).hexdigest()
        cursor.execute(self.L("SELECT password FROM users WHERE username = %s"), (username, ))
        data = cursor.fetchall()
        if len(data) == 0:
            return False
        storage = data[0][0]
        # print(storage)
        self.cursor_finish(cursor)
        if storage == password:
            return True
        return False

    def user_get_head(self, username):
        if self.check_in("users", "username", username) is False:
            # return self.make_result(self.errors["NoUser"])
            return ""
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT head FROM users WHERE username = %s"), (username, ))
        head = cursor.fetchall()[0][0]
        self.cursor_finish(cursor)
        return head

    # 创建鉴权避免麻烦。鉴权格式：MD5(username, secret, time)
    def create_auth(self, username, password):
        cursor = self.cursor_get()
        if not self.user_check(username, password):
            return self.make_result(self.errors["Password"])
        string = "%s %s %s" % (username, self.secret, str(time.time()))
        auth = hashlib.md5(string.encode()).hexdigest()

        if self.check_in("auth", "username", username):
            cursor.execute(self.L("UPDATE auth SET auth = %s WHERE username = %s"), (auth, username))
        else:
            cursor.execute(self.L("INSERT INTO auth (username, auth) VALUES (%s, %s)"), (username, auth))

        self.cursor_finish(cursor)
        # head = self.get_head(auth)
        # return self.make_result(0, auth=auth, head=head)
        myinfo = json.loads(self.user_get_info(username=username))
        myinfo = myinfo['data']['user_info']
        myinfo.update({'auth': auth})
        return self.make_result(0, user_info=myinfo)

    def check_auth(self, auth):
        result = self.check_in("auth", "auth", auth)
        if result is True:
            return True
        return False

    def auth2username(self, auth):
        if self.check_auth(auth) is False:
            return 'No_User'
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT username FROM auth WHERE auth = %s"), (auth,))
        username = cursor.fetchall()[0][0]
        self.cursor_finish(cursor)
        return username

    def get_head(self, auth):
        if self.check_auth(auth) is False:
            return ""
        username = self.auth2username(auth)
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT head FROM users WHERE username = %s"), (username, ))
        head = cursor.fetchall()[0][0]
        self.cursor_finish(cursor)
        return head

    def get_head_public(self, username):
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT head FROM users WHERE username = %s"), (username, ))
        data = cursor.fetchall()
        if len(data) == 0:
            return ''
        head = data[0][0]
        self.cursor_finish(cursor)
        return head

    def room_check_in(self, auth, gid):
        # 检验是否在房间内
        username = self.auth2username(auth)
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT username FROM members WHERE username = %s AND gid = %s"), (username, gid))
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
        username = self.auth2username(auth)
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT rooms FROM users WHERE username = %s"), (username, ))
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

        username = self.auth2username(auth)

        head = self.user_get_head(username)
        last_mid = self.update_last_mid()

        if self.room_check_exist(gid) is False:
            return self.make_result(self.errors["RoomNumber"])
        cursor = self.cursor_get()
        cursor.execute(self.L("INSERT INTO message (mid, gid, username, head, "
                              "type, text, send_time) VALUES (%s, %s, %s, %s, %s, %s, %s)"),
                       (last_mid, gid, username, head, message_type, text, int(time.time())))
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
            result.append(copy.deepcopy(unit_))
        self.cursor_finish(cursor)
        return self.make_result(0, message=result)

    def user_get_latest_mid(self, auth=None, username=None):
        if auth is None and username is None:
            return ""
        if username is None:
            username = self.auth2username(auth)
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT gid, latest_mid FROM new_messages "
                       "WHERE username = %s"),
                       (username, ))
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
        username = self.auth2username(auth)
        if head is not None:
            cursor.execute(self.L("UPDATE users SET head = %s WHERE username = %s"), (head, username))
        if motto is not None:
            cursor.execute(self.L("UPDATE users SET motto = %s WHERE username = %s"), (motto, username))
        if email is not None:
            cursor.execute(self.L("UPDATE users SET email = %s WHERE username = %s"), (email, username))
        self.cursor_finish(cursor)
        return self.make_result(0)

    def have_read(self, auth, gid, latest_mid):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])
        username = self.auth2username(auth)

        cursor = self.cursor_get()
        cursor.execute(self.L("UPDATE new_messages SET latest_mid = %s WHERE username = %s AND gid = %s"),
                       (int(latest_mid), username, gid))
        self.cursor_finish(cursor)
        return self.make_result(0)

    def file_upload(self, auth, filename: str='FILE', url: str=''):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])
        username = self.auth2username(auth)
        cursor = self.cursor_get()
        cursor.execute(self.L("INSERT INTO files (username, filename, url) VALUES (%s, %s, %s)"),
                       (username, filename, url))
        self.cursor_finish(cursor)
        return self.make_result(0)

    def file_get(self, auth, limit: int=30, offset: int=0):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])
        username = self.auth2username(auth)
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT DISTINCT username, filename, url FROM files "
                              "WHERE username = %s ORDER BY filename "
                              "LIMIT %s OFFSET %s"),
                       (username, limit, offset))
        data = cursor.fetchall()
        self.cursor_finish(cursor)
        result = []
        for d in data:
            result.append({'username': d[0], 'filename': d[1], 'url': d[2]})
        return self.make_result(0, files=result)

    def make_friends(self, auth, friend):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])
        if self.check_in("users", "username", friend) is False:
            return self.make_result(self.errors["NoUser"])
        username = self.auth2username(auth)
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT friend FROM friends WHERE username = %s AND friend = %s"), (username, friend))
        data = cursor.fetchall()
        if len(data) != 0:
            return self.make_result(self.errors['HaveBeenFriends'])
        user_info = json.loads(self.user_get_info(username=friend))['data']['user_info']
        my_info = json.loads(self.user_get_info(username=username))['data']['user_info']
        user_head = "%s|%s" % (user_info['head'], my_info['head'])
        if user_info['user_type'] == 'printer':
            gid = self.create_room(auth, '%s|%s' % (username, friend), room_type='printer', user_head=user_head)
        else:
            gid = self.create_room(auth, '%s|%s' % (username, friend), room_type='private', user_head=user_head)
        # self.room_set_info(auth, gid, head=self.get_head_public(friend))
        cursor.execute(self.L("INSERT INTO friends (username, friend, gid) VALUES (%s, %s, %s)"),
                       (username, friend, gid))
        cursor.execute(self.L("INSERT INTO friends (username, friend, gid) VALUES (%s, %s, %s)"),
                       (friend, username, gid))
        self.cursor_finish(cursor)
        self.room_join_in_friend(friend, gid)
        print("make_friends(): ", user_info)
        print("\troom_info: ", self.room_get_info(auth=auth, gid=gid))
        return self.make_result(0)

    def get_friends(self, auth):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])
        username = self.auth2username(auth)
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT friend FROM friends WHERE username = %s"), (username, ))
        data = cursor.fetchall()
        for d in data:
            pass

    def user_get_info(self, username):
        cursor = self.cursor_get()
        cursor.execute(self.L("SELECT uid, username, email, head, motto, rooms, user_type "
                              "FROM users WHERE username = %s"),
                       (username, ))
        info = cursor.fetchall()[0]
        self.cursor_finish(cursor)
        rooms = info[5]
        rooms = list(map(lambda x: int(x), rooms.split()))
        result = {
            'uid': info[0], 'username': info[1], 'email': info[2],
            'head': info[3], 'motto': info[4], 'rooms': rooms, "user_type": info[6]
        }
        return self.make_result(0, user_info=result)


def module_test():
    db = DataBase()
    db.db_init()
    # exit()
    db.create_user("Lance", "1352040930lxr")
    db.create_user("Lance2", "1352040930lxr")
    # print(db.check_in("users", "username", "Lance"))
    _au = json.loads(db.create_auth("Lance", "1352040930lxr"))['data']['auth']
    _au2 = json.loads(db.create_auth("Lance2", "1352040930lxr"))['data']['auth']
    print(db.check_auth(_au), db.check_auth(_au2))
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
    print(db.send_message(_au2, _gid, "Sent by Lance2"))
    print(db.send_message(_au2, _gid, "Sent by Lance2"))
    print(db.get_message(_au, _gid))
    print(db.room_get_all(_au))
    print(db.room_get_members(_au, _gid))


def jsonify(string: str):
    return json.loads(string)


def MiniTest():
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
    au1, au2 = jsonify(db.create_auth('Lance', ''))['data']['auth'], \
               jsonify(db.create_auth('Tony', ''))['data']['auth']
    print(au1, au2)
    gid1 = db.create_room(au1, 'Lance\'s Room')
    gid2 = db.create_room(au2, 'Tony\'s Room')
    print('Lance | gid1=%d: room_get_all():' % gid1, db.room_get_all(au1))
    print('Tony  | gid2=%d: room_get_all():' % gid2, db.room_get_all(au2))
    print('make_friends(): ', db.make_friends(au1, 'Tony'))
    print('make_friends(): ', db.make_friends(au2, 'Lance'))
    print('Lance | gid1=%d: room_get_all():' % gid1, db.room_get_all(au1))
    print('Tony  | gid2=%d: room_get_all():' % gid2, db.room_get_all(au2))


if __name__ == '__main__':
    # db = DataBase()
    # db.db_init()
    # print(db.update_last_mid())
    # print(db.make_result(0, messages={"s": "a"}))

    # module_test()
    # MiniTest()
    friend_test()
