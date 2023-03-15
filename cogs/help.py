import disnake
from disnake.ext import commands
import utils.functions as functions
from utils.constants import *
import utils.classes as classes


class Help(commands.Cog):
    def __init__(self, bot: classes.EvaBot) -> None:
        self.bot = bot

    @commands.slash_command(name="help", dm_permission=True)
    async def help(self, inter: disnake.ApplicationCommandInteraction):
        """
            Afficher le menu d'aide pour les commandes d'Eva Bot. {{HELP}}
        """
        embed = disnake.Embed(
            color=EVA_COLOR, timestamp=functions.getTimeStamp())
        embed.set_thumbnail(self.bot.user.display_avatar.url)
        embed.description = functions.getLocalization(
            self.bot, "HELP_RESPONSE_DESCRIPTION", inter.locale)
        if inter.guild:
            if inter.channel.permissions_for(inter.author).manage_guild:
                embed.description += "\n\n**Éxécutez la commande `/setup` avant toute autre commande en premier lieu pour configurer totalement le bot.** *Vous devez éxécuter cette commande qu'une seule fois.*"
        else:
            embed.description += "\n\n**Éxécutez la commande `/setup` dans le serveur avant toute autre commande en premier lieu pour configurer totalement le bot.** *Vous devez éxécuter cette commande qu'une seule fois.*"

        cogs = sorted(self.bot.cogs.items(
        ), key=lambda x: COGS_NAMES[x[0]] if x[0] in COGS_NAMES.keys() else x[0])
        for name, cog in cogs:
            commands = {}
            command_name, command_description = None, None
            for c in cog.get_slash_commands():
                if not inter.guild or c.body.default_member_permissions == None or inter.author.guild_permissions > c.body.default_member_permissions:
                    if c.qualified_name in functions.HIDDEN_COMMANDS:
                        continue

                    if c.body.name_localizations.data is not None:
                        command_name = f"`/{c.body.name_localizations.data.get(str(inter.locale))}`"
                    else:
                        command_name = f"`/{c.qualified_name}`"
                    if c.body.description_localizations.data is not None:
                        command_description = c.body.description_localizations.data.get(
                            str(inter.locale))
                    else:
                        command_description = c.description

                    commands[command_name] = command_description

            if command_name and command_description:
                embed.add_field(name=f"**{functions.COGS_NAMES[name]}**", value="\n".join(
                    [f"{n}: {d}" for n, d in commands.items()]), inline=False)
        await inter.response.send_message(embed=embed, ephemeral=True)


def setup(bot: classes.EvaBot):
    bot.add_cog(Help(bot))
