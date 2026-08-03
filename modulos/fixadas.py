import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite

DB_NAME = "fixadas.db"


class MensagemModal(discord.ui.Modal, title="📝 Mensagem Fixada"):
    mensagem = discord.ui.TextInput(
        label="Mensagem",
        placeholder="Digite a mensagem...",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=4000
    )

    def __init__(self, painel):
        super().__init__()
        self.painel = painel
        self.mensagem.default = painel.mensagem

    async def on_submit(self, interaction):
        self.painel.mensagem = self.mensagem.value
        await interaction.response.send_message(
            "✅ Mensagem atualizada!",
            ephemeral=True
        )


class EmbedModal(discord.ui.Modal, title="🎨 Personalizar Embed"):
    titulo = discord.ui.TextInput(
        label="Título",
        placeholder="Título do Embed",
        required=False,
        max_length=256
    )

    descricao = discord.ui.TextInput(
        label="Descrição",
        placeholder="Descrição do Embed",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=4000
    )

    cor = discord.ui.TextInput(
        label="Cor HEX",
        placeholder="8B5CF6",
        required=False,
        max_length=7
    )

    imagem = discord.ui.TextInput(
        label="Imagem (URL)",
        placeholder="https://...",
        required=False,
        max_length=500
    )

    footer = discord.ui.TextInput(
        label="Footer",
        placeholder="Texto do rodapé",
        required=False,
        max_length=2048
    )

    def __init__(self, painel):
        super().__init__()
        self.painel = painel

        self.titulo.default = painel.titulo
        self.descricao.default = painel.descricao
        self.cor.default = painel.cor
        self.imagem.default = painel.imagem
        self.footer.default = painel.footer

    async def on_submit(self, interaction):
        self.painel.titulo = self.titulo.value
        self.painel.descricao = self.descricao.value
        self.painel.cor = self.cor.value or "8B5CF6"
        self.painel.imagem = self.imagem.value
        self.painel.footer = self.footer.value

        await interaction.response.send_message(
            "✅ Embed atualizado!",
            ephemeral=True
        )


class BotaoModal(discord.ui.Modal, title="🔗 Adicionar Botão"):
    texto = discord.ui.TextInput(
        label="Texto do botão",
        placeholder="Ex: 🌐 Discord",
        required=True,
        max_length=80
    )

    link = discord.ui.TextInput(
        label="Link",
        placeholder="https://...",
        required=True,
        max_length=500
    )

    def __init__(self, painel):
        super().__init__()
        self.painel = painel

    async def on_submit(self, interaction):
        if not self.link.value.startswith(("https://", "http://")):
            await interaction.response.send_message(
                "❌ O link precisa começar com https:// ou http://.",
                ephemeral=True
            )
            return

        self.painel.botao_texto = self.texto.value
        self.painel.botao_link = self.link.value

        await interaction.response.send_message(
            "✅ Botão configurado!",
            ephemeral=True
        )


