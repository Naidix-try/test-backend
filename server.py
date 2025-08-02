from flask import Flask, request, jsonify, session
from flask_session import Session
from flask_cors import CORS
from datetime import timedelta
import psycopg2
import os
from werkzeug.utils import secure_filename
app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['SESSION_TYPE'] = 'filesystem'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.permanent_session_lifetime = timedelta(minutes=60)
Session(app)
CORS(app, supports_credentials=True)
DB_NAME = 'mydb_6lrh'
DB_USER = 'naidix'
DB_PASSWORD = 'TGAme9ViTASsRv5SP6qWJX3AEKPfgYwG'
DB_HOST = 'dpg-d273lcggjchc73f2njk0-a'
DB_PORT = '5432'
def get_db_connection():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    return conn
Admin="mouloud"
pp="nayla"
@app.route('/check_session', methods=['GET'])
def check_session():
    if 'mouloud' in session:
        return jsonify({'logged_in': True, 'user': session['mouloud'],'admin':True})
    return jsonify({'logged_in': False}), 401
@app.route('/admin_login', methods=['POST'])
def admin_login():
    if request.method == 'OPTIONS':
        return '', 204

    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username == Admin and password == pp:
        session['mouloud'] = username
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401
@app.route('/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, login_date FROM users")
    rows = cur.fetchall()
    users = [{'id': row[0], 'name': row[1], 'date': row[2]} for row in rows]
    cur.close()
    conn.close()

    return jsonify(users)
import bcrypt  # Add this at the top
@app.route('/add_user', methods=['POST'])
def add_user():
    
    data = request.get_json()
    name = data.get('name')
    password = data.get('password')

    if not name or not password:
        return jsonify({'error': 'Name and password are required'}), 400

    # 🔐 Hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

    # Insert into database
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (name, password_hash) VALUES (%s, %s)",
        (name, hashed_password.decode('utf-8'))  # decode to store as string
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'message': 'User added successfully'}), 201

@app.route('/delete_user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'User deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/add_entry', methods=['POST'])
def add_entry():
    amount = request.form.get('amount')
    type_ = request.form.get('type')
    category = request.form.get('category')
    pic = request.files.get('pic')

    filename = None
    if pic:
        filename = secure_filename(pic.filename)
        pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    # Save entry to DB (assuming a PostgreSQL connection is already established)
    conn = psycopg2.connect(dbname='mydb', user='naidix', password='naidix38008040', host='localhost')
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO entries (amount, type, category, date_added, pic_url) VALUES (%s, %s, %s,NOW(), %s)',
        (amount, type_, category, filename)
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'message': 'Entry added successfully'})

@app.route('/summary', methods=['GET'])
def get_summary():
    conn = get_db_connection()
    cur = conn.cursor()

    # Get total income
    cur.execute("SELECT COALESCE(SUM(amount), 0) FROM entries WHERE type = 'income'")
    income = cur.fetchone()[0]

    # Get total expense
    cur.execute("SELECT COALESCE(SUM(amount), 0) FROM entries WHERE type = 'outcome'")
    expense = cur.fetchone()[0]

    # Income by category
    cur.execute("""
        SELECT category, SUM(amount)
        FROM entries
        WHERE type = 'income'
        GROUP BY category
    """)
    income_categories = {row[0]: float(row[1]) for row in cur.fetchall()}

    # Expense by category
    cur.execute("""
        SELECT category, SUM(amount)
        FROM entries
        WHERE type = 'outcome'
        GROUP BY category
    """)
    expense_categories = {row[0]: float(row[1]) for row in cur.fetchall()}

    cur.close()
    conn.close()

    return jsonify({
        'total_income': float(income),
        'total_expense': float(expense),
        'income_by_category': income_categories,
        'expense_by_category': expense_categories
    })
if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
