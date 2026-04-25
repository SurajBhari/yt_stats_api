import sqlite3
import os
from db import db

def migrate():
    # Initialize PostgreSQL
    db.init_db()
    pg_conn = db.get_connection()
    
    try:
        # Find all sqlite .db files
        db_files = [f for f in os.listdir(".") if f.endswith(".db") and f != "database.db"]
        
        for db_file in db_files:
            channel_id = db_file.replace(".db", "")
            print(f"Migrating data for channel: {channel_id} from {db_file}...")
            
            sqlite_conn = sqlite3.connect(db_file)
            sqlite_cursor = sqlite_conn.cursor()
            
            try:
                sqlite_cursor.execute("SELECT stream_id, user_id, user_name, user_avatar, message_timestamp, message_origin_time, message_content FROM CHATS")
                rows = sqlite_cursor.fetchall()
                
                if not rows:
                    print(f"No data found in {db_file}")
                    continue
                
                with pg_conn.cursor() as pg_cursor:
                    # Use execute_batch or similar for performance, but simple execute for now
                    inserted = 0
                    for row in rows:
                        try:
                            pg_cursor.execute("""
                                INSERT INTO chats 
                                (channel_id, stream_id, user_id, user_name, user_avatar, message_timestamp, message_origin_time, message_content)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """, (channel_id, *row))
                            inserted += 1
                        except Exception as e:
                            print(f"Error inserting row: {e}")
                            continue
                    
                    pg_conn.commit()
                    print(f"Successfully migrated {inserted} rows for {channel_id}.")
                    
            except sqlite3.Error as e:
                print(f"Error reading SQLite database {db_file}: {e}")
            finally:
                sqlite_conn.close()
                
    finally:
        db.return_connection(pg_conn)
        print("Migration complete.")

if __name__ == "__main__":
    migrate()
