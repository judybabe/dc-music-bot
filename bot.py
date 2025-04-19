import os
import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
import asyncio
from dotenv import load_dotenv
import random
import os.path


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

<<<<<<< HEAD
=======
if not os.path.exists("cookies.txt"):
    print("⚠️ 找不到 cookies.txt，YouTube 播放可能會失敗。請確認已正確上傳。")
>>>>>>> b2a3c20 (youtube cookies)
# YouTube 撥放設定（含 cookies.txt）
ydl_opts = {
    'format': 'bestaudio',
    'quiet': True,
    'default_search': 'ytsearch',
    'noplaylist': True,
    'cookiefile': 'cookies.txt'
}

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("你必須先加入語音頻道！")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("我不在語音頻道內。")

@bot.command()
async def play(ctx, *, search: str):
    queue.append(search)
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await play_next(ctx)

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()

@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        await ctx.voice_client.pause()

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        await ctx.voice_client.resume()

@bot.command()
async def loop(ctx):
    global looping
    looping = not looping
    await ctx.send(f"循環播放 {'開啟' if looping else '關閉'}")

@bot.command()
async def shuffle(ctx):
    random.shuffle(queue)
    await ctx.send("播放清單已隨機排序 🎲")

@bot.command()
async def now(ctx):
    await ctx.send(f"目前播放：{queue[0]}" if queue else "目前沒有播放歌曲。")

@bot.command()
async def stop(ctx):
    queue.clear()
    if ctx.voice_client:
        ctx.voice_client.stop()
    await ctx.send("已停止播放並清空播放清單。")

async def play_next(ctx):
    if not queue:
        return

    search = queue[0]
    vc = ctx.voice_client
    if not vc or not vc.is_connected():
        await ctx.send("❗ 我還沒加入語音頻道，請先輸入 `!join`")
        return

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            url = info['url']
            title = info.get('title', '未知歌曲')
    except Exception as e:
        await ctx.send(f"❗ 音樂取得失敗：{e}")
        queue.pop(0)
        return

    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }

    source = discord.FFmpegPCMAudio(url, **ffmpeg_options)

    def after_playing(err):
        if err:
            print(f"播放中斷錯誤：{err}")
        if not looping:
            queue.pop(0)
        fut = asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        try:
            fut.result()
        except Exception as e:
            print(f"播放後錯誤: {e}")

    vc.play(source, after=after_playing)
    await ctx.send(f"🎶 正在播放：**{title}**")

@bot.event
async def on_ready():
    print(f"機器人上線：{bot.user}")

bot.run(TOKEN)
