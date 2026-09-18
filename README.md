# Gourmet Bistro Order & Revenue Tracker

A full-stack local web application built with Python, HTML5, and SQLite. This project transitions a command-line terminal script into a functional web server that handles menu searches, order calculations, cash payment validation, and sales analytics.

---

## Key Features & Business Logic

### 1. Menu Search & 3-Item History Buffer (Option 1 & Option 4)
* **Dynamic Search:** Queries the SQLite database for menu items using case-insensitive SQL matching (`LIKE %query%`).
* **Ring Buffer History:** Maintains an array in memory that tracks the 3 most recent search terms, automatically cycling out older queries when new ones are made.

### 2. Order Processing & Bulk Discounts (Option 2)
* **Automated 10% Discount:** Evaluates each selected item's quantity. If quantity $\ge 3$, a 10% discount is applied to that item's total cost (`(unit_price * qty) * 0.90`).
* **Two-Step Checkout Flow:** Python processes the grand total on a review page before asking for payment input.
* **Cash Validation & Change Calculation:**
  * Compares `cash_paid` against `grand_total`.
  * If `cash_paid < grand_total`, blocks database insertion and displays the remaining balance owed.
  * If `cash_paid >= grand_total`, calculates exact change due (`cash_paid - grand_total`) and saves the transaction.

### 3. Sales Revenue Analytics (Option 3)
* Aggregates revenue data directly from the `orders` table using an optimized SQL query:
  ```sql
  SELECT menu_name, SUM(qty) AS total_qty, SUM(total_price) AS total_revenue
  FROM orders
  GROUP BY menu_name
  HAVING SUM(total_price) > 0;
