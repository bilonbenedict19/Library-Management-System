import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('movies.db')
c = conn.cursor()

# Create tables
c.execute('''
CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    price INTEGER NOT NULL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS showtimes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id INTEGER,
    time TEXT,
    FOREIGN KEY(movie_id) REFERENCES movies(id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'user'
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

# Insert sample data
c.execute("INSERT INTO movies (title, price) VALUES ('Inception', 10)")
c.execute("INSERT INTO movies (title, price) VALUES ('The Matrix', 12)")
c.execute("INSERT INTO movies (title, price) VALUES ('Interstellar', 15)")

c.execute("INSERT INTO showtimes (movie_id, time) VALUES (1, '1:00 PM')")
c.execute("INSERT INTO showtimes (movie_id, time) VALUES (1, '4:00 PM')")
c.execute("INSERT INTO showtimes (movie_id, time) VALUES (1, '7:00 PM')")
c.execute("INSERT INTO showtimes (movie_id, time) VALUES (2, '2:00 PM')")
c.execute("INSERT INTO showtimes (movie_id, time) VALUES (2, '5:00 PM')")
c.execute("INSERT INTO showtimes (movie_id, time) VALUES (2, '8:00 PM')")
c.execute("INSERT INTO showtimes (movie_id, time) VALUES (3, '12:00 PM')")
c.execute("INSERT INTO showtimes (movie_id, time) VALUES (3, '3:00 PM')")
c.execute("INSERT INTO showtimes (movie_id, time) VALUES (3, '6:00 PM')")

# 5x5 seat grid: A1–A5, B1–B5, ..., E1–E5 for each showtime
showtime_ids = [row[0] for row in c.execute('SELECT id FROM showtimes').fetchall()]
seat_rows = ['A', 'B', 'C', 'D', 'E']
seat_numbers = [str(i) for i in range(1, 6)]
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
