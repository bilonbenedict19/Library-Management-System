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

# --- MIGRATION: Add 'rating' column to movies if it doesn't exist ---
conn = sqlite3.connect('movies.db')
c = conn.cursor()
columns = [row[1] for row in c.execute("PRAGMA table_info(movies)").fetchall()]
if 'rating' not in columns:
    c.execute("ALTER TABLE movies ADD COLUMN rating TEXT DEFAULT 'G'")
conn.commit()
conn.close()

# --- MIGRATION: Add 'poster_url' column to movies if it doesn't exist ---
conn = sqlite3.connect('movies.db')
c = conn.cursor()
columns = [row[1] for row in c.execute("PRAGMA table_info(movies)").fetchall()]
if 'poster_url' not in columns:
    c.execute("ALTER TABLE movies ADD COLUMN poster_url TEXT")
conn.commit()
conn.close()

# --- MIGRATION: Add 'release_date' column to movies if it doesn't exist ---
conn = sqlite3.connect('movies.db')
c = conn.cursor()
columns = [row[1] for row in c.execute("PRAGMA table_info(movies)").fetchall()]
if 'release_date' not in columns:
    c.execute("ALTER TABLE movies ADD COLUMN release_date TEXT")
conn.commit()
conn.close()

# --- Authentication Routes ---

@app.route('/login', methods=['POST'])
def login():
    username = request.form['login_username']
    password = request.form['login_password']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    next_page = request.form.get('next') or request.args.get('next') or url_for('index')
    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        flash('Logged in successfully!')
        if user['role'] == 'admin' and (not next_page or next_page == url_for('index')):
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(next_page)
    else:
        flash('Invalid username or password.')
        return redirect(next_page)

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['signup_username']
    password = request.form['signup_password']
    conn = get_db_connection()
    existing = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    next_page = request.form.get('next') or request.args.get('next') or url_for('index')
    if existing:
        flash('Username already exists.')
        conn.close()
        return redirect(next_page)
    password_hash = generate_password_hash(password)
    conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password_hash))
    conn.commit()
    conn.close()
    flash('Account created! Please log in.')
    return redirect(next_page)

@app.route('/logout', methods=['POST'])
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
        status = request.form.get('status', 'now_showing')
        rating = request.form.get('rating', 'G')
        poster_url = request.form.get('poster_url', '')
        conn = get_db_connection()
        conn.execute('INSERT INTO movies (title, price, status, rating, poster_url) VALUES (?, ?, ?, ?, ?)', (title, price, status, rating, poster_url))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_dashboard'))
    return render_template('add_movie.html')

@app.route('/admin/edit_movie/<int:movie_id>', methods=['GET', 'POST'])
@admin_required
def edit_movie(movie_id):
    conn = get_db_connection()
    movie = conn.execute('SELECT * FROM movies WHERE id = ?', (movie_id,)).fetchone()
    if not movie:
        conn.close()
        flash('Movie not found.')
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        title = request.form['title']
        price = request.form['price']
        status = request.form.get('status', 'now_showing')
        rating = request.form.get('rating', 'G')
        poster_url = request.form.get('poster_url', '')
        release_date = request.form.get('release_date', movie['release_date'] if 'release_date' in movie.keys() else None)
        conn.execute('UPDATE movies SET title = ?, price = ?, status = ?, rating = ?, poster_url = ?, release_date = ? WHERE id = ?', (title, price, status, rating, poster_url, release_date, movie_id))
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
        # For demo: add date and cinema fields
        date = request.form.get('date', '2025-05-22')
        cinema = request.form.get('cinema', 'Cinema 1')
        conn = get_db_connection()
        conn.execute('INSERT INTO showtimes (movie_id, time, date, cinema) VALUES (?, ?, ?, ?)', (movie_id, time, date, cinema))
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

