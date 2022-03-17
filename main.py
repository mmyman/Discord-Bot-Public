from distutils.command.upload import upload
import discord
from discord.ext import commands, tasks
import os
import json
from Bet import Bet
from dotenv import load_dotenv
from google.cloud import storage
from discord.voice_client import VoiceClient
import DiscordUtils
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
client_credentials_manager = SpotifyClientCredentials(client_id='YOUR KEY HERE', client_secret='YOUR KEY HERE')
sp = spotipy.Spotify(client_credentials_manager = client_credentials_manager)

music = DiscordUtils.Music()
bucket_name = "goose_data_bucket"
#file_name = "C:/Users/miles/Documents/GitHub/matts-mom-disc-bot/bank.json"
file_name = '/app/bank.json'
obj_name = "bank-data"
def upload_blob():
    """Uploads a file to the bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"
    # The path to your file to upload
    # source_file_name = "local/path/to/file"
    # The ID of your GCS object
    # destination_blob_name = "storage-object-name"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(obj_name)

    blob.upload_from_filename(file_name)
    
def download_blob():
    """Downloads a blob from the bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"

    # The ID of your GCS object
    # source_blob_name = "storage-object-name"

    # The path to which the file should be downloaded
    # destination_file_name = "local/path/to/file"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    # Construct a client side representation of a blob.
    # Note `Bucket.blob` differs from `Bucket.get_blob` as it doesn't retrieve
    # any content from Google Cloud Storage. As we don't need additional data,
    # using `Bucket.blob` is preferred here.
    blob = bucket.blob(obj_name)
    blob.download_to_filename(file_name)

load_dotenv()

os.chdir("/app/")
#os.chdir("C:/Users/miles/Documents/GitHub/matts-mom-disc-bot")
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'matts-mom-coin-f84bcd7213da.json'
client = commands.Bot(command_prefix='~', activity=discord.Game(name="With Miles"))
storage_client = storage.Client()

bet_active = False
bet = Bet()


@client.event
async def on_ready():
    print('Bot Online')


@client.command(help="Check how many Mom coins you currently have", aliases = ['bal'])
async def balance(ctx):
    await open_account(ctx.author)

    user = ctx.author
    with open("bank.json", "r") as f:
        users = json.load(f)
    wallet_amt = users[str(user.id)]["wallet"]

    em = discord.Embed(title=f"{ctx.author}'s balance", color=discord.Color.blue())
    em.add_field(name="Mom Coins", value=wallet_amt)

    await ctx.send(embed=em)


async def open_account(user):
    users = await get_bank_data()

    if str(user.id) in users:
        return False
    else:
        users[str(user.id)] = {}
        users[str(user.id)]["wallet"] = 0

    with open("bank.json", "w") as f:
        json.dump(users, f)
    return True


async def get_bank_data():
    download_blob()
    with open("bank.json", "r") as f:
        users = json.load(f)
    return users


# ------------------------------------------------------
#Detecting Mom


@client.event
async def on_message(message):
    if message.author.bot:
        pass
    elif "mom" in message.content.lower() or "mommy" in message.content.lower():
        await message.channel.send("<:milesEyes:840033898372661248>")
        await earn_coins(message.author, 1)
        # Emoji for real server <:milesEyes:840033898372661248>
    await client.process_commands(message)


# ---------------------------------------------------------------------------------
#Gambling

async def earn_coins(user, amt):
    await open_account(user)
    users = await get_bank_data()
    amt = int(amt)
    if str(user.id) in users:
        users[str(user.id)]["wallet"] += amt * 2
    with open("bank.json", "w") as f:
        json.dump(users, f)
    upload_blob()

async def lose_coins(user, amt):
    await open_account(user)
    users = await get_bank_data()
    amt = int(amt)
    if str(user.id) in users:
        users[str(user.id)]["wallet"] -= amt
        print()
    with open("bank.json", "w") as f:
        json.dump(users, f)
    upload_blob()


