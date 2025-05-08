# create_db.py
import sqlite3

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
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id INTEGER,
    showtime_id INTEGER,
    tickets INTEGER,
    name TEXT,
    FOREIGN KEY(movie_id) REFERENCES movies(id),
    FOREIGN KEY(showtime_id) REFERENCES showtimes(id)
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

conn.commit()
conn.close()
