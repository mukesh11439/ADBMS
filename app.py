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
    db_type = (os.getenv("DB_TYPE") or "sqlite").strip().lower()

    if db_type == "sqlite":
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
    customers = [
        ("Alice Johnson", "alice@example.com", "555-0101", "123 Main St"),
        ("Brian Smith", "brian@example.com", "555-0102", "456 Oak Ave"),
        ("Carla Gomez", "carla@example.com", "555-0103", "789 Pine Rd"),
        ("David Lee", "david@example.com", "555-0104", "321 Birch Ln"),
        ("Emma Wilson", "emma@example.com", "555-0105", "18 Lake View Rd"),
        ("Farhan Khan", "farhan@example.com", "555-0106", "44 Green Park"),
        ("Grace Chen", "grace@example.com", "555-0107", "72 Hill Street"),
        ("Harish Patel", "harish@example.com", "555-0108", "9 Market Road"),
        ("Isha Sharma", "isha@example.com", "555-0109", "56 River Lane"),
        ("Jack Turner", "jack@example.com", "555-0110", "31 Sunrise Avenue"),
        ("Kavya Rao", "kavya@example.com", "555-0111", "20 Garden Street"),
        ("Leo Martin", "leo@example.com", "555-0112", "85 Central Avenue"),
    ]
    products = [
        ("Laptop Pro 14", "Electronics", 1200.00, 25),
        ("Wireless Mouse", "Accessories", 25.00, 200),
        ("4K Monitor", "Electronics", 520.00, 30),
        ("Mechanical Keyboard", "Accessories", 110.00, 60),
        ("USB-C Hub", "Accessories", 45.00, 120),
        ("Office Chair", "Furniture", 220.00, 20),
        ("Noise-Cancelling Headphones", "Audio", 180.00, 35),
        ("Webcam HD", "Electronics", 75.00, 50),
        ("Bluetooth Speaker", "Audio", 95.00, 40),
        ("Desk Lamp", "Furniture", 38.00, 65),
        ("Laptop Stand", "Accessories", 42.00, 55),
        ("Portable SSD 1TB", "Storage", 130.00, 28),
        ("Wi-Fi Router", "Networking", 89.00, 32),
        ("Smartphone 128GB", "Electronics", 699.00, 4),
    ]

    if is_sqlite_connection(conn):
        cur = conn.cursor()
        for customer in customers:
            cur.execute("SELECT 1 FROM customers WHERE email = ?", (customer[1],))
            if cur.fetchone() is None:
                cur.execute(
                    "INSERT INTO customers (name, email, phone, address) VALUES (?, ?, ?, ?)",
                    customer,
                )
        for product in products:
            cur.execute("SELECT 1 FROM products WHERE name = ?", (product[0],))
            if cur.fetchone() is None:
                cur.execute(
                    "INSERT INTO products (name, category, price, stock_quantity) VALUES (?, ?, ?, ?)",
                    product,
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
    for customer in customers:
        cur.execute("SELECT 1 FROM customers WHERE email = %s", (customer[1],))
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO customers (name, email, phone, address) VALUES (%s, %s, %s, %s)",
                customer,
            )
    for product in products:
        cur.execute("SELECT 1 FROM products WHERE name = %s", (product[0],))
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO products (name, category, price, stock_quantity) VALUES (%s, %s, %s, %s)",
                product,
            )
    cur.execute("SELECT COUNT(*) AS c FROM orders")
    if cur.fetchone()["c"] == 0:
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
            raise ValueError(f"Product {product_id} was not found.")
        if int(quantity) <= 0:
            raise ValueError("Order quantities must be greater than zero.")
        if int(quantity) > int(product["stock_quantity"]):
            raise ValueError(f"Not enough stock for {product['name']}.")
        unit_price = float(product.get("price", 0.0))
        subtotal = unit_price * int(quantity)
        total_amount += subtotal
        prepared_items.append((int(product_id), int(quantity), unit_price, subtotal))

    if not prepared_items:
        raise ValueError("Choose at least one product quantity.")

    if is_sqlite_connection(conn):
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO orders (customer_id, order_date, status, total_amount, notes) VALUES (?, ?, ?, ?, ?)",
                (int(customer_id), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status, round(total_amount, 2), notes),
            )
            order_id = cur.lastrowid
            for product_id, quantity, unit_price, subtotal in prepared_items:
                cur.execute(
                    "UPDATE products SET stock_quantity = stock_quantity - ? WHERE product_id = ? AND stock_quantity >= ?",
                    (quantity, product_id, quantity),
                )
                if cur.rowcount != 1:
                    raise ValueError("Stock changed while creating the order. Refresh and try again.")
                cur.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES (?, ?, ?, ?, ?)",
                    (order_id, product_id, quantity, unit_price, subtotal),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    else:
        conn.start_transaction()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO orders (customer_id, order_date, status, total_amount, notes) VALUES (%s, %s, %s, %s, %s)",
                (int(customer_id), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status, round(total_amount, 2), notes),
            )
            order_id = cur.lastrowid
            for product_id, quantity, unit_price, subtotal in prepared_items:
                cur.execute(
                    "UPDATE products SET stock_quantity = stock_quantity - %s WHERE product_id = %s AND stock_quantity >= %s",
                    (quantity, product_id, quantity),
                )
                if cur.rowcount != 1:
                    raise ValueError("Stock changed while creating the order. Refresh and try again.")
                cur.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES (%s, %s, %s, %s, %s)",
                    (order_id, product_id, quantity, unit_price, subtotal),
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def update_order_status(order_id: int, status: str) -> None:
    conn = get_connection()
    if is_sqlite_connection(conn):
        conn.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
    else:
        conn.cursor().execute("UPDATE orders SET status = %s WHERE order_id = %s", (status, order_id))
    conn.commit()


