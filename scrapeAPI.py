import asyncio
from aiohttp import web
import discord
import sys
import json

with open("config.json") as config:
	config = json.load(config)
	
with open("chats.json") as config:
	config = json.load(config)

client = discord.Client()

@client.event
async def on_ready():
	print("Authed ["+client.id+"]")
	msg = await (client.get_channel(log_channel)).send("**Ember Helper** has logged on.")
	game = discord.Game(f"Sniping names")
	await client.change_presence(status=discord.Status.online, activity=game)

async def api():
	routes = web.RouteTableDef()

	@routes.get('/')
	async def ping(request):
		print(request.host)
		return web.Response(text="Hello World")

	async def startServer():
		app = web.Application()
		app.add_routes(routes)

		runner = web.AppRunner(app)
		await runner.setup()
		site = web.TCPSite(runner,host="0.0.0.0",port=5000)
		await site.start()

	asyncio.create_task(startServer())

	while True:
		await asyncio.sleep(0.01)

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

client.run(token)