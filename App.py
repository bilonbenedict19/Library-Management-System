from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session/flash

def get_db_connection():
    conn = sqlite3.connect('movies.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/login', methods=['POST'])
def login():
    username = request.form['login_username']
    password = request.form['login_password']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    if user and user['password'] == password:  # For demo; use hash in production!
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
    # For demo, store plain password; use hash in production!
    conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    conn.commit()
    conn.close()
    flash('Account created! Please log in.')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.')
    return redirect(url_for('index'))
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Admin access required.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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
        card_number = request.form['card_number']
        card_name = request.form['card_name']
        paid = 1 if card_number and card_name else 0
        user_id = session.get('user_id')  # None if not logged in
        conn = get_db_connection()
        conn.execute('INSERT INTO bookings (movie_id, showtime_id, tickets, name, user_id, paid) VALUES (?, ?, ?, ?, ?, ?)',
                     (movie_id, showtime_id, tickets, name, user_id, paid))
        conn.commit()
        conn.close()
        return render_template('confirmation.html', movie=movie, showtime_id=showtime_id, tickets=tickets, name=name, paid=paid)
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
