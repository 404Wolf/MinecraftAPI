import asyncio  # for async code
from aiohttp import web  # for async api
import aiohttp  # for async web requests
import discord  # for discord bot to grab namemc info
import sys  # to check if user is using windows, for asyncio event policy
import json  # for json loading/dumping
from random import randint  # to generate random code for input string
from time import (
    mktime,
    time,
)  # for converting string time to unix time, and getting current time
from datetime import datetime  # for converting string time to unix time
import socket  # for getting the current machine's ip (to log the ip that the API is running on)
import base64  # decode mojang texture info

"""
Load in the config file
"""
with open("config.json") as configFile:  # open config.json file
    config = json.load(configFile)  # load the config file as a dict

"""
Set the global variables
"""
client = discord.Client()  # create discord client object
cache = {}  # empty dict which cached names' data will be stored in
current = 0  # current chat number to use (resets after reaching 100)
currentRequests = 0  # current requests being handled


@client.event
async def on_ready():
    try:
        """
        Runs after the bot finishes authing, begins the api tasks,
        and creates needed channels for the bot to run if they do not already exist.
        """

        global channels  # list where all channels will be stored
        global session  # for aiohttp session requests

        print("Bot has authed")  # announce that the bot has finished authing

        # change the bot's status to "Scraping NameMC"
        game = discord.Game("Scraping NameMC")
        await client.change_presence(status=discord.Status.online, activity=game)

        asyncio.create_task(api())  # begin the api (as a background task)

        channels = []  # define the channels variable to be a list
        guild = client.get_guild(
            config["server"]
        )  # guild = server; get guild from serverId found in config.json
        for channel in guild.text_channels:
            channels.append(
                channel
            )  # add all the channels from the server to the channels variable

        # if the server doesn't have 100 channels (the amount the bot creates during auto set-up), purge server and
        if len(channels) != 100:
            channels = []
            for channel in channels:
                await channel.delete()  # delete preexisting channels
            for i in range(100):  # create 100 new channels
                channels.append(
                    await client.get_guild(config["server"]).create_text_channel(
                        "scraper-" + str(i + 1)
                    )
                )  # create new ones

        session = aiohttp.ClientSession()  # create aiohttp client session object

        while True:  # keep aiohttp session active
            await asyncio.sleep(1)
    finally:
        await session.close()  # before terminating, make sure session gets closed


async def mojang(target):
    """
    Get uuid, skin, capes, and mojang info on the target
    """
    async with session.get(
        "https://api.mojang.com/users/profiles/minecraft/" + target
    ) as resp:
        if (
            resp.status != 204
        ):  # if there is a user with that name then fetch textures and uuid
            uuid = await resp.json()  # get uuid
            uuid = uuid["id"]
            async with session.get(
                "https://sessionserver.mojang.com/session/minecraft/profile/" + uuid
            ) as resp:  # get textures
                # undecode the textures
                textures = await resp.json()
                textures = textures["properties"][0]["value"]
                textures = base64.b64decode(textures)
                textures = json.loads(textures)
                skin = textures["textures"]["SKIN"]["url"]
            async with session.get(
                "https://api.mojang.com/user/profiles/" + uuid + "/names"
            ) as resp:  # get name history
                nameHist = await resp.json()
                if len(nameHist) == 1:
                    nameHist = "prename"
            return (uuid, skin, nameHist)  # return gathered data
        else:
            return None  # if nobody has the name, return None


async def namemc(target):
    """
    Function to look up searches + droptime/status for a username.
    Sends a message to the "current" (a counter variable) channel, wait for discord to
    auto-generate an embed which includes the searches/status of the name, and then parse that info
    and return a clean dict as output.
    """

    global channels
    global current

    data = ""  # sometimes the embed takes time to load in, so we wait until there's actually content to return
    while len(str(data)) < 10:

        """
        Set the channel to send a message to to the current varaible.
        Then tick it up by 1. If it has reached the max length of available channels to
        send messages to, then reset it
        """
        try:
            channel = channels[
                current
            ]  # set channel to channels indexed at counter varaible
        except IndexError:
            current = 0  # reset counter variable
            channel = channels[0]  # set channel to the first channel in channels array
        finally:
            current += 1  # increase current counter

        # send message to the channel, which will trigger discord to load an embed
        async def send(repeats):
            toSend = ""
            for x in range(repeats):
                toSend += (
                    "https://namemc.com/search?q="
                    + target
                    + "&c="
                    + str(randint(int("1" * 20), int("9" * 20)))
                ) + "\n"
            if len(toSend) > 2000:
                await channel.send(
                    "https://namemc.com/search?q=Error_Name_Is_Too_Long_To_Check"
                )
            # note that we add a "&c=<random_number>" to the link, so discord doesn't use a cached embed, and instead treats it as a new link
            await channel.send(toSend)

        """
        Sometimes (randomlly) an embed won't generate, no matter how long we wait.
        To avoid this, there is an "attemmpts" variable. The script keeps trying (every 0.075 seconds)
        to fetch the embed, and if it isn't present, it increases the "attempts" variable.
        If there are over 4 attempts, and the attempts are devisable by 4, it resends the message, which
        will hopefully trigger discord to create an embed. (and continues doing so until discord does)
        """
        attempts = 0  # set attempts to 0
        while True:
            try:
                if (attempts == 0) or ((attempts >= 4) and attempts % 4 == 0):
                    await send(
                        attempts + 1
                    )  # send message on first attempt, and then when (attempts >= 4) and (attempts % 4 == 0)

                data = {
                    "target": target
                }  # create data dict. this function will return the data variable when complete

                async for message in channel.history(
                    limit=1
                ):  # fetch last message in channel message was sent to
                    messageFromHist = message  # grab thbe message

                # raw is the embed's description string, which hopefully contains searches and other useful info
                raw = messageFromHist.embeds[0].description

                # grab searches by parsing the embed's description string
                data["searches"] = int(
                    raw[raw.find("Searches: ") :]
                    .replace("Searches: ", "")
                    .replace(" / month", "")
                )

                # check the status of the name:
                if (
                    "Availability" in raw
                ):  # name is dropping if "Availability" is found in the embed
                    # parse the droptime out of the raw embed string
                    droptime = mktime(
                        datetime.strptime(
                            raw[: raw.find("Z,")].replace("Time of Availability: ", ""),
                            "%Y-%m-%dT%H:%M:%S",
                        ).timetuple()
                    )
                    data["status"] = "dropping"
                    data[
                        "droptime"
                    ] = droptime  # since the name is dropping, there is a droptime, so set the output's "droptime" to the droptime
                elif (
                    "Unavailable" in raw
                ):  # name is taken if "Unavailable" is in the embed
                    data["status"] = "unavailable"
                    data["droptime"] = None
                elif (
                    "Available*" in raw
                ):  # name is not taken if "available" is in the embed
                    data["status"] = "available"
                    data["droptime"] = None
                elif (
                    "Invalid" or "Too" in raw
                ):  # name is invalid and not taken if "Invalid" or "Too" is in the embed
                    data["status"] = "invalid"
                    data["droptime"] = None
                else:
                    # if the embed string isn't ready yet/is empty or malformed, raise an exception, triggering a retry
                    raise Exception
                break
            except:
                # if the embed string isn't ready yet/is empty or malformed, retry
                await asyncio.sleep(0.075)  # wait a bit before retrying
                attempts += 1  # increase attempts counter

    return data  # finally, return the organized data output


