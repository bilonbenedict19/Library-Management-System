from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this in production!

def get_db_connection():
    conn = sqlite3.connect('movies.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- Authentication Routes ---

@app.route('/login', methods=['POST'])
def login():
    username = request.form['login_username']
    password = request.form['login_password']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        flash('Logged in successfully!')
    else:
        flash('Invalid username or password.')
    return redirect(url_for('index'))

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['signup_username']
    password = request.form['signup_password']
    conn = get_db_connection()
    existing = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if existing:
        flash('Username already exists.')
        conn.close()
        return redirect(url_for('index'))
    password_hash = generate_password_hash(password)
    conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password_hash))
    conn.commit()
    conn.close()
    flash('Account created! Please log in.')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.')
    return redirect(url_for('index'))

# --- Admin Decorator ---

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Admin access required.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Admin Routes ---

@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    movies = conn.execute('SELECT * FROM movies').fetchall()
    showtimes = conn.execute('SELECT * FROM showtimes').fetchall()
    conn.close()
    return render_template('admin_dashboard.html', movies=movies, showtimes=showtimes)

@app.route('/admin/add_movie', methods=['GET', 'POST'])
@admin_required
def add_movie():
    if request.method == 'POST':
        title = request.form['title']
        price = request.form['price']
        conn = get_db_connection()
        conn.execute('INSERT INTO movies (title, price) VALUES (?, ?)', (title, price))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_dashboard'))
    return render_template('add_movie.html')

@app.route('/admin/edit_movie/<int:movie_id>', methods=['GET', 'POST'])
@admin_required
def edit_movie(movie_id):
    conn = get_db_connection()
    movie = conn.execute('SELECT * FROM movies WHERE id = ?', (movie_id,)).fetchone()
    if request.method == 'POST':
        title = request.form['title']
        price = request.form['price']
        conn.execute('UPDATE movies SET title = ?, price = ? WHERE id = ?', (title, price, movie_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_dashboard'))
    conn.close()
    return render_template('edit_movie.html', movie=movie)

@app.route('/admin/delete_movie/<int:movie_id>')
@admin_required
def delete_movie(movie_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM movies WHERE id = ?', (movie_id,))
    conn.execute('DELETE FROM showtimes WHERE movie_id = ?', (movie_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_showtime/<int:movie_id>', methods=['GET', 'POST'])
@admin_required
def add_showtime(movie_id):
    if request.method == 'POST':
        time = request.form['time']
        conn = get_db_connection()
        conn.execute('INSERT INTO showtimes (movie_id, time) VALUES (?, ?)', (movie_id, time))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_dashboard'))
    return render_template('add_showtime.html', movie_id=movie_id)

@app.route('/admin/delete_showtime/<int:showtime_id>')
@admin_required
def delete_showtime(showtime_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM showtimes WHERE id = ?', (showtime_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

# --- Main User Routes ---

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
    selected_showtime_id = request.form.get('showtime') if request.method == 'POST' else None
    available_seats = []
    if selected_showtime_id:
        available_seats = conn.execute(
            'SELECT * FROM seats WHERE showtime_id = ? AND is_booked = 0', (selected_showtime_id,)
        ).fetchall()
    conn.close()
    if request.method == 'POST':
        showtime_id = request.form['showtime']
        tickets = int(request.form['tickets'])
        name = request.form['name']
        card_number = request.form['card_number']
        card_name = request.form['card_name']
        selected_seats = request.form.getlist('seats')
        paid = 1 if card_number and card_name else 0
        user_id = session.get('user_id')
        if len(selected_seats) != tickets:
            flash('Number of selected seats must match number of tickets.')
            return redirect(request.url)
        conn = get_db_connection()
        # Insert booking
        cur = conn.cursor()
        cur.execute('INSERT INTO bookings (movie_id, showtime_id, tickets, name, user_id, paid) VALUES (?, ?, ?, ?, ?, ?)',
                    (movie_id, showtime_id, tickets, name, user_id, paid))
        booking_id = cur.lastrowid
        # Mark seats as booked
        for seat in selected_seats:
            cur.execute('UPDATE seats SET is_booked = 1, booking_id = ? WHERE showtime_id = ? AND seat_number = ?',
                        (booking_id, showtime_id, seat))
        conn.commit()
        conn.close()
        return render_template('confirmation.html', movie=movie, showtime_id=showtime_id, tickets=tickets, name=name, paid=paid, seats=selected_seats)
    return render_template('book.html', movie=movie, showtimes=showtimes, available_seats=available_seats)

@app.route('/cancel_booking/<int:booking_id>')
def cancel_booking(booking_id):
    conn = get_db_connection()
    # Free up seats
    conn.execute('UPDATE seats SET is_booked = 0, booking_id = NULL WHERE booking_id = ?', (booking_id,))
    # Delete booking
    conn.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))
    conn.commit()
    conn.close()
    flash('Booking cancelled and seats released.')
    return redirect(url_for('index'))

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
