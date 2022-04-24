-- upgrade --
DROP INDEX "idx_mangaentry_source__e7ff2c";
CREATE INDEX "idx_mangaentry_guild_i_cc93cb" ON "mangaentry" ("guild_id", "channel_id");
CREATE INDEX "idx_mangaentry_source__7efd4c" ON "mangaentry" ("source_id", "item_id");
-- downgrade --
DROP INDEX "idx_mangaentry_source__7efd4c";
DROP INDEX "idx_mangaentry_guild_i_cc93cb";
CREATE INDEX "idx_mangaentry_source__e7ff2c" ON "mangaentry" ("source_id");
