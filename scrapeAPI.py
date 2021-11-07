import asyncio
from aiohttp import web
import discord
import sys
import json
from random import randint
from time import mktime
from datetime import datetime

with open("config.json") as configFile:
	config = json.load(configFile)

client = discord.Client()
cachedChecks = {}
responded = False

@client.event
async def on_ready():
	print("Bot has authed")
	game = discord.Game("Scraping NameMC")
	await client.change_presence(status=discord.Status.online, activity=game)
	asyncio.create_task(api())

async def lookup(target):
	tag = str(randint(int("1"*20),int("9"*20)))
	channel = client.get_channel(config['channel'])
	await channel.send("https://namemc.com/search?q="+target+"&c="+tag)
	while True:
		try:
			data = {"target":target}
			async for message in channel.history(limit=1):
				messageFromHist = message
			raw = messageFromHist.embeds[0].description
			data["searches"] = int(raw[raw.find("Searches: "):].replace("Searches: ","").replace(" / month",""))
			if "Unavailable" in raw:
				data["status"] = "unavailable"
				data["droptime"] = None
			elif "Available*" in raw:
				data["status"] = "available"
				data["droptime"] = None
			else:
				droptime = mktime(datetime.strptime(raw[:raw.find("Z,")].replace("Time of Availability: ",""), "%Y-%m-%dT%H:%M:%S").timetuple())
				data["status"] = "dropping"
				data["droptime"] = droptime
			return data
		except IndexError:
			await asyncio.sleep(.1)

async def api():
	routes = web.RouteTableDef()

	@routes.get('/')
	async def api_ping(request):
		return web.Response(text="API for scraping NameMC data")

	@routes.get("/lookup")
	async def api_lookup(request):
		try:
			target = request.headers["target"]
		except KeyError:
			target = request.query_string.replace("target=","")

		check = False
		if target in data:
			if target["recheck"] < time():
				check = True
		else:
			check = True

		if check:
			data = str(await lookup(target))
			cachedChecks[target] = {"data":data,"recheck":time()+10}
			return web.Response(text=data)
		else:
			return cachedChecks[target]

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