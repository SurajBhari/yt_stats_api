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

running api.py will expose 2 gateway on port 5000 </br>

`/channel` it is recommended you don't use this gateway as it is resource heavy. so stay away if you don't have beefy machine.</br>

`/stats` this automatically returns the stats for the person who queried for it. for privacy reason only the person who queried can have the data. + from nightbot only for the time being. 

as for NightBot 
you can use </br>`!commands add !stats $(urlfetch http://your_url:5000/stats)`
</br>`!commands add !channelstats $(urlfetch http://your_url:5000/channel)` # try avoiding as mentioned above
