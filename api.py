from flask import Flask, request
import os 
from json import load
from datetime import datetime, timedelta
from urllib.parse import parse_qs
import requests
import asyncio
import time
import humanize
from db import db
from config import config

app = Flask(__name__)

# Ensure DB is initialized
db.init_db()

no_data_str = "We don't have data of this channel. please contact AG at http://discord.surajbhari.com"

<<<<<<< HEAD
def get_channel_info():
    try:
        channel = parse_qs(request.headers.get('Nightbot-Channel', ''))
        channel_id = channel.get("providerId", [None])[0]
        return channel_id
    except Exception:
        return None

def get_user_info():
    try:
        user = parse_qs(request.headers.get('Nightbot-User', ''))
        user_id = user.get("providerId", [None])[0]
        user_name = user.get("displayName", [None])[0]
        return user_id, user_name
    except Exception:
        return None, None
=======
no_data_str = "We don't have data of this channel. please contact Your admin"
>>>>>>> 9cc4c94eebe87233c73a251da43a759515cf503e

@app.get("/")
def main():
    channel_id = get_channel_info()
    if not channel_id:
        return "If you are reading this, then stats are working fine. (No channel info detected)"

    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT message_origin_time FROM chats WHERE channel_id = %s ORDER BY message_origin_time DESC LIMIT 1;", (channel_id,))
            data = cursor.fetchone()
            if not data:
                date = "No chats"
            else:
                now = datetime.now()
                last_message_time = datetime.fromtimestamp(float(data[0]))
                relative = now - last_message_time
                date = humanize.naturaltime(relative)
    finally:
        db.return_connection(conn)

    return f"If you are reading this, then stats are working fine. Last known message was {date}."

@app.get("/stats")
def stats():
    channel_id = get_channel_info()
    user_id, user_name = get_user_info()

    if not channel_id or not user_id:
        return "Not able to auth"

    ranking_data = get_ranking_data(channel_id)
    oldest_data = get_oldest_data(channel_id)

    if not ranking_data:
        return no_data_str

    ranking = 0
    user_rank_data = None
    for i, x in enumerate(ranking_data, 1):
        if x[0] == user_id:
            ranking = i
            user_rank_data = x
            break

    if not user_rank_data:
        return f"{user_name} has no recorded messages in this channel."

    old_ranking = 0
    first_message = None
    for i, y in enumerate(oldest_data, 1):
        if y[0] == user_id:
            old_ranking = i
            first_message = y
            break

    total_count = len(oldest_data)
    first_stream_dt = datetime.fromtimestamp(float(first_message[3]))
    ago = datetime.now() - first_stream_dt
    
    return f"{user_name} is ranked #{ranking} in chat with {user_rank_data[4]} messages. Their first message was on a stream {ago.days} days ago. Member #{old_ranking}/{total_count} of this cult."

def get_oldest_data(channel_id: str):
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            # PostgreSQL requires all selected columns to be in GROUP BY or used in aggregate
            query = """
                SELECT DISTINCT ON (user_id) 
                    user_id, user_name, stream_id, message_origin_time, message_content 
                FROM chats 
                WHERE channel_id = %s 
                ORDER BY user_id, message_origin_time ASC
            """
            cursor.execute(query, (channel_id,))
            data = cursor.fetchall()
            # Re-sort by message_origin_time ASC as the DISTINCT ON requires ORDER BY user_id first
            data.sort(key=lambda x: float(x[3]))
            return data
    finally:
        db.return_connection(conn)

def get_ranking_data(channel_id: str):
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            query = """
                SELECT user_id, MAX(user_name), MAX(stream_id), MAX(message_origin_time), COUNT(*) as num_messages 
                FROM chats 
                WHERE channel_id = %s 
                GROUP BY user_id 
                ORDER BY num_messages DESC
            """
            cursor.execute(query, (channel_id,))
            return cursor.fetchall()
    finally:
        db.return_connection(conn)

