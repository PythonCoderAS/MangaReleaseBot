-- upgrade --
DROP INDEX "idx_mangaentry_source__7efd4c";
CREATE INDEX "idx_mangaentry_source__e7ff2c" ON "mangaentry" ("source_id");
-- downgrade --
DROP INDEX "idx_mangaentry_source__e7ff2c";
CREATE INDEX "idx_mangaentry_source__7efd4c" ON "mangaentry" ("source_id", "item_id");
