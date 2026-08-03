import asyncio
import discord
from discord.ext import commands

# Configuração dos Intents (Message Content é obrigatório para as mensagens automáticas)
intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"--------------------------------------------------")
    print(f"Bot conectado com sucesso!")
    print(f"Nome: {bot.user} (ID: {bot.user.id})")
    print(f"--------------------------------------------------")
    
    try:
        # Coloca aqui o ID do teu servidor (ex: discord.Object(id=123456789012345678))
        meu_servidor = discord.Object(id=1423721700478025850) 
        
        bot.tree.copy_global_to(guild=meu_servidor)
        synced = await bot.tree.sync(guild=meu_servidor)
        print(f"Sincronizados {len(synced)} comando(s) instantaneamente no servidor.")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")

async def main():
    async with bot:
        await bot.load_extension("modulos.fixadas")
        print("Módulo 'modulos.fixadas' carregado.")
        
        await bot.start("MTUzMzkzMTM4NTEzMDA2MTk0NQ.GB5u-o.9wPU4r0Kjg3w05nCQIygCFPedHOZftAzfZsMoo")

if __name__ == "__main__":
    asyncio.run(main())