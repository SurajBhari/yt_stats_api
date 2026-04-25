# yt_stats_api
![Refresh ytstats](https://cronitor.io/badges/iBsIeh/production/8E7fTxi5f5-KsWy0k5D4-74vS_A.svg) </br>

Check the [Operational Status here.](https://suraj.cronitorstatus.com/)

This improved version, yt_stats_api, surpasses its predecessor, yt_chat_arranger. Realizing the limitations of using JSON for storing substantial data, it has transitioned to a more robust SQL storage solution.

Currently, the refresher is operational for the streamers mentioned in the badge above. If you wish to host it yourself, consider setting up a cron job with a command like:</br>
```python
python3 main.py -c UCLcNciLKdI380VqdpDlIbxw
```
You can queue multiple queries sequentially to avoid overwhelming the source or crashing the SQL connection.</br>
```python
python3 main.py -c UCbZZmB8L3IEHutGbvpWo9Ow && python3 main.py -c UCLcNciLKdI380VqdpDlIbxw
```

Running `api.py` exposes three gateways on port 5000:

2. **`/top`**: Returns the top 10 chatters in the chat in string format. To get more, you can use `/top/20`, for example, to get the top 20. The request is automatically denied if you input anything other than a number.

3. **`/wordcount/<word>`**: Returns the number of times a message with the specified "word" was sent in the chat. It is case-insensitive.

For NightBot integration, you can add these commands to your chat. Replace `stats.streamsnip.com` with your own domain if self-hosting.

### How to add commands:
Copy and paste the following lines into your YouTube/Twitch chat where Nightbot is active.

```bash
!addcom !streak $(urlfetch https://stats.streamsnip.com/streak)
!addcom !top $(urlfetch https://stats.streamsnip.com/top/$(query))
!addcom !stats $(urlfetch https://stats.streamsnip.com/stats)
!addcom !wordcount $(urlfetch https://stats.streamsnip.com/wordcount/$(querystring))
!addcom !oldest $(urlfetch https://stats.streamsnip.com/oldest/$(query))
!addcom !youngest $(urlfetch https://stats.streamsnip.com/youngest/$(query))
!addcom !firstsaid $(urlfetch https://stats.streamsnip.com/firstsaid/$(querystring))
```

### Available Endpoints:

1. **`/stats`**: Automatically returns your own chat stats (rank, message count, first seen).
2. **`/top/<n>`**: Returns the top N chatters. Default is 5.
3. **`/streak`**: Shows your current consecutive stream attendance streak.
4. **`/wordcount/<word>`**: Counts how many times a word has been said.
5. **`/firstsaid/<word>`**: Shows who first said a word and provides a link to the exact moment in the stream.
6. **`/oldest/<n>`**: Shows the first N people who joined the "cult" (your chat).
7. **`/youngest/<n>`**: Shows the most recent N people to join the chat.

Feel free to explore the enhanced functionalities of yt_stats_api!
