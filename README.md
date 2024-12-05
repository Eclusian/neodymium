# Setting up your own instance of Neodymium

To use Neodymium yourself you will either need access to a login token, or
you can create your own Discord bot via the [Discord Developer Portal](https://discord.com/developers/applications).
After creating your own bot, place the token in a file in the base directory
called `.env` with the following two lines:

```
# .env
DISCORD_TOKEN="Your bot's token here"
```

Then you can either run the bot using a Python instance or you can build
a Docker image using

`$ docker built . -t 'python-neodymium'`

which you can then run in the background with

`$ docker run -d --name="neodymium" --restart unless-stopped python-neodymium`
