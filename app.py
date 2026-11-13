from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import plotly.express as px
import streamlit as st

try:
    import mysql.connector
except Exception:  # pragma: no cover
    mysql = None

ROOT = Path(__file__).resolve().parent
DB_FILE = ROOT / "sales_demo.db"


def is_sqlite_connection(conn: Any) -> bool:
    return conn.__class__.__module__.startswith("sqlite3")


def get_db_config() -> dict[str, Any]:
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "sales_analytics"),
    }


@st.cache_resource
def get_connection():
    db_type = os.getenv("DB_TYPE", "mysql")
    if db_type.lower() == "sqlite":
        conn = __import__("sqlite3").connect(DB_FILE, check_same_thread=False)
        conn.row_factory = __import__("sqlite3").Row
        return conn

    if mysql is None:
        st.warning("MySQL connector not installed. Falling back to SQLite demo database.")
        conn = __import__("sqlite3").connect(DB_FILE, check_same_thread=False)
        conn.row_factory = __import__("sqlite3").Row
        return conn

    try:
        conn = mysql.connector.connect(**get_db_config())
        conn.autocommit = True
        return conn
    except Exception:
        st.warning("Unable to connect to MySQL. Falling back to SQLite demo database.")
        conn = __import__("sqlite3").connect(DB_FILE, check_same_thread=False)
        conn.row_factory = __import__("sqlite3").Row
        return conn


def execute_sql(script: str) -> None:
    conn = get_connection()
    if is_sqlite_connection(conn):
        conn.executescript(script)
    else:
        for statement in [s.strip() for s in script.split(";") if s.strip()]:
            conn.cursor().execute(statement)
    conn.commit()


def init_db() -> None:
    schema_path = ROOT / "database" / "schema.sql"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    script = schema_path.read_text(encoding="utf-8")
    try:
        execute_sql(script)
    except Exception as exc:
        st.error(f"Failed to initialize database: {exc}")


