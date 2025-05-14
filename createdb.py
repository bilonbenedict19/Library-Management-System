import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('movies.db')
c = conn.cursor()



# Create tables
c.execute('''
CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    price INTEGER NOT NULL,
    status TEXT DEFAULT 'now_showing'
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS showtimes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id INTEGER,
    time TEXT,
    date TEXT,
    cinema TEXT,
    FOREIGN KEY(movie_id) REFERENCES movies(id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    balance INTEGER DEFAULT 0
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id INTEGER,
    showtime_id INTEGER,
    tickets INTEGER,
    name TEXT,
    user_id INTEGER,
    paid INTEGER DEFAULT 0,
    FOREIGN KEY(movie_id) REFERENCES movies(id),
    FOREIGN KEY(showtime_id) REFERENCES showtimes(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS seats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    showtime_id INTEGER,
    seat_number TEXT,
    is_booked INTEGER DEFAULT 0,
    booking_id INTEGER,
    FOREIGN KEY(showtime_id) REFERENCES showtimes(id),
    FOREIGN KEY(booking_id) REFERENCES bookings(id)
)
''')

# --- MIGRATION LOGIC FOR NEW COLUMNS ---
def add_column_if_not_exists(table, column, coltype):
    c.execute(f"PRAGMA table_info({table})")
    columns = [info[1] for info in c.fetchall()]
    if column not in columns:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")

# Add 'rating' and 'poster_url' to movies if missing
add_column_if_not_exists('movies', 'rating', 'TEXT')
add_column_if_not_exists('movies', 'poster_url', 'TEXT')

# Add 'date' and 'cinema' to showtimes if missing
add_column_if_not_exists('showtimes', 'date', 'TEXT')
add_column_if_not_exists('showtimes', 'cinema', 'TEXT')

# --- END MIGRATION LOGIC ---

# Insert sample data
c.execute("INSERT INTO movies (title, price, rating, poster_url) VALUES ('Inception', 10, 'PG-13', 'https://link-to-inception-poster.jpg')")
c.execute("INSERT INTO movies (title, price, rating, poster_url) VALUES ('The Matrix', 12, 'R', 'https://link-to-matrix-poster.jpg')")
c.execute("INSERT INTO movies (title, price, rating, poster_url) VALUES ('Interstellar', 15, 'PG', 'https://link-to-interstellar-poster.jpg')")

# Insert sample showtimes with date and cinema
c.execute("INSERT INTO showtimes (movie_id, time, date, cinema) VALUES (1, '1:00 PM', '2025-05-22', 'Cinema 1')")
c.execute("INSERT INTO showtimes (movie_id, time, date, cinema) VALUES (1, '4:00 PM', '2025-05-22', 'Cinema 1')")
c.execute("INSERT INTO showtimes (movie_id, time, date, cinema) VALUES (1, '7:00 PM', '2025-05-22', 'Cinema 2')")
c.execute("INSERT INTO showtimes (movie_id, time, date, cinema) VALUES (2, '2:00 PM', '2025-05-23', 'Cinema 1')")
c.execute("INSERT INTO showtimes (movie_id, time, date, cinema) VALUES (2, '5:00 PM', '2025-05-23', 'Cinema 2')")
c.execute("INSERT INTO showtimes (movie_id, time, date, cinema) VALUES (2, '8:00 PM', '2025-05-24', 'Cinema 1')")
c.execute("INSERT INTO showtimes (movie_id, time, date, cinema) VALUES (3, '12:00 PM', '2025-05-24', 'Cinema 2')")
c.execute("INSERT INTO showtimes (movie_id, time, date, cinema) VALUES (3, '3:00 PM', '2025-05-25', 'Cinema 1')")
c.execute("INSERT INTO showtimes (movie_id, time, date, cinema) VALUES (3, '6:00 PM', '2025-05-25', 'Cinema 2')")

# 10x5 seat grid: A1–A10, B1–B10, ..., E1–E10 for each showtime
showtime_ids = [row[0] for row in c.execute('SELECT id FROM showtimes').fetchall()]
seat_rows = ['A', 'B', 'C', 'D', 'E']
seat_numbers = [str(i) for i in range(1, 11)]  # 1 to 10
for showtime_id in showtime_ids:
    for row in seat_rows:
        for num in seat_numbers:
            seat = f"{row}{num}"
            c.execute("INSERT INTO seats (showtime_id, seat_number) VALUES (?, ?)", (showtime_id, seat))

# Insert a sample admin user (username: admin, password: admin, role: admin) with hashed password
admin_password_hash = generate_password_hash('admin')
c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', admin_password_hash, 'admin'))

conn.commit()
conn.close()
