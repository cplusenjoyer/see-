import discord
from discord.ext import commands
import requests
import asyncio

API_KEY = "sk-7d18873c91c747038c3bfbb839c6c55f"
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
            await ctx.send("❌ Ошибка: " + str(data.get("error", {}).get("message", "Неизвестно")), delete_after=20)
            print(f"[ERROR] {data}")

    except Exception as e:
        await ctx.send("❌ Ошибка при соединении с API.", delete_after=20)
        print(f"[ERROR] {e}")

@bot.command()
async def meta(ctx):
    url = "https://api.opendota.com/api/heroStats"
    try:
        response = requests.get(url)
        heroes = response.json()

        pos_roles = {1: [], 2: [], 3: [], 4: [], 5: []}

        for hero in heroes:
            pro_win = hero.get("pro_win", 0)
            pro_pick = hero.get("pro_pick", 0)
            name = hero.get("localized_name", "Неизвестно")

            if pro_pick >= 50:
                winrate = pro_win / pro_pick if pro_pick else 0
                roles = hero.get("roles", [])

                if "Carry" in roles:
                    pos_roles[1].append((name, winrate, pro_pick))
                if "Mid" in roles:
                    pos_roles[2].append((name, winrate, pro_pick))
                if "Offlaner" in roles or "Initiator" in roles:
                    pos_roles[3].append((name, winrate, pro_pick))
                if "Support" in roles:
                    if "Hard Support" in roles or "Disabler" in roles:
                        pos_roles[5].append((name, winrate, pro_pick))
                    else:
                        pos_roles[4].append((name, winrate, pro_pick))

        result = ""
        for pos in range(1, 6):
            top = sorted(pos_roles[pos], key=lambda x: (x[1], x[2]), reverse=True)[:5]
            result += f"\n**Позиция {pos}**:\n"
            for i, (name, wr, picks) in enumerate(top, 1):
                result += f"{i}. {name} — {wr*100:.1f}% WR / {picks} игр\n"

        await ctx.send(result[:2000])

    except Exception as e:
        await ctx.send("❌ Ошибка при получении меты.")
        print(f"[ERROR] {e}")

bot.run("MTM4OTY2NjQ1NjIwNzEwMjA1Mg.GMiU3s.ecGxJbdVIYeoxbyvAvY6eY5VvEmiByozpnYhNg")
