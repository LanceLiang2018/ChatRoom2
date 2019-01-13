CREATE TABLE users (
    -- 用户id号。
    uid INT,
    -- 最重要的用户名以及密码。密码按照MD5储存。
    -- 校验密码只校验MD5。
    username VARCHAR(64),
    password VARCHAR(128),
    -- 昵称
    name VARCHAR(512),
    email VARCHAR(512),
    -- 头像
    head VARCHAR(2048),
    -- 拥有的群组，是一个字符串，以‘ ’为分界
    --groups VARCHAR(2048),
    motto VARCHAR(8192),
    -- 用户状态：在线(Online(1))或者下线(Offline(0))
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

-- 维护用表
CREATE TABLE maintain (
    -- 最新一个用户id和群组id，消息id。
    last_uid INT,
    last_gid INT,
    last_mid INT,
    -- 用于识别该列
    flag VARCHAR(32)
);

-- 鉴权认证储存
CREATE TABLE auth (
    username VARCHAR(512),
    auth VARCHAR(128)
);

-- 初始化维护
INSERT INTO maintain (last_uid, last_gid, last_mid, flag) VALUES (0, 0, 0, 'FLAG');

-- 消息
CREATE TABLE message (
    -- 发送者，头像（展示变化用）
    uid INT,
    -- 消息id（排序用）
    mid INT,
    -- 重要：gid，表明所属以便SELECT
    gid INT,
    username VARCHAR(512),
    head VARCHAR(2048),
    -- 类型：{'text', 'image', 'file'}
    type VARCHAR(32),
    -- 不一定是文本内容。如果是image或者file，将包含一个链接。
    text VARCHAR(10240),
    send_time INT
);

-- 群基本信息
CREATE TABLE info (
    -- Group id
    gid INT,
    -- Group name
    name VARCHAR(512),
    -- 创建时间（time.asctime()）varchar
    create_time INT,
    -- 目前成员个数
    member_number INT,
    -- 上次活跃时间
    last_post_time INT
);

-- 成员-group关联列表（加群记录）
CREATE TABLE members (
    gid INT,
    username VARCHAR(256)
);