async def api():
    """
    Function for the api to run in the background, with the api's endpoints.
    Uses aiohttp to allow for an async api, able to handle concurrent requests.
    """

    routes = (
        web.RouteTableDef()
    )  # define routes as the name of the decorator for api endpoints

    @routes.get("/lookup")
    async def api_lookup(request):
        """
        Api endpoint for getting the searches/droptime (if name is dropping)/status of a name
        """

        # tick the currrent request count being handled by 1
        global currentRequests
        currentRequests += 1

        try:
            if currentRequests > 15:
                return web.json_response(
                    {"Error": "Ratelimit hit! Please try again in a few seconds."},
                    status=429,
                )  # return request timed out error if too many concurrent

            # try to get the requested "target" from their query_string, or from their headers
            try:  # try getting from headers
                target = request.headers["target"]
            except KeyError:  # try getting from query string
                target = request.query_string.replace("target=", "")
            else:  # return an error if they didn't pass it
                return web.json_response(
                    {"Error": "Target not included"}
                )  # return the requested lookup from the name

            target = (
                target.lower()
            )  # make the name requested lowercase, so it caches as lowercase (and doesn't get treated as different)

            # if the target is not in the cache, or is due for a recheck, lookup info for the name
            if (target not in cache) or (cache[target]["recheck"] < time()):
                mojangData = asyncio.create_task(mojang(target))

                while True:  # keep trying to lookup name until it works
                    try:
                        # attempt to fetch the data for the name
                        # try to fetch the data, or retry if it takes too long
                        data = await asyncio.wait_for(namemc(target), 2)
                        break
                    except asyncio.TimeoutError:
                        await asyncio.sleep(
                            0.1
                        )  # if it times out, retry after .1 seconds

                """
                Add data extras
                """
                data["uuid"] = None
                data["skin"] = None
                data["nameHist"] = None
                try:
                    mojangData = await asyncio.wait_for(mojangData, 0.4)
                    if mojangData != None:
                        data["uuid"] = mojangData[0]
                        data["skin"] = mojangData[1]
                        data["nameHist"] = mojangData[2]
                except asyncio.TimeoutError:  # if api times out then don't get info for mojang
                    pass

                # cache the name
                cache[target] = {}  # create entry in cache
                cache[target][
                    "data"
                ] = data  # set cached entry's data the looked up data
                cache[target]["recheck"] = (
                    time() + 60 * 10
                )  # allow the cached output to be used for the next 10 minutes

                return web.json_response(
                    data
                )  # return the requested lookup from the name
            else:
                # otherwise, just return the cached output of the name
                return web.json_response(cache[target]["data"])

        finally:
            currentRequests -= 1  # request has been handled

    async def startServer():
        """
        Begin the async server using aiohttp, which will run in the background
        """

        # create the api and add it's endpoints
        app = web.Application()
        app.add_routes(routes)
        # set up the api background task
        runner = web.AppRunner(app)
        await runner.setup()

        # run the api on localhost, with port 5000
        site = web.TCPSite(runner, port=5000)
        await site.start()

        # log that the API has booted, and the current machine's ip
        print(
            "API has booted on " + socket.gethostbyname(socket.gethostname()) + ":5000"
        )

    # start the server as a background task, and continue to run it in the background
    asyncio.create_task(startServer())

    # ensure that this function does not terminate
    while True:
        await asyncio.sleep(0.01)


# set the event policy to windows if the user is using windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# begin booting the discord bot, which will then boot the api after it finishes authing
client.run(config["token"])
