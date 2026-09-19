# Gourmet Bistro Order and Revenue Tracker

A web-based order placement and revenue tracking system built with HTML, Python, and SQLite. The application enables customers to search menu items, place orders with quantity-based discounts, process cash or card payments, and allows administrators to view itemized sales reports.

## Features

* **Menu Browsing & Search**: Search across menu items[cite: 1, 2] with automatic retention of the 3 most recent search queries.
* **Dynamic Order Calculation**: Interactive order form with optional add-ons[cite: 1] that automatically applies a 10% discount for items ordered with a quantity of 3 or more.
* **Payment Processing**: Supports Cash and Card options, validates cash amount against total cost, prompts re-entry if payment is insufficient, and calculates change.
* **Database Integration**: Automatically creates and seeds an SQLite database (`bistro_order.db`) with initial menu items and logs submitted orders.
* **Admin Sales Dashboard**: Secure report route (`/sales?key=admin123`) displaying items sold, quantity counts, and aggregate revenue.

## Tech Stack

* **Backend Framework**: Python 
* **Database**: SQLite3
* **Frontend**: HTML5[cite: 1]

## Repository Structure

```text
.
├── index.html        # Main interface template (Menu, Search, Order Form)
├── main2.py          # Python application server and database logic
└── bistro_order.db   # SQLite database (automatically generated on startup)
