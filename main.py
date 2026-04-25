from chat_downloader import ChatDownloader, errors
import scrapetube
from datetime import datetime
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from db import db
from config.sample import config

# Initialize DB
db.init_db()

def get_approved_channels():
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT channel_id FROM channels WHERE status = 'approved'")
            return [row[0] for row in cursor.fetchall()]
    finally:
        db.return_connection(conn)

def get_existing_stream_ids(channel_id):
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT stream_id FROM chats WHERE channel_id = %s", (channel_id,))
            return {row[0] for row in cursor.fetchall()}
    finally:
        db.return_connection(conn)

def update_last_updated(channel_id):
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE channels SET last_updated = %s WHERE channel_id = %s", (datetime.now(), channel_id))
            conn.commit()
    finally:
        db.return_connection(conn)

# Thread-safe print
print_lock = threading.Lock()

def process_video(vid, channel_id):
    stream_id = vid["videoId"]
    conn = db.get_connection()
    
    try:
        chat = ChatDownloader().get_chat(stream_id)
    except Exception as e:
        with print_lock:
            print(f"[ERROR] Failed to download chat for {stream_id}: {e}")
        db.return_connection(conn)
        return
    
    inserted_count = 0
    try:
        with conn.cursor() as cursor:
            for message in chat:
                try:
                    user_id = message["author"]["id"]
                    user_name = message["author"]["name"]
                    user_avatar = message["author"]["images"][0]["url"]
                    message_timestamp = message["time_in_seconds"]
                    message_content = message["message"]
                    time_of_message = message["timestamp"] / 1000000
                except Exception:
                    continue

                try:
                    cursor.execute("""
                        INSERT INTO chats 
                        (channel_id, stream_id, user_id, user_name, user_avatar, message_timestamp, message_origin_time, message_content)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                        (
                            channel_id,
                            stream_id,
                            user_id,
                            user_name,
                            user_avatar,
                            message_timestamp,
                            time_of_message,
                            message_content,
                        )
                    )
                    inserted_count += 1
                except Exception:
                    continue
            conn.commit()
    finally:
        db.return_connection(conn)

    with print_lock:
        print(f"[DONE] {stream_id}: Inserted {inserted_count} messages.")

def process_channel(channel_id):
    print(f"\nProcessing channel: {channel_id}")
    existing_stream_ids = get_existing_stream_ids(channel_id)
    
    # Get video list
    try:
        vids = scrapetube.get_channel(channel_id, content_type="streams")
        videos = [
            vid for vid in vids 
            if vid["videoId"] not in existing_stream_ids and 
               vid["thumbnailOverlays"][0]["thumbnailOverlayTimeStatusRenderer"]["style"] != "LIVE"
        ]
    except Exception as e:
        print(f"Error fetching videos for {channel_id}: {e}")
        return

    videos = videos[::-1]
    print(f"Found {len(videos)} unprocessed videos for {channel_id}.")

    if not videos:
        update_last_updated(channel_id)
        return

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_video, vid, channel_id) for vid in videos]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"[Thread Error] {e}")
    
    update_last_updated(channel_id)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--Channel", help="Specific Channel ID to process (bypasses DB status)")
    args = parser.parse_args()

    if args.Channel:
        process_channel(args.Channel)
    else:
        channels = get_approved_channels()
        if not channels:
            print("No approved channels found in database.")
            return
        
        print(f"Found {len(channels)} approved channels to process.")
        for channel_id in channels:
            process_channel(channel_id)

if __name__ == "__main__":
    main()
