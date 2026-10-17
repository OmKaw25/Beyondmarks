ALTER TABLE transfer_tasks ADD COLUMN phase VARCHAR(20) NOT NULL DEFAULT 'transfer';
ALTER TABLE transfer_tasks ADD COLUMN interaction_json JSONB NOT NULL DEFAULT '{}';
ALTER TABLE independent_tasks ADD COLUMN phase VARCHAR(20) NOT NULL DEFAULT 'independent';
ALTER TABLE independent_tasks ADD COLUMN interaction_json JSONB NOT NULL DEFAULT '{}';
