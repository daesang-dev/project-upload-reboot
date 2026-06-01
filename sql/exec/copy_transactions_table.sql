PRAGMA foreign_keys = ON;

INSERT INTO transactions
SELECT * FROM stg_transactions;