def ensure_demo_data() -> None:
    conn = get_connection()
    if is_sqlite_connection(conn):
        tables = [
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('customers','products','orders','order_items','payments')"
            ).fetchall()
        ]
        if len(tables) == 5 and all(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] > 0 for table in tables):
            return
    else:
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("SHOW TABLES")
            tables = {row[f"Tables_in_{get_db_config()['database']}"] for row in cur.fetchall()}
            if {"customers", "products", "orders", "order_items", "payments"}.issubset(tables):
                counts = []
                for table in ["customers", "products", "orders", "order_items", "payments"]:
                    cur.execute(f"SELECT COUNT(*) AS c FROM {table}")
                    counts.append(cur.fetchone()["c"])
                if all(count > 0 for count in counts):
                    return
        except Exception:
            pass

    customers = [
        ("Alice Johnson", "alice@example.com", "555-0101", "123 Main St"),
        ("Brian Smith", "brian@example.com", "555-0102", "456 Oak Ave"),
        ("Carla Gomez", "carla@example.com", "555-0103", "789 Pine Rd"),
        ("David Lee", "david@example.com", "555-0104", "321 Birch Ln"),
    ]
    products = [
        ("Laptop Pro 14", "Electronics", 1200.00, 25),
        ("Wireless Mouse", "Accessories", 25.00, 200),
        ("4K Monitor", "Electronics", 520.00, 30),
        ("Mechanical Keyboard", "Accessories", 110.00, 60),
        ("USB-C Hub", "Accessories", 45.00, 120),
        ("Office Chair", "Furniture", 220.00, 20),
    ]

    if is_sqlite_connection(conn):
        cur = conn.cursor()
        existing_customers = cur.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        existing_products = cur.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if existing_customers == 0:
            cur.executemany(
                "INSERT INTO customers (name, email, phone, address) VALUES (?, ?, ?, ?)",
                customers,
            )
        if existing_products == 0:
            cur.executemany(
                "INSERT INTO products (name, category, price, stock_quantity) VALUES (?, ?, ?, ?)",
                products,
            )
        if cur.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0:
            order_rows = [
                (1, "2025-01-12 10:00:00", "Completed", 1175.00, "First order"),
                (2, "2025-02-18 12:30:00", "Completed", 610.00, "Bulk purchase"),
                (3, "2025-03-22 09:45:00", "Paid", 840.00, "Repeat customer"),
                (4, "2025-04-04 15:15:00", "Pending", 165.00, "New order"),
            ]
            for customer_id, order_date, status, total_amount, notes in order_rows:
                cur.execute(
                    "INSERT INTO orders (customer_id, order_date, status, total_amount, notes) VALUES (?, ?, ?, ?, ?)",
                    (customer_id, order_date, status, total_amount, notes),
                )

            order_items = [
                (1, 1, 1, 1200.00, 1200.00),
                (1, 5, 1, 45.00, 45.00),
                (2, 2, 10, 25.00, 250.00),
                (2, 4, 3, 110.00, 330.00),
                (3, 3, 1, 520.00, 520.00),
                (3, 5, 2, 45.00, 90.00),
                (4, 2, 2, 25.00, 50.00),
                (4, 6, 1, 220.00, 220.00),
            ]
            cur.executemany(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES (?, ?, ?, ?, ?)",
                order_items,
            )
            payments = [
                (1, "2025-01-12 10:30:00", "Card", 1175.00, "Paid"),
                (2, "2025-02-18 13:00:00", "Bank Transfer", 610.00, "Paid"),
                (3, "2025-03-22 10:00:00", "Card", 840.00, "Paid"),
                (4, "2025-04-04 15:30:00", "Cash", 165.00, "Pending"),
            ]
            cur.executemany(
                "INSERT INTO payments (order_id, payment_date, payment_method, amount_paid, payment_status) VALUES (?, ?, ?, ?, ?)",
                payments,
            )
        conn.commit()
        return

    cur = conn.cursor(dictionary=True)
    if cur.execute("SELECT COUNT(*) AS c FROM customers").fetchone()["c"] == 0:
        for row in customers:
            cur.execute(
                "INSERT INTO customers (name, email, phone, address) VALUES (%s, %s, %s, %s)",
                row,
            )
    if cur.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"] == 0:
        for row in products:
            cur.execute(
                "INSERT INTO products (name, category, price, stock_quantity) VALUES (%s, %s, %s, %s)",
                row,
            )
    if cur.execute("SELECT COUNT(*) AS c FROM orders").fetchone()["c"] == 0:
        for customer_id, order_date, status, total_amount, notes in [
            (1, "2025-01-12 10:00:00", "Completed", 1175.00, "First order"),
            (2, "2025-02-18 12:30:00", "Completed", 610.00, "Bulk purchase"),
            (3, "2025-03-22 09:45:00", "Paid", 840.00, "Repeat customer"),
            (4, "2025-04-04 15:15:00", "Pending", 165.00, "New order"),
        ]:
            cur.execute(
                "INSERT INTO orders (customer_id, order_date, status, total_amount, notes) VALUES (%s, %s, %s, %s, %s)",
                (customer_id, order_date, status, total_amount, notes),
            )

        for order_id, product_id, quantity, unit_price, subtotal in [
            (1, 1, 1, 1200.00, 1200.00),
            (1, 5, 1, 45.00, 45.00),
            (2, 2, 10, 25.00, 250.00),
            (2, 4, 3, 110.00, 330.00),
            (3, 3, 1, 520.00, 520.00),
            (3, 5, 2, 45.00, 90.00),
            (4, 2, 2, 25.00, 50.00),
            (4, 6, 1, 220.00, 220.00),
        ]:
            cur.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES (%s, %s, %s, %s, %s)",
                (order_id, product_id, quantity, unit_price, subtotal),
            )

        for order_id, payment_date, payment_method, amount_paid, payment_status in [
            (1, "2025-01-12 10:30:00", "Card", 1175.00, "Paid"),
            (2, "2025-02-18 13:00:00", "Bank Transfer", 610.00, "Paid"),
            (3, "2025-03-22 10:00:00", "Card", 840.00, "Paid"),
            (4, "2025-04-04 15:30:00", "Cash", 165.00, "Pending"),
        ]:
            cur.execute(
                "INSERT INTO payments (order_id, payment_date, payment_method, amount_paid, payment_status) VALUES (%s, %s, %s, %s, %s)",
                (order_id, payment_date, payment_method, amount_paid, payment_status),
            )
    conn.commit()


