-- options table
CREATE TABLE IF NOT EXISTS options (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL UNIQUE
);

-- pre-populate if empty (optional)
INSERT INTO options (text)
SELECT * FROM (VALUES
    ('')
) AS t(text)
WHERE NOT EXISTS (SELECT 1 FROM options);