@client.command(pass_context=True, help="Start a new bet")
async def newbet(ctx):
    message = ctx.message.content[8:]
    global bet_active
    if bet_active:
        await ctx.channel.send("ERROR: There is a current active bet")
    else:
        bet_active = True
        bet.set_title(message)
        await ctx.channel.send("Bet Created: " + message)


@client.command(pass_context=True, help="Believe in the current bet")
async def believe(ctx, message):
    await open_account(ctx.author)
    user = ctx.author
    with open("bank.json", "r") as f:
        users = json.load(f)
    bal = int(users[str(user.id)]["wallet"])

    global bet_active
    if not bet_active:
        await ctx.channel.send("ERROR: There is a no active bet")
    elif message.lower() == 'all':
        bet.believe(user, bal)
        em = discord.Embed(title=f"{ctx.author}'s bet", color=discord.Color.green())
        em.add_field(name="Amount Believed", value=bal)
        await ctx.send(embed=em)
        await lose_coins(ctx.author, bal)
    elif not message.isdigit():
        await ctx.channel.send("ERROR: Please enter a numerical bet amount")
    elif int(message) > bal:
        message = int(message)
        await ctx.channel.send("Too Poor, call me mom more")
    else:
        bet.believe(user, message)
        em = discord.Embed(title=f"{ctx.author}'s bet", color=discord.Color.green())
        em.add_field(name="Amount Believed", value=message)
        await ctx.send(embed=em)
        await lose_coins(ctx.author, message)


@client.command(pass_context=True, help="Doubt the current bet")
async def doubt(ctx, message):
    await open_account(ctx.author)
    user = ctx.author
    with open("bank.json", "r") as f:
        users = json.load(f)
    bal = int(users[str(user.id)]["wallet"])

    global bet_active
    if not bet_active:
        await ctx.channel.send("ERROR: There is a no active bet")
    elif message.lower() == 'all':
        bet.doubt(user, bal)
        em = discord.Embed(title=f"{ctx.author}'s bet", color=discord.Color.red())
        em.add_field(name="Amount Doubted", value=bal)
        await ctx.send(embed=em)
        await lose_coins(ctx.author, bal)
    elif not message.isdigit():
        await ctx.channel.send("ERROR: Please enter a numerical bet amount")
    elif int(message) > bal:
        message = int(message)
        await ctx.channel.send("Too Poor, call me mom more")
    else:
        bet.doubt(user, message)
        em = discord.Embed(title=f"{ctx.author}'s bet", color=discord.Color.red())
        em.add_field(name="Amount Doubted", value=message)
        await ctx.send(embed=em)
        await lose_coins(ctx.author, message)


@client.command(pass_context=True, help="End the current bet")
async def closebet(ctx, message):
    global bet_active
    if message.lower() == 'believer' or message.lower() == 'believe':
        for x in range(len(bet.believers)):
            await earn_coins(bet.believers[x], bet.believe_bets[x])
        em = discord.Embed(title="BELIEVERS WIN", color=discord.Color.green())
        await ctx.send(embed=em)
        bet.reset()
        bet_active = False
    elif message.lower() == 'doubter' or message.lower() == 'doubt':
        for x in range(len(bet.doubters)):
            await earn_coins(bet.doubters[x], bet.doubt_bets[x])
        em = discord.Embed(title="DOUBTERS WIN", color=discord.Color.red())
        await ctx.send(embed=em)
        bet.reset()
        bet_active = False
    else:
        await ctx.channel.send("ERROR: Please enter either Believer or Doubter")


@client.command(help="Call before shutting down bot")
async def getwalletdata(ctx):
    with open("bank.json", "r") as f:
        users = json.load(f)
    print(users)

