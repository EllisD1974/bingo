-- options table
CREATE TABLE IF NOT EXISTS options (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL UNIQUE
);

-- pre-populate if empty (optional)
INSERT INTO options (text)
SELECT * FROM (VALUES
    ('Option 1'),
    ('Option 2'),
    ('Option 3'),
    ('Option 4'),
    ('Option 5'),
    ('Option 6'),
    ('Option 7'),
    ('Option 8'),
    ('Option 9'),
    ('Option 10'),
    ('Option 11'),
    ('Option 12'),
    ('Option 13'),
    ('Option 14'),
    ('Option 15'),
    ('Option 16'),
    ('Option 17'),
    ('Option 18'),
    ('Option 19'),
    ('Option 20'),
    ('Option 21'),
    ('Option 22'),
    ('Option 23'),
    ('Option 24'),
    ('Option 25')
) AS t(text)
WHERE NOT EXISTS (SELECT 1 FROM options);
