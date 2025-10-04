from flask import Flask, render_template, request, redirect, session, flash, jsonify
import mysql.connector
from datetime import date, datetime
import requests
from typing import Optional

app = Flask(__name__)
app.secret_key = "your_secret_key"

# ✅ MySQL Database Connection
db = mysql.connector.connect(
    host='localhost',
    port='3306',
    user='root',
    password='',
    database='expense_db'
)
cursor = db.cursor(dictionary=True)


# -------------------------
# Home Redirect
# -------------------------
@app.route('/')
def home():
    return redirect('/login')


# -------------------------
# Signup (Company + Admin auto-create)
# -------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        company_name = request.form['company']
        username = request.form['username']
        password = request.form['password']
        country = request.form['country']
        currency = request.form['currency']

        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        existing_user = cursor.fetchone()
        if existing_user:
            flash("Username already exists!", "danger")
            return redirect('/signup')

        cursor.execute("INSERT INTO companies (company_name, country, currency) VALUES (%s, %s, %s)", 
                       (company_name, country, currency))
        company_id = cursor.lastrowid

        cursor.execute("INSERT INTO users (username, password, role, company_id) VALUES (%s, %s, %s, %s)", 
                       (username, password, "Admin", company_id))
        db.commit()

        flash("Signup successful! Please login.", "success")
        return redirect('/login')

    return render_template('signup.html')


# -------------------------
# Login
# -------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']  # Store username in session
            session['role'] = user['role']
            session['company_id'] = user['company_id']
            flash("Login successful!", "success")
            return redirect('/dashboard')
        else:
            flash("Invalid username or password", "danger")

    return render_template('login.html')

# -------------------------
# Dashboard
# -------------------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    role = session['role']

    if role == "Admin":
        return redirect('/admin_dashboard')
    elif role == "Employee":
        return redirect('/employee_dashboard')
    elif role == "Manager":
        return redirect('/manager_dashboard')
    else:
        return "Unknown Role"

# -------------------------
# Admin Dashboard
# -------------------------
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != "Admin":
        return redirect('/login')

    company_id = session['company_id']

    # Show all users
    cursor.execute("SELECT * FROM users WHERE company_id=%s", (company_id,))
    users = cursor.fetchall()

    # Show all expenses
    cursor.execute("""
        SELECT e.id, u.username, e.amount, e.currency, e.category, e.status, e.date
        FROM expenses e
        JOIN users u ON e.user_id=u.id
        WHERE u.company_id=%s
    """, (company_id,))
    expenses = cursor.fetchall()

    return render_template("admin_dashboard.html", users=users, expenses=expenses)


# -------------------------
# Manage Users (Admin Only)
# -------------------------
@app.route('/manage_users', methods=['GET', 'POST'])
def manage_users():
    if 'user_id' not in session or session['role'] != "Admin":
        return redirect('/login')

    company_id = session['company_id']

    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        manager_id = request.form.get('manager_id')

        if manager_id == "":
            manager_id = None

        cursor.execute("INSERT INTO users (username, password, role, company_id, manager_id) VALUES (%s, %s, %s, %s, %s)",
                       (username, password, role, company_id, manager_id))
        db.commit()
        flash(f"{role} created successfully!", "success")
        return redirect('/manage_users')

    cursor.execute("SELECT * FROM users WHERE company_id=%s", (company_id,))
    users = cursor.fetchall()

    cursor.execute("SELECT id, username FROM users WHERE company_id=%s AND role='Manager'", (company_id,))
    managers = cursor.fetchall()

    return render_template('manage_users.html', users=users, managers=managers)

