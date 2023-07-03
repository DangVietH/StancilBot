CREATE TABLE IF NOT EXISTS leveling (
    id SERIAL PRIMARY KEY,
    guild BIGINT,
    member BIGINT,
    level INTEGER,
    xp INTEGER,
    card_bg TEXT
);


CREATE TABLE IF NOT EXISTS level_config (
    guild BIGINT PRIMARY KEY,
    xp INTEGER,
    lvl_up_text TEXT,
    lvl_up_channel BIGINT,
    ignore_channel BIGINT ARRAY,
    role_level BIGINT ARRAY,
    role_id BIGINT ARRAY
);



CREATE TABLE IF NOT EXISTS remindme (
    id BIGINT PRIMARY KEY,
    users BIGINT,
    end_time TIMESTAMP,
    reminder TEXT
);


CREATE TABLE IF NOT EXISTS server (
    id BIGINT PRIMARY KEY,
    prefix TEXT,
    mute_role BIGINT,
    config_role BIGINT,
    mod_role BIGINT,
    ban_message TEXT
);


CREATE TABLE IF NOT EXISTS tag (
    id SERIAL PRIMARY KEY,
    name TEXT,
    content TEXT,
    owner BIGINT,
    guild BIGINT,
    stats INTEGER,
    create_at TIMESTAMP
);


CREATE TABLE IF NOT EXISTS starboard_config (
    guild BIGINT PRIMARY KEY,
    sb_channel BIGINT,
    amount INTEGER,
    emoji TEXT,
    self_star BOOL,
    lock BOOL,
    nsfw BOOL,
    ignore_channel BIGINT ARRAY
);

CREATE TABLE IF NOT EXISTS starboard_message (
    message BIGINT PRIMARY KEY,
    channel BIGINT,
    sb_message BIGINT,
    guild BIGINT,
    amount INTEGER
);

CREATE TABLE IF NOT EXISTS role (
    message BIGINT PRIMARY KEY,
    guild BIGINT,
    button BOOL,
    embed_title TEXT,
    embed_desc TEXT,
    emojis TEXT ARRAY,
    roles BIGINT ARRAY,
    button_msg TEXT ARRAY
);