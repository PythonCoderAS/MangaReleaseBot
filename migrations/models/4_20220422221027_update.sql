-- upgrade --
ALTER TABLE "mangaentry" ALTER COLUMN "item_id" TYPE VARCHAR(1024) USING "item_id"::VARCHAR(1024);
-- downgrade --
ALTER TABLE "mangaentry" ALTER COLUMN "item_id" TYPE VARCHAR(256) USING "item_id"::VARCHAR(256);