def fetch_table(table_name: str) -> pd.DataFrame:
    conn = get_connection()
    if is_sqlite_connection(conn):
        return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    cur = conn.cursor(dictionary=True)
    cur.execute(f"SELECT * FROM {table_name}")
    return pd.DataFrame(cur.fetchall())


def add_customer(name: str, email: str, phone: str, address: str) -> None:
    conn = get_connection()
    if is_sqlite_connection(conn):
        conn.execute(
            "INSERT INTO customers (name, email, phone, address) VALUES (?, ?, ?, ?)",
            (name, email, phone, address),
        )
    else:
        conn.cursor().execute(
            "INSERT INTO customers (name, email, phone, address) VALUES (%s, %s, %s, %s)",
            (name, email, phone, address),
        )
    conn.commit()


def add_product(name: str, category: str, price: float, stock_quantity: int) -> None:
    conn = get_connection()
    if is_sqlite_connection(conn):
        conn.execute(
            "INSERT INTO products (name, category, price, stock_quantity) VALUES (?, ?, ?, ?)",
            (name, category, price, stock_quantity),
        )
    else:
        conn.cursor().execute(
            "INSERT INTO products (name, category, price, stock_quantity) VALUES (%s, %s, %s, %s)",
            (name, category, price, stock_quantity),
        )
    conn.commit()


def add_order(customer_id: int, status: str, notes: str, items: Iterable[tuple[int, int]]) -> None:
    conn = get_connection()
    product_df = fetch_table("products")
    product_lookup = product_df.set_index("product_id").to_dict("index")
    total_amount = 0.0
    prepared_items = []
    for product_id, quantity in items:
        product = product_lookup.get(int(product_id), {})
        if not product:
            continue
        unit_price = float(product.get("price", 0.0))
        subtotal = unit_price * int(quantity)
        total_amount += subtotal
        prepared_items.append((product_id, quantity, unit_price, subtotal))

    if not prepared_items:
        return

    if is_sqlite_connection(conn):
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO orders (customer_id, order_date, status, total_amount, notes) VALUES (?, ?, ?, ?, ?)",
            (int(customer_id), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status, round(total_amount, 2), notes),
        )
        order_id = cur.lastrowid
        for product_id, quantity, unit_price, subtotal in prepared_items:
            cur.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES (?, ?, ?, ?, ?)",
                (order_id, int(product_id), quantity, unit_price, subtotal),
            )
        conn.commit()
    else:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "INSERT INTO orders (customer_id, order_date, status, total_amount, notes) VALUES (%s, %s, %s, %s, %s)",
            (int(customer_id), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status, round(total_amount, 2), notes),
        )
        order_id = cur.lastrowid
        for product_id, quantity, unit_price, subtotal in prepared_items:
            cur.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES (%s, %s, %s, %s, %s)",
                (order_id, int(product_id), quantity, unit_price, subtotal),
            )
        conn.commit()


def delete_record(table_name: str, key_name: str, record_id: int) -> None:
    conn = get_connection()
    if is_sqlite_connection(conn):
        conn.execute(f"DELETE FROM {table_name} WHERE {key_name} = ?", (record_id,))
    else:
        conn.cursor().execute(f"DELETE FROM {table_name} WHERE {key_name} = %s", (record_id,))
    conn.commit()


