from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('movies.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    movies = conn.execute('SELECT * FROM movies').fetchall()
    showtimes = conn.execute('SELECT * FROM showtimes').fetchall()
    conn.close()
    # Group showtimes by movie
    showtimes_by_movie = {}
    for show in showtimes:
        showtimes_by_movie.setdefault(show['movie_id'], []).append(show)
    return render_template('index.html', movies=movies, showtimes_by_movie=showtimes_by_movie)

@app.route('/book/<int:movie_id>', methods=['GET', 'POST'])
def book(movie_id):
    conn = get_db_connection()
    movie = conn.execute('SELECT * FROM movies WHERE id = ?', (movie_id,)).fetchone()
    showtimes = conn.execute('SELECT * FROM showtimes WHERE movie_id = ?', (movie_id,)).fetchall()
    conn.close()
    if request.method == 'POST':
        showtime_id = request.form['showtime']
        tickets = int(request.form['tickets'])
        name = request.form['name']
        conn = get_db_connection()
        conn.execute('INSERT INTO bookings (movie_id, showtime_id, tickets, name) VALUES (?, ?, ?, ?)',
                     (movie_id, showtime_id, tickets, name))
        conn.commit()
        conn.close()
        return render_template('confirmation.html', movie=movie, showtime_id=showtime_id, tickets=tickets, name=name)
    return render_template('book.html', movie=movie, showtimes=showtimes)

@app.route('/showtime/<int:showtime_id>')
def get_showtime(showtime_id):
    conn = get_db_connection()
    showtime = conn.execute('SELECT * FROM showtimes WHERE id = ?', (showtime_id,)).fetchone()
    conn.close()
    return showtime['time'] if showtime else ''

@app.context_processor
def utility_processor():
    def get_showtime_time(showtime_id):
        conn = get_db_connection()
        showtime = conn.execute('SELECT * FROM showtimes WHERE id = ?', (showtime_id,)).fetchone()
        conn.close()
        return showtime['time'] if showtime else ''
    return dict(get_showtime_time=get_showtime_time)

if __name__ == '__main__':
    app.run(debug=True)
