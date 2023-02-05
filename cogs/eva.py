import os
import disnake
from utils.errors import *
from disnake import Localized
from disnake.ext import commands
from disnake.ext.commands import errors as commandsErrors
from disnake.ui import TextInput, Button
import utils.functions as functions
from utils.constants import *

class Eva(commands.Cog):
    def __init__(self, bot: commands.InteractionBot) -> None:
        self.bot = bot

    @commands.slash_command(name="stats", dm_permission=True)
    async def stats(self, inter: disnake.ApplicationCommandInteraction, player: disnake.User, saison: str, private: str = commands.Param("No", choices=[Localized("No", key="BOOL_NO"), Localized("Yes", key="BOOL_YES")])):
        """
            Afficher les stats publiques d'un Joueur Eva. {{STATS}}

            Parameters
            ----------
            player: :class:`disnake.User`
                Choisissez le membre dont vous voulez afficher les stats. {{STATS_PLAYER}}
            saison: :class:`int`
                Quelle Saison souhaitez-vous afficher ? {{STATS_SEASON}}
            private: :class:`bool`
                Voulez-vous être la seule personne à voir les stats ? {{STATS_PRIVATE}}
            
            Examples
            --------
            :meth:`/stats` @Garoh 1 Non
        """
        if private == "Yes":
            await inter.response.defer(with_message=True, ephemeral=True)
        else:
            await inter.response.defer(with_message=True, ephemeral=False)

        embed = disnake.Embed(color=EVA_COLOR, timestamp=functions.getTimeStamp())

        user = await functions.getPlayerInfos(self.bot, player, True)

        embed.set_author(name=f"{player.display_name}#{player.discriminator}", icon_url=player.display_avatar.url)
        if user:
            userId = user.get("player_id")
            await functions.updatePlayerInfos(self.bot.pool, user)

            if saison == "Total":
                player_profile, stats_player = {}, {}
                for season in self.bot.get_cog("Variables").seasons_list:
                    season = season["seasonNumber"]
                    p, s = await functions.getStats(userId, season)
                    if "player" not in stats_player.keys():
                        player_profile = p
                        stats_player["player"] = s["player"]
                    else:
                        for name, data in p["player"]["experience"].items():
                            for n, d in player_profile["player"]["experience"].items():
                                if name == n:
                                    if name == "levelProgressionPercentage":
                                        player_profile["player"]["experience"][n] = (player_profile["player"]["experience"]["experience"] * 100) / player_profile["player"]["experience"]["experienceForNextLevel"]
                                    else:
                                        player_profile["player"]["experience"][n] = d + data

                        for name, data in s["player"]["statistics"]["data"].items():
                            for n, d in stats_player["player"]["statistics"]["data"].items():
                                if name == n:
                                    if name == "bestKillStreak":
                                        stats_player["player"]["statistics"]["data"][n] = max(d, data)
                                    else:
                                        stats_player["player"]["statistics"]["data"][n] = d + data
                        stats_player["player"]["statistics"]["data"]["killsByDeaths"] = stats_player["player"]["statistics"]["data"]["killsByDeaths"] / len(self.bot.get_cog("Variables").seasons_list)

            else:
                saison = int(saison)
                player_profile, stats_player = await functions.getStats(userId, saison)
            
            player_profile = player_profile["player"]
            stats_player = stats_player["player"]["statistics"]["data"]
            if stats_player['gameDefeatCount'] > 0:
                stats_player["victoriesByDefeats"] = round(stats_player['gameVictoryCount'] / stats_player['gameDefeatCount'], 3)
            else:
                stats_player["victoriesByDefeats"] = stats_player['gameVictoryCount']

            embed.description = functions.getLocalization(self.bot, "STATS_EMBED_DESCRIPTION_LEVEL", inter.locale, level=player_profile['experience']['level'], experience=player_profile['experience']['experience'], experienceForNextLevel=player_profile['experience']['experienceForNextLevel'])
            embed.url = f"https://www.eva.gg/profile/public/{player_profile['username']}/"
            if saison == "Total":
                embed.set_author(name=f"Saisons {' + '.join([str(i['seasonNumber']) for i in self.bot.get_cog('Variables').seasons_list])}", url="https://www.eva.gg/profile/season/")
            else:
                embed.set_author(name=functions.getLocalization(self.bot, "STATS_EMBED_SEASON", inter.locale, season=saison), url="https://www.eva.gg/profile/season/")
            embed.set_thumbnail(url=player.display_avatar.url)

            if player_profile['experience']['levelProgressionPercentage']:
                embed.set_footer(text=functions.getLocalization(self.bot, "STATS_EMBED_LEVEL_PROGRESSION", inter.locale, levelProgressionPercentage=round(player_profile['experience']['levelProgressionPercentage']), level=player_profile['experience']['level']+1))
            else:
                embed.set_footer(text=functions.getLocalization(self.bot, "STATS_EMBED_LEVEL_PROGRESSION", inter.locale, levelProgressionPercentage=0, level=player_profile['experience']['level']+1))

            if player_profile["seasonPass"]["active"] == True:
                embed.title = functions.getLocalization(self.bot, "STATS_EMBED_SEASON_PASS_ACTIVE", inter.locale, username=player_profile['username'])
            else:
                embed.title = functions.getLocalization(self.bot, "STATS_EMBED_SEASON_PASS_DEACTIVE", inter.locale, username=player_profile['username'])

            embed.add_field(name=functions.getLocalization(self.bot, "STATS_EMBED_GAMES", inter.locale), value=stats_player["gameCount"], inline=True)
            embed.add_field(name=functions.getLocalization(self.bot, "STATS_EMBED_VICTORIES", inter.locale), value=stats_player["gameVictoryCount"], inline=True)
            embed.add_field(name=functions.getLocalization(self.bot, "STATS_EMBED_DEFEATS", inter.locale), value=stats_player["gameDefeatCount"], inline=True)
            embed.add_field(name=functions.getLocalization(self.bot, "STATS_EMBED_RATE_VICTORIES_DEFEATS", inter.locale), value=f"{stats_player['victoriesByDefeats']} ({round(stats_player['victoriesByDefeats'] * 100)}%)", inline=True)
            if stats_player["gameTime"]:
                embed.add_field(name=functions.getLocalization(self.bot, "STATS_EMBED_TOTAL_GAME_TIME", inter.locale), value=functions.getLocalization(self.bot, "STATS_EMBED_TOTAL_GAME_TIME_VALUE", inter.locale, gameTime=round(stats_player['gameTime']/3600, 1)), inline=True)
            embed.add_field(name=functions.getLocalization(self.bot, "STATS_EMBED_KILLS", inter.locale), value=stats_player["kills"], inline=True)
            embed.add_field(name=functions.getLocalization(self.bot, "STATS_EMBED_DEATHS", inter.locale), value=stats_player["deaths"], inline=True)
            embed.add_field(name=functions.getLocalization(self.bot, "STATS_EMBED_ASSISTANCES", inter.locale), value=stats_player["assists"], inline=True)
            if stats_player["killsByDeaths"]:
                embed.add_field(name=functions.getLocalization(self.bot, "STATS_EMBED_RATE_KILLS_DEATHS", inter.locale), value=f"{round(stats_player['killsByDeaths'], 3)} ({round(stats_player['killsByDeaths'] * 100)}%)", inline=True)
            embed.add_field(name=functions.getLocalization(self.bot, "STATS_EMBED_KILLSTREAK", inter.locale), value=stats_player["bestKillStreak"], inline=True)
            if stats_player['traveledDistance']:
                embed.add_field(name=functions.getLocalization(self.bot, "STATS_EMBED_TOTAL_DISTANCE_TRAVELLED", inter.locale), value=functions.getLocalization(self.bot, "STATS_EMBED_TOTAL_DISTANCE_TRAVELLED_VALUE", inter.locale, traveledDistance=round(stats_player['traveledDistance'])), inline=True)
        else:
            raise UserNotLinked("L'utilisateur n'a pas associé son compte EVA.")
        
        await inter.edit_original_response(embed=embed, components=[Button(style=disnake.ButtonStyle.danger, label="Associer compte EVA", custom_id="link_button", emoji="🪢")])

    @stats.autocomplete("saison")
    async def saison_autocomplete(self, inter: disnake.ApplicationCommandInteraction, saison: str):
        seasons_list = [str(season["seasonNumber"]) for season in sorted(self.bot.get_cog("Variables").seasons_list, key=lambda x: x["seasonNumber"], reverse=True)]
        seasons_list.append("Total")
        return seasons_list

    @commands.slash_command(name="lastgame", dm_permission=True)
    async def lastgame(self, inter: disnake.ApplicationCommandInteraction, player: disnake.User, position: int = commands.Param(choices=[i for i in range(1,21)]), private: str = commands.Param("No", choices=[Localized("No", key="BOOL_NO"), Localized("Yes", key="BOOL_YES")])):
        """
        Afficher jusqu'à la 20ème partie souhaitée de la plus récente à la plus ancienne. {{LAST_GAME}}

        Parameters
        ----------
        player: :class:`disnake.User`
            Choisissez le membre dont vous voulez afficher la partie. {{LAST_GAME_PLAYER}}
        position: :class:`int`
            Quelle partie souhaitez-vous afficher ? (1 -> 20) {{LAST_GAME_POSITION}}
        private: :class:`bool`
            Voulez-vous être la seule personne à voir la partie ? {{LAST_GAME_PRIVATE}}

        Examples
        --------
        :meth:`/lastgame` @Garoh 1 Oui
        
        :meth:`/lastgame` @Garoh 2 Non
        """
        if private == "Yes":
            await inter.response.defer(with_message=True, ephemeral=True)
        else:
            await inter.response.defer(with_message=True, ephemeral=False)

        embed = disnake.Embed(color=EVA_COLOR, timestamp=functions.getTimeStamp())
        current_season_id = functions.getCurrentSeasonNumber(self.bot)

        user = await functions.getPlayerInfos(self.bot, player, True)

        if user:
            embed.set_footer(text=f"{player.display_name}", icon_url=player.display_avatar.url)
            userId = user["player_id"]

            last_game = await functions.getLastGame(userId, current_season_id, position)
            if last_game:
                scoreboard_path = functions.getScoreboard(last_game)
                embed.title = f"{position}e partie la plus récente"
                embed.url = f"https://www.eva.gg/fr/profile/public/{user['player_username']}/history/{last_game['id']}"
                embed.set_image(file=disnake.File(f"assets/Images/tmp/{scoreboard_path}"))
                os.remove(f"assets/Images/tmp/{scoreboard_path}")
            else:
                embed.title = "Aucune partie récente"
        else:
            raise UserNotLinked("L'utilisateur n'a pas associé son compte EVA.")
        
        await inter.edit_original_response(embed=embed, components=[Button(style=disnake.ButtonStyle.danger, label="Associer compte EVA", custom_id="link_button", emoji="🪢")])
    
    @commands.slash_command(name="link")
    async def link(self, inter: disnake.ApplicationCommandInteraction):
        """
            __**⚠️ Important ⚠️**__ Associer son compte Eva à son compte Discord.
        """
        await inter.response.send_modal(title="Associer son compte EVA", custom_id="link_modal", components=[TextInput(label="Compte EVA", custom_id="link_eva", style=disnake.TextInputStyle.single_line, placeholder="Entrez votre pseudo EVA complet", required=False, min_length=7, max_length=26), TextInput(label="Compte Twitch (optionnel)", custom_id="link_twitch", style=disnake.TextInputStyle.single_line, placeholder="Entrez votre pseudo Twitch (optionnel)", required=False, min_length=4 ,max_length=25)])

    @commands.user_command(name="stats")
    async def stats_user(self, inter: disnake.ApplicationCommandInteraction, player: disnake.User):
        await self.stats(inter, player=player, saison=functions.getCurrentSeasonNumber(self.bot), private = "Yes")

    @commands.user_command(name="lastgame")
    async def lastgame_user(self, inter: disnake.ApplicationCommandInteraction, player: disnake.User):
        await self.lastgame(inter, player=player, position=1, private="Yes")

    @stats.error
    async def stats_error(self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError):
        """
            Gestionnaire d'erreur spécifique de la commande :meth:`stats`
        """
        params = inter.filled_options
        if isinstance(error, commandsErrors.CommandInvokeError):
            if isinstance(error.original, UserIsPrivate):
                await functions.send_error(inter, error.original.args[0])
            elif isinstance(error.original, UserNotLinked):
                user: disnake.User = params['player']
                embed = disnake.Embed(color=EVA_COLOR, timestamp=functions.getTimeStamp())
                embed.title = f":x: Compte EVA de {user.display_name} non associé :x:"
                embed.description = f"L'utilisateur {user.mention} n'a pas de compte Eva relié à Discord.\nIl doit taper la commande `/link` pour associer son compte."
                await inter.send(embed=embed)
    
    @stats_user.error
    async def stats_user_error(self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError):
        await self.stats_error(inter, error)

    @lastgame.error
    async def lastgame_error(self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError):
        """
            Gestionnaire d'erreur spécifique de la commande :meth:`lastgame`
        """
        params = inter.filled_options
        if isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, UserIsPrivate):
                await functions.send_error(inter, error.original.args[0])
            elif isinstance(error.original, IndexError):
                await functions.send_error(inter, f"{params['player'].mention} n'a pas joué {params['position']} parties !")
            elif isinstance(error.original, UserNotLinked):
                user: disnake.User = params['player']
                embed = disnake.Embed(color=EVA_COLOR, timestamp=functions.getTimeStamp())
                embed.title = f":x: Compte EVA de {user.display_name} non associé :x:"
                embed.description = f"L'utilisateur {user.mention} n'a pas de compte Eva relié à Discord.\nIl doit taper la commande `/link` pour associer son compte."
                await inter.send(embed=embed)

    @lastgame_user.error
    async def lastgame_user_error(self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError):
        await self.lastgame_error(inter, error)

    @link.error
    async def link_error(self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError):
        """
            Gestionnaire d'erreur spécifique de la commande :meth:`link`
        """
        await inter.response.defer(with_message=True, ephemeral=True)
        embed = disnake.Embed(color=disnake.Color.red(), timestamp=functions.getTimeStamp())
        user_embed = embed.copy()
        if isinstance(error, commandsErrors.PrivateMessageOnly):
            user_embed.title = f"/{inter.application_command.name}"
            user_embed.description = f"Veuillez utiliser la commande `/{inter.application_command.name}` **UNIQUEMENT** __ici__ en message privé, pour des raisons de confidentialité."
            await inter.author.send(embed=user_embed)
            embed.title = ":point_right: Accédez à vos messages privés en cliquant sur ce message :point_left:"
            embed.url = inter.author.dm_channel.jump_url
            embed.description = f"Veuillez utiliser la commande `/{inter.application_command.name}` **UNIQUEMENT** en message privé, pour des raisons de confidentialité."

        if embed.description:   
            await inter.followup.send(embed=embed, ephemeral=True)
            return

def setup(bot: commands.InteractionBot):
    bot.add_cog(Eva(bot))