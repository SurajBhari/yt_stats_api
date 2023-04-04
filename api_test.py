from flask import Flask, request
from json import load
import sqlite3
from datetime import datetime, timedelta
from urllib.parse import parse_qs
import requests

import asyncio

app = Flask(__name__)

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()


@app.get('/')
def main():
    return "if you are reading this. then stats are working fine."

@app.get("/stats")
def stats():
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
        user = parse_qs(request.headers["Nightbot-User"])
    except KeyError:
        return "Not able to auth"

    channel_id = channel.get("providerId")[0]
    #channel_id = "UCIzzPhdRf8Olo3WjiexcZSw"
    channel_id = channel_id.replace("-", "_") # YT is weird with channel ids. some have - in them. but sql tables cant have - in them. so we replace it with _
    user_id = user.get("providerId")[0]
    #user_id = "UCPgQs00LJYcATD0Uf7naPwA"
    user_name = user.get("displayName")[0]
    data = get_ranking(channel_id)
    cursor.execute(f"SELECT * FROM {channel_id} WHERE user_id = ? ORDER BY message_origin_time LIMIT 1", (user_id,))
    try:
        first_message = list(cursor.fetchall())[0]
    except IndexError:
        return f"{user_name} has not sent any messages yet. Is this your first time on this channel ? :D Consider Subscribing to the channel to support the streamer."
    
    print(first_message)
    first_stream_id = first_message[0]
    first_stream_timestamp = str(int(float(first_message[4])))
    first_stream_dt = datetime.fromtimestamp(int(float(first_message[5])))
    ago = (datetime.now() - first_stream_dt)

    ranking_data = get_ranking(channel_id)
    ranking = 0
    for x in ranking_data:
        ranking += 1
        if x[0] == user_id:
            break
    return f"{user_name} is ranked #{ranking} in chat with {x[2]} messages. Their first message was on stream that was streamed {ago.days} days ago."


def get_ranking(channel_id:str):
    query = f"SELECT user_id, user_name, COUNT(*) as num_messages FROM {channel_id} GROUP BY user_id ORDER BY num_messages DESC;"
    cursor.execute(query)
    data = cursor.fetchall()
    conn.commit()
    return data


@app.get("/top/<query>")
@app.get("/top/")
async def top(query=None):
    if not query:
        query = 5
    try:
        query = int(query)
    except ValueError:
        return "Not a valid query, you must pass a number not more than 20"
    if query > 20:
        return "Not a valid query, you must pass a number not more than 20"
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
        response_url = request.headers["Nightbot-Response-Url"]
    except KeyError:
        return "Not able to auth"

    channel_id = channel.get("providerId")[0]
    #channel_id = "UCIzzPhdRf8Olo3WjiexcZSw"
    channel_id = channel_id.replace("-", "_")
    data = get_ranking(channel_id)
    string = ""
    counter = 1
    for x in data[0:query]:
        string += f"{str(counter)}.{str(x[1])}: {str(x[2])}.  "
        counter += 1
    print(string)
    if len(string) > 200:
        # split the string into parts of 200 characters and send it to request_url
        parts = [string[i:i+200] for i in range(0, len(string), 200)]
        print(parts)
        #yield parts[0]
        for part in parts:
            requests.post(response_url, data={"message": part})
            # if its not the second last part, wait for 5 seconds
            if part != parts[-2]:
                await asyncio.sleep(5)
            else:
                return parts[-1]
        return "Here ^^"
    return string
        

    
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