@app.get("/streak")
def streak():
    channel_id = get_channel_info()
    user_id, user_name = get_user_info()

    if not channel_id or not user_id:
        return "Not able to auth"

    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            # Fetch all streams (sorted) and check user presence
            cursor.execute("""
                SELECT stream_id, 
                       MIN(message_origin_time) AS min_time,
                       EXISTS (SELECT 1 FROM chats u WHERE u.user_id = %s AND u.stream_id = c.stream_id AND u.channel_id = c.channel_id) AS is_present
                FROM chats c
                WHERE channel_id = %s
                GROUP BY stream_id, channel_id
                ORDER BY min_time ASC;
            """, (user_id, channel_id))

            results = cursor.fetchall()
    finally:
        db.return_connection(conn)

    if not results:
        return no_data_str

    streams = [row[0] for row in results]
    user_presence = {row[0]: row[2] for row in results}

    count = 0
    for stream in reversed(streams):
        if not user_presence[stream]:
            break
        count += 1

    present_in = sum(1 for row in results if row[2])

    return f"@{user_name} {count} streams in a row. You were present in {present_in}/{len(streams)} streams."

@app.get("/youngest/<query>")
@app.get("/youngest/")
async def youngest(query=None):
    query = min(int(query or 5), 20)
    channel_id = get_channel_info()
    response_url = request.headers.get("Nightbot-Response-Url")

    if not channel_id or not response_url:
        return "Not able to auth"
    
    data = get_oldest_data(channel_id)
    if not data:
        return no_data_str

    string = ""
    counter = 1
    # Get last 'query' members
    for x in data[-query:][::-1]:
        ago = datetime.now() - datetime.fromtimestamp(float(x[3]))
        hours_ago = ago.days * 24 + ago.seconds // 3600
        string += f"| {counter}.{x[1]}: {hours_ago} hours ago.  "
        counter += 1

    await send_nightbot_response(response_url, string)
    return "Processing youngest members..."

@app.get("/oldest/<query>")
@app.get("/oldest/")
async def oldest(query=None):
    query = min(int(query or 5), 20)
    channel_id = get_channel_info()
    response_url = request.headers.get("Nightbot-Response-Url")

    if not channel_id:
        return "Not able to auth"

    data = get_oldest_data(channel_id)
    if not data:
        return no_data_str

    string = ""
    for i, x in enumerate(data[:query], 1):
        ago = (datetime.now() - datetime.fromtimestamp(float(x[3]))).days
        string += f"{i}.{x[1]}: {ago} days ago. "

    if response_url and len(string) > 200:
        await send_nightbot_response(response_url, string)
        return "Processing oldest members..."
    return string

@app.get("/top/<query>")
@app.get("/top/")
async def top(query=None):
    query = min(int(query or 5), 20)
    channel_id = get_channel_info()
    response_url = request.headers.get("Nightbot-Response-Url")

    if not channel_id:
        return "Not able to auth"

    data = get_ranking_data(channel_id)
    if not data:
        return no_data_str

    string = ""
    for i, x in enumerate(data[:query], 1):
        string += f"{i}.{x[1]}: {x[4]}.  "

    if response_url and len(string) > 200:
        await send_nightbot_response(response_url, string)
        return "Processing top members..."
    return string

@app.get("/wordcount/")
@app.get("/wordcount/<word>")
def wordcount(word: str = None):
    if not word:
        return "Please pass a word(s) to count for."
    channel_id = get_channel_info()
    if not channel_id:
        return "Not able to auth"

    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM chats WHERE channel_id = %s AND LOWER(message_content) LIKE %s", 
                (channel_id, f"%{word.lower()}%")
            )
            count = cursor.fetchone()[0]
    finally:
        db.return_connection(conn)

    return f"'{word}' has been said {count} times in chat."

@app.get("/firstsaid/")
@app.get("/firstsaid/<word>")
def firstsaid(word: str = None):
    if not word:
        return "Please pass a word(s) to count for."
    channel_id = get_channel_info()
    if not channel_id:
        return "Not able to auth"

    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT stream_id, user_name, message_timestamp, message_origin_time FROM chats WHERE channel_id = %s AND LOWER(message_content) LIKE %s ORDER BY message_origin_time ASC LIMIT 1",
                (channel_id, f"%{word.lower()}%")
            )
            data = cursor.fetchone()
    finally:
        db.return_connection(conn)

    if not data:
        return f"'{word}' has never been said in chat."

    ago = (datetime.now() - datetime.fromtimestamp(float(data[3]))).days
    return f"'{word}' was first said by {data[1]} exactly {ago} days ago. https://youtu.be/{data[0]}?t={int(float(data[2]))}"

async def send_nightbot_response(url, message):
    parts = [message[i : i + 200] for i in range(0, len(message), 200)]
    for part in parts:
        requests.post(url, data={"message": part})
        await asyncio.sleep(1) # Small delay to avoid rate limiting

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
