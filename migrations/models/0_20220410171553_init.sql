-- upgrade --
CREATE TABLE IF NOT EXISTS "mangaentry" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "guild_id" BIGINT NOT NULL,
    "channel_id" BIGINT NOT NULL,
    "creator_id" BIGINT NOT NULL,
    "item_id" VARCHAR(256) NOT NULL,
    "source_id" VARCHAR(20) NOT NULL,
    "extra_config" JSONB,
    "message_channel_first" BOOL NOT NULL  DEFAULT False
);
CREATE TABLE IF NOT EXISTS "ping" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "mention_id" BIGINT NOT NULL,
    "is_role" BOOL NOT NULL  DEFAULT False,
    "item_id" BIGINT NOT NULL REFERENCES "mangaentry" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
