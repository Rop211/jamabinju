CREATE TABLE IF NOT EXISTS farmers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    contact TEXT NOT NULL,
    medical_history TEXT,
    last_checkup_date TEXT,
    next_checkup_date TEXT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL  -- New column for farmer login
);

CREATE TABLE IF NOT EXISTS doctors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS diagnoses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    farmer_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    disease TEXT NOT NULL,
    recommendations TEXT NOT NULL,
    follow_up_date TEXT,
    FOREIGN KEY (farmer_id) REFERENCES farmers (id),
    FOREIGN KEY (doctor_id) REFERENCES doctors (id)
);