def export_csv(table_name: str) -> str:
    df = fetch_table(table_name)
    output_path = ROOT / f"{table_name}_export.csv"
    df.to_csv(output_path, index=False)
    return str(output_path)


st.set_page_config(page_title="Sales Analytics & Management System", page_icon="📊", layout="wide")

init_db()
ensure_demo_data()

st.title("Sales Analytics & Management System")

with st.sidebar:
    st.markdown("### Navigation")
    page = st.radio("Go to", ["Dashboard", "Customers", "Products", "Orders", "Reports", "Export"])

if page == "Dashboard":
    orders = fetch_table("orders")
    customers = fetch_table("customers")
    products = fetch_table("products")
    order_items = fetch_table("order_items")
    payments = fetch_table("payments")

    total_sales = float(orders["total_amount"].sum()) if not orders.empty else 0.0
    revenue = float(payments["amount_paid"].sum()) if not payments.empty else 0.0
    total_customers = int(customers["customer_id"].nunique()) if not customers.empty else 0
    total_products = int(products["product_id"].nunique()) if not products.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Sales", f"₹{total_sales:,.0f}")
    col2.metric("Revenue", f"₹{revenue:,.0f}")
    col3.metric("Customers", total_customers)
    col4.metric("Products", total_products)

    if not order_items.empty and not products.empty:
        order_items_with_names = order_items.merge(products[["product_id", "name"]], on="product_id", how="left")
        product_sales = order_items_with_names.groupby("name", as_index=False)["subtotal"].sum().sort_values("subtotal", ascending=False)
    else:
        product_sales = pd.DataFrame(columns=["name", "subtotal"])

    if not orders.empty:
        sales_df = orders.assign(order_date=pd.to_datetime(orders["order_date"]))
        sales_df["month"] = sales_df["order_date"].dt.strftime("%Y-%m")
        monthly_sales = sales_df.groupby("month", as_index=False)["total_amount"].sum()
    else:
        monthly_sales = pd.DataFrame(columns=["month", "total_amount"])

    left_col, right_col = st.columns(2)
    with left_col:
        st.subheader("Sales Trend")
        if not monthly_sales.empty:
            fig_line = px.line(monthly_sales, x="month", y="total_amount", markers=True)
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No sales data available.")
    with right_col:
        st.subheader("Top Products")
        if not product_sales.empty:
            fig_bar = px.bar(product_sales.head(5), x="name", y="subtotal", color="subtotal")
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No product sales data available.")

    st.subheader("Revenue by Product")
    if not product_sales.empty:
        fig_pie = px.pie(product_sales, values="subtotal", names="name", hole=0.45)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No product sales data available yet.")