@client.command(help="View active bet")
async def viewbet(ctx):
    global bet_active
    if not bet_active:
        em = discord.Embed(title="ERROR: No active bet", color=discord.Color.red())
        await ctx.send(embed=em)
    elif bet_active:
        em = discord.Embed(title="The current bet is "+bet.title, color=discord.Color.green())
        await ctx.send(embed=em)

#---------------------------------------------------------------------------
#Music

async def is_connected(ctx):
    voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
    return voice_client and voice_client.is_connected()

@client.command(help="Play a song", aliases = ["p"])
async def play(ctx, *, url):
    global sp
    if not await is_connected(ctx):
        await ctx.author.voice.channel.connect()
    player = music.get_player(guild_id=ctx.guild.id)
    if not player:
        player = music.create_player(ctx, ffmpeg_error_betterfix=True)
    if not ctx.voice_client.is_playing():
        if 'spotify' in url:
            playlist_URI = url.split("/")[-1].split("?")[0]
            await player.queue(str(sp.playlist_tracks(playlist_URI)["items"][0]["track"]["name"]) +' '+ str(sp.playlist_tracks(playlist_URI)["items"][0]["track"]["artists"][0]["name"]), search=True)
            song = await player.play()
            for track in sp.playlist_tracks(playlist_URI)["items"][1:]:
                await player.queue(str(track["track"]["name"]) +' '+ str(track["track"]["artists"][0]["name"]), search=True)
        else:
            await player.queue(url, search=True)
            song = await player.play()
        await ctx.send(f"Playing {song.name}")
    else:
        if 'spotify' in url:
            playlist_URI = url.split("/")[-1].split("?")[0]
            for track in sp.playlist_tracks(playlist_URI)["items"]:
                await player.queue(track["track"]["name"], search=True)
                await ctx.send(f"Queued {song.name}")
        else:
            song = await player.queue(url, search=True)
            await ctx.send(f"Queued {song.name}")
@client.command(help = "Pause the music")
async def pause(ctx):
    player = music.get_player(guild_id=ctx.guild.id)
    song = await player.pause()
    await ctx.send(f"Paused {song.name}")
    
@client.command(help ="Resume the paused music")
async def resume(ctx):
    player = music.get_player(guild_id=ctx.guild.id)
    song = await player.resume()
    await ctx.send(f"Resumed {song.name}")
    
@client.command(help ="Stop the music")
async def stop(ctx):
    player = music.get_player(guild_id=ctx.guild.id)
    await player.stop()
    await ctx.send("Stopped")
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_connected():
        await voice.disconnect()
    
@client.command(help = "Loop the music")
async def loop(ctx):
    player = music.get_player(guild_id=ctx.guild.id)
    song = await player.toggle_song_loop()
    if song.is_looping:
        await ctx.send(f"Enabled loop for {song.name}")
    else:
        await ctx.send(f"Disabled loop for {song.name}")
    
@client.command(help ="View the queue")
async def queue(ctx):
    player = music.get_player(guild_id=ctx.guild.id)
    em = discord.Embed(title="Current Queue", color=discord.Color.blue())
    for song in player.current_queue():
        em.add_field(name="Song", value=song.name)
    await ctx.send(embed=em)

    
@client.command(help ="Gets the song currently playing")
async def np(ctx):
    player = music.get_player(guild_id=ctx.guild.id)
    song = player.now_playing()
    await ctx.send(song.name)
    
@client.command(help = "Skips the current song")
async def skip(ctx):
    player = music.get_player(guild_id=ctx.guild.id)
    data = await player.skip(force=True)
    if len(data) == 2:
        await ctx.send(f"Skipped from {data[0].name} to {data[1].name}")
    else:
        await ctx.send(f"Skipped {data[0].name}")

@client.command(help = "Removes the song from the queue at the given index")
async def remove(ctx, index):
    player = music.get_player(guild_id=ctx.guild.id)
    song = await player.remove_from_queue(int(index))
    await ctx.send(f"Removed {song.name} from queue")
client.run(os.getenv("BOTID"))
