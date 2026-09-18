import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__, template_folder=".")

# Option 4 tracking: Fixed ring buffer for the 3 most recent search terms
search_history = []


def init_db():
    conn = sqlite3.connect("bistro_order.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            category TEXT,
            price REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            email TEXT,
            menu_name TEXT,
            category TEXT,
            qty INTEGER,
            total_price REAL,
            payment_type TEXT
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM menu")
    if cursor.fetchone()[0] == 0:
        cursor.executescript("""
            INSERT INTO menu (name, category, price) VALUES
            ('Truffle Fries', 'Starters', 8.50),
            ('Garlic Butter Steak', 'Main Course', 24.00),
            ('Creamy Mushroom Pasta', 'Main Course', 16.50),
            ('Chocolate Lava Cake', 'Desserts', 7.00),
            ('Iced Lemon Tea', 'Drinks', 3.50),
            ('Extra Sauce', 'Add-Ons', 1.00),
            ('Rush Delivery', 'Add-Ons', 10.00);
        """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("index.html")


# OPTION 1: Search Menu (Stores up to 3 queries in search_history)
@app.route("/search", methods=["GET"])
def search_menu():
    global search_history
    query = request.args.get("query", "").strip()

    results = []
    if query:
        # Maintain max 3 entries in history
        if len(search_history) >= 3:
            search_history.pop(0)
        search_history.append(query)

        conn = sqlite3.connect("bistro_order.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, category, price FROM menu WHERE LOWER(name) LIKE ?",
            (f"%{query.lower()}%",),
        )
        results = cursor.fetchall()
        conn.close()

    results_html = (
        "".join([
            f"<li><b>{row[0]}</b> ({row[1]}) - ${row[2]:.2f}</li>"
            for row in results
        ])
        if results
        else "<li>No matching menu items found.</li>"
    )

    return f"""
        <div style="text-align: center; font-family: sans-serif; margin-top: 50px;">
            <h2>Search Results for "{query}"</h2>
            <ul style="list-style: none; padding: 0;">{results_html}</ul>
            <br><a href="/">Back to Home</a>
        </div>
    """


# OPTION 4: Search History (Displays the last 3 searches)
@app.route("/history")
def view_history():
    history_html = (
        "".join([f"<li>{term}</li>" for term in reversed(search_history)])
        if search_history
        else "<li>No searches recorded yet.</li>"
    )

    return f"""
        <div style="text-align: center; font-family: sans-serif; margin-top: 50px;">
            <h2>Search History (Last 3 Searches)</h2>
            <ul style="list-style: none; padding: 0;">{history_html}</ul>
            <br><a href="/">Back to Home</a>
        </div>
    """


# OPTION 3: View Sales Report (Aggregates revenue using SQL GROUP BY)
@app.route("/sales")
def view_sales():
    conn = sqlite3.connect("bistro_order.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT menu_name, SUM(qty) AS total_qty, SUM(total_price) AS total_revenue
        FROM orders
        GROUP BY menu_name
        HAVING SUM(total_price) > 0;
    """)

    results = cursor.fetchall()
    conn.close()

    rows = (
        "".join([
            f"<tr><td style='border:1px solid black; padding:8px;'>{r[0]}</td><td style='border:1px solid black; padding:8px;'>{r[1]}</td><td style='border:1px solid black; padding:8px;'>${r[2]:.2f}</td></tr>"
            for r in results
        ])
        if results
        else "<tr><td colspan='3' style='padding:8px;'>No sales recorded yet.</td></tr>"
    )

    return f"""
        <div style="text-align: center; font-family: sans-serif; margin-top: 50px;">
            <h2>Sales Revenue Report</h2>
            <table style="border: 1px solid black; margin: auto; border-collapse: collapse;">
                <tr>
                    <th style="border:1px solid black; padding:8px;">Item Name</th>
                    <th style="border:1px solid black; padding:8px;">Quantity Sold</th>
                    <th style="border:1px solid black; padding:8px;">Total Revenue</th>
                </tr>
                {rows}
            </table>
            <br><a href="/">Back to Home</a>
        </div>
    """


# OPTION 2: Process Order (Calculates 10% discount, validates cash, computes change)
@app.route("/submit", methods=["POST"])
def submit_order():
    customer_name = request.form.get("customer_name")
    email = request.form.get("email")
    payment = request.form.get("payment")

    cash_raw = request.form.get("cash_paid")
    cash_paid = float(cash_raw) if cash_raw and cash_raw.strip() else 0.0

    conn = sqlite3.connect("bistro_order.db")
    cursor = conn.cursor()

    cursor.execute("SELECT name, category, price FROM menu")
    menu_catalog = {
        row[0]: {"category": row[1], "price": row[2]}
        for row in cursor.fetchall()
    }

    items_config = [
        ("food_fries", "qty_fries"),
        ("food_steak", "qty_steak"),
        ("food_pasta", "qty_pasta"),
        ("food_cake", "qty_cake"),
        ("food_tea", "qty_tea"),
        ("food_sauce", "qty_sauce"),
        ("food_rush", None),
    ]

    processed_orders = []
    grand_total = 0.0

    for food_key, qty_key in items_config:
        item_name = request.form.get(food_key)

        if item_name and item_name in menu_catalog:
            qty = (
                int(request.form.get(qty_key, 1))
                if qty_key and request.form.get(qty_key)
                else 1
            )
            unit_price = menu_catalog[item_name]["price"]
            category = menu_catalog[item_name]["category"]

            # 10% discount applied when qty >= 3
            if qty >= 3:
                total_price = (unit_price * qty) * 0.90
            else:
                total_price = unit_price * qty

            grand_total += total_price
            processed_orders.append((item_name, category, qty, total_price))

    if not processed_orders:
        conn.close()
        return "<h2>No items selected!</h2><br><a href='/'>Back to Form</a>"

    # Payment insufficient retry check
    if payment == "Cash" and cash_paid < grand_total:
        conn.close()
        return f"""
            <div style="text-align: center; font-family: sans-serif; margin-top: 50px;">
                <h1 style="color: red;">Payment Insufficient!</h1>
                <p>Order Total: <b>${grand_total:.2f}</b></p>
                <p>Cash Provided: <b>${cash_paid:.2f}</b></p>
                <h3>Amount Remaining: ${grand_total - cash_paid:.2f}</h3>
                <br>
                <a href="javascript:history.back()">Go Back and Retry Payment</a>
            </div>
        """

    # Record entries into SQLite database
    for item_name, category, qty, total_price in processed_orders:
        cursor.execute(
            """
            INSERT INTO orders (customer_name, email, menu_name, category, qty, total_price, payment_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                customer_name,
                email,
                item_name,
                category,
                qty,
                total_price,
                payment,
            ),
        )

    conn.commit()
    conn.close()

    change = cash_paid - grand_total if payment == "Cash" else 0.0
    summary_list = "".join([
        f"<li>{item[0]} (x{item[2]}) - ${item[3]:.2f}</li>"
        for item in processed_orders
    ])

    return f"""
        <div style="text-align: center; font-family: sans-serif; margin-top: 50px;">
            <h1>Payment Success!</h1>
            <p>Customer: <b>{customer_name}</b> ({email})</p>
            <p>Payment Method: <b>{payment}</b></p>
            <h3>Purchased Items:</h3>
            <ul style="list-style: none; padding: 0;">{summary_list}</ul>
            <h2>Grand Total: ${grand_total:.2f}</h2>
            {"<h3>Cash Paid: $" + f"{cash_paid:.2f}" + " | Change Due: $" + f"{change:.2f}" + "</h3>" if payment == "Cash" else ""}
            <br>
            <a href="/">Place Another Order</a>
        </div>
    """

if __name__ == "__main__":
    init_db()
    app.run(debug=True)