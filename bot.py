import discord
from discord.ext import commands
import requests
import asyncio

API_KEY = ""
API_URL = "https://api.deepseek.com/chat/completions"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

TEMP_CHANNEL_NAME = "[Создание Канала]"
CATEGORY_ID = 1389672039249612830
created_channels = {}

@bot.event
async def on_ready():
    print(f"[DEBUG] Бот запущен как {bot.user}")

@bot.event
async def on_voice_state_update(member, before, after):
    print(f"[DEBUG] {member.name} переключился: {before.channel} → {after.channel}")
    guild = member.guild

    if after.channel and after.channel.name == TEMP_CHANNEL_NAME:
        print("[DEBUG] Вошёл в канал создания, создаём...")
        category = discord.utils.get(guild.categories, id=CATEGORY_ID)
        new_channel = await guild.create_voice_channel(
            name=f"Канал {member.name}",
            category=category
        )
        created_channels[new_channel.id] = True
        await member.move_to(new_channel)
        print(f"[DEBUG] Перемещён в: {new_channel.name}")

    if before.channel and before.channel.id in created_channels:
        if len(before.channel.members) == 0:
            print(f"[DEBUG] Удаляем пустой канал: {before.channel.name}")
            await before.channel.delete()
            created_channels.pop(before.channel.id, None)

@bot.command()
async def ask(ctx, *, prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 1000,
        "stream": False
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        data = response.json()

        if "choices" in data:
            answer = data["choices"][0]["message"]["content"]
            bot_msg = await ctx.send(answer[:2000])
            await asyncio.sleep(15)
            await ctx.message.delete()
            await bot_msg.delete()
        else:
            await ctx.send("Ошибка: " + str(data.get("error", {}).get("message", "Неизвестно")), delete_after=20)
            print(f"[ERROR] {data}")

    except Exception as e:
        await ctx.send("Ошибка при соединении с API.", delete_after=20)
        print(f"[ERROR] {e}")

bot.run("")
