-- PostgreSQL 16.2
-- This file is used to create the initial database schema
START TRANSACTION;

-- Create the Shard Metadata Table
CREATE TABLE IF NOT EXISTS shardT (
	stud_id_low INTEGER PRIMARY KEY,
	shard_id TEXT NOT NULL UNIQUE,
	shard_size INTEGER NOT NULL,
	valid_at INTEGER NOT NULL DEFAULT 0
);

COMMIT TRANSACTION;
