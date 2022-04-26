-- upgrade --
ALTER TABLE "mangaentry" ADD "paused" TIMESTAMPTZ;
-- downgrade --
ALTER TABLE "mangaentry" DROP COLUMN "paused";
