from flask import Flask, request
from json import load
import sqlite3
from datetime import datetime, timedelta
from urllib.parse import parse_qs
import requests
import asyncio
import time

app = Flask(__name__)

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()


@app.get("/")
def main():
    return "if you are reading this. then stats are working fine."


@app.get("/stats")
def stats():
    tt = time.time()
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
        user = parse_qs(request.headers["Nightbot-User"])
        response_url = request.headers["Nightbot-Response-Url"]
    except KeyError:
        return "Not able to auth"

    channel_id = channel.get("providerId")[0]
    # channel_id = "UCIzzPhdRf8Olo3WjiexcZSw"
    channel_id = channel_id.replace(
        "-", "_"
    )  # YT is weird with channel ids. some have - in them. but sql tables cant have - in them. so we replace it with _
    user_id = user.get("providerId")[0]
    # user_id = "UCPgQs00LJYcATD0Uf7naPwA"
    user_name = user.get("displayName")[0]
    ranking_data = get_ranking(channel_id)
    oldest_data = get_oldest(channel_id)
    ranking = 0
    for x in ranking_data:
        ranking += 1
        if x[0] == user_id:
            break

    old_ranking = 0
    for y in oldest_data:
        old_ranking += 1
        if y[0] == user_id:
            first_message = y
            break

    total_count = len(oldest_data)
    first_stream_dt = datetime.fromtimestamp(int(float(first_message[3])))
    ago = datetime.now() - first_stream_dt
    return f"{user_name} is ranked #{ranking} in chat with {ranking_data[ranking-1][4]} messages. Their first message was on stream that was streamed {ago.days} days ago. and {old_ranking}/{total_count} member to this cult."


def get_oldest(channel_id: str):
    query = f"SELECT user_id, user_name, stream_id, message_origin_time, MIN(message_origin_time) AS first_message_time, message_content FROM {channel_id} GROUP BY user_id ORDER BY first_message_time ASC;"
    cursor.execute(query)
    data = cursor.fetchall()
    return data


def get_ranking(channel_id: str):
    query = f"SELECT user_id, user_name, stream_id, message_origin_time, COUNT(*) as num_messages FROM {channel_id} GROUP BY user_id ORDER BY num_messages DESC;"
    cursor.execute(query)
    data = cursor.fetchall()
    return data

@app.get("/streak")
def streak():
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
        response_url = request.headers["Nightbot-Response-Url"]
        user = parse_qs(request.headers["Nightbot-User"])
    except KeyError:
        return "Not able to auth" 
    user_id = user['providerId'][0]
    channel_id = channel.get("providerId")[0]
    # channel_id = "UCIzzPhdRf8Olo3WjiexcZSw"
    channel_id = channel_id.replace(
        "-", "_"
    )  # YT is weird with channel ids. some have - in them. but sql tables cant have - in them. so we replace it with _
    user_name = user.get("displayName")[0]
    cursor.execute(f"SELECT DISTINCT stream_id FROM {channel_id}")
    streams = cursor.fetchall()
    count = 0
    cursor.execute(f"SELECT DISTINCT stream_id FROM {channel_id} WHERE user_id = '{user_id}'")
    data = cursor.fetchall()
    present_in = len(data)
    total_streams = len(streams)
    for i in range(len(streams)):
        if streams[i] != data[i]:
            break
        count += 1
    return f"@{user_name} {count} streams in a row. You were present in {present_in}/{total_streams} streams."

@app.get("/youngest/<query>")
@app.get("/youngest/")
async def youngest(query=None):
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
    # channel_id = "UCIzzPhdRf8Olo3WjiexcZSw"
    channel_id = channel_id.replace("-", "_")
    try:
        return "Sorry, for spam!"
    finally:
        data = get_oldest(channel_id)
        string = ""
        counter = 1
        x = query * -1 - 1
        for x in data[x:-1][::-1]:
            ago = datetime.now() - datetime.fromtimestamp(int(float(x[4])))
            ago = ago.days * 24 + ago.seconds // 3600
            string += f"| {str(counter)}.{str(x[1])}: {ago} hours ago.  "
            counter += 1
        if len(string) > 200:
            parts = [string[i : i + 200] for i in range(0, len(string), 200)]
            for part in parts:
                await asyncio.sleep(4.5)

                requests.post(response_url, data={"message": part})
        else:
            requests.post(response_url, data={"message": string})


@app.get("/oldest/<query>")
@app.get("/oldest/")
async def oldest(query=None):
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
    # channel_id = "UCIzzPhdRf8Olo3WjiexcZSw"
    channel_id = channel_id.replace("-", "_")
    data = get_oldest(channel_id)
    string = ""
    counter = 1
    for x in data[0:query]:
        ago = (datetime.now() - datetime.fromtimestamp(int(float(x[4])))).days
        # convert it to hours
        string += f"{str(counter)}.{str(x[1])}: {ago} days ago. "
        counter += 1
    if len(string) > 200:
        try:
            "Sorry, for spam!"
        finally:
            parts = [string[i : i + 200] for i in range(0, len(string), 200)]
            for part in parts:
                requests.post(response_url, data={"message": part})
    else:
        return string
     

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
    # channel_id = "UCIzzPhdRf8Olo3WjiexcZSw"
    channel_id = channel_id.replace("-", "_")

    data = get_ranking(channel_id)
    string = ""
    counter = 1
    for x in data[0:query]:
        string += f"{str(counter)}.{str(x[1])}: {str(x[4])}.  "
        counter += 1
    if len(string) > 200:
        try:
            return "Sorry, for spam!"
        finally:
            parts = [string[i : i + 200] for i in range(0, len(string), 200)]
            for part in parts:
                requests.post(response_url, data={"message": part})
    else:
        return string


@app.get("/wordcount/")
@app.get("/wordcount/<word>")
def wordcount(word: str = None):
    if not word:
        return "Please pass a word(s) to count for."
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
    except KeyError:
        return "Not able to auth"

    channel_id = channel.get("providerId")[0]
    # Find all the queries as count that have the word in it
    cursor.execute(
        f"SELECT * FROM {channel_id} WHERE message_content LIKE ?", (f"%{word}%",)
    )
    data = cursor.fetchall()
    conn.commit()
    return f"'{word}' has been said {len(data)} times in chat."


@app.get("/firstsaid/")
@app.get("/firstsaid/<word>")
def firstsaid(word: str = None):
    if not word:
        return "Please pass a word(s) to count for."
    try:
        channel = parse_qs(request.headers["Nightbot-Channel"])
        response_url = request.headers["Nightbot-Response-Url"]
    except KeyError:
        return "Not able to auth"

    channel_id = channel.get("providerId")[0]
    # channel_id = "UCIzzPhdRf8Olo3WjiexcZSw"
    # Find all the queries as count that have the word in it
    cursor.execute(
        f"SELECT * FROM {channel_id} WHERE message_content LIKE ? ORDER BY message_origin_time ASC LIMIT 1 ",
        (f"%{word}%",),
    )
    data = cursor.fetchall()
    conn.commit()
    if len(data) == 0:
        return f"'{word}' has never been said in chat."

    ago = (datetime.now() - datetime.fromtimestamp(int(float(data[0][5])))).days
    return f"'{word}' was first said by {data[0][2]} exactly {ago} days ago. https://youtu.be/{data[0][0]}?t={str(int(float(data[0][4])))}"


app.run(host="0.0.0.0", port=5000)
