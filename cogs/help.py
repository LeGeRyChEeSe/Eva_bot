import disnake
from disnake.ext import commands
import utils.functions as functions
from utils.constants import *

class Help(commands.Cog):
    def __init__(self, bot: commands.InteractionBot) -> None:
        self.bot = bot

    @commands.slash_command(name="help", dm_permission=True)
    async def help(self, inter: disnake.ApplicationCommandInteraction):
        """
            Affiche le menu d'aide pour les commandes d'Eva Bot. {{HELP}}
        """
        embed = disnake.Embed(color=EVA_COLOR, timestamp=functions.getTimeStamp())
        embed.set_thumbnail(self.bot.user.display_avatar.url)
        embed.description = functions.getLocalization(self.bot, "HELP_RESPONSE_DESCRIPTION", inter.locale)
        if inter.channel.permissions_for(inter.author).manage_guild:
            embed.description += "\n\n**Éxécutez la commande `/setup` avant toute autre commande en premier lieu pour configurer totalement le bot.** *Vous devez éxécuter cette commande qu'une seule fois.*"

        for c in self.bot.all_slash_commands.values():
            if c.body.default_member_permissions == None or inter.author.guild_permissions > c.body.default_member_permissions:
                if c.body.name_localizations.data is not None:
                    command_name = c.body.name_localizations.data.get(str(inter.locale))
                else:
                    command_name = c.qualified_name
                if c.body.description_localizations.data is not None:
                    command_description = c.body.description_localizations.data.get(str(inter.locale))
                else:
                    command_description = c.description
                embed.add_field(name=f"`/{command_name}`", value=command_description, inline=False)
        await inter.response.send_message(embed=embed, ephemeral=True)

def setup(bot: commands.InteractionBot):
    bot.add_cog(Help(bot))