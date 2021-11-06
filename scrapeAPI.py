import asyncio
from aiohttp import web
import discord
import sys
import json

with open("config.json") as configFile:
	config = json.load(configFile)

with open("chats.json") as chatsFile:
	chats = json.load(chatsFile)

client = discord.Client()

@client.event
async def on_ready():
	print("Bot has authed")
	game = discord.Game("Scraping NameMC")
	await client.change_presence(status=discord.Status.online, activity=game)
	asyncio.create_task(api())

async def api():
	routes = web.RouteTableDef()

	@routes.get('/')
	async def ping(request):
		print(request.host)
		return web.Response(text="API for scraping NameMC data")

	async def startServer():
		app = web.Application()
		app.add_routes(routes)
		runner = web.AppRunner(app)
		await runner.setup()
		site = web.TCPSite(runner,host="0.0.0.0",port=5000)
		await site.start()
		print("API has booted")

	asyncio.create_task(startServer())

	while True:
		await asyncio.sleep(0.01)

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

client.run(config['token'])