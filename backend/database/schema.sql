-- Construction cost estimator database schema

CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,  -- concrete, masonry, steel, finishes, insulation, openings, roofing
    unit TEXT NOT NULL,       -- m3, m2, kg, unit, lin_m, ton
    price_gel REAL NOT NULL,
    description TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS labor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade TEXT NOT NULL,      -- mason, carpenter, electrician, plumber, tiler, painter, general
    unit TEXT NOT NULL,       -- day, hour
    price_gel REAL NOT NULL,
    description TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    unit TEXT NOT NULL,       -- day, week, month
    price_gel REAL NOT NULL,
    description TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at TEXT DEFAULT (datetime('now')),
    image_path TEXT,
    estimate_json TEXT,
    message_count INTEGER DEFAULT 0
);
