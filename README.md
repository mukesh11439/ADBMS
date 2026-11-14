# Sales Analytics & Management System

A Python + MySQL + Streamlit project for managing customers, products, orders, and payments with analytics dashboards and sales reports.

## Features

- KPI dashboard with sales, revenue, pending-order, and low-stock metrics
- Customer and product management with search/category filters
- Order creation with automatic totals and stock deduction
- Full inventory view with editable stock quantities and low-stock alerts
- Order status management and filtering
- Monthly sales, best-selling products, and top-customer reports
- Interactive charts and downloadable CSV exports

## Stack

- Python
- MySQL
- Streamlit
- Pandas
- Plotly

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. By default, the app uses SQLite for local demo/testing. If you want MySQL instead, set these environment variables or add a `.env` file:
   ```env
   DB_TYPE=mysql
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=sales_analytics
   ```
4. Run the app:
   ```bash
   streamlit run app.py
   ```

If MySQL is not configured or is unavailable, the app automatically falls back to the local SQLite database file `sales_demo.db`.

## Database design

The schema includes the following tables:

- customers
- products
- orders
- order_items
- payments

## Sample data

The app adds a repeat-safe demo catalog of 12 customers and 14 products, plus starter orders and payments when the database is empty. Existing customers and products are preserved; missing demo entries are added once. The sample data is synthetic and can be removed from the Customers and Products pages.

The SQLite database and generated CSV exports are local runtime files and are intentionally excluded from Git. A fresh clone creates the database and demo data automatically on first run.
