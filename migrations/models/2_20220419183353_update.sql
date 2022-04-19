-- upgrade --
ALTER TABLE "mangaentry" ADD "private_thread" BOOL NOT NULL  DEFAULT False;
-- downgrade --
ALTER TABLE "mangaentry" DROP COLUMN "private_thread";
