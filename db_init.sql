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
    head VARCHAR(512),
    -- 最新消息
    latest_mid INT,
    -- 用户状态：在线(Online(1))或者下线(Offline(0))
    status INT
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
    head VARCHAR(128),
    -- 类型：{'text', 'image', 'file'}
    type VARCHAR(32),
    -- 不一定是文本内容。如果是image或者file，将包含一个链接。
    text VARCHAR(8192),
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
--INSERT INTO info (gid, name, create_time, member_number, last_post_time) VALUES (0, 'New group', '', 0, '')
--INSERT INTO message (gid, uid, username, head, type, text) VALUES (0, 0, 'Administrator', 'https://s.gravatar.com/avatar/544b5009873b27f5e0aa6dd8ffc1d3d8?s=512', 'text', 'Welcome to this group!')
);