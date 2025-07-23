from flask import Flask, render_template, request, redirect, jsonify, send_file, session, url_for, abort
import sqlite3
import os
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'tua_chiave_segreta_super_sicura'

DB_PATH = "database.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        conn.execute('''
            CREATE TABLE prodotti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                prezzo_acquisto REAL NOT NULL,
                prezzo_vendita REAL
            )
        ''')
        conn.execute('''
            CREATE TABLE utenti (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0
            )
        ''')
        # Crea utente admin iniziale
        from werkzeug.security import generate_password_hash
        admin_pw = generate_password_hash("dev")
        conn.execute("INSERT INTO utenti (username, password, is_admin) VALUES (?, ?, ?)", ("dev", admin_pw, 1))
        conn.commit()
        conn.close()

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    db = get_db()
    prodotti = db.execute("SELECT * FROM prodotti").fetchall()
    tot_acquisto = sum(p['prezzo_acquisto'] for p in prodotti)
    tot_vendita = sum(p['prezzo_vendita'] or 0 for p in prodotti)
    profitto = tot_vendita - tot_acquisto
    return render_template("index.html", prodotti=prodotti, tot_acquisto=tot_acquisto, tot_vendita=tot_vendita, profitto=profitto)


@app.route('/add', methods=['POST'])
def add_product():
    nome = request.json['nome']
    prezzo_acquisto = float(request.json['acquisto'])
    db = get_db()
    db.execute("INSERT INTO prodotti (nome, prezzo_acquisto) VALUES (?, ?)", (nome, prezzo_acquisto))
    db.commit()
    return jsonify(success=True)


@app.route('/sell/<int:id>', methods=['POST'])
def sell_product(id):
    prezzo_vendita = float(request.json['vendita'])
    db = get_db()
    db.execute("UPDATE prodotti SET prezzo_vendita = ? WHERE id = ?", (prezzo_vendita, id))
    db.commit()
    return jsonify(success=True)


@app.route('/delete/<int:id>', methods=['DELETE'])
def delete_product(id):
    db = get_db()
    db.execute("DELETE FROM prodotti WHERE id = ?", (id,))
    db.commit()
    return jsonify(success=True)


@app.route('/export')
def export():
    db = get_db()
    prodotti = db.execute("SELECT * FROM prodotti").fetchall()
    df = pd.DataFrame(prodotti)
    os.makedirs('exports', exist_ok=True)
    file_path = 'exports/prodotti.xlsx'
    df.to_excel(file_path, index=False)
    return send_file(file_path, as_attachment=True)

@app.route('/api/statistiche')
def api_statistiche():
    db = get_db()
    prodotti = db.execute("SELECT * FROM prodotti").fetchall()
    tot_acquisto = sum(p['prezzo_acquisto'] for p in prodotti)
    tot_vendita = sum(p['prezzo_vendita'] or 0 for p in prodotti)
    return jsonify({
        'speso': round(tot_acquisto, 2),
        'guadagnato': round(tot_vendita, 2),
        'profitto': round(tot_vendita - tot_acquisto, 2)
    })

@app.route('/api/prodotti')
def api_prodotti():
    db = get_db()
    prodotti = db.execute("SELECT * FROM prodotti").fetchall()
    return jsonify([dict(row) for row in prodotti])


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        user = db.execute("SELECT * FROM utenti WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user['password'], password):
            session['logged_in'] = True
            session['username'] = username
            session['is_admin'] = user['is_admin']
            return redirect(url_for('index'))
        else:
            error = 'Credenziali non valide'
    return render_template('login.html', error=error)




@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/crea-utente', methods=['GET', 'POST'])
def crea_utente():
    if not session.get('logged_in') or not session.get('is_admin'):
        return redirect(url_for('login'))

    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_admin = 1 if 'is_admin' in request.form else 0

        hashed_pw = generate_password_hash(password)

        try:
            db = get_db()
            db.execute("INSERT INTO utenti (username, password, is_admin) VALUES (?, ?, ?)",
                       (username, hashed_pw, is_admin))
            db.commit()
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            error = "Username già esistente"

    return render_template('crea_utente.html', error=error)

from flask import session, abort

@app.route('/admin/users')
def admin_users():
    if not session.get('is_admin'):
        abort(403)  # accesso negato

    db = get_db()
    users = db.execute("SELECT id, username, is_admin FROM utenti").fetchall()
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    if not session.get('is_admin'):
        abort(403)

    db = get_db()
    db.execute("DELETE FROM utenti WHERE id = ?", (user_id,))
    db.commit()
    return jsonify(success=True)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
