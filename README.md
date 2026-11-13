# Sales Analytics & Management System

A Python + MySQL + Streamlit project for managing customers, products, orders, and payments with analytics dashboards and sales reports.

## Features

- Admin dashboard with KPI cards
- Customer management
- Product management
- Order management
- Automatic sales calculation
- Monthly and yearly sales reports
- Best-selling products and top customers
- Revenue and profit analysis
- Interactive charts and filters
- CSV export / database backup

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
3. Configure MySQL in environment variables or `.env`:
   ```env
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

If MySQL is not available, the app automatically falls back to a local SQLite database for demonstration and testing.

## Database design

The schema includes the following tables:

- customers
- products
- orders
- order_items
- payments

## Sample data

The app seeds the database automatically with a small demo dataset when tables are empty.
