-- upgrade --
ALTER TABLE "mangaentry" ADD "deleted" TIMESTAMPTZ;
CREATE TABLE IF NOT EXISTS "threaddata" (
    "thread_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "entry_id" INT NOT NULL REFERENCES "mangaentry" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_threaddata_entry_i_497ad6" ON "threaddata" ("entry_id");-- downgrade --
ALTER TABLE "mangaentry" DROP COLUMN "deleted";
DROP TABLE IF EXISTS "threaddata";
