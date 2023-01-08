from disnake.ext import commands

class Variables(commands.Cog):
    def __init__(self, bot: commands.InteractionBot) -> None:
        self.bot = bot
        self.guilds_ranking = {}
        self.resa_channels = []
        self.seasons_list = []
        self.eva_cities = {}

def setup(bot: commands.InteractionBot):
    bot.add_cog(Variables(bot))