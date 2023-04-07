# yt_stats_api
![ToasterRoaster Eyeq Eupho Xyaa](https://cronitor.io/badges/2AOCSO/production/1I2dyvqRJwTPnHEX-cdldqeYGZA.svg)

This is a better version of my previously made yt_chat_arranger </br>
who knew json are not good storage when you are storing this much of data ? 
use sql insted

I am currently running the refresher for the streamers mentioned in the badge above

if you wanna host it yourself. you can 
have a cron job entry for something like </br>
`python3 main.py -c UCLcNciLKdI380VqdpDlIbxw` </br>


you can put the query in queue by doing something like</br> `python3 main.py -c UCbZZmB8L3IEHutGbvpWo9Ow && python3 main.py -c UCLcNciLKdI380VqdpDlIbxw` </br>
so it go one by one. instead of going parallely and limiting the source/crash the sql connection

running api.py will expose 3 gateway on port 5000 </br>


`/stats` this automatically returns the stats for the person who queried for it. for privacy reason only the person who queried can have the data. + from nightbot only for the time being. 

`/top` this returns top 10 chatters in the chat in a string format. if you want more you can pass something like `/top/20` to get top 20. this automatically denies the request if you put anything other than a number say for `/top/what` will return immediatly. i have decided top 20 because its nice and doesn't spam the chat. 

`/wordcount/<word>` returns the number of times a message was sent in chat with that "word" in it. case insensitive. not passing word will return immediatly.

as for NightBot 
you can use </br>
`!addcom !top $(urlfetch http://surajbhari.info:5000/top/$(query))` </br>
`!addcom !stats $(urlfetch http://surajbhari.info:5000/stats)` </br>
`!addcom !wordcount $(urlfetch http://surajbhari.info:5000/wordcount/$(querystring))` </br>