def update_product_stock(product_id: int, stock_quantity: int) -> None:
    conn = get_connection()
    if is_sqlite_connection(conn):
        conn.execute(
            "UPDATE products SET stock_quantity = ? WHERE product_id = ?",
            (stock_quantity, product_id),
        )
    else:
        conn.cursor().execute(
            "UPDATE products SET stock_quantity = %s WHERE product_id = %s",
            (stock_quantity, product_id),
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
    page = st.radio("Go to", ["Dashboard", "Customers", "Products", "Inventory", "Orders", "Reports", "Export"])

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
    pending_orders = int(orders["status"].isin(["Pending"]).sum()) if not orders.empty else 0
    low_stock_count = int((products["stock_quantity"] <= 5).sum()) if not products.empty else 0

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total Sales", f"₹{total_sales:,.0f}")
    col2.metric("Revenue", f"₹{revenue:,.0f}")
    col3.metric("Customers", total_customers)
    col4.metric("Products", total_products)
    col5.metric("Pending Orders", pending_orders)
    col6.metric("Low Stock Items", low_stock_count)
    if low_stock_count:
        st.warning(f"{low_stock_count} product(s) have 5 or fewer units in stock. Review the Inventory page.")

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
            st.plotly_chart(fig_line, width="stretch")
        else:
            st.info("No sales data available.")
    with right_col:
        st.subheader("Top Products")
        if not product_sales.empty:
            fig_bar = px.bar(product_sales.head(5), x="name", y="subtotal", color="subtotal")
            st.plotly_chart(fig_bar, width="stretch")
        else:
            st.info("No product sales data available.")

    st.subheader("Revenue by Product")
    if not product_sales.empty:
        fig_pie = px.pie(product_sales, values="subtotal", names="name", hole=0.45)
        st.plotly_chart(fig_pie, width="stretch")
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
        query = st.text_input("Search customers by name, email, or phone")
        if query:
            searchable = customer_df[["name", "email", "phone"]].fillna("").astype(str).agg(" ".join, axis=1)
            customer_df = customer_df[searchable.str.contains(query, case=False, regex=False)]
        st.caption(f"{len(customer_df)} customer(s) shown")
        st.dataframe(customer_df, width="stretch")
    all_customers = fetch_table("customers")
    if not all_customers.empty:
        selected_customer = st.selectbox("Delete customer", all_customers["customer_id"].tolist())
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
        categories = ["All"] + sorted(product_df["category"].dropna().unique().tolist())
        category = st.selectbox("Filter by category", categories)
        if category != "All":
            product_df = product_df[product_df["category"] == category]
        st.dataframe(product_df, width="stretch")
        st.caption(f"{len(product_df)} product(s) shown")
        product_df = fetch_table("products")
        selected_product = st.selectbox("Delete product", product_df["product_id"].tolist())
        if st.button("Delete Selected Product"):
            delete_record("products", "product_id", int(selected_product))
            st.success("Product deleted.")
            st.rerun()
    else:
        st.info("No products found.")

elif page == "Inventory":
    st.subheader("Inventory Management")
    product_df = fetch_table("products")
    if product_df.empty:
        st.info("Add products to start managing inventory.")
    else:
        threshold = st.number_input("Low-stock threshold", min_value=0, value=5, step=1)
        low_stock = product_df[product_df["stock_quantity"] <= threshold]
        if low_stock.empty:
            st.success("No products are below the selected stock threshold.")
        else:
            st.warning(f"{len(low_stock)} product(s) are at or below {threshold} units.")

        show_low_stock_only = st.checkbox("Show only low-stock products", value=False)
        inventory_view = low_stock if show_low_stock_only else product_df
        st.caption("Edit the Available Stock cells, then select Save Inventory Changes.")
        with st.form("inventory_editor_form"):
            edited_inventory = st.data_editor(
                inventory_view[["product_id", "name", "category", "price", "stock_quantity"]],
                column_config={
                    "product_id": st.column_config.NumberColumn("ID", disabled=True),
                    "name": st.column_config.TextColumn("Product", disabled=True),
                    "category": st.column_config.TextColumn("Category", disabled=True),
                    "price": st.column_config.NumberColumn("Price", format="₹%.2f", disabled=True),
                    "stock_quantity": st.column_config.NumberColumn(
                        "Available Stock",
                        min_value=0,
                        step=1,
                    ),
                },
                disabled=["product_id", "name", "category", "price"],
                hide_index=True,
                width="stretch",
                key="inventory_stock_editor",
            )
            save_inventory = st.form_submit_button("Save Inventory Changes")

        if save_inventory:
            changed_stock = edited_inventory[["product_id", "stock_quantity"]].merge(
                product_df[["product_id", "stock_quantity"]],
                on="product_id",
                suffixes=("_edited", "_current"),
            )
            changed_stock = changed_stock[
                changed_stock["stock_quantity_edited"] != changed_stock["stock_quantity_current"]
            ]
            for row in changed_stock.itertuples(index=False):
                update_product_stock(int(row.product_id), int(row.stock_quantity_edited))
            if changed_stock.empty:
                st.info("No stock values were changed.")
            else:
                st.success(f"Updated stock for {len(changed_stock)} product(s).")
                st.rerun()

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
                qty = st.number_input(
                    f"{product['name']} — ₹{float(product['price']):,.2f} ({int(product['stock_quantity'])} in stock)",
                    min_value=0,
                    max_value=int(product["stock_quantity"]),
                    step=1,
                    key=f"qty_{product['product_id']}",
                )
                if qty > 0:
                    selected_items.append((int(product["product_id"]), int(qty)))
            if st.form_submit_button("Create Order"):
                try:
                    add_order(int(customer_id), status, notes, selected_items)
                    st.success("Order created successfully.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    orders_df = fetch_table("orders")
    if not orders_df.empty:
        statuses = ["All"] + sorted(orders_df["status"].dropna().unique().tolist())
        order_status = st.selectbox("Filter orders by status", statuses)
        visible_orders = orders_df if order_status == "All" else orders_df[orders_df["status"] == order_status]
        st.dataframe(visible_orders, width="stretch")
        order_id = st.selectbox("Update order status", orders_df["order_id"].tolist())
        new_status = st.selectbox("New status", ["Pending", "Paid", "Completed", "Cancelled"])
        if st.button("Save Order Status"):
            update_order_status(int(order_id), new_status)
            st.success("Order status updated.")
            st.rerun()
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
        st.dataframe(best_products, width="stretch")

        top_customers = orders.merge(customers[["customer_id", "name"]], on="customer_id").groupby("name", as_index=False)["total_amount"].sum().sort_values("total_amount", ascending=False)
        st.subheader("Top customers")
        st.dataframe(top_customers, width="stretch")

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
