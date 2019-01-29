CREATE TABLE users (
    uid INT,
    username VARCHAR(64),
    password VARCHAR(128),
    email VARCHAR(512),
    head VARCHAR(2048),
    motto VARCHAR(8192),
    rooms VARCHAR(8192),
    user_type VARCHAR(32),
    status INT
);

CREATE TABLE files (
    username VARCHAR(64),
    url VARCHAR(2048),
    filename VARCHAR(2048)
);

CREATE TABLE new_messages (
    username VARCHAR(64),
    gid INT,
    latest_mid INT
);

CREATE TABLE maintain (
    last_uid INT,
    last_gid INT,
    last_mid INT,
    flag VARCHAR(32)
);

CREATE TABLE auth (
    username VARCHAR(512),
    auth VARCHAR(128)
);

INSERT INTO maintain (last_uid, last_gid, last_mid, flag) VALUES (0, 0, 0, 'FLAG');

CREATE TABLE message (
    uid INT,
    mid INT,
    gid INT,
    username VARCHAR(512),
    head VARCHAR(2048),
    type VARCHAR(32),
    text VARCHAR(8192),
    send_time INT
);

CREATE TABLE info (
    gid INT,
    room_type VARCHAR(32),
    name VARCHAR(512),
    head VARCHAR(2048),
    create_time INT,
    member_number INT,
    last_post_time INT
);

CREATE TABLE members (
    gid INT,
    username VARCHAR(256)
);

CREATE TABLE friends (
    username VARCHAR(64),
    friend VARCHAR(64),
    gid INT
);