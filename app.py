import sqlite3
import tkinter as tk
from tkinter import messagebox
import datetime

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

def create_tables(conn):
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        id integer PRIMARY KEY,
                        type text NOT NULL,
                        category text NOT NULL,
                        amount real NOT NULL,
                        description text,
                        date text NOT NULL);''')
        c.execute('''CREATE TABLE IF NOT EXISTS monthly_budgets (
                        id integer PRIMARY KEY,
                        month text NOT NULL,
                        year text NOT NULL,
                        budget_amount real NOT NULL);''')
    except sqlite3.Error as e:
        print(e)

def add_transaction(conn, transaction):
    sql = '''INSERT INTO transactions(type, category, amount, description, date)
             VALUES(?,?,?,?,?)'''
    cur = conn.cursor()
    cur.execute(sql, transaction)
    conn.commit()
    return cur.lastrowid

def view_transactions(conn):
    """View all transactions in the transactions table"""
    cur = conn.cursor()
    cur.execute("SELECT * FROM transactions")
    rows = cur.fetchall()

    for row in rows:
        print(row)


def edit_transaction(conn, transaction_id, updated_transaction):
    """Edit an existing transaction"""
    sql = ''' UPDATE transactions
              SET type = ? ,
                  category = ? ,
                  amount = ? ,
                  description = ?,
                  date = ?
              WHERE id = ?'''
    cur = conn.cursor()
    cur.execute(sql, updated_transaction + (transaction_id,))
    conn.commit()

def delete_transaction(conn, transaction_id):
    """Delete a transaction by transaction id"""
    sql = 'DELETE FROM transactions WHERE id=?'
    cur = conn.cursor()
    cur.execute(sql, (transaction_id,))
    conn.commit()

def calculate_totals(conn):
    """Calculate total income, expenses, and balance"""
    cur = conn.cursor()
    cur.execute("SELECT type, SUM(amount) FROM transactions GROUP BY type")
    rows = cur.fetchall()
    totals = {'income': 0, 'expense': 0, 'balance': 0}
    for row in rows:
        if row[0] == 'income':
            totals['income'] = row[1]
        elif row[0] == 'expense':
            totals['expense'] = row[1]

    totals['balance'] = totals['income'] - totals['expense']
    return totals

def add_monthly_budget(conn, month, year, budget_amount):
    """Add a monthly budget"""
    sql = '''INSERT INTO monthly_budgets(month, year, budget_amount)
             VALUES(?,?,?)'''
    cur = conn.cursor()
    cur.execute(sql, (month, year, budget_amount))
    conn.commit()
    return cur.lastrowid

def get_monthly_expenditure(conn, month, year):
    """Get the total expenditure for a specific month and year"""
    cur = conn.cursor()
    cur.execute("SELECT SUM(amount) FROM transactions WHERE type='expense' AND strftime('%m', date) = ? AND strftime('%Y', date) = ?", (month, year))
    row = cur.fetchone()
    return row[0] if row[0] is not None else 0

def suggest_expenditure_reductions(conn, month, year, budget_amount):
    """Suggest reductions in expenditures based on budget"""
    total_expenditure = get_monthly_expenditure(conn, month, year)
    if total_expenditure > budget_amount:
        excess = total_expenditure - budget_amount
        cur = conn.cursor()
        cur.execute("SELECT category, SUM(amount) FROM transactions WHERE type='expense' AND strftime('%m', date) = ? AND strftime('%Y', date) = ? GROUP BY category ORDER BY SUM(amount) DESC", (month, year))
        categories = cur.fetchall()
        suggestions = []
        for category, amount in categories:
            if amount > excess:
                suggestions.append(f"Reduce spending in '{category}' by at least {excess:.2f}.")
                break
            else:
                suggestions.append(f"Consider reducing spending in '{category}'.")
                excess -= amount
        return suggestions
    else:
        return ["Expenditure is within the budget. No reductions necessary."]


def add_transaction_ui():
    transaction = (type_entry.get(), category_entry.get(), float(amount_entry.get()), description_entry.get(), date_entry.get())
    add_transaction(conn, transaction)
    messagebox.showinfo("Transaction Added", "Transaction has been added successfully")
    view_transactions_ui()

def view_transactions_ui():
    transactions_text.delete(1.0, tk.END)
    cur = conn.cursor()
    cur.execute("SELECT * FROM transactions")
    rows = cur.fetchall()
    for row in rows:
        transactions_text.insert(tk.END, str(row) + "\n")

database = "personal_finance.db"
conn = create_connection(database)
if conn is not None:
    create_tables(conn)
else:
    print("Error! cannot create the database connection.")

# UI setup
root = tk.Tk()
root.title("Budget Tracking Application")

transaction_frame = tk.Frame(root)
transaction_frame.pack(padx=10, pady=10)

tk.Label(transaction_frame, text="Add Transaction").pack()
tk.Label(transaction_frame, text="Type:").pack()
type_entry = tk.Entry(transaction_frame)
type_entry.pack()

tk.Label(transaction_frame, text="Category:").pack()
category_entry = tk.Entry(transaction_frame)
category_entry.pack()

tk.Label(transaction_frame, text="Amount:").pack()
amount_entry = tk.Entry(transaction_frame)
amount_entry.pack()

tk.Label(transaction_frame, text="Description:").pack()
description_entry = tk.Entry(transaction_frame)
description_entry.pack()

tk.Label(transaction_frame, text="Date:").pack()
date_entry = tk.Entry(transaction_frame)
date_entry.pack()

tk.Button(transaction_frame, text="Add Transaction", command=add_transaction_ui).pack(pady=5)

budget_frame = tk.Frame(root)
budget_frame.pack(padx=10, pady=10)

tk.Label(budget_frame, text="Set Monthly Budget").pack()
tk.Label(budget_frame, text="Month:").pack()
month_entry = tk.Entry(budget_frame)
month_entry.pack()

tk.Label(budget_frame, text="Year:").pack()
year_entry = tk.Entry(budget_frame)
year_entry.pack()

tk.Label(budget_frame, text="Budget Amount:").pack()
budget_entry = tk.Entry(budget_frame)
budget_entry.pack()

tk.Button(budget_frame, text="Set Budget", command=lambda: add_monthly_budget(conn, month_entry.get(), year_entry.get(), float(budget_entry.get()))).pack(pady=5)

tk.Label(root, text="Transactions:").pack()
transactions_text = tk.Text(root, height=10)
transactions_text.pack(padx=10, pady=10)


from tkinter import ttk  
#styling
style = ttk.Style(root)
style.configure('TFrame', background='#f0f0f0')
style.configure('TLabel', background='#f0f0f0', font=('Arial', 12))
style.configure('TButton', font=('Arial', 12))
style.configure('TEntry', font=('Arial', 12))

tab_control = ttk.Notebook(root)

tab_months = ttk.Frame(tab_control)
tab_years = ttk.Frame(tab_control)

tab_control.add(tab_months, text='Months')
tab_control.add(tab_years, text='Years')

tab_control.pack(expand=1, fill='both')

root.mainloop()
