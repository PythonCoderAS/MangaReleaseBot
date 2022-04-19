-- upgrade --
ALTER TABLE "mangaentry" ALTER COLUMN "id" TYPE INT USING "id"::INT;
ALTER TABLE "ping" ALTER COLUMN "item_id" TYPE INT USING "item_id"::INT;
CREATE INDEX "idx_mangaentry_source__e7ff2c" ON "mangaentry" ("source_id");
CREATE INDEX "idx_ping_item_id_2338bf" ON "ping" ("item_id");
CREATE INDEX "idx_ping_mention_1ac96c" ON "ping" ("mention_id");
-- downgrade --
DROP INDEX "idx_mangaentry_source__e7ff2c";
DROP INDEX "idx_ping_mention_1ac96c";
DROP INDEX "idx_ping_item_id_2338bf";
ALTER TABLE "mangaentry" ALTER COLUMN "id" TYPE BIGINT USING "id"::BIGINT;
ALTER TABLE "ping" ALTER COLUMN "item_id" TYPE BIGINT USING "item_id"::BIGINT;
