import asyncio
import os
import random
import string
import logging
from urllib.parse import quote

import aiohttp  # pip install aiohttp
from aiohttp import web  # pip install aiohttp
from benedict import benedict as bdict  # pip install python-benedict
from telethon import TelegramClient, events  # pip install telethon

logging.basicConfig(level=logging.WARNING)

try:
    os.mkdir('download')
except Exception as e:
    print(str(e))
if not os.path.exists("downloaded.txt"):
    with open("downloaded.txt", 'w') as out:
        out.write("")

WEBSITE_URL: str = ""
chat_id: int = 
port: int = 
token: str = ""

routes = web.RouteTableDef()

api_id: int = 
api_hash: str = ""

client = TelegramClient("bot", api_id, api_hash)
client.start(bot_token=token)


@client.on(events.NewMessage(pattern="/subscribe (.*)"))
async def sub_event(event):
    channel = event.text.replace("/subscribe", "").strip()
    try:
        await subscribe_to_channel(channel)
        await event.reply("subbed")
    except Exception as e:
        await event.reply("Error happened : " + str(e))


async def subscribe_to_channel(channel_id):
    topic_url = 'https://www.youtube.com/xml/feeds/videos.xml?channel_id={channel_id}'

    dictionary = {
        "hub.callback": WEBSITE_URL,
        "hub.mode": "subscribe",
        "hub.topic": topic_url.format(channel_id=channel_id),
        "hub.verify": "async",
        "hub.verify_token": "",
        "hub.secret": "",
        "hub.lease_seconds": "",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post('https://pubsubhubbub.appspot.com/subscribe',
                                data=dictionary) as resp:
            assert resp.status == 202


async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()
    # dunno how to parse this
    if proc.returncode == 0:
        return True
    else:
        print(stderr.decode("utf-8"))
        return False


command = "youtube-dl {link} -o '{directory}/%(title)s.%(ext)s'"


def random_string(string_length=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(string_length))


async def download_youtube(link):
    await client.send_message(chat_id, 'New video link ' + link)
    down = random_string(10)

    try:
        os.mkdir('./download/' + down)
    except Exception as e:
        print(str(e))
    new = command.format(link=link, directory="./download/" + down)
    res = await run(new)
    arr = os.listdir("./download/" + down)
    if res:
        await client.send_message(chat_id,
                                  'Download video from ' + WEBSITE_URL + "/download/" + down + "/" + quote(arr[0]))
    else:
        await client.send_message(chat_id, 'An error has happened (probably private or deleted)')


@routes.get('/download/{folder}/{name}')
async def download_video(request):
    folder = request.match_info['folder']
    name = request.match_info['name']
    return web.FileResponse(f'./download/{folder}/{name}')


@routes.post('/')
async def get_link(request):
    xml_stuff = await request.text()
    data = bdict.from_xml(xml_stuff)
    t_list = data['feed.entry.link']
    link = t_list["@href"]
    with open('downloaded.txt', 'r') as out:
        result = out.read()
        if link in result:
            return

    with open('downloaded.txt', 'a') as out:
        out.write("\n" + link)
    asyncio.create_task(download_youtube(link))
    return web.Response(text="NO")


@routes.get('/')
async def verify_ourself(request):
    data = request.query.get("hub.challenge")
    if data:
        return web.Response(text=data)
    else:
        return web.Response(text="NO")


app = web.Application()
app.add_routes(routes)
web.run_app(app, port=port)
