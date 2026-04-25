import sys
from db import db

def list_tables():
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            return [row[0] for row in cursor.fetchall()]
    finally:
        db.return_connection(conn)

def drop_all_tables():
    tables = list_tables()
    if not tables:
        print("No tables found.")
        return

    print(f"WARNING: You are about to drop ALL tables: {', '.join(tables)}")
    confirm1 = input("Are you absolutely sure? (y/N): ")
    if confirm1.lower() != 'y':
        print("Aborted.")
        return
    
    confirm2 = input("This will DELETE ALL DATA. Type 'DELETE ALL' to confirm: ")
    if confirm2 != 'DELETE ALL':
        print("Confirmation failed. Aborted.")
        return

    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            for table in tables:
                print(f"Dropping table: {table}")
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            conn.commit()
        print("All tables dropped successfully.")
    except Exception as e:
        print(f"Error dropping tables: {e}")
    finally:
        db.return_connection(conn)

def drop_table():
    tables = list_tables()
    if not tables:
        print("No tables found.")
        return

    print("\nAvailable tables:")
    for i, table in enumerate(tables, 1):
        print(f"{i}. {table}")
    
    try:
        choice = int(input("\nEnter the number of the table to drop (0 to cancel): "))
        if choice == 0:
            return
        if 1 <= choice <= len(tables):
            table_to_drop = tables[choice-1]
            confirm = input(f"Are you sure you want to drop '{table_to_drop}'? (y/N): ")
            if confirm.lower() == 'y':
                conn = db.get_connection()
                try:
                    with conn.cursor() as cursor:
                        cursor.execute(f"DROP TABLE IF EXISTS {table_to_drop} CASCADE")
                        conn.commit()
                    print(f"Table '{table_to_drop}' dropped successfully.")
                finally:
                    db.return_connection(conn)
            else:
                print("Aborted.")
        else:
            print("Invalid choice.")
    except ValueError:
        print("Please enter a valid number.")

def main():
    while True:
        print("\n--- DB Maintenance Task ---")
        print("1. List all tables")
        print("2. Drop a specific table")
        print("3. Drop ALL tables (Nuclear Option)")
        print("4. Initialize/Sync DB (Run init_db)")
        print("5. Exit")
        
        choice = input("\nSelect an option: ")
        
        if choice == '1':
            tables = list_tables()
            print("\nTables:", ", ".join(tables) if tables else "None")
        elif choice == '2':
            drop_table()
        elif choice == '3':
            drop_all_tables()
        elif choice == '4':
            print("Initializing database...")
            db.init_db()
            print("Done.")
        elif choice == '5':
            print("Exiting.")
            break
        else:
            print("Invalid selection.")

if __name__ == "__main__":
    main()
