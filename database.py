import hashlib
# import os
import time
import copy
import json


def get_head(email):
    return 'https://s.gravatar.com/avatar/' + hashlib.md5(email.encode()).hexdigest() + '?s=144'


class DataBase:
    def __init__(self):
        self.file_db_init = "db_init.sql"
        self.file_room_init = "room_init.sql"
        self.secret = "This program is owned by Lance."

        self.error_preview = "Error."
        self.success = 'Success.'

        self.error = {
            "Success": "%s" % self.success,
            "Error": "%s" % self.error_preview,
            "Auth": "%s Auth Error." % self.error_preview,
            "RoomNumber": "%s Room Error. Room number error." % self.error_preview,
            "NotIn": "%s Room Error. You are not in this group." % self.error_preview,
            "NoUser": "%s No such of user." % self.error_preview,
            "UserExist": "%s User exists." % self.error_preview,
            "Password": "%s Password Error." % self.error_preview,
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
        }
        self.tables = ['users', 'maintain', 'auth',
                       'message', 'info', 'members', ]

        # self.sql_type = "PostgreSQL"
        self.sql_types = {"SQLite": 0, "PostgreSQL": 1}
        self.sql_type = self.sql_types['PostgreSQL']
        # self.sql_type = self.sql_types['PostgreSQL']
        self.sql_chars = ["?", "%s"]
        self.sql_char = self.sql_chars[self.sql_type]

        self.connect_init()

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
        cursor.execute("UPDATE maintain SET last_uid = %s WHERE flag = %s".replace('%s', self.sql_char), (last_uid, "FLAG"))
        self.cursor_finish(cursor)
        return last_uid

    def update_last_gid(self):
        cursor = self.cursor_get()
        last_gid = self.get_last_gid()
        # 更新last_gid
        last_gid = last_gid + 1
        cursor.execute("UPDATE maintain SET last_gid = %s WHERE flag = %s".replace('%s', self.sql_char), (last_gid, "FLAG"))
        self.cursor_finish(cursor)
        return last_gid

    def update_last_mid(self):
        cursor = self.cursor_get()
        last_mid = self.get_last_mid()
        # 更新last_mid
        last_mid = last_mid + 1
        cursor.execute("UPDATE maintain SET last_mid = %s WHERE flag = %s".replace('%s', self.sql_char), (last_mid, "FLAG"))
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
                    cursor.execute("DROP TABLE %s" % table)
                except Exception as e:
                    print('Error when dropping:', 'Exception:\n', e)
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
        cursor.execute("UPDATE info SET member_number = %s WHERE gid = %s".replace('%s', self.sql_char), (member_number, gid))
        self.cursor_finish(cursor)

    def room_init(self):
        cursor = self.cursor_get()
        last_gid = self.update_last_gid()

        cursor.execute("INSERT INTO info (gid, name, create_time, member_number, last_post_time) "
                       "VALUES (%s, %s, %s, %s, %s)".replace('%s', self.sql_char), (last_gid, 'New Group', int(time.time()), 0, int(time.time())))
        cursor.execute("INSERT INTO message (gid, mid, uid, username, head, type, text, send_time) VALUES "
                       "(%s, 0, 0, 'Administrator', 'https://s.gravatar.com/avatar/544b5009873b27f5e0aa6dd8ffc1d3d8?s".replace('%s', self.sql_char) +
                       "=512', 'text',  %s, %s)".replace('%s', self.sql_char), (last_gid, "Welcome to this room!", int(time.time())))

        self.cursor_finish(cursor)
        # 返回这次建立的gid
        return last_gid

    # 返回值：创建的房间号。房间号自动递增
    def create_room(self, auth, name='New group'):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])

        gid = self.room_init()
        # 让本人加群
        self.room_join_in(auth, gid)

        # 设置本群基本信息
        cursor = self.cursor_get()
        cursor.execute('UPDATE info SET name = %s, create_time = %s, last_post_time = %s WHERE gid = %s'.replace('%s', self.sql_char),
                       (name, int(time.time()), int(time.time()), gid))
        self.cursor_finish(cursor)

        self.room_update_active_time(gid)

        # 返回房间号码
        return gid

    def room_join_in(self, auth, gid):
        # 检查房间存在
        if self.room_check_exist(gid) is False:
            return self.make_result(self.errors["RoomNumber"])
        cursor = self.cursor_get()
        username = self.auth2username(auth)
        cursor.execute("INSERT INTO members (gid, username) VALUES (%s, %s)".replace('%s', self.sql_char), (gid, username))
        self.cursor_finish(cursor)
        self.room_update_number(gid)
        return self.make_result(0)

    # 设置房间基本信息
    def room_set_info(self, auth, gid, name):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])
        if self.room_check_exist(gid) is False:
            return self.make_result(self.errors["RoomNumber"])
        cursor = self.cursor_get()
        cursor.execute("UPDATE info SET name = %s WHERE gid = %s".replace('%s', self.sql_char), (name, gid))
        self.cursor_finish(cursor)
        return self.make_result(0)

    def room_get_members(self, auth, gid):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])
        if self.room_check_exist(gid) is False:
            return self.make_result(self.errors["RoomNumber"])
        cursor = self.cursor_get()
        cursor.execute("SELECT username FROM members WHERE gid = %s".replace('%s', self.sql_char), (gid, ))
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
        cursor.execute("SELECT name FROM info WHERE gid = %s".replace('%s', self.sql_char), (gid, ))
        name = cursor.fetchall()[0][0]
        cursor.close()
        self.cursor_finish(cursor)
        return name

    # 获取房间信息
    def room_get_info(self, auth, gid):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])
        cursor = self.cursor_get()
        cursor.execute("SELECT name, create_time, member_number, last_post_time "
                       "FROM info WHERE gid = %s".replace('%s', self.sql_char), (gid, ))
        data = cursor.fetchall()[0]
        self.cursor_finish(cursor)

        info = {
            'gid': int(gid), 'name': data[0], 'create_time': data[1],
            'member_number': data[2], 'last_post_time': data[3]
        }
        return self.make_result(0, info=info)

    # 默认：password为空，name和email默认
    def create_user(self, username='Lance', password='', name='Nickname',
                    email='lanceliang2018@163.com'):
        if self.check_in("users", "username", username):
            return self.make_result(self.errors["UserExist"])

        cursor = self.cursor_get()
        last_uid = self.update_last_uid()

        password = hashlib.md5(password.encode()).hexdigest()
        email = email.lower()
        head = get_head(email)
        cursor.execute("INSERT INTO users (uid, username, password, name, email, head) VALUES (%s, %s, %s, %s, %s, %s)".replace('%s', self.sql_char),
                       (last_uid, username, password, name, email, head))

        self.update_last_uid()
        self.cursor_finish(cursor)
        return self.make_result(0)

    # 检查密码是否符合
    def user_check(self, username, password):
        if self.check_in("users", "username", username) is False:
            return False
        cursor = self.cursor_get()
        password = hashlib.md5(password.encode()).hexdigest()
        cursor.execute("SELECT password FROM users WHERE username = %s".replace('%s', self.sql_char), (username, ))
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
            return self.make_result(self.errors["NoUser"])
        cursor = self.cursor_get()
        cursor.execute("SELECT head FROM users WHERE username = %s".replace('%s', self.sql_char), (username, ))
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
            cursor.execute("UPDATE auth SET auth = %s WHERE username = %s".replace('%s', self.sql_char), (auth, username))
        else:
            cursor.execute("INSERT INTO auth (username, auth) VALUES (%s, %s)".replace('%s', self.sql_char), (username, auth))

        self.cursor_finish(cursor)
        head = self.get_head(auth)
        return self.make_result(0, auth=auth, head=head)

    def check_auth(self, auth):
        result = self.check_in("auth", "auth", auth)
        if result is True:
            return True
        return False

    def auth2username(self, auth):
        if self.check_auth(auth) is False:
            return 'No_User'
        cursor = self.cursor_get()
        cursor.execute("SELECT username FROM auth WHERE auth = %s".replace('%s', self.sql_char), (auth,))
        username = cursor.fetchall()[0][0]
        self.cursor_finish(cursor)
        return username

    def get_head(self, auth):
        if self.check_auth(auth) is False:
            return ""
        username = self.auth2username(auth)
        cursor = self.cursor_get()
        cursor.execute("SELECT head FROM users WHERE username = %s".replace('%s', self.sql_char), (username, ))
        head = cursor.fetchall()[0][0]
        self.cursor_finish(cursor)
        return head


    def room_check_in(self, auth, gid):
        # 检验是否在房间内
        username = self.auth2username(auth)
        cursor = self.cursor_get()
        cursor.execute("SELECT username FROM members WHERE username = %s AND gid = %s".replace('%s', self.sql_char), (username, gid))
        data = cursor.fetchall()
        self.cursor_finish(cursor)
        if len(data) == 0:
            return False
        return True

    def room_check_exist(self, gid):
        cursor = self.cursor_get()
        cursor.execute("SELECT gid FROM info WHERE gid = %s".replace('%s', self.sql_char), (gid, ))
        data = cursor.fetchall()
        self.cursor_finish(cursor)
        if len(data) == 0:
            return False
        return True

    def room_get_all(self, auth):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])
        # 列出所有room
        cursor = self.cursor_get()
        cursor.execute("SELECT gid, name FROM info")
        data = cursor.fetchall()
        if len(data) == 0:
            return []
        print(data)
        result = []
        for d in data:
            result.append({"name": d[1], "gid": int(d[0])})
        self.cursor_finish(cursor)
        return self.make_result(0, room_data=result)

    def room_update_active_time(self, gid):
        cursor = self.cursor_get()
        cursor.execute("UPDATE info SET last_post_time = %s WHERE gid = %s".replace('%s', self.sql_char), (int(time.time()), gid))
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
        cursor.execute("INSERT INTO message (mid, gid, username, head, type, text, send_time) "
                       "VALUES (%s, %s, %s, %s, %s, %s, %s)".replace('%s', self.sql_char),
                       (last_mid, gid, username, head, message_type, text, int(time.time())))
        self.cursor_finish(cursor)

        self.room_update_active_time(gid)
        return self.make_result(0)

    # 返回格式：(username, head, type, text)(json)
    def get_message(self, auth, gid, limit=30):
        if self.check_auth(auth) is False:
            return self.make_result(self.errors["Auth"])
        if self.room_check_exist(gid) is False:
            return self.make_result(self.errors["RoomNumber"])
        # if self.room_check_in(auth, gid) is False:
        #     return self.make_result(self.errors["NotIn"])

        cursor = self.cursor_get()
        result = []
        unit_ = {}
        cursor.execute("SELECT username, head, type, text, send_time FROM message "
                       "WHERE gid = %s ORDER BY mid DESC LIMIT %s".replace('%s', self.sql_char),
                       (gid, limit))
        data = cursor.fetchall()
        for d in data:
            unit_['username'], unit_['head'], unit_['type'], unit_['text'], unit_['send_time'] = d
            result.append(copy.deepcopy(unit_))
        self.cursor_finish(cursor)
        return self.make_result(0, message=result)


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


if __name__ == '__main__':
    # db = DataBase()
    # db.db_init()
    # print(db.update_last_mid())
    # print(db.make_result(0, messages={"s": "a"}))

    module_test()

