from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Initialize the database using schema.sql
def init_db():
    conn = sqlite3.connect('farmers.db')
    cursor = conn.cursor()
    with open('schema.sql', 'r') as f:
        cursor.executescript(f.read())
    conn.commit()
    conn.close()

# Insert default doctor and farmer into the database
def insert_default_users():
    conn = sqlite3.connect('farmers.db')
    cursor = conn.cursor()
    
    # Insert default doctor
    cursor.execute('SELECT id FROM doctors WHERE username = ?', ('Dr.Tobias',))
    doctor = cursor.fetchone()
    if not doctor:
        cursor.execute('INSERT INTO doctors (username, password) VALUES (?, ?)', ('Dr.Tobias', '3204'))
    
    # Insert default farmer
    cursor.execute('SELECT id FROM farmers WHERE username = ?', ('farmer1',))
    farmer = cursor.fetchone()
    if not farmer:
        cursor.execute('''
            INSERT INTO farmers (name, age, contact, username, medical_history, last_checkup_date, next_checkup_date, password)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('John Doe', 45, '+1234567890', 'farmer1', 'Hypertension', '2023-01-15', '2023-07-15', 'farmer123'))
    
    conn.commit()
    conn.close()

# Homepage with minimal UI
@app.route('/')
def index():
    return render_template('index.html')

# Farmer registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age')
        contact = request.form.get('contact')
        username = request.form.get('username')
        medical_history = request.form.get('medical_history')
        last_checkup_date = request.form.get('last_checkup_date')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('register'))

        # Calculate next check-up date (6 months from last check-up)
        if last_checkup_date:
            last_date = datetime.strptime(last_checkup_date, '%Y-%m-%d')
            next_checkup_date = (last_date + timedelta(days=180)).strftime('%Y-%m-%d')
        else:
            next_checkup_date = None

        conn = sqlite3.connect('farmers.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO farmers (name, age, contact, username, medical_history, last_checkup_date, next_checkup_date, password)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, age, contact, username, medical_history, last_checkup_date, next_checkup_date, password))
        conn.commit()
        conn.close()

        flash('Farmer registered successfully! Please log in.', 'success')
        return redirect(url_for('farmer_login'))  # Redirect to login page after registration

    return render_template('register.html')

# Farmer login page
@app.route('/farmer/login', methods=['GET', 'POST'])
def farmer_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Username and password are required!', 'error')
            return redirect(url_for('farmer_login'))

        conn = sqlite3.connect('farmers.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM farmers WHERE username = ? AND password = ?', (username, password))
        farmer = cursor.fetchone()
        conn.close()

        if farmer:
            session['farmer_id'] = farmer[0]  # Store farmer ID in session
            return redirect(url_for('farmer_dashboard'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('farmer_login'))  # Redirect back to login page with error message

    return render_template('farmer_login.html')

# Farmer dashboard
@app.route('/farmer/dashboard')
def farmer_dashboard():
    if 'farmer_id' not in session:
        return redirect(url_for('farmer_login'))

    conn = sqlite3.connect('farmers.db')
    cursor = conn.cursor()
    
    # Get farmer details
    cursor.execute('SELECT * FROM farmers WHERE id = ?', (session['farmer_id'],))
    farmer = cursor.fetchone()
    
    # Get diagnoses and recommendations
    cursor.execute('''
        SELECT d.disease, d.recommendations, d.follow_up_date, doc.username
        FROM diagnoses d
        JOIN doctors doc ON d.doctor_id = doc.id
        WHERE d.farmer_id = ?
    ''', (session['farmer_id'],))
    diagnoses = cursor.fetchall()
    
    conn.close()
    
    return render_template('farmer_dashboard.html', farmer=farmer, diagnoses=diagnoses)

# Health Tips Page
@app.route('/health-tips')
def health_tips():
    return render_template('health_tips.html')

# Disease Prevention Page
@app.route('/disease-prevention')
def disease_prevention():
    return render_template('disease_prevention.html')

# Mental Health Page
@app.route('/mental-health')
def mental_health():
    return render_template('mental_health.html')

# Logout farmer
@app.route('/farmer/logout')
def farmer_logout():
    session.pop('farmer_id', None)
    return redirect(url_for('index'))

# Doctor login page
@app.route('/doctor/login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = sqlite3.connect('farmers.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM doctors WHERE username = ? AND password = ?', (username, password))
        doctor = cursor.fetchone()
        conn.close()

        if doctor:
            session['doctor_id'] = doctor[0]  # Store doctor ID in session
            return redirect(url_for('doctor_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('doctor_login.html')

# Doctor's dashboard
@app.route('/doctor/dashboard')
def doctor_dashboard():
    if 'doctor_id' not in session:
        return redirect(url_for('doctor_login'))

    conn = sqlite3.connect('farmers.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM farmers')
    farmers = cursor.fetchall()
    conn.close()
    return render_template('doctor_dashboard.html', farmers=farmers)

# Delete a patient
@app.route('/doctor/delete/<int:farmer_id>')
def delete_patient(farmer_id):
    if 'doctor_id' not in session:
        return redirect(url_for('doctor_login'))

    conn = sqlite3.connect('farmers.db')
    cursor = conn.cursor()
    
    # Delete diagnoses associated with the farmer
    cursor.execute('DELETE FROM diagnoses WHERE farmer_id = ?', (farmer_id,))
    
    # Delete the farmer
    cursor.execute('DELETE FROM farmers WHERE id = ?', (farmer_id,))
    
    conn.commit()
    conn.close()

    flash('Patient deleted successfully!', 'success')
    return redirect(url_for('doctor_dashboard'))

# View/add farmer details (diagnosis and recommendations)
@app.route('/doctor/farmer/<int:farmer_id>', methods=['GET', 'POST'])
def doctor_farmer_details(farmer_id):
    if 'doctor_id' not in session:
        return redirect(url_for('doctor_login'))

    if request.method == 'POST':
        disease = request.form.get('disease')
        recommendations = request.form.get('recommendations')
        follow_up_date = request.form.get('follow_up_date')

        conn = sqlite3.connect('farmers.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO diagnoses (farmer_id, doctor_id, disease, recommendations, follow_up_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (farmer_id, session['doctor_id'], disease, recommendations, follow_up_date))
        conn.commit()
        conn.close()

        flash('Diagnosis and recommendations added successfully!', 'success')
        return redirect(url_for('doctor_dashboard'))

    conn = sqlite3.connect('farmers.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM farmers WHERE id = ?', (farmer_id,))
    farmer = cursor.fetchone()
    cursor.execute('SELECT * FROM diagnoses WHERE farmer_id = ?', (farmer_id,))
    diagnoses = cursor.fetchall()
    conn.close()

    return render_template('doctor_farmer_details.html', farmer=farmer, diagnoses=diagnoses)

# Logout doctor
@app.route('/doctor/logout')
def doctor_logout():
    session.pop('doctor_id', None)
    return redirect(url_for('index'))  # Redirect to homepage after logout

# Run the application
if __name__ == '__main__':
    init_db()  # Initialize the database using schema.sql
    insert_default_users()  # Insert default doctor and farmer
    app.run(debug=True, port=5001)
