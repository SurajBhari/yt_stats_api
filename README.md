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

1. **`/stats`**: Automatically returns the stats for the person who queried it. For privacy reasons, only the person who queried and Nightbot can access the data.

2. **`/top`**: Returns the top 10 chatters in the chat in string format. To get more, you can use `/top/20`, for example, to get the top 20. The request is automatically denied if you input anything other than a number.

3. **`/wordcount/<word>`**: Returns the number of times a message with the specified "word" was sent in the chat. It is case-insensitive.

For NightBot integration:

```bash
!addcom !streak $(urlfetch http://surajbhari.info:5000/streak)
!addcom !top $(urlfetch http://surajbhari.info:5000/top/$(query))
!addcom !stats $(urlfetch http://surajbhari.info:5000/stats)
!addcom !wordcount $(urlfetch http://surajbhari.info:5000/wordcount/$(querystring))
!addcom !oldest $(urlfetch http://surajbhari.info:5000/oldest/$(query))
!addcom !youngest $(urlfetch http://surajbhari.info:5000/youngest/$(query))
!addcom !firstsaid $(urlfetch http://surajbhari.info:5000/firstsaid/$(querystring))
```
Feel free to explore the enhanced functionalities of yt_stats_api!
