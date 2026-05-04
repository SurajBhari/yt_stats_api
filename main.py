from chat_downloader.sites import YouTubeChatDownloader
from chat_downloader import ChatDownloader
import scrapetube
from datetime import datetime
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from db import db
import os
from config import config
import random
from tqdm import tqdm
import time

# Initialize DB
db.init_db()
cookies = ""
if "cookies.txt" in os.listdir():
    cookies = "cookies.txt"
else:
    cookies = None
    print("Cookies not found. Please add cookies.txt to the directory.")

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
            # Check both processed_videos and chats table (for legacy data)
            cursor.execute("""
                SELECT video_id FROM processed_videos WHERE channel_id = %s
                UNION
                SELECT DISTINCT stream_id FROM chats WHERE channel_id = %s
            """, (channel_id, channel_id))
            return {row[0] for row in cursor.fetchall()}
    finally:
        db.return_connection(conn)

def mark_video_processed(video_id, channel_id, status, message_count=0):
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO processed_videos (video_id, channel_id, status, message_count)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (video_id) DO UPDATE SET 
                    status = EXCLUDED.status,
                    message_count = EXCLUDED.message_count,
                    processed_at = CURRENT_TIMESTAMP
            """, (video_id, channel_id, status, message_count))
            conn.commit()
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

def process_video(vid, channel_id, pbar=None):
    stream_id = vid["videoId"]
    
    try:
        chat = ChatDownloader(cookies=cookies).get_chat(stream_id)
    except Exception as e:
        error_msg = str(e)
        log_msg = f"[ERROR] Failed to download chat for {stream_id}: {error_msg}"
        if pbar:
            pbar.write(log_msg)
        else:
            with print_lock:
                print(log_msg)
        
        # If live chat is not available, mark it as such so we don't retry
        if "Live chat replay is not available" in error_msg:
            mark_video_processed(stream_id, channel_id, 'no_replay')
        elif "No chat found" in error_msg: # Some other potential error strings
            mark_video_processed(stream_id, channel_id, 'no_chat')
        
        return
    
    conn = db.get_connection()
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
                except Exception as e:
                    print(f"[ERROR] Failed to insert message: {message} error: {e}")
                    continue
            conn.commit()
    finally:
        db.return_connection(conn)

    # Mark as processed with the count of messages
    status = 'success' if inserted_count > 0 else 'no_chat'
    mark_video_processed(stream_id, channel_id, status, inserted_count)

    log_msg = f"[DONE] {stream_id}: Inserted {inserted_count} messages."
    if pbar:
        pbar.write(log_msg)
    else:
        with print_lock:
            print(log_msg)

def get_unprocessed_videos(channel_id):
    existing_stream_ids = get_existing_stream_ids(channel_id)
    
    try:
        vids = scrapetube.get_channel(channel_id, content_type="streams")
        videos = [
            (vid, channel_id) for vid in vids 
            if vid["videoId"] not in existing_stream_ids and 
               vid["thumbnailOverlays"][0]["thumbnailOverlayTimeStatusRenderer"]["style"] != "LIVE"
        ]
        return videos[::-1] # Oldest first
    except Exception as e:
        print(f"Error fetching videos for {channel_id}: {e}")
        return []

def process_all_videos(all_tasks, max_workers=1):
    if not all_tasks:
        return

    print(f"Starting processing of {len(all_tasks)} videos using {max_workers} threads...")
    
    # Custom bar format to meet user requirements
    bar_format = "{desc}: {percentage:3.2f}% | {n_fmt}/{total_fmt} | Speed: {rate_fmt} | ETA: {remaining} | {postfix}"

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        pbar = tqdm(total=len(all_tasks), desc="Processing", bar_format=bar_format)
        
        futures = {executor.submit(process_video, vid, channel_id, pbar): (vid, channel_id) for vid, channel_id in all_tasks}
        
        for future in as_completed(futures):
            pbar.update(1)
            done = pbar.n
            left = pbar.total - done
            pbar.set_postfix_str(f"Done: {done}, Left: {left}")
            
            try:
                future.result()
            except Exception as e:
                pbar.write(f"[Thread Error] {e}")
        
        pbar.close()

    # Update last_updated for all involved channels
    unique_channels = set(task[1] for task in all_tasks)
    for channel_id in unique_channels:
        update_last_updated(channel_id)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--Channel", help="Specific Channel ID to process (bypasses DB status)")
    parser.add_argument("-t", "--threads", help="Number of threads to use", default=1)
    
    args = parser.parse_args()

    max_workers = int(args.threads)
    print(f"Using {max_workers} threads.")
    
    all_tasks = []
    if args.Channel:
        print(f"Fetching videos for channel: {args.Channel}")
        all_tasks.extend(get_unprocessed_videos(args.Channel))
    else:
        channels = get_approved_channels()
        if not channels:
            print("No approved channels found in database.")
            return
        
        random.shuffle(channels)
        print(f"Found {len(channels)} approved channels. Fetching video lists...")
        
        # Use tqdm for channel list fetching too
        for channel_id in tqdm(channels, desc="Scanning channels"):
            all_tasks.extend(get_unprocessed_videos(channel_id))
    
    if not all_tasks:
        print("No new videos found to process.")
        return

    process_all_videos(all_tasks, max_workers=max_workers)

if __name__ == "__main__":
    main()
