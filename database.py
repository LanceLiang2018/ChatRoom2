import sqlite3 as sql
import hashlib
import os
import time
import copy


def get_head(email):
    return 'https://s.gravatar.com/avatar/' + hashlib.md5(email.encode()).hexdigest() + '?s=144'


class DataBase:
    def __init__(self):
        self.file_db_init = "db_init.sql"
        self.file_room_init = "room_init.sql"
        self.dir_data = "data/"
        self.secret = "This program is owned by Lance."

        self.error_preview = "Error."
        self.error = {
            "Error": "%s" % self.error_preview,
            "Auth": "%s Auth Error." % self.error_preview,
            "RoomNumber": "%s Room Error. Room number error." % self.error_preview,
            "NotIn": "%s Room Error. You are not in this group." % self.error_preview,
            "NoUser": "%s No such of user." % self.error_preview,
            "UserExist": "%s User exists." % self.error_preview,
            "Password": "%s Password Error." % self.error_preview,
        }
        self.success = 'Success.'

        self.conn = sql.connect('database.db', check_same_thread=False)

    def cursor_get(self):
        cursor = self.conn.cursor()
        return cursor

    def cursor_finish(self, cursor):
        self.conn.commit()
        cursor.close()

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

    def update_last_uid(self):
        cursor = self.cursor_get()
        last_uid = self.get_last_uid()
        # 更新last_uid
        last_uid = last_uid + 1
        cursor.execute("UPDATE maintain SET last_uid = ? WHERE flag = FLAG", (last_uid, ))
        self.cursor_finish(cursor)
        return last_uid

    def update_last_gid(self):
        cursor = self.cursor_get()
        last_gid = self.get_last_gid()
        # 更新last_gid
        last_gid = last_gid + 1
        cursor.execute("UPDATE maintain SET last_gid = ? WHERE flag = FLAG", (last_gid, ))
        self.cursor_finish(cursor)
        return last_gid

    def check_in(self, table, line, value):
        cursor = self.cursor_get()
        try:
            cursor.execute("SELECT %s FROM %s WHERE %s = \"%s\"" % (line, table, line, value))
        except Exception as e:
            print(e)
            return False
        # cursor.execute("SELECT username FROM users WHERE username = \"Lance\"")
        result = cursor.fetchall()
        # print(len(result))
        self.cursor_finish(cursor)
        if len(result) > 0:
            return True
        return False

    def db_init(self):
        self.conn.close()
        try:
            os.remove('database.db')
        except Exception as e:
            print(e)
        self.conn = sql.connect('database.db', check_same_thread=False)
        cursor = self.cursor_get()
        # Python 的SQLite，一次只能执行一个语句。需要分割。
        with open(self.file_db_init, encoding='utf8') as f:
            string = f.read()
            for s in string.split(';'):
                cursor.execute(s)
        self.cursor_finish(cursor)

    def room_conn_get(self, gid):
        path = "%s%d" % (self.dir_data, gid)
        filename = "%s/room.db" % path
        if not os.path.exists(path):
            return None
        return sql.connect(filename, check_same_thread=False)

    def room_conn_finish(self, conn):
        conn.commit()
        conn.close()

    def room_update_last_mid(self, gid):
        conn = self.room_conn_get(gid)
        cursor = conn.cursor()
        cursor.execute("SELECT last_mid FROM info")
        last_mid = cursor.fetchall()[0][0]
        new_mid = last_mid + 1
        cursor.execute("UPDATE info SET last_mid = ? WHERE last_mid = ?", (new_mid, last_mid))
        self.room_conn_finish(conn)
        return last_mid

    def room_update_number(self, gid):
        conn = self.room_conn_get(gid)
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM members")
        member_number = len(cursor.fetchall()[0])
        cursor.execute("UPDATE info SET member_number = ? WHERE flag = ?", (member_number, "FLAG"))
        self.room_conn_finish(conn)
        # return None

    def room_init(self):
        cursor = self.cursor_get()
        last_gid = self.update_last_gid()

        path = "%s%d" % (self.dir_data, last_gid)
        filename = "%s/room.db" % path
        if not os.path.exists(path):
            os.mkdir(path)

        # 更新目录下的子数据库
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass
        conn = sql.connect(filename)
        c = conn.cursor()
        with open(self.file_room_init, encoding='utf8') as f:
            for s in f.read().split(';'):
                c.execute(s)
        conn.commit()
        conn.close()

        self.cursor_finish(cursor)
        # 返回这次建立的gid
        return last_gid

    # 返回值：创建的房间号。房间号自动递增
    def create_room(self, auth, name='New group'):
        if self.check_auth(auth) is False:
            return self.error["Auth"]

        gid = self.room_init()
        # 让本人加群
        self.room_join_in(auth, gid)

        # # 加入是否在群中的检验
        # cursor = self.cursor_get()
        # username = self.auth2username(auth)
        # cursor.execute("INSERT INTO rooms (username, gid) VALUES (?, ?)", (username, gid))
        # self.cursor_finish(cursor)

        # 设置本群基本信息
        conn = self.room_conn_get(gid)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO info (name, create_time, last_post_time) VALUES '
                       '(?, ?, ?)', (name, time.asctime(), time.asctime()))
        self.room_conn_finish(conn)

        self.room_update_active_time(gid)

        # 返回房间号码
        return gid

    def room_join_in(self, auth, gid):
        # 检查房间存在
        if self.room_check_exist(gid) is False:
            return self.error["RoomNumber"]
        conn = self.room_conn_get(gid)
        cursor = conn.cursor()
        username = self.auth2username(auth)
        cursor.execute("INSERT INTO members (username) VALUES (?)", (username,))
        cursor.close()
        self.room_conn_finish(conn)
        self.room_update_number(gid)
        return self.success

    # 设置房间基本信息
    def room_set_info(self, auth, gid, name):
        if self.check_auth(auth) is False:
            return self.error["Auth"]
        if self.room_check_exist(gid) is False:
            return self.error["RoomNumber"]
        conn = self.room_conn_get(gid)
        cursor = conn.cursor()
        cursor.execute("UPDATE info SET name = ? WHERE flag = ?", (name, "FLAG"))
        cursor.close()
        self.room_conn_finish(conn)
        return self.success

    # 房间号→Name
    def number2name(self, gid):
        conn = self.room_conn_get(gid)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM info WHERE flag = ?", ("FLAG", ))
        name = cursor.fetchall()[0][0]
        cursor.close()
        self.room_conn_finish(conn)
        return name

    # 获取房间信息
    def room_get_info(self, auth, gid):
        if self.check_auth(auth) is False:
            return self.error["Auth"]
        conn = self.room_conn_get(gid)
        cursor = conn.cursor()
        cursor.execute("SELECT gid, name, create_time, member_number, last_post_time "
                       "FROM info WHERE flag = ?", ("FLAG", ))
        data = cursor.fetchall()[0]
        cursor.close()

        info = {
            'gid': data[0], 'name': data[1], 'create_time': data[2],
            'member_number': data[3], 'last_post_time': data[4]
        }
        self.room_conn_finish(conn)
        return info

    # 默认：password为空，name和email默认
    def create_user(self, username='Lance', password='', name='Nickname',
                    email='lanceliang2018@163.com'):
        if self.check_in("users", "username", username):
            return self.error["UserExist"]

        cursor = self.cursor_get()
        last_uid = self.update_last_uid()

        password = hashlib.md5(password.encode()).hexdigest()
        email = email.lower()
        head = get_head(email)
        cursor.execute("INSERT INTO users (uid, username, password, name, email, head) VALUES (?, ?, ?, ?, ?, ?)",
                       (last_uid, username, password, name, email, head))

        self.update_last_uid()
        self.cursor_finish(cursor)
        return self.success

    # 检查密码是否符合
    def user_check(self, username, password):
        if self.check_in("users", "username", username) is False:
            return False
        cursor = self.cursor_get()
        password = hashlib.md5(password.encode()).hexdigest()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username, ))
        storage = cursor.fetchall()[0][0]
        # print(storage)
        self.cursor_finish(cursor)
        if storage == password:
            return True
        return False

    def user_get_head(self, username):
        if self.check_in("users", "username", username) is False:
            return self.error["NoUser"]
        cursor = self.cursor_get()
        cursor.execute("SELECT head FROM users WHERE username = ?", (username, ))
        head = cursor.fetchall()[0][0]
        self.cursor_finish(cursor)
        return head

    # 创建鉴权避免麻烦。鉴权格式：MD5(username, secret, time)
    def create_auth(self, username, password):
        cursor = self.cursor_get()
        if not self.user_check(username, password):
            return self.error["Password"]
        string = "%s %s %s" % (username, self.secret, str(time.time()))
        auth = hashlib.md5(string.encode()).hexdigest()

        if self.check_in("auth", "username", username):
            cursor.execute("UPDATE auth SET auth = ? WHERE username = ?", (auth, username))
        else:
            cursor.execute("INSERT INTO auth (username, auth) VALUES (?, ?)", (username, auth))

        self.cursor_finish(cursor)
        return auth

    def check_auth(self, auth):
        result = self.check_in("auth", "auth", auth)
        if result is True:
            return True
        return False

    def auth2username(self, auth):
        if self.check_auth(auth) is False:
            return 'No_User'
        cursor = self.cursor_get()
        cursor.execute("SELECT username FROM auth WHERE auth = ?", (auth, ))
        username = cursor.fetchall()[0][0]
        self.cursor_finish(cursor)
        return username

    def room_check_in(self, auth, gid):
        # 检验是否在房间内
        username = self.auth2username(auth)
        conn = self.room_conn_get(gid)
        if conn is None:
            return False
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM members WHERE username = ?", (username,))
        data = cursor.fetchall()
        cursor.close()
        self.room_conn_finish(conn)
        if len(data) == 0:
            return False
        return True

    def room_check_exist(self, gid):
        conn = self.room_conn_get(gid)
        if conn is None:
            return False
        return True

    def room_get_all(self, auth):
        if self.check_auth(auth) is False:
            return self.error["Auth"]
        # 列出所有room
        li = os.listdir('./data/')
        li = list(map(lambda x: int(x), li))
        names = list(map(self.number2name, li))
        result = []
        for i in range(len(li)):
            result.append({"name": names[i], "gid": li[i]})
        return result

    def room_update_active_time(self, gid):
        conn = self.room_conn_get(gid)
        cursor = conn.cursor()
        cursor.execute("UPDATE info SET last_post_time = ? WHERE flag = ?", (time.asctime(), "FLAG"))
        self.room_conn_finish(conn)

    def send_message(self, auth, gid, text, message_type='text'):
        if self.check_auth(auth) is False:
            return self.error["Auth"]
        if self.room_check_exist(gid) is False:
            return self.error["RoomNumber"]
        if self.room_check_in(auth, gid) is False:
            return self.error["NotIn"]

        username = self.auth2username(auth)

        head = self.user_get_head(username)
        last_mid = self.room_update_last_mid(gid)

        if self.room_check_exist(gid) is False:
            return self.error["RoomNumber"]
        conn = self.room_conn_get(gid)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO message (mid, username, head, type, text) VALUES (?, ?, ?, ?, ?)",
                       (last_mid, username, head, message_type, text))
        cursor.close()
        self.room_conn_finish(conn)

        self.room_update_active_time(gid)
        return self.success

    # 返回格式：(username, head, type, text)(json)
    def get_message(self, auth, gid, limit=30):
        if self.check_auth(auth) is False:
            return self.error["Auth"]
        if self.room_check_exist(gid) is False:
            return self.error["RoomNumber"]
        if self.room_check_in(auth, gid) is False:
            return self.error["NotIn"]

        conn = self.room_conn_get(gid)
        cursor = conn.cursor()
        result = []
        unit_ = {}
        cursor.execute("SELECT username, head, type, text FROM message ORDER BY mid DESC LIMIT ?", (limit, ))
        data = cursor.fetchall()
        for d in data:
            unit_['username'] = d[0]
            unit_['head'] = d[1]
            unit_['type'] = d[2]
            unit_['text'] = d[3]
            result.append(copy.deepcopy(unit_))
        cursor.close()
        self.room_conn_finish(conn)
        return result


if __name__ == '__main__':
    db = DataBase()

    db.db_init()
    exit()
    db.create_user("Lance", "1352040930lxr")
    db.create_user("Lance2", "1352040930lxr")
    # print(db.check_in("users", "username", "Lance"))

    _au = db.create_auth("Lance", "1352040930lxr")
    print(db.check_auth(_au))

    # name = db.auth2username(_au)
    # print(name)

    print(_au)

    _gid = db.create_room(_au, "TEST GROUP")
    print(type(_gid), _gid)
    print(db.send_message(_au, _gid, "Test message"))
    print(db.send_message(_au, _gid, "Sent by Lance"))
    print(db.get_message(_au, _gid))

    _au2 = db.create_auth("Lance2", "1352040930lxr")
    print(db.send_message(_au2, _gid, "Sent by Lance2"))
    res = db.room_join_in(_au2, _gid)
    print(db.send_message(_au2, _gid, "Sent by Lance2"))
    print(res)

    print(db.get_message(_au, _gid))

    print(db.room_get_all(_au))


