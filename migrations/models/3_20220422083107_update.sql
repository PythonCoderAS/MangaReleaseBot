-- upgrade --
CREATE TABLE IF NOT EXISTS "metadata" (
    "key" VARCHAR(256) NOT NULL  PRIMARY KEY,
    "value" JSONB NOT NULL
);
-- downgrade --
DROP TABLE IF EXISTS "metadata";