@app.route('/admin/edit_showtime/<int:showtime_id>', methods=['GET', 'POST'])
@admin_required
def edit_showtime(showtime_id):
    conn = get_db_connection()
    showtime = conn.execute('SELECT * FROM showtimes WHERE id = ?', (showtime_id,)).fetchone()
    if not showtime:
        conn.close()
        flash('Showtime not found.')
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        time = request.form['time']
        date = request.form['date']
        cinema = request.form['cinema']
        conn.execute('UPDATE showtimes SET time = ?, date = ?, cinema = ? WHERE id = ?', (time, date, cinema, showtime_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_dashboard'))
    conn.close()
    return render_template('edit_showtime.html', showtime=showtime)

# --- Main User Routes ---

@app.route('/')
def index():
    conn = get_db_connection()
    now_showing = conn.execute("SELECT * FROM movies WHERE status = 'now_showing'").fetchall()
    upcoming_movies = conn.execute("SELECT * FROM movies WHERE status = 'upcoming'").fetchall()
    showtimes = conn.execute('SELECT * FROM showtimes').fetchall()
    user_balance = None
    if 'user_id' in session:
        user = conn.execute('SELECT balance FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        if user:
            user_balance = user['balance']
    conn.close()
    showtimes_by_movie = {}
    for show in showtimes:
        showtimes_by_movie.setdefault(show['movie_id'], []).append(show)
    return render_template(
        'index.html',
        now_showing=now_showing,
        upcoming_movies=upcoming_movies,
        showtimes_by_movie=showtimes_by_movie,
        user_balance=user_balance
    )

@app.route('/book/<int:movie_id>', methods=['GET', 'POST'])
def book(movie_id):
    conn = get_db_connection()
    movie = conn.execute('SELECT * FROM movies WHERE id = ?', (movie_id,)).fetchone()
    showtimes = conn.execute('SELECT * FROM showtimes WHERE movie_id = ?', (movie_id,)).fetchall()
    conn.close()

    # --- Extract available dates and cinemas from showtimes ---
    available_dates = sorted(list(set(show['date'] for show in showtimes if 'date' in show.keys()))) if showtimes and 'date' in showtimes[0].keys() else ['2025-05-22']
    available_cinemas = sorted(list(set(show['cinema'] for show in showtimes if 'cinema' in show.keys()))) if showtimes and 'cinema' in showtimes[0].keys() else ['Cinema 1', 'Cinema 2']

    selected_date = request.form.get('date') or request.args.get('date') or (available_dates[0] if available_dates else '')
    selected_cinema = request.form.get('cinema') or request.args.get('cinema') or (available_cinemas[0] if available_cinemas else '')

    if session.get('pending_booking'):
        booking = session.pop('pending_booking')
        if request.method == 'GET':
            conn = get_db_connection()
            showtimes = conn.execute('SELECT * FROM showtimes WHERE movie_id = ?', (booking['movie_id'],)).fetchall()
            available_seats = conn.execute(
                'SELECT * FROM seats WHERE showtime_id = ? AND is_booked = 0', (booking['showtime'],)
            ).fetchall()
            conn.close()
            seat_map = {}
            for seat in available_seats:
                row = seat['seat_number'][0]
                seat_map.setdefault(row, []).append(seat['seat_number'])
            return render_template('book.html',
                                   movie={'id': int(booking['movie_id']), 'title': booking.get('movie_title', ''), 'price': int(booking['movie_price'])},
                                   showtimes=showtimes,
                                   step=2,
                                   selected_showtime=booking['showtime'],
                                   tickets=int(booking['tickets']),
                                   seat_map=seat_map,
                                   selected_seats=booking.get('seats', []),
                                   name=booking['name'],
                                   available_dates=available_dates,
                                   available_cinemas=available_cinemas,
                                   selected_date=selected_date,
                                   selected_cinema=selected_cinema)

    if request.method == 'GET' or (request.method == 'POST' and 'step' not in request.form):
        return render_template('book.html',
                               movie=movie,
                               showtimes=showtimes,
                               step=1,
                               selected_showtime=None,
                               tickets=1,
                               seat_map={},
                               selected_seats=[],
                               name=session.get('username', ''),
                               available_dates=available_dates,
                               available_cinemas=available_cinemas,
                               selected_date=selected_date,
                               selected_cinema=selected_cinema)

    if request.method == 'POST':
        step = int(request.form.get('step', 1))
        selected_showtime = request.form.get('showtime')
        tickets = int(request.form.get('tickets', 1))
        name = request.form.get('name', session.get('username', ''))
        selected_date = request.form.get('date', selected_date)
        selected_cinema = request.form.get('cinema', selected_cinema)

        if step == 1:
            conn = get_db_connection()
            available_seats = conn.execute(
                'SELECT * FROM seats WHERE showtime_id = ? AND is_booked = 0', (selected_showtime,)
            ).fetchall()
            conn.close()
            seat_map = {}
            for seat in available_seats:
                row = seat['seat_number'][0]
                seat_map.setdefault(row, []).append(seat['seat_number'])
            return render_template('book.html',
                                   movie=movie,
                                   showtimes=showtimes,
                                   step=2,
                                   selected_showtime=selected_showtime,
                                   tickets=tickets,
                                   seat_map=seat_map,
                                   selected_seats=[],
                                   name=name,
                                   available_dates=available_dates,
                                   available_cinemas=available_cinemas,
                                   selected_date=selected_date,
                                   selected_cinema=selected_cinema)
        elif step == 2:
            selected_seats = request.form.getlist('seats')
            user_id = session.get('user_id')
            card_number = request.form.get('card_number')
            card_name = request.form.get('card_name')
            paid = 1 if card_number and card_name else 0

            if len(selected_seats) != int(tickets):
                flash('Number of selected seats must match number of tickets.')
                conn = get_db_connection()
                available_seats = conn.execute(
                    'SELECT * FROM seats WHERE showtime_id = ? AND is_booked = 0', (selected_showtime,)
                ).fetchall()
                conn.close()
                seat_map = {}
                for seat in available_seats:
                    row = seat['seat_number'][0]
                    seat_map.setdefault(row, []).append(seat['seat_number'])
                return render_template('book.html',
                                       movie=movie,
                                       showtimes=showtimes,
                                       step=2,
                                       selected_showtime=selected_showtime,
                                       tickets=tickets,
                                       seat_map=seat_map,
                                       selected_seats=selected_seats,
                                       name=name,
                                       available_dates=available_dates,
                                       available_cinemas=available_cinemas,
                                       selected_date=selected_date,
                                       selected_cinema=selected_cinema)

            conn = get_db_connection()
            user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
            total_cost = int(movie['price']) * int(tickets)
            if user['balance'] < total_cost:
                conn.close()
                session['pending_booking'] = {
                    'movie_id': movie_id,
                    'movie_title': movie['title'],
                    'movie_price': movie['price'],
                    'showtime': selected_showtime,
                    'tickets': tickets,
                    'name': name,
                    'seats': selected_seats
                }
                return render_template('insufficient_funds.html', movie=movie, showtime_id=selected_showtime, tickets=tickets, name=name, seats=selected_seats, total_cost=total_cost, balance=user['balance'])

            new_balance = user['balance'] - total_cost
            conn.execute('UPDATE users SET balance = ? WHERE id = ?', (new_balance, user_id))
            cur = conn.cursor()
            cur.execute('INSERT INTO bookings (movie_id, showtime_id, tickets, name, user_id, paid) VALUES (?, ?, ?, ?, ?, ?)',
                        (movie_id, selected_showtime, tickets, name, user_id, paid))
            booking_id = cur.lastrowid
            for seat in selected_seats:
                cur.execute('UPDATE seats SET is_booked = 1, booking_id = ? WHERE showtime_id = ? AND seat_number = ?',
                            (booking_id, selected_showtime, seat))
            conn.commit()
            conn.close()
            return render_template('confirmation.html', movie=movie, showtime_id=selected_showtime, tickets=tickets, name=name, paid=paid, seats=selected_seats, total_cost=total_cost, new_balance=new_balance)

    return redirect(url_for('index'))

@app.route('/cancel_booking/<int:booking_id>')
def cancel_booking(booking_id):
    conn = get_db_connection()
    conn.execute('UPDATE seats SET is_booked = 0, booking_id = NULL WHERE booking_id = ?', (booking_id,))
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

@app.route('/showtime/<int:showtime_id>/seats')
def showtime_seats(showtime_id):
    conn = get_db_connection()
    seats = conn.execute(
        'SELECT seat_number, is_booked FROM seats WHERE showtime_id = ?', (showtime_id,)
    ).fetchall()
    conn.close()
    return {'seats': [dict(seat) for seat in seats]}

@app.route('/deposit', methods=['POST'])
def deposit():
    user_id = session.get('user_id')
    amount = int(request.form['amount'])
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    new_balance = user['balance'] + amount
    conn.execute('UPDATE users SET balance = ? WHERE id = ?', (new_balance, user_id))
    conn.commit()
    conn.close()
    flash(f'Deposited ₱{amount}. New balance: ₱{new_balance}')
    pending = session.get('pending_booking')
    if pending:
        return redirect(url_for('book', movie_id=pending['movie_id']))
    return redirect(url_for('index'))

@app.context_processor
def utility_processor():
    def get_showtime_time(showtime_id):
        conn = get_db_connection()
        showtime = conn.execute('SELECT * FROM showtimes WHERE id = ?', (showtime_id,)).fetchone()
        conn.close()
        return showtime['time'] if showtime else ''
    return dict(get_showtime_time=get_showtime_time)

@app.route('/movie/<int:movie_id>')
def movie_details(movie_id):
    conn = get_db_connection()
    movie = conn.execute('SELECT * FROM movies WHERE id = ?', (movie_id,)).fetchone()
    showtimes = conn.execute('SELECT * FROM showtimes WHERE movie_id = ?', (movie_id,)).fetchall()
    conn.close()
    return render_template('movie_details.html', movie=movie, showtimes=showtimes)

if __name__ == '__main__':
    app.run(debug=True)