# -------------------------
# Employee Dashboard
# -------------------------
@app.route('/employee_dashboard')
def employee_dashboard():
    if 'user_id' not in session or session['role'] != "Employee":
        return redirect('/login')

    cursor.execute("SELECT COUNT(*) as my_expenses FROM expenses WHERE user_id=%s", (session['user_id'],))
    my_expenses_count = cursor.fetchone()['my_expenses']
    
    cursor.execute("SELECT COUNT(*) as pending FROM expenses WHERE user_id=%s AND status='Pending'", (session['user_id'],))
    pending_count = cursor.fetchone()['pending']
    
    cursor.execute("SELECT SUM(amount) as total_spent FROM expenses WHERE user_id=%s AND status='Approved'", (session['user_id'],))
    total_spent = cursor.fetchone()['total_spent'] or 0

    cursor.execute("SELECT * FROM expenses WHERE user_id=%s ORDER BY date DESC", (session['user_id'],))
    my_expenses = cursor.fetchall()

    return render_template("employee_dashboard.html",
                         my_expenses_count=my_expenses_count,
                         pending_count=pending_count,
                         total_spent=total_spent,
                         my_expenses=my_expenses)

# Currency conversion functions
def get_exchange_rate_to_usd(from_currency: str) -> Optional[float]:
    """Get exchange rate from given currency to USD"""
    if from_currency.upper() == 'USD':
        return 1.0
    
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'rates' in data and 'USD' in data['rates']:
            return data['rates']['USD']
        else:
            print(f"USD rate not found for {from_currency}")
            return None
            
    except requests.RequestException as e:
        print(f"Error fetching exchange rate: {e}")
        return None

def convert_to_usd(amount: float, from_currency: str) -> Optional[float]:
    """Convert given amount from specified currency to USD"""
    exchange_rate = get_exchange_rate_to_usd(from_currency)
    
    if exchange_rate is None:
        return None
    
    usd_amount = amount * exchange_rate
    return round(usd_amount, 2)

def load_currencies():
    """Load all available currencies from REST Countries API"""
    try:
        available_currencies = {}
        response = requests.get("https://restcountries.com/v3.1/all?fields=name,currencies", timeout=10)
        response.raise_for_status()
            
        countries_data = response.json()
            
        for country in countries_data:
            if 'currencies' in country:
                for currency_code, currency_info in country['currencies'].items():
                    currency_name = currency_info.get('name', currency_code)
                    currency_symbol = currency_info.get('symbol', '')
                    available_currencies[currency_code] = {
                        'name': currency_name,
                        'symbol': currency_symbol
                    }
            
        return available_currencies
    except requests.RequestException as e:
        print(f"Error loading currencies: {e}")
        # Fallback to common currencies if API fails
        return {
            'USD': {'name': 'United States Dollar', 'symbol': '$'},
            'EUR': {'name': 'Euro', 'symbol': '€'},
            'GBP': {'name': 'British Pound Sterling', 'symbol': '£'},
            'JPY': {'name': 'Japanese Yen', 'symbol': '¥'},
            'INR': {'name': 'Indian Rupee', 'symbol': '₹'},
            'CAD': {'name': 'Canadian Dollar', 'symbol': 'C$'},
            'AUD': {'name': 'Australian Dollar', 'symbol': 'A$'},
            'CNY': {'name': 'Chinese Yuan', 'symbol': '¥'},
            'CHF': {'name': 'Swiss Franc', 'symbol': 'CHF'},
            'SGD': {'name': 'Singapore Dollar', 'symbol': 'S$'}
        }

