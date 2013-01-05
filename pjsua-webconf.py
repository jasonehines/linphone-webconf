#!/usr/bin/env python2
from __future__ import with_statement
from contextlib import closing

import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
import os


DATABASE = 'flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD  = 'default'

app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
  return sqlite3.connect(app.config['DATABASE'])

def init_db():
  with closing(connect_db()) as db:
    with app.open_resource('schema.sql') as schema:
      db.cursor().executescript(schema.read())
      setauth(db,app.config['USERNAME'],app.config['PASSWORD'])
    db.commit()

def auth(user,password):
  import md5
  cur = g.db.execute('select username, password from auth')
  for row  in cur:
    db_user = row[0]
    db_pass = row[1]
  try:
    hash = md5.new(password)
    if (user == db_user) and (hash.hexdigest() == db_pass):
      return True
  except TypeError:
      return False
  return False

def setauth(db,user,password):
  import md5
  pashash = md5.new()
  pashash.update(password)
  db.execute("delete from auth")
  db.execute("insert into auth (username, password) values('{0}', '{1}')".format(user,pashash.hexdigest()))
  db.commit()

# App stuff
@app.before_request 
def before_request():
  g.db = connect_db()
  
@app.teardown_request
def teardown_request(exception):
  g.db.close()

@app.route('/')
def show_entries():
  cur = g.db.execute('select title, username, server, waittime from entries order by id')
  entries = [dict(title=row[0], username=row[1], server=row[2], waittime=row[3] ) for row in cur.fetchall()]
  return render_template('show_entries.html',entries=entries)

@app.route('/add', methods=['POST'])
def add_entry():
  if not session.get('logged_in'):
    abort(401)
  g.db.execute('insert into entries (title, username, password, server, waittime) values(?, ?, ?, ?, ?)', [request.form['title'],request.form['text']])
  g.db.commit()
  flash('New entry successfuly posted')
  return redirect(url_for('show_entries'))

@app.route('/login', methods=['GET','POST'])
def login():
  error = None
  if request.method == 'POST':
    if not auth(request.form['username'], request.form['password']):
      error = 'Authentication failure '
    else:
      session['logged_in'] = True
      flash('You were logged in!')
      return(redirect(url_for('show_entries')))

  return render_template('login.html', error=error)
  
@app.route('/changepassword',methods=['GET','POST'])
def changepassword():
  error = None
  if request.method == 'POST':
    print request.form
    username = request.form['username']
    password = request.form['password']
    rpassword = request.form['rpassword']
    if len(username) == 0:
      error = "Username is Empty"
    elif password != rpassword:
      error = 'Passwords do not match'
    else :
      setauth(g.db,username,password)
      flash('Password changed')
      return(redirect(url_for('show_entries')))
  return render_template('password.html', error=error)

  
@app.route('/logout')
def logout():
  session.pop('logged_in', None)
  flash('You were logged out')
  return redirect(url_for('show_entries'))

if __name__ == "__main__":
  if not os.path.isfile(app.config['DATABASE']):
    init_db()
  app.run()
  