elif page == "Customers":
    st.subheader("Customer Management")
    with st.form("add_customer_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        address = st.text_area("Address")
        submitted = st.form_submit_button("Add Customer")
        if submitted and name:
            add_customer(name, email, phone, address)
            st.success("Customer added successfully.")
            st.rerun()

    customer_df = fetch_table("customers")
    if not customer_df.empty:
        st.dataframe(customer_df, use_container_width=True)
        selected_customer = st.selectbox("Delete customer", customer_df["customer_id"].tolist())
        if st.button("Delete Selected Customer"):
            delete_record("customers", "customer_id", int(selected_customer))
            st.success("Customer deleted.")
            st.rerun()
    else:
        st.info("No customers found.")

elif page == "Products":
    st.subheader("Product Management")
    with st.form("add_product_form"):
        name = st.text_input("Product Name")
        category = st.text_input("Category")
        price = st.number_input("Price", min_value=0.0, step=1.0)
        stock_quantity = st.number_input("Stock Quantity", min_value=0, step=1)
        submitted = st.form_submit_button("Add Product")
        if submitted and name:
            add_product(name, category, float(price), int(stock_quantity))
            st.success("Product added successfully.")
            st.rerun()

    product_df = fetch_table("products")
    if not product_df.empty:
        st.dataframe(product_df, use_container_width=True)
        selected_product = st.selectbox("Delete product", product_df["product_id"].tolist())
        if st.button("Delete Selected Product"):
            delete_record("products", "product_id", int(selected_product))
            st.success("Product deleted.")
            st.rerun()
    else:
        st.info("No products found.")

elif page == "Orders":
    st.subheader("Order Management")
    customer_df = fetch_table("customers")
    product_df = fetch_table("products")

    if customer_df.empty or product_df.empty:
        st.warning("Add at least one customer and one product before creating orders.")
    else:
        with st.form("create_order_form"):
            customer_id = st.selectbox(
                "Customer",
                customer_df["customer_id"].tolist(),
                format_func=lambda cid: customer_df.loc[customer_df["customer_id"] == cid, "name"].iat[0],
            )
            status = st.selectbox("Status", ["Pending", "Paid", "Completed", "Cancelled"])
            notes = st.text_area("Notes")
            selected_items: list[tuple[int, int]] = []
            for _, product in product_df.iterrows():
                qty = st.number_input(f"{product['name']} qty", min_value=0, step=1, key=f"qty_{product['product_id']}")
                if qty > 0:
                    selected_items.append((int(product["product_id"]), int(qty)))
            if st.form_submit_button("Create Order"):
                if selected_items:
                    add_order(int(customer_id), status, notes, selected_items)
                    st.success("Order created successfully.")
                    st.rerun()
                else:
                    st.warning("Choose at least one product quantity.")

    orders_df = fetch_table("orders")
    if not orders_df.empty:
        st.dataframe(orders_df, use_container_width=True)
    else:
        st.info("No orders yet.")

elif page == "Reports":
    orders = fetch_table("orders")
    order_items = fetch_table("order_items")
    customers = fetch_table("customers")
    products = fetch_table("products")

    st.subheader("Monthly and yearly sales reports")
    if not orders.empty:
        sales_df = orders.assign(order_date=pd.to_datetime(orders["order_date"]))
        sales_df["month"] = sales_df["order_date"].dt.strftime("%Y-%m")
        monthly_sales = sales_df.groupby("month", as_index=False)["total_amount"].sum()
        st.bar_chart(monthly_sales.set_index("month")["total_amount"])

        best_products = order_items.merge(products[["product_id", "name"]], on="product_id")
        best_products = best_products.groupby("name", as_index=False)["subtotal"].sum().sort_values("subtotal", ascending=False)
        st.subheader("Best-selling products")
        st.dataframe(best_products, use_container_width=True)

        top_customers = orders.merge(customers[["customer_id", "name"]], on="customer_id").groupby("name", as_index=False)["total_amount"].sum().sort_values("total_amount", ascending=False)
        st.subheader("Top customers")
        st.dataframe(top_customers, use_container_width=True)

        revenue_profit = pd.DataFrame(
            {
                "Metric": ["Revenue", "Estimated Profit"],
                "Value": [float(orders["total_amount"].sum()), float(orders["total_amount"].sum() * 0.32)],
            }
        )
        st.subheader("Revenue and profit analysis")
        st.bar_chart(revenue_profit.set_index("Metric")["Value"])
    else:
        st.info("No sales records available for reporting.")

elif page == "Export":
    st.subheader("Export Data")
    table_name = st.selectbox("Table", ["customers", "products", "orders", "order_items", "payments"])
    if st.button("Export to CSV"):
        file_path = export_csv(table_name)
        st.success(f"Exported to {file_path}")
        with open(file_path, "rb") as data_file:
            st.download_button(
                "Download file",
                data=data_file.read(),
                file_name=f"{table_name}_export.csv",
                mime="text/csv",
            )

st.caption("Demo database: SQLite fallback is enabled when MySQL is unavailable.")
