import discord
from discord.ext import commands
import yt_dlp
import asyncio
import random
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

queue = []
loop_mode = False
now_playing = None

@bot.event
async def on_ready():
    print(f'機器人上線：{bot.user.name}')

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f'已加入 {channel}')
    else:
        await ctx.send('你必須先在語音頻道內！')

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send('已離開語音頻道')

@bot.command()
async def play(ctx, *, query):
    queue.append(query)
    await ctx.send(f'加入播放列表：{query}')
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await play_next(ctx)

@bot.command()
async def playlist(ctx, *, queries):
    tracks = [q.strip() for q in queries.split('|')]
    queue.extend(tracks)
    await ctx.send(f'已加入 {len(tracks)} 首歌曲到播放清單')
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await play_next(ctx)

@bot.command()
async def shuffle(ctx):
    random.shuffle(queue)
    await ctx.send('播放清單已隨機排序')

@bot.command()
async def loop(ctx):
    global loop_mode
    loop_mode = not loop_mode
    await ctx.send(f'循環播放：{"開啟" if loop_mode else "關閉"}')

@bot.command()
async def now(ctx):
    if now_playing:
        await ctx.send(f'🎶 現在播放：{now_playing}')
    else:
        await ctx.send('目前沒有播放任何音樂')

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send('已停止播放')

@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ 已暫停播放")
    else:
        await ctx.send("⚠️ 目前沒有正在播放的音樂")

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ 已繼續播放")
    else:
        await ctx.send("⚠️ 音樂未處於暫停狀態")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ 已切到下一首歌曲")
    else:
        await ctx.send("⚠️ 沒有正在播放的音樂可以切歌")

async def play_next(ctx):
    global now_playing

    if not queue:
        await ctx.send('播放清單結束')
        return

    query = queue.pop(0)

    vc = ctx.voice_client
    if not vc or not vc.is_connected():
        await ctx.send("❗錯誤：我還沒加入語音頻道，請先輸入 `!join`")
        return

    ydl_opts = {
        'format': 'bestaudio',
        'quiet': True,
        'default_search': 'ytsearch',
        'noplaylist': True,
        'cookiefile': 'cookies.txt',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            audio_url = info['url']
            now_playing = info['title']
    except Exception as e:
        await ctx.send(f"❗歌曲取得失敗：{e}")
        return

    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }

    try:
        source = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)
        vc.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
        await ctx.send(f'🎶 正在播放：{now_playing}')
    except Exception as e:
        await ctx.send(f"❗播放失敗：{e}")

bot.run(os.getenv("DISCORD_TOKEN"))
