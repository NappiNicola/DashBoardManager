from flask import Flask, render_template, request, redirect, jsonify, send_file
import sqlite3
import os
import pandas as pd

app = Flask(__name__)

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
        conn.commit()
        conn.close()

@app.route('/')
def index():
    db = get_db()
    prodotti = db.execute("SELECT * FROM prodotti").fetchall()
    tot_acquisto = sum(p['prezzo_acquisto'] for p in prodotti)
    tot_vendita = sum(p['prezzo_vendita'] or 0 for p in prodotti)
    profitto = tot_vendita - tot_acquisto
    return render_template("index.html", prodotti=prodotti, tot_acquisto=tot_acquisto, tot_vendita=tot_vendita,profitto=profitto)

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


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
