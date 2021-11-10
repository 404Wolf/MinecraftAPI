# All-In-One Minecraft API

### This is an all-in-one Minecraft username -> data api. 
### It both pulls data from mojang, and NameMC, to fetch:
* Droptime (for dropping names)
* NameMC Searches
* Status of name (taken, not taken, dropping, invalid)
* UUID
* Skin
* Name History 

NameMC makes it a pain to scrape their website, but somehow, discord has found a magical way to scrape it for us.
How discord does it? No clue. But, I've made a simple, super fast api, to use discord to scrape it for us.

I've decided to open source this project, mostly because currently, there's lots of similar projects,
which either cost lots of money, or are public apis which have frequent downtime. I'm not hosting this api publically,
but you can! Feel free to fork, or share ideas.

Enjoy! To see how it works, you can follow the below guide:


### To set up:
1. Create a `config.json` file, and just put empty braces in it for now (`{}`)
1. Go to [discord's dev portal](https://discord.com/developers/applications), and create a new application. Then go to the bot page, click "create bot," copy the token, and go back to your config.json file.
1. In the `config.json` file, add `{"token":"token_you_just_copied"}`.
1. Go to the o2auth page, click the checkmark next to "bot," scroll down, click the checkmark next to "administrator," and copy the bot invite link that should now be generated.
1. Go back to [discord's normal website](https://discord.com/app). Go to discord settings, advanced, and then enable developer mode.
1. Create a new fresh discord server, and then delete the chats that it comes with when you make it.
1. Paste the invite link into a new tab, and invite the discord bot to the server you made.
1. Right click on the server's icon, and click "copy id."
1. In the `config.json` file, change the format to `{"token":"token_you_copied_earlier","server":server_id}`.
1. In file explorer, click the directory address, and type "cmd" into the address. A new console window should open.
1. Double click `"dependencies.sh"` to install needed dependencies for the api to run.
1. Assuming python is installed, type "python api.py" to run the script. If python isn't installed, google how to install it.
1. Open a new tab in your browser, and go to "http://localhost:5000/lookup?target=test." The api is now working.

### If you have any questions, I can be reached at `@Twilak#7765`. Enjoy!

(example of speed and content API fetches)<br>
![Example of speed and content API fetches](https://i.imgur.com/72mWz27.png)

