from chat_downloader import ChatDownloader, errors
import scrapetube
from datetime import datetime
from os import listdir, mkdir
import json
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("-c", "--Channel", help = "Channel ID")
args = parser.parse_args()
if not args.Channel:    
    channel_id = str(input("Enter Channel ID"))
else:
    channel_id = args.Channel
errorss = ''



import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()


vids = scrapetube.get_channel(channel_id, content_type="streams")
print(channel_id)
cursor.execute(f"CREATE TABLE IF NOT EXISTS {channel_id} (stream_id varchar(255), user_id varchar(255), user_name varchar(255), user_avatar varchar(255),  message_timestamp varchar(255), message_origin_time varchar(255), message_content varchar(255))")
conn.commit()

"""
for vid in video_ids_list:
    for x in range(5):
        cursor.execute(f"INSERT INTO {channel_id} (stream_id) VALUES ('{vid}')")
    conn.commit()"""

cursor.execute(f"SELECT DISTINCT stream_id FROM {channel_id}")
stream_ids = cursor.fetchall()

x = stream_ids
stream_ids = []
stream_ids = [y[0] for y in x]
print(stream_ids)
videos = [vid for vid in vids if vid["videoId"] not in stream_ids]

for vid in videos[0:1]:
    stream_id = vid['videoId']
    print(f"processing {stream_id}")
    chat = ChatDownloader().get_chat(stream_id)
    #print(json.dumps(vid, indent=4))
    for message in chat:
        try:
            user_id = message['author']['id']
            user_name = message['author']['name']
            user_avatar = message['author']['images'][0]['url']
            message_timestamp = message['time_in_seconds']
            message_content = message['message']
            time_of_message = message['timestamp']/1000000
        except Exception as e:
            continue
        cursor.execute(f"INSERT INTO {channel_id} (stream_id, user_id, user_name, user_avatar, message_timestamp, message_origin_time, message_content) VALUES (?, ?, ?, ?, ?, ?)", (stream_id, user_id, user_name, user_avatar, message_timestamp, time_of_message ,message_content))
        print(json.dumps(message, indent=4))
        
    conn.commit()
