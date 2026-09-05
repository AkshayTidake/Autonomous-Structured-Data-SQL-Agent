import sqlite3

class MockSQLiteDatabase:
    def __init__(self,db_path):
        self.db_path = db_path

    def seed_mock_enterprise_database(self):

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

         # 1. Create Tables
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY,
            name TEXT,
            country TEXT,
            tier TEXT
        )""")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT,
            category TEXT,
            price REAL
        )""")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            product_id INTEGER,
            order_date TEXT,
            quantity INTEGER,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY(product_id) REFERENCES products(product_id)
        )""")

           
        # 2. Check if already seeded to prevent duplicate inserts
        cursor.execute("SELECT COUNT(*) FROM customers")
        if cursor.fetchone()[0] == 0:
            # Seed Customers
            cursor.executemany("INSERT INTO customers VALUES (?,?,?,?)", [
                (1, 'Alice Smith', 'USA', 'Premium'),
                (2, 'Bob Jones', 'Canada', 'Standard'),
                (3, 'Charlie Brown', 'USA', 'Standard'),
                (4, 'Diana Prince', 'UK', 'Premium')
            ])
            # Seed Products
            cursor.executemany("INSERT INTO products VALUES (?,?,?,?)", [
                (101, 'AI Software License', 'SaaS', 1200.00),
                (102, 'Cloud Storage Suite', 'Infrastructure', 450.00),
                (103, 'Developer Pro Laptop', 'Hardware', 2500.00)
            ])
            # Seed Orders
            cursor.executemany("INSERT INTO orders VALUES (?,?,?,?,?)", [
                (501, 1, 101, '2026-01-15', 2),  # Alice bought 2 AI Licenses ($2400)
                (502, 2, 102, '2026-02-10', 1),  # Bob bought Cloud Storage ($450)
                (503, 1, 103, '2026-03-01', 1),  # Alice bought Laptop ($2500)
                (504, 4, 101, '2026-04-12', 5),  # Diana bought 5 AI Licenses ($6000)
                (505, 3, 102, '2026-05-20', 3)   # Charlie bought 3 Cloud Storage ($1350)
            ])
            conn.commit()
        conn.close()