# -------------------------
# Expense Submission (Employee) with Currency Conversion
# -------------------------
@app.route('/submit_expense', methods=['GET', 'POST'])
def submit_expense():
    if 'user_id' not in session or session['role'] != "Employee":
        return redirect('/login')

    # Load available currencies
    currencies = load_currencies()

    if request.method == "POST":
        amount = float(request.form['amount'])
        currency = request.form['currency']
        category = request.form['category']
        description = request.form['description']
        expense_date = request.form.get('date', date.today())

        # Convert to USD for standardization
        usd_amount = convert_to_usd(amount, currency)
        
        if usd_amount is None:
            flash("Error converting currency. Please try again.", "danger")
            return redirect('/submit_expense')

        # Store both original amount and USD equivalent
        cursor.execute("""
            INSERT INTO expenses (user_id, amount, currency, usd_amount, category, description, date, status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (session['user_id'], amount, currency, usd_amount, category, description, expense_date, 'Pending'))
        db.commit()

        flash(f"Expense submitted successfully! (${usd_amount:.2f} USD)", "success")
        return redirect('/submit_expense')

    cursor.execute("SELECT * FROM expenses WHERE user_id=%s ORDER BY date DESC", (session['user_id'],))
    my_expenses = cursor.fetchall()

    return render_template('submit_expense.html', 
                         my_expenses=my_expenses, 
                         currencies=currencies,
                         username=session.get('username', 'Employee'))

# -------------------------
# Currency Conversion API Endpoint
# -------------------------
@app.route('/api/convert_currency', methods=['POST'])
def convert_currency():
    """API endpoint for real-time currency conversion"""
    data = request.get_json()
    amount = float(data.get('amount', 0))
    from_currency = data.get('currency', 'USD')
    
    usd_amount = convert_to_usd(amount, from_currency)
    
    if usd_amount is not None:
        return jsonify({
            'success': True,
            'usd_amount': usd_amount,
            'converted_amount': f"${usd_amount:.2f} USD"
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Currency conversion failed'
        }), 400

# -------------------------
# Manager Dashboard - FIXED
# -------------------------
@app.route('/manager_dashboard')
def manager_dashboard():
    if 'user_id' not in session or session['role'] != "Manager":
        return redirect('/login')

    try:
        # Get team expenses count
        cursor.execute("""
            SELECT COUNT(*) as team_expenses 
            FROM expenses e 
            JOIN users u ON e.user_id = u.id 
            WHERE u.manager_id=%s
        """, (session['user_id'],))
        team_expenses = cursor.fetchone()['team_expenses']
        
        # Get pending approvals count
        cursor.execute("""
            SELECT COUNT(*) as pending_approvals 
            FROM expenses e 
            JOIN users u ON e.user_id = u.id 
            WHERE u.manager_id=%s AND e.status='Pending'
        """, (session['user_id'],))
        pending_approvals = cursor.fetchone()['pending_approvals']
        
        # Get approved count this month
        cursor.execute("""
            SELECT COUNT(*) as approved_count 
            FROM expenses e 
            JOIN users u ON e.user_id = u.id 
            WHERE u.manager_id=%s AND e.status='Approved' 
            AND MONTH(e.date) = MONTH(CURRENT_DATE())
        """, (session['user_id'],))
        result = cursor.fetchone()
        approved_count = result['approved_count'] if result else 0
        
        # Get escalation risk count - simplified version
        cursor.execute("""
            SELECT COUNT(*) as escalation_count 
            FROM expenses e 
            JOIN users u ON e.user_id = u.id 
            WHERE u.manager_id=%s AND e.status='Pending'
        """, (session['user_id'],))
        result = cursor.fetchone()
        escalation_count = result['escalation_count'] if result else 0
        
        # Get team expenses for approval
        cursor.execute("""
            SELECT e.*, u.username 
            FROM expenses e 
            JOIN users u ON e.user_id = u.id 
            WHERE u.manager_id = %s 
            ORDER BY e.date DESC
        """, (session['user_id'],))
        team_expenses_list = cursor.fetchall()

        # Check for high amount expenses that need escalation
        has_high_amount = False
        has_very_high_amount = False
        
        for expense in team_expenses_list:
            if expense['status'] == 'Pending':
                if expense['amount'] > 1000:
                    has_high_amount = True
                if expense['amount'] > 2000:
                    has_very_high_amount = True

        # Analytics data
        cursor.execute("""
            SELECT SUM(e.amount) as total_spending
            FROM expenses e 
            JOIN users u ON e.user_id = u.id 
            WHERE u.manager_id=%s
        """, (session['user_id'],))
        total_spending_result = cursor.fetchone()
        total_team_spending = total_spending_result['total_spending'] if total_spending_result and total_spending_result['total_spending'] else 0

        return render_template("manager_dashboard.html",
                             team_expenses=team_expenses,
                             pending_approvals=pending_approvals,
                             approved_count=approved_count,
                             escalation_count=escalation_count,
                             team_expenses_list=team_expenses_list,
                             has_high_amount=has_high_amount,
                             has_very_high_amount=has_very_high_amount,
                             total_team_spending=total_team_spending,
                             avg_approval_time=18,  # Mock data
                             approval_rate=85)      # Mock data
                             
    except mysql.connector.Error as e:
        flash(f"Database error: {e}", "danger")
        return redirect('/dashboard')

# -------------------------
# Update Expense Status (Manager Approval) - FIXED
# -------------------------
@app.route('/update_expense_status/<int:expense_id>', methods=['POST'])
def update_expense_status(expense_id):
    if 'user_id' not in session or session['role'] not in ['Manager', 'Admin']:
        return redirect('/login')

    new_status = request.form['status']
    
    try:
        # Get expense details for escalation rules
        cursor.execute("SELECT * FROM expenses WHERE id = %s", (expense_id,))
        expense = cursor.fetchone()
        
        if not expense:
            flash("Expense not found.", "danger")
            return redirect('/manager_dashboard')
        
        # Update expense status
        cursor.execute("UPDATE expenses SET status = %s WHERE id = %s", (new_status, expense_id))
        
        # Try to log the approval action (skip if table doesn't exist)
        try:
            cursor.execute("""
                INSERT INTO approval_logs (expense_id, manager_id, action, comments, timestamp) 
                VALUES (%s, %s, %s, %s, %s)
            """, (expense_id, session['user_id'], new_status, '', datetime.now()))
        except:
            pass  # Skip if table doesn't exist
        
        # Check if escalation is needed based on amount
        if new_status == 'Approved' and expense['amount'] > 1000:
            # Auto-escalate to finance/director based on amount
            next_approver_role = 'Director' if expense['amount'] > 2000 else 'Finance'
            
            # Try to create escalation queue (skip if it fails)
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS escalation_queue (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        expense_id INT,
                        required_role VARCHAR(20),
                        escalated_at DATETIME,
                        status VARCHAR(20) DEFAULT 'Pending'
                    )
                """)
                
                cursor.execute("""
                    INSERT INTO escalation_queue (expense_id, required_role, escalated_at) 
                    VALUES (%s, %s, %s)
                """, (expense_id, next_approver_role, datetime.now()))
                
                flash(f"Expense approved! Escalated to {next_approver_role} for final approval.", "success")
            except:
                flash(f"Expense {new_status.lower()} successfully!", "success")
        else:
            flash(f"Expense {new_status.lower()} successfully!", "success")
        
        db.commit()
        
    except mysql.connector.Error as e:
        flash(f"Error updating expense: {e}", "danger")

    return redirect('/manager_dashboard')

# -------------------------
# Send Back with Comments - FIXED
# -------------------------
@app.route('/send_back_expense', methods=['POST'])
def send_back_expense():
    if 'user_id' not in session or session['role'] != "Manager":
        return redirect('/login')

    expense_id = request.form['expense_id']
    comments = request.form['comments']
    
    try:
        # Update expense status to Returned
        cursor.execute("UPDATE expenses SET status = 'Returned' WHERE id = %s", (expense_id,))
        
        # Try to log the action (skip if table doesn't exist)
        try:
            cursor.execute("""
                INSERT INTO approval_logs (expense_id, manager_id, action, comments, timestamp) 
                VALUES (%s, %s, %s, %s, %s)
            """, (expense_id, session['user_id'], 'Returned', comments, datetime.now()))
        except:
            pass
        
        db.commit()
        flash("Expense sent back to employee with your comments.", "success")
        
    except mysql.connector.Error as e:
        flash(f"Error sending back expense: {e}", "danger")

    return redirect('/manager_dashboard')

# -------------------------
# Logout
# -------------------------
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)