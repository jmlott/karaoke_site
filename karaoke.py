# -*- coding: utf-8 -*-


import collections
import re
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask import make_response, Flask, request, session, redirect, url_for, \
     render_template, flash
from functools import update_wrapper, wraps


app = Flask(__name__)

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="<DATABASE USERNAME>",
    password="<DATABASE PASSWORD>",
    hostname="<PA USERNAME>.mysql.pythonanywhere-services.com",
    databasename="<DATABASE NAME>",
)
app.config.update(dict(
    DEBUG=False,
    SECRET_KEY='development key',
    SQLALCHEMY_DATABASE_URI=SQLALCHEMY_DATABASE_URI,
    SQLALCHEMY_POOL_RECYCLE=299,
    USERNAME='<ADMIN USERNAME>',
    PASSWORD='<ADMIN PASSWORD>'
))

db = SQLAlchemy(app)


def initialize_db():
    """Clears songs table."""
    drop_sql = 'DROP TABLE songs'
    create_sql = 'CREATE TABLE songs (id int NOT NULL AUTO_INCREMENT PRIMARY KEY, user varchar(255) NOT NULL, artist varchar(255) NOT NULL, title varchar(255) NOT NULL)'
    drop_results = db.engine.execute(drop_sql)
    drop_results.close()
    create_results = db.engine.execute(create_sql)
    create_results.close()


def is_duplicate():
    """Returns boolean indicating if song is dupe or not."""
    regex = '[^A-Za-z0-9 ]+'
    sql = 'SELECT artist, title FROM songs'
    entries = db.engine.execute(sql)
    artist = re.sub(regex, '', str(request.form['artist'])).lower()
    title = re.sub(regex, '', str(request.form['title'])).lower()
    for entry in entries:
        e_artist = re.sub(regex, '', str(entry.artist)).lower()
        e_title = re.sub(regex, '', str(entry.title)).lower()
        if [e_artist, e_title] == [artist, title]:
          return True
    return False


def sort_queue(entries_temp):
    """Sorts the song list into a karaoke queue."""
    queue = []
    entries = [x for x in entries_temp]
    users = collections.OrderedDict([(x['user'], x['title']) for x in entries_temp]).keys()
    users_temp = [x for x in users]
    last_loop = len(entries)
    # Loop over entries until none are left
    while len(entries) > 0:
        # Keep count of loops
        loop = len(entries)
        for entry in entries:
          # Users are deleted from list as it sorts, so refresh it
          if len(users_temp) == 0:
            users_temp = [x for x in users]
          next_user = users_temp[0]
          # Compare user of current entry to expected next in line
          if entry['user'] == next_user:
            queue.append(entry)
            entries.remove(entry)
            del users_temp[0]
            # Decrement last_loop used to ensure no unending loops
            last_loop -= 1
            # Break out to next loop
            break
        # Don't allow loop to continue forever if user has no more songs
        if loop == last_loop:
            del users_temp[0]
    return queue
    

def get_songs():
    """Get song requests from DB and store them as list of dicts."""
    entries = []
    sql = 'SELECT id, user, artist, title FROM songs ORDER BY id ASC'
    results = db.engine.execute(sql)
    for result in results:
        res_dict = {'id': result.id,
                    'user': result.user,
                    'artist': result.artist,
                    'title': result.title}
        entries.append(res_dict)
    queue = sort_queue(entries)
    return queue


def set_started(value):
    sql = 'UPDATE started SET value = %i' % value
    db.engine.execute(sql)


def is_started():
    started = None
    sql = 'SELECT value FROM started'
    results = db.engine.execute(sql)
    if [x.value for x in results][0] == 0:
        started = False
    else:
        started = True
    return started


def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    return update_wrapper(no_cache, view)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/song_list', methods=['GET', 'POST'])
def show_song_list():
    if request.method == 'POST':
        sql = 'DELETE FROM songs WHERE id=%s' % request.form['delete_id']
        db.engine.execute(sql)
    entries = get_songs()
    return render_template('song_list.html', entries=entries)


@app.route('/request_song', methods=['GET', 'POST'])
@nocache
def request_song():
    STARTED = is_started()
    if request.method == 'POST':
        sql = "INSERT INTO songs (user, artist, title) values (%s, %s, %s)"
        if is_duplicate() == False:
            db.engine.execute(sql, request.form['user'], request.form['artist'], request.form['title'])
            flash('New request was successfully submitted')
        else:
            flash('Song already requested by another singer. Please choose another.')
    return render_template('request.html', started=STARTED)


@app.route('/admin', methods=['GET', 'POST'])
@nocache
def admin():
    error = None
    if session['logged_in'] == False:
        error = 'Must be logged in and have admin privileges to access admin console.'
        return render_template('login.html', error=error)
    if request.method == 'POST':
        if request.form['button'] == 'Delete':
            initialize_db()
            flash('Songs database successfully cleared.')
        elif request.form['button'] == 'Start':
            set_started(True)
            flash('Karaoke started. Users can requests songs now.')
        elif request.form['button'] == 'End':
            set_started(False)
            flash('Karaoke ended. Song requests are closed.')
    STARTED = is_started()
    return render_template('admin.html', started=STARTED)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_song_list'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_song_list'))


if __name__ == "__main__":
  app.run()
