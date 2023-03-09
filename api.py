from flask import Flask, request
from json import load
import sqlite3
from datetime import datetime, timedelta
from urllib.parse import parse_qs


app = Flask(__name__)

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()


@app.get('/')
def main():
    return "hello world"

@app.get("/stats")
def stats():
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
        user = parse_qs(request.headers["Nightbot-User"])
    except KeyError:
        return "Not able to auth"

    channel_id = channel.get("providerId")[0]
    user_id = user.get("providerId")[0]
    user_name = user.get("displayName")[0]

    cursor.execute(f"SELECT * FROM {channel_id} WHERE user_id = ? ORDER BY message_origin_time", (user_id,))
    user_data = cursor.fetchall()
    conn.commit()
    count = len(user_data)
    try:
        first_message = user_data[0]
    except IndexError:
        return f"{user_name} has not said anything in chat yet. Is this your first stream? :D"
    print(first_message)
    first_stream_id = first_message[0]
    first_stream_timestamp = str(int(float(first_message[4])))
    first_stream_dt = datetime.fromtimestamp(int(float(first_message[5])))
    ago = (datetime.now() - first_stream_dt)
    first_stream_link = f"https://www.youtube.com/watch?v={first_stream_id}&t={first_stream_timestamp}s"
    return f"{user_name} has said {count} messages in chat. Their first message was on {first_stream_link} which was streamed {ago.days} days ago."

@app.get("/channel")
def channel_stats():
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
    except KeyError:
        return "Not able to auth"
    
    channel_id = channel.get("providerId")[0]
    cursor.execute(f"SELECT * FROM {channel_id}")
    channel_data = cursor.fetchall()
    count = len(channel_data)

    cursor.execute(f"SELECT COUNT(DISTINCT user_id) FROM {channel_id}")
    individual_count = cursor.fetchone()[0]
    conn.commit()

    cursor.execute(f"SELECT COUNT(DISTINCT stream_id) FROM {channel_id}")
    streams_count = cursor.fetchone()[0]
    conn.commit()
    return f"Channel has {count} messages in chat, {individual_count} people interacted across {streams_count} streams."


app.run(host="0.0.0.0", port=5000)