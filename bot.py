import os
import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
import asyncio
from dotenv import load_dotenv
import random

# 假 Web server for Render port binding
from threading import Thread
from http.server import HTTPServer, SimpleHTTPRequestHandler

def keep_alive():
    server = HTTPServer(('0.0.0.0', 8080), SimpleHTTPRequestHandler)
    server.serve_forever()

Thread(target=keep_alive, daemon=True).start()

# 環境變數
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

queue = []
looping = False

# YouTube 撥放設定（含 cookies.txt）
ydl_opts = {
    'format': 'bestaudio',
    'quiet': True,
    'default_search': 'ytsearch',
    'noplaylist': True,
    'cookiefile': 'cookies.txt'
}

# 指令：加入語音
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("你必須先加入語音頻道！")

# 指令：離開語音
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("我不在語音頻道內。")

# 指令：播放音樂
@bot.command()
async def play(ctx, *, search: str):
    queue.append(search)
    if not ctx.voice_client.is_playing():
        await play_next(ctx)

# 指令：下一首
@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()

# 指令：暫停
@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        await ctx.voice_client.pause()

# 指令：繼續
@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        await ctx.voice_client.resume()

# 指令：循環播放
@bot.command()
async def loop(ctx):
    global looping
    looping = not looping
    await ctx.send(f"循環播放 {'開啟' if looping else '關閉'}")

# 指令：隨機播放
@bot.command()
async def shuffle(ctx):
    random.shuffle(queue)
    await ctx.send("播放清單已隨機排序 🎲")

# 指令：目前播放
@bot.command()
async def now(ctx):
    await ctx.send(f"目前播放：{queue[0]}" if queue else "目前沒有播放歌曲。")

# 指令：清除清單
@bot.command()
async def stop(ctx):
    queue.clear()
    if ctx.voice_client:
        ctx.voice_client.stop()
    await ctx.send("已停止播放並清空播放清單。")

# 撥放下一首
async def play_next(ctx):
    if not queue:
        return

    search = queue[0]
    vc = ctx.voice_client

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search, download=False)
        if 'entries' in info:
            info = info['entries'][0]
        url = info['url']
        title = info.get('title', '未知歌曲')

    source = await discord.FFmpegOpusAudio.from_probe(url)
    
    def after_playing(err):
        if not looping:
            queue.pop(0)
        fut = asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        try:
            fut.result()
        except Exception as e:
            print(f"播放後錯誤: {e}")

    vc.play(source, after=after_playing)
    await ctx.send(f"🎶 正在播放：**{title}**")

# 啟動機器人
@bot.event
async def on_ready():
    print(f"機器人上線：{bot.user}")

bot.run(TOKEN)