class PainelFixar(discord.ui.View):

    def __init__(self, cog, canal):
        super().__init__(timeout=600)

        self.cog = cog
        self.canal = canal

        self.mensagem = ""
        self.titulo = ""
        self.descricao = ""
        self.cor = "8B5CF6"
        self.imagem = ""
        self.footer = ""

        self.botao_texto = ""
        self.botao_link = ""

    def criar_embed(self):
        if not (
            self.titulo
            or self.descricao
            or self.imagem
            or self.footer
        ):
            return None

        try:
            cor = int(self.cor.replace("#", ""), 16)
        except ValueError:
            cor = 0x8B5CF6

        embed = discord.Embed(
            title=self.titulo or None,
            description=self.descricao or None,
            color=cor
        )

        if self.imagem:
            embed.set_image(url=self.imagem)

        if self.footer:
            embed.set_footer(text=self.footer)

        return embed

    def criar_botoes(self):
        if not self.botao_texto or not self.botao_link:
            return None

        view = discord.ui.View()

        view.add_item(
            discord.ui.Button(
                label=self.botao_texto,
                url=self.botao_link,
                style=discord.ButtonStyle.link
            )
        )

        return view

    @discord.ui.button(
        label="📝 Mensagem",
        style=discord.ButtonStyle.secondary,
        row=0
    )
    async def mensagem_button(self, interaction, button):
        await interaction.response.send_modal(
            MensagemModal(self)
        )

    @discord.ui.button(
        label="🎨 Embed",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def embed_button(self, interaction, button):
        await interaction.response.send_modal(
            EmbedModal(self)
        )

    @discord.ui.button(
        label="🔗 Botão",
        style=discord.ButtonStyle.secondary,
        row=0
    )
    async def botao_button(self, interaction, button):
        await interaction.response.send_modal(
            BotaoModal(self)
        )

    @discord.ui.button(
        label="👁️ Pré-visualizar",
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def preview_button(self, interaction, button):
        embed = self.criar_embed()
        view = self.criar_botoes()

        if not self.mensagem and not embed:
            await interaction.response.send_message(
                "❌ Configure uma mensagem ou Embed primeiro.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            content=self.mensagem or None,
            embed=embed,
            view=view,
            ephemeral=True
        )

    @discord.ui.button(
        label="✅ Ativar",
        style=discord.ButtonStyle.success,
        row=1
    )
    async def ativar_button(self, interaction, button):

        embed = self.criar_embed()

        if not self.mensagem and not embed:
            await interaction.response.send_message(
                "❌ Configure uma mensagem ou Embed primeiro.",
                ephemeral=True
            )
            return

        anterior = await self.cog.buscar_config(
            self.canal.id
        )

        if anterior and anterior["bot_message_id"]:
            try:
                mensagem_antiga = await self.canal.fetch_message(
                    anterior["bot_message_id"]
                )
                await mensagem_antiga.delete()
            except (discord.NotFound, discord.Forbidden):
                pass

        view = self.criar_botoes()

        nova = await self.canal.send(
            content=self.mensagem or None,
            embed=embed,
            view=view
        )

        await self.cog.salvar_config(
            self.canal.id,
            self.mensagem,
            self.titulo,
            self.descricao,
            self.cor,
            self.imagem,
            self.footer,
            self.botao_texto,
            self.botao_link,
            nova.id
        )

        await interaction.response.send_message(
            f"✅ Mensagem ativada em {self.canal.mention}!",
            ephemeral=True
        )

    @discord.ui.button(
        label="🛑 Desativar",
        style=discord.ButtonStyle.danger,
        row=2
    )
    async def desativar_button(self, interaction, button):

        config = await self.cog.buscar_config(
            self.canal.id
        )

        if not config:
            await interaction.response.send_message(
                "⚠️ Não existe uma configuração ativa neste canal.",
                ephemeral=True
            )
            return

        if config["bot_message_id"]:
            try:
                mensagem = await self.canal.fetch_message(
                    config["bot_message_id"]
                )
                await mensagem.delete()
            except (discord.NotFound, discord.Forbidden):
                pass

        await self.cog.desativar_config(
            self.canal.id
        )

        await interaction.response.send_message(
            "🛑 Mensagem automática desativada neste canal.",
            ephemeral=True
        )

    @discord.ui.button(
        label="🗑️ Limpar configuração",
        style=discord.ButtonStyle.danger,
        row=2
    )
    async def limpar_button(self, interaction, button):

        config = await self.cog.buscar_config(
            self.canal.id
        )

        if config and config["bot_message_id"]:
            try:
                mensagem = await self.canal.fetch_message(
                    config["bot_message_id"]
                )
                await mensagem.delete()
            except (discord.NotFound, discord.Forbidden):
                pass

        await self.cog.limpar_config(
            self.canal.id
        )

        self.mensagem = ""
        self.titulo = ""
        self.descricao = ""
        self.cor = "8B5CF6"
        self.imagem = ""
        self.footer = ""
        self.botao_texto = ""
        self.botao_link = ""

        await interaction.response.send_message(
            "🗑️ Configuração completamente apagada!",
            ephemeral=True
        )


class Fixadas(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def preparar_banco(self):
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS fixadas (
                    canal_id INTEGER PRIMARY KEY,
                    mensagem TEXT,
                    titulo TEXT,
                    descricao TEXT,
                    cor TEXT,
                    imagem TEXT,
                    footer TEXT,
                    botao_texto TEXT,
                    botao_link TEXT,
                    bot_message_id INTEGER,
                    ativo INTEGER DEFAULT 1
                )
            """)

            try:
                await db.execute(
                    "ALTER TABLE fixadas ADD COLUMN ativo INTEGER DEFAULT 1"
                )
            except Exception:
                pass

            await db.commit()

    async def buscar_config(self, canal_id):

        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute("""
                SELECT
                    mensagem,
                    titulo,
                    descricao,
                    cor,
                    imagem,
                    footer,
                    botao_texto,
                    botao_link,
                    bot_message_id,
                    ativo
                FROM fixadas
                WHERE canal_id = ?
            """, (canal_id,))

            row = await cursor.fetchone()

        if not row:
            return None

        return {
            "mensagem": row[0] or "",
            "titulo": row[1] or "",
            "descricao": row[2] or "",
            "cor": row[3] or "8B5CF6",
            "imagem": row[4] or "",
            "footer": row[5] or "",
            "botao_texto": row[6] or "",
            "botao_link": row[7] or "",
            "bot_message_id": row[8] or 0,
            "ativo": row[9] if row[9] is not None else 1
        }

    async def salvar_config(
        self,
        canal_id,
        mensagem,
        titulo,
        descricao,
        cor,
        imagem,
        footer,
        botao_texto,
        botao_link,
        bot_message_id
    ):

        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("""
                INSERT OR REPLACE INTO fixadas (
                    canal_id,
                    mensagem,
                    titulo,
                    descricao,
                    cor,
                    imagem,
                    footer,
                    botao_texto,
                    botao_link,
                    bot_message_id,
                    ativo
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                canal_id,
                mensagem,
                titulo,
                descricao,
                cor,
                imagem,
                footer,
                botao_texto,
                botao_link,
                bot_message_id
            ))

            await db.commit()

    async def desativar_config(self, canal_id):

        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("""
                UPDATE fixadas
                SET ativo = 0,
                    bot_message_id = 0
                WHERE canal_id = ?
            """, (canal_id,))

            await db.commit()

    async def limpar_config(self, canal_id):

        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("""
                DELETE FROM fixadas
                WHERE canal_id = ?
            """, (canal_id,))

            await db.commit()

    @app_commands.command(
        name="fixar",
        description="Abre o painel de mensagem fixada neste canal."
    )
    async def fixar(self, interaction):

        canal = interaction.channel

        if not isinstance(canal, discord.TextChannel):
            await interaction.response.send_message(
                "❌ Use este comando em um canal de texto.",
                ephemeral=True
            )
            return

        config = await self.buscar_config(
            canal.id
        )

        painel = PainelFixar(
            self,
            canal
        )

        if config:
            painel.mensagem = config["mensagem"]
            painel.titulo = config["titulo"]
            painel.descricao = config["descricao"]
            painel.cor = config["cor"]
            painel.imagem = config["imagem"]
            painel.footer = config["footer"]
            painel.botao_texto = config["botao_texto"]
            painel.botao_link = config["botao_link"]

        embed = discord.Embed(
            title="📌 Painel de Mensagem Fixada",
            description=(
                f"Configure a mensagem automática para "
                f"{canal.mention}."
            ),
            color=0x8B5CF6
        )

        embed.add_field(
            name="📝 Mensagem",
            value="Configure o texto.",
            inline=True
        )

        embed.add_field(
            name="🎨 Embed",
            value="Título, descrição, imagem e footer.",
            inline=True
        )

        embed.add_field(
            name="🔗 Botão",
            value="Adicione um link.",
            inline=True
        )

        embed.add_field(
            name="🛑 Desativar",
            value="Para a mensagem automática.",
            inline=True
        )

        embed.add_field(
            name="🗑️ Limpar",
            value="Apaga toda a configuração.",
            inline=True
        )

        embed.set_footer(
            text="As configurações são salvas permanentemente."
        )

        await interaction.response.send_message(
            embed=embed,
            view=painel,
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            return

        config = await self.buscar_config(
            message.channel.id
        )

        if not config or not config["ativo"]:
            return

        canal = message.channel

        if config["bot_message_id"]:
            try:
                mensagem_antiga = await canal.fetch_message(
                    config["bot_message_id"]
                )
                await mensagem_antiga.delete()
            except (discord.NotFound, discord.Forbidden):
                pass

        embed = None

        if (
            config["titulo"]
            or config["descricao"]
            or config["imagem"]
            or config["footer"]
        ):

            try:
                cor = int(
                    config["cor"].replace("#", ""),
                    16
                )
            except ValueError:
                cor = 0x8B5CF6

            embed = discord.Embed(
                title=config["titulo"] or None,
                description=config["descricao"] or None,
                color=cor
            )

            if config["imagem"]:
                embed.set_image(
                    url=config["imagem"]
                )

            if config["footer"]:
                embed.set_footer(
                    text=config["footer"]
                )

        view = None

        if (
            config["botao_texto"]
            and config["botao_link"]
        ):
            view = discord.ui.View()

            view.add_item(
                discord.ui.Button(
                    label=config["botao_texto"],
                    url=config["botao_link"],
                    style=discord.ButtonStyle.link
                )
            )

        nova = await canal.send(
            content=config["mensagem"] or None,
            embed=embed,
            view=view
        )

        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("""
                UPDATE fixadas
                SET bot_message_id = ?
                WHERE canal_id = ?
            """, (
                nova.id,
                canal.id
            ))

            await db.commit()


async def setup(bot):
    cog = Fixadas(bot)

    await cog.preparar_banco()
    await bot.add_cog(cog)

    print("Sistema de mensagens fixadas carregado.")