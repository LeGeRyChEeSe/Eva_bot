import copy
import json
import logging
from math import ceil
from typing import List
import typing
import disnake
from disnake import SelectOption, errors
from disnake.ext import commands
from disnake.ext.commands import errors as commandsErrors
from disnake.ui import Button, Select, ActionRow
from disnake.utils import format_dt
import traceback
from utils.constants import *
import utils.functions as functions

class Listeners(commands.Cog):
    def __init__(self, bot: commands.InteractionBot) -> None:
        self.bot = bot
    
    def check_author(self, *args):
        def inner(message):
            inter = args[0]
            return str(message.author.id) == str(inter.author.id) and message.channel == inter.message.channel
        return inner

    @commands.Cog.listener()
    async def on_ready(self):
        """
            Définis l'action effectuée quand le Bot est en ligne.
        """
        await self.bot.change_presence(activity=disnake.Activity(type=disnake.ActivityType.watching, name="/help"))
        logging.warning(f"{self.bot.user.display_name.title()}#{self.bot.user.discriminator} est prêt")
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild: disnake.Guild):
        async with self.bot.pool.acquire() as con:
            await con.execute('''
            INSERT INTO global_config(guild_id, guild_name, guild_owner_id)
            VALUES($1, $2, $3)
            ON CONFLICT (guild_id)
            DO UPDATE
            SET guild_name = $2, guild_owner_id = $3
            WHERE global_config.guild_id = $1
            ''', guild.id, guild.name, guild.owner_id)
        
        await self.bot.get_cog("Tasks").set_variables()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: disnake.Guild):
        async with self.bot.pool.acquire() as con:
            await con.execute('''
            DELETE FROM global_config
            WHERE guild_id = $1
            ''', guild.id)

    @commands.Cog.listener()
    async def on_guild_update(self, before: disnake.Guild, after: disnake.Guild):
        async with self.bot.pool.acquire() as con:
            await con.execute('''
            UPDATE global_config
            SET guild_id = $2, guild_name = $3, guild_owner_id = $4
            WHERE global_config.guild_id = $1
            ''', before.id, after.id, after.name, after.owner_id)

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send(f'Bienvenue {member.mention} chez {member.guild.name}!')

    @commands.Cog.listener()
    async def on_dropdown(self, inter: disnake.MessageInteraction):
        """
            Fonction appelée lors de l'interaction avec un menu de sélection.

            Paramètres
            ----------
            inter: :class:`disnake.MessageInteraction`
                L'interaction avec le message.
        """
        await inter.response.defer(with_message=True, ephemeral=True)
        custom_id = inter.component.custom_id
        
        embed = disnake.Embed(timestamp=functions.getTimeStamp(), color=EVA_COLOR)
        select: disnake.SelectMenu = inter.component
        username = inter.author.display_name

        if custom_id.startswith("unique_role"):
            role_selected = inter.guild.get_role(int(inter.values[0]))
            embed.description = f":white_check_mark: Le Rôle {role_selected.mention} vous a bien été attribué!"

            for option in select.options:
                role_id = int(option.value)
                role_to_delete = inter.guild.get_role(role_id)

                for user_role in inter.author.roles:
                    if role_id == user_role.id and role_id != role_selected.id:
                        await inter.author.remove_roles(role_to_delete)
            
            await inter.author.add_roles(role_selected)

            if custom_id.endswith("and_set_username"):
                for role in inter.guild.roles:
                    if f"({role.name})" in username:
                        username = username.split(f"({role.name})")[0]

                new_username = f"{username}({role_selected.name})"
                if len(new_username) <= 32:
                    await inter.author.edit(nick=new_username)
                else:
                    embed.description = f"Votre pseudo n'a pas été modifié car l'association de votre pseudo avec le rôle dépasse `32` caractères.\n\nLongueur de votre pseudo {inter.author.mention}: `{len(username)}` caractères.\nLongueur du rôle {role.name} + les caractères '(' et ')': `{len(role.name)+2}` caractères.\nLongueur de votre pseudo + le rôle + les caractères '(' et ')': `{len(new_username)}` caractères.\n\nRetirez `{len(new_username)-32}` caractères à votre pseudo pour afficher votre rôle dans votre pseudo !"
                
            await inter.followup.send(embed=embed)

        elif custom_id == "multiple_roles":
            roles_id = [int(v) for v in inter.values]
            roles = [inter.guild.get_role(r) for r in roles_id]

            if len(roles) > 1:
                embed.description = f":white_check_mark: Les Rôles {', '.join([role.mention for role in roles])} vous ont bien été attribué!"
            elif len(roles) < 1:
                embed.description = ":white_check_mark: Tous les Rôles de la liste vous ont bien été retiré!"
            else:
                embed.description = f":white_check_mark: Le Rôle {roles[0].mention} vous a bien été attribué!"

            for option in select.options:
                option = int(option.value)
                for user_role in inter.author.roles:
                    if option == user_role.id and option not in roles_id:
                        role_to_delete = inter.guild.get_role(int(option))
                        await inter.author.remove_roles(role_to_delete)

            for role in roles:
                await inter.author.add_roles(role)
            
            await inter.followup.send(embed=embed)

        elif custom_id == "other_ranking":
            embed = disnake.Embed(color=functions.perfectGrey(), timestamp=functions.getTimeStamp())
            selections = inter.values

            if inter.message.embeds[0].author.name.startswith("Classement des meilleurs joueurs"):
                city = inter.message.embeds[0].author.name.split("EVA")[1].split("(")[0].strip()
                players = copy.deepcopy(self.bot.get_cog("Variables").guilds_ranking[inter.guild_id])
                embed.title = f"Classement par {STATS.get(selections[0])} des meilleurs joueurs de EVA {city}"
                embed.set_author(name=inter.guild.name, icon_url=inter.guild.icon.url if inter.guild.icon else None)
            else:
                players = copy.deepcopy(self.bot.get_cog("Variables").guilds_ranking["all_players"])
                embed.title = f"Classement mondial par {STATS.get(selections[0])} des meilleurs joueurs EVA"

            pages = ceil(len(players)/MAX_PLAYERS_SCOREBOARD)
            buttons = None
            reverse = True

            embed.set_footer(text=f"Page 1/{pages}")
            embed.description = ""

            if selections[0] in ["deaths", "gameDefeatCount"]:
                reverse = False

            if selections[0] == "experience":
                players.sort(key=lambda x: x["player_infos"]["experience"][selections[0]] or 0, reverse=reverse)

            else:
                players.sort(key=lambda x: x["player_stats"][selections[0]] or 0, reverse=reverse)

            for i in range(len(players)):
                if i == MAX_PLAYERS_SCOREBOARD:
                    break

                member = inter.guild.get_member(players[i]['player_infos']['memberId'])

                if i == 0:
                    first_message = ":first_place:"
                elif i == 1:
                    first_message = ":second_place:"
                elif i == 2:
                    first_message = ":third_place:"
                else:
                    number = str(i+1)
                    new_number = ""
                    for n in number:
                        new_number += numbers[int(n)]
                    first_message =  f"{new_number}"

                # Définitions des prefixes et des suffixes

                content, suffixe, prefixe = "", "", ""

                if selections[0] == "experience":
                    content = players[i]['player_infos']['experience']["level"] or 0
                    prefixe="Niveau "
                else:
                    if selections[0] == "gameCount":
                        suffixe = " Parties"
                    elif selections[0] == "gameTime":
                        suffixe = " Heures"
                    elif selections[0] == "gameVictoryCount":
                        suffixe = " Victoires"
                    elif selections[0] == "gameDefeatCount":
                        suffixe = " Défaites"
                    elif selections[0] == "kills":
                        suffixe = " Tués"
                    elif selections[0] == "deaths":
                        suffixe = " Morts"
                    elif selections[0] == "assists":
                        suffixe = " Assistances"
                    elif selections[0] == "killsByDeaths":
                        suffixe = " K/D"
                    elif selections[0] == "traveledDistance":
                        suffixe = " Mètres"
                    elif selections[0] == "traveledDistanceAverage":
                        suffixe = " Mètres"
                    elif selections[0] == "bestKillStreak":
                        suffixe = " Tués"
                    elif selections[0] == "inflictedDamage":
                        suffixe = " Dégats infligés"
                    
                    if selections[0] == "gameTime":
                        content = round(players[i]['player_stats'][selections[0]] / 3600, 1) or 0
                    elif selections[0] == "killsByDeaths":
                        content = round(players[i]['player_stats'][selections[0]], 3) or 0
                    elif selections[0] in ["traveledDistanceAverage", "traveledDistance"]:
                        content = round(players[i]['player_stats'][selections[0]])
                    else:
                        content = players[i]['player_stats'][selections[0]] or 0

                if i + 1 == len(players):
                    embed.description += f"{first_message}: {member.mention if not inter.author.is_on_mobile() and member else players[i]['player_infos']['username']} | `{prefixe}{content}{suffixe}`\n\n"
                else:
                    embed.description += f"{first_message}: {member.mention if not inter.author.is_on_mobile() and member else players[i]['player_infos']['username']} | `{prefixe}{content}{suffixe}`\n┣┅┅┅┅┅┅┅┅┅┅┅\n"
            
            if pages == 1:
                buttons = [
                    Button(custom_id="begin_ranking", emoji="⏪", disabled=True),
                    Button(custom_id="previous_ranking", emoji="⬅️", disabled=True),
                    Button(custom_id="next_ranking", emoji="➡️", disabled=True),
                    Button(custom_id="final_ranking", emoji="⏩", disabled=True)
                ]
            else:
                buttons = [
                    Button(custom_id="begin_ranking", emoji="⏪", disabled=True),
                    Button(custom_id="previous_ranking", emoji="⬅️", disabled=True),
                    Button(custom_id="next_ranking", emoji="➡️"),
                    Button(custom_id="final_ranking", emoji="⏩")
                ]
            
            bottom_button = Button(style=disnake.ButtonStyle.success, label="Mon classement", custom_id="my_rank_ranking")

            await inter.followup.send(embed=embed, components=[buttons, bottom_button])

        elif custom_id == "reservation":
            await inter.delete_original_response()
            day = json.loads(inter.values[0])
            cities = functions.getCities(self)
            city = functions.getCityfromDict(cities, city_id=day["loc"])

            nb_max = functions.getRoomSize(cities, city["name"], 1)
            date = datetime.datetime.strptime(day['date']+ ' ' + day['start'], '%Y-%m-%d %H:%M')
            
            resa_embed = disnake.Embed(title=f"Réservation à {day['start']}", color=functions.perfectGrey())
            resa_embed.description = f"__**Liste des joueurs**__:\n{inter.author.mention}"
            resa_embed.add_field(name="Ville", value=city["name"], inline=False)
            resa_embed.add_field(name="Horaire choisi", value=f"{format_dt(date)} | {format_dt(date, style='R')}", inline=False)
            resa_embed.add_field(name="Nombre de joueurs maximum", value=nb_max, inline=False)

            buttons = [
                Button(style=disnake.ButtonStyle.url, label="Réserver (EVA.GG)", url=f"https://www.eva.gg/fr/calendrier?locationId={city['id']}&gameId=1&currentDate={day['date']}"),
                Button(style=disnake.ButtonStyle.success, label="J'ai réservé", custom_id="subscribe_reservation"),
                Button(style=disnake.ButtonStyle.danger, label="J'ai annulé", custom_id="unsubscribe_reservation")
            ]

            await inter.channel.send(embed=resa_embed, components=buttons)

    @commands.Cog.listener("on_button_click")
    async def on_button_click(self, inter: disnake.MessageInteraction):
        custom_id = inter.component.custom_id

        def check_subscribed(players):
            for p in players:
                if str(inter.author.id) in p:
                    return p
            return False
        
        def check_number_players(players: List[str], nb_max: int):
            nb_max = nb_max

            if len(players) > nb_max:
                return False
            else:
                return True

        if custom_id == "subscribe_reservation":
            embed = inter.message.embeds[0]
            players = embed.description.split("\n")
            nb_max = int(embed.fields[-1].value)
            response_embed = disnake.Embed(color=EVA_COLOR)
            await inter.response.defer(with_message=True, ephemeral=True)

            if not check_subscribed(players) and check_number_players(players, nb_max):
                embed.description = f"{embed.description}\n{inter.author.mention}"
                response_embed.title = ":white_check_mark: Inscription réussie"
                await inter.message.edit(embed=embed)
            elif not check_number_players(players, nb_max):
                response_embed.title = ":x: Il n'y a plus de places pour cette session"
            else:
                response_embed.title = ":x: Vous êtes déjà inscrit"

            await inter.followup.send(embed=response_embed)

        elif custom_id == "unsubscribe_reservation":
            embed = inter.message.embeds[0]
            players = embed.description.split("\n")
            await inter.response.defer(with_message=True, ephemeral=True)
            response_embed = disnake.Embed(color=EVA_COLOR)
            check = check_subscribed(players)

            if check:
                del players[players.index(check)]
                if len(players) <= 1:
                    response_embed.title = ":white_check_mark: Réservation supprimée car personne n'est inscrit à cette session"
                    await inter.message.delete()
                else:     
                    embed.description = "\n".join(players)
                    response_embed.title = ":white_check_mark: Désinscription réussie"
                    await inter.message.edit(embed=embed)
            else:
                response_embed.title = ":x: Vous n'êtes pas inscrit"

            await inter.followup.send(embed=response_embed)
        
        elif custom_id == "more_ranking":
            players = copy.deepcopy(self.bot.get_cog("Variables").guilds_ranking[inter.guild_id])
            await inter.response.defer(with_message=True, ephemeral=True)
            city = inter.message.embeds[0].author.name.split("EVA")[1].split("(")[0].strip()
            reverse = True

            if not city:
                embed_title = "Classement mondial des meilleurs joueurs EVA"
            else:
                embed_title = f"Classement des meilleurs joueurs de EVA {city}"

            for k, v in STATS.items():
                if v in inter.message.embeds[0].title:
                    if k in ["deaths", "gameDefeatCount"]:
                        reverse = False
                    if k == "experience":
                        players.sort(key=lambda x: x["player_infos"]["experience"][k] or 0, reverse=reverse)
                    else:
                        players.sort(key=lambda x: x["player_stats"][k] or 0, reverse=reverse)
                    embed_title = f"Classement par {v} des meilleurs joueurs de EVA {city}"

            embed = disnake.Embed(title=embed_title, color=functions.perfectGrey(), timestamp=functions.getTimeStamp())
            embed.set_author(name=inter.guild.name, icon_url=inter.guild.icon.url if inter.guild.icon else None)
            
            embed.set_footer(text=f"Page 1/{ceil(len(players)/MAX_PLAYERS_SCOREBOARD)}")
            embed.description = ""

            for i in range(len(players)):
                if i == MAX_PLAYERS_SCOREBOARD:
                    break

                member = inter.guild.get_member(players[i]['player_infos']['memberId'])

                if i == 0:
                    first_message = ":first_place:"
                elif i == 1:
                    first_message = ":second_place:"
                elif i == 2:
                    first_message = ":third_place:"
                else:
                    number = str(i+1)
                    new_number = ""
                    for n in number:
                        new_number += numbers[int(n)]
                    first_message =  f"{new_number}"

                if i + 1 == len(players):
                    embed.description += f"{first_message}: {member.mention if not inter.author.is_on_mobile() and member else players[i]['player_infos']['username']} | `{players[i]['rank']} Points`\n\n"
                else:
                    embed.description += f"{first_message}: {member.mention if not inter.author.is_on_mobile() and member else players[i]['player_infos']['username']} | `{players[i]['rank']} Points`\n┣┅┅┅┅┅┅┅┅┅┅┅\n"

            buttons = [
                Button(custom_id="begin_ranking", emoji="⏪", disabled=True),
                Button(custom_id="previous_ranking", emoji="⬅️", disabled=True),
                Button(custom_id="next_ranking", emoji="➡️"),
                Button(custom_id="final_ranking", emoji="⏩")
            ]

            bottom_button = Button(style=disnake.ButtonStyle.success, label="Mon classement", custom_id="my_rank_ranking")
            
            await inter.followup.send(embed=embed, components=[buttons, bottom_button], ephemeral=True)

        elif custom_id == "begin_ranking":
            city = inter.message.embeds[0].title.split("EVA")[1].split("(")[0].strip()
            components = []

            if not city:
                players = copy.deepcopy(self.bot.get_cog("Variables").guilds_ranking["all_players"])
                embed_title = "Classement mondial des meilleurs joueurs EVA"
            else:
                players = copy.deepcopy(self.bot.get_cog("Variables").guilds_ranking[inter.guild_id])
                embed_title = f"Classement des meilleurs joueurs de EVA {city}"

            pages = ceil(len(players)/MAX_PLAYERS_SCOREBOARD)
            reverse = True
            stat = ""
            
            for k, v in STATS.items():
                if v in inter.message.embeds[0].title:
                    if k in ["deaths", "gameDefeatCount"]:
                        reverse = False
                    if k == "experience":
                        players.sort(key=lambda x: x["player_infos"]["experience"][k] or 0, reverse=reverse)
                    else:
                        players.sort(key=lambda x: x["player_stats"][k] or 0, reverse=reverse)
                    stat = k
                    if not city:
                        embed_title = f"Classement mondial par {v} des meilleurs joueurs EVA"
                    else:
                        embed_title = f"Classement par {v} des meilleurs joueurs de EVA {city}"

            embed = disnake.Embed(title=embed_title, color=functions.perfectGrey(), timestamp=functions.getTimeStamp())
            embed.set_author(name=inter.guild.name, icon_url=inter.guild.icon.url if inter.guild.icon else None)
            embed.set_footer(text=f"Page 1/{pages}")
            embed.description = ""

            for i in range(len(players)):
                if i == MAX_PLAYERS_SCOREBOARD:
                    break

                member = inter.guild.get_member(players[i]['player_infos']['memberId'])

                if i == 0:
                    first_message = ":first_place:"
                elif i == 1:
                    first_message = ":second_place:"
                elif i == 2:
                    first_message = ":third_place:"
                else:
                    number = str(i+1)
                    new_number = ""
                    for n in number:
                        new_number += numbers[int(n)]
                    first_message =  f"{new_number}"

                # Définitions des prefixes et des suffixes

                content, suffixe, prefixe = "", "", ""

                if stat == "experience":
                    content = players[i]['player_infos']['experience']["level"] or 0
                    prefixe="Niveau "
                else:
                    if stat == "gameCount":
                        suffixe = " Parties"
                    elif stat == "gameTime":
                        suffixe = " Heures"
                    elif stat == "gameVictoryCount":
                        suffixe = " Victoires"
                    elif stat == "gameDefeatCount":
                        suffixe = " Défaites"
                    elif stat == "kills":
                        suffixe = " Tués"
                    elif stat == "deaths":
                        suffixe = " Morts"
                    elif stat == "assists":
                        suffixe = " Assistances"
                    elif stat == "killsByDeaths":
                        suffixe = " K/D"
                    elif stat == "traveledDistance":
                        suffixe = " Mètres"
                    elif stat == "traveledDistanceAverage":
                        suffixe = " Mètres"
                    elif stat == "bestKillStreak":
                        suffixe = " Tués"
                    elif stat == "inflictedDamage":
                        suffixe = " Dégats infligés"
                    
                    if stat == "gameTime":
                        content = round(players[i]['player_stats'][stat] / 3600, 1) or 0
                    elif stat == "killsByDeaths":
                        content = round(players[i]['player_stats'][stat], 3) or 0
                    elif stat in ["traveledDistanceAverage", "traveledDistance"]:
                        content = round(players[i]['player_stats'][stat])
                    else:
                        if stat:
                            content = players[i]['player_stats'][stat] or 0
                        else:
                            content = players[i]["rank"] or 0
                            suffixe = " Points"
                
                if i + 1 == len(players):
                    embed.description += f"{first_message}: {member.mention if not inter.author.is_on_mobile() and member else players[i]['player_infos']['username']} | `{prefixe}{content}{suffixe}`\n\n"
                else:
                    embed.description += f"{first_message}: {member.mention if not inter.author.is_on_mobile() and member else players[i]['player_infos']['username']} | `{prefixe}{content}{suffixe}`\n┣┅┅┅┅┅┅┅┅┅┅┅\n"

            buttons = [
                Button(custom_id="begin_ranking", emoji="⏪", disabled=True),
                Button(custom_id="previous_ranking", emoji="⬅️", disabled=True),
                Button(custom_id="next_ranking", emoji="➡️"),
                Button(custom_id="final_ranking", emoji="⏩")
            ]

            components.append(buttons)
            
            bottom_button = Button(style=disnake.ButtonStyle.success, label="Mon classement", custom_id="my_rank_ranking")
            components.append(bottom_button)

            select_menu = None
            rows = ActionRow.rows_from_message(inter.message)
            for _, component in ActionRow.walk_components(rows):
                if component.type == disnake.ComponentType.string_select:
                    components.append(component)
            
            await inter.response.edit_message(embed=embed, components=components)

        elif custom_id == "previous_ranking":
            city = inter.message.embeds[0].title.split("EVA")[1].split("(")[0].strip()
            components = []

            if not city:
                players = copy.deepcopy(self.bot.get_cog("Variables").guilds_ranking["all_players"])   
                embed_title = "Classement mondial des meilleurs joueurs EVA"
            else:
                players = copy.deepcopy(self.bot.get_cog("Variables").guilds_ranking[inter.guild_id])   
                embed_title = f"Classement des meilleurs joueurs de EVA {city}"

            pages = ceil(len(players)/MAX_PLAYERS_SCOREBOARD)
            actual_page = int(''.join(filter(str.isdigit, inter.message.embeds[0].footer.text.split("/")[0])))
            previous_page = actual_page - 1
            reverse = True
            
            stat = ""

            for k, v in STATS.items():
                if v in inter.message.embeds[0].title:
                    if k in ["deaths", "gameDefeatCount"]:
                        reverse = False
                    if k == "experience":
                        players.sort(key=lambda x: x["player_infos"]["experience"][k] or 0, reverse=reverse)
                    else:
                        players.sort(key=lambda x: x["player_stats"][k] or 0, reverse=reverse)
                    stat = k
                    if not city:
                        embed_title = f"Classement mondial par {v} des meilleurs joueurs EVA"
                    else:
                        embed_title = f"Classement par {v} des meilleurs joueurs de EVA {city}"

            embed = disnake.Embed(title=embed_title, color=functions.perfectGrey(), timestamp=functions.getTimeStamp())
            embed.set_author(name=inter.guild.name, icon_url=inter.guild.icon.url if inter.guild.icon else None)
            embed.set_footer(text=f"Page {previous_page}/{pages}")
            embed.description = ""

            for i in range(MAX_PLAYERS_SCOREBOARD * previous_page - MAX_PLAYERS_SCOREBOARD, len(players)):
                if i == MAX_PLAYERS_SCOREBOARD * previous_page:
                    break

                member = inter.guild.get_member(players[i]['player_infos']['memberId'])

                if i == 0:
                    first_message = ":first_place:"
                elif i == 1:
                    first_message = ":second_place:"
                elif i == 2:
                    first_message = ":third_place:"
                else:
                    number = str(i+1)
                    new_number = ""
                    for n in number:
                        new_number += numbers[int(n)]
                    first_message =  f"{new_number}"

                # Définitions des prefixes et des suffixes

                content, suffixe, prefixe = "", "", ""

                if stat == "experience":
                    content = players[i]['player_infos']['experience']["level"] or 0
                    prefixe="Niveau "
                else:
                    if stat == "gameCount":
                        suffixe = " Parties"
                    elif stat == "gameTime":
                        suffixe = " Heures"
                    elif stat == "gameVictoryCount":
                        suffixe = " Victoires"
                    elif stat == "gameDefeatCount":
                        suffixe = " Défaites"
                    elif stat == "kills":
                        suffixe = " Tués"
                    elif stat == "deaths":
                        suffixe = " Morts"
                    elif stat == "assists":
                        suffixe = " Assistances"
                    elif stat == "killsByDeaths":
                        suffixe = " K/D"
                    elif stat == "traveledDistance":
                        suffixe = " Mètres"
                    elif stat == "traveledDistanceAverage":
                        suffixe = " Mètres"
                    elif stat == "bestKillStreak":
                        suffixe = " Tués"
                    elif stat == "inflictedDamage":
                        suffixe = " Dégats infligés"
                    
                    if stat == "gameTime":
                        content = round(players[i]['player_stats'][stat] / 3600, 1) or 0
                    elif stat == "killsByDeaths":
                        content = round(players[i]['player_stats'][stat], 3) or 0
                    elif stat in ["traveledDistanceAverage", "traveledDistance"]:
                        content = round(players[i]['player_stats'][stat])
                    else:
                        if stat:
                            content = players[i]['player_stats'][stat] or 0
                        else:
                            content = players[i]["rank"] or 0
                            suffixe = " Points"

                if i + 1 == len(players):
                    embed.description += f"{first_message}: {member.mention if not inter.author.is_on_mobile() and member else players[i]['player_infos']['username']} | `{prefixe}{content}{suffixe}`\n\n"
                else:
                    embed.description += f"{first_message}: {member.mention if not inter.author.is_on_mobile() and member else players[i]['player_infos']['username']} | `{prefixe}{content}{suffixe}`\n┣┅┅┅┅┅┅┅┅┅┅┅\n"

            if previous_page == 1:
                buttons = [
                    Button(custom_id="begin_ranking", emoji="⏪", disabled=True),
                    Button(custom_id="previous_ranking", emoji="⬅️", disabled=True),
                    Button(custom_id="next_ranking", emoji="➡️"),
                    Button(custom_id="final_ranking", emoji="⏩")
                ]
            else:
                buttons = [
                    Button(custom_id="begin_ranking", emoji="⏪"),
                    Button(custom_id="previous_ranking", emoji="⬅️"),
                    Button(custom_id="next_ranking", emoji="➡️"),
                    Button(custom_id="final_ranking", emoji="⏩")
                ]

            components.append(buttons)
            
            bottom_button = Button(style=disnake.ButtonStyle.success, label="Mon classement", custom_id="my_rank_ranking")
            components.append(bottom_button)

            select_menu = None
            rows = ActionRow.rows_from_message(inter.message)
            for _, component in ActionRow.walk_components(rows):
                if component.type == disnake.ComponentType.string_select:
                    components.append(component)
            
            await inter.response.edit_message(embed=embed, components=components)

        elif custom_id == "next_ranking":
            city = inter.message.embeds[0].title.split("EVA")[1].split("(")[0].strip()
            components = []

            if not city:
                players = copy.deepcopy(self.bot.get_cog("Variables").guilds_ranking["all_players"])   
                embed_title = "Classement mondial des meilleurs joueurs EVA"
            else:
                players = copy.deepcopy(self.bot.get_cog("Variables").guilds_ranking[inter.guild_id])   
                embed_title = f"Classement des meilleurs joueurs de EVA {city}"

            pages = ceil(len(players)/MAX_PLAYERS_SCOREBOARD)
            actual_page = int(''.join(filter(str.isdigit, inter.message.embeds[0].footer.text.split("/")[0])))
            next_page = actual_page + 1
            reverse = True
            
            stat = ""

            for k, v in STATS.items():
                if v in inter.message.embeds[0].title:
                    if k in ["deaths", "gameDefeatCount"]:
                        reverse = False
                    if k == "experience":
                        players.sort(key=lambda x: x["player_infos"]["experience"][k] or 0, reverse=reverse)
                    else:
                        players.sort(key=lambda x: x["player_stats"][k] or 0, reverse=reverse)
                    stat = k
                    if not city:
                        embed_title = f"Classement mondial par {v} des meilleurs joueurs EVA"
                    else:
                        embed_title = f"Classement par {v} des meilleurs joueurs de EVA {city}"

            embed = disnake.Embed(title=embed_title, color=functions.perfectGrey(), timestamp=functions.getTimeStamp())
            embed.set_author(name=inter.guild.name, icon_url=inter.guild.icon.url if inter.guild.icon else None)
            embed.set_footer(text=f"Page {next_page}/{pages}")
            embed.description = ""

            for i in range(MAX_PLAYERS_SCOREBOARD * actual_page, len(players)):
                if i == MAX_PLAYERS_SCOREBOARD * next_page:
                    break

                member = inter.guild.get_member(players[i]['player_infos']['memberId'])

                if i == 0:
                    first_message = ":first_place:"
                elif i == 1:
                    first_message = ":second_place:"
                elif i == 2:
                    first_message = ":third_place:"
                else:
                    number = str(i+1)
                    new_number = ""
                    for n in number:
                        new_number += numbers[int(n)]
                    first_message =  f"{new_number}"

                # Définitions des prefixes et des suffixes

                content, suffixe, prefixe = "", "", ""

                if stat == "experience":
                    content = players[i]['player_infos']['experience']["level"] or 0
                    prefixe="Niveau "
                else:
                    if stat == "gameCount":
                        suffixe = " Parties"
                    elif stat == "gameTime":
                        suffixe = " Heures"
                    elif stat == "gameVictoryCount":
                        suffixe = " Victoires"
                    elif stat == "gameDefeatCount":
                        suffixe = " Défaites"
                    elif stat == "kills":
                        suffixe = " Tués"
                    elif stat == "deaths":
                        suffixe = " Morts"
                    elif stat == "assists":
                        suffixe = " Assistances"
                    elif stat == "killsByDeaths":
                        suffixe = " K/D"
                    elif stat == "traveledDistance":
                        suffixe = " Mètres"
                    elif stat == "traveledDistanceAverage":
                        suffixe = " Mètres"
                    elif stat == "bestKillStreak":
                        suffixe = " Tués"
                    elif stat == "inflictedDamage":
                        suffixe = " Dégats infligés"
                    
                    if stat == "gameTime":
                        content = round(players[i]['player_stats'][stat] / 3600, 1) or 0
                    elif stat == "killsByDeaths":
                        content = round(players[i]['player_stats'][stat], 3) or 0
                    elif stat in ["traveledDistanceAverage", "traveledDistance"]:
                        content = round(players[i]['player_stats'][stat])
                    else:
                        if stat:
                            content = players[i]['player_stats'][stat] or 0
                        else:
                            content = players[i]["rank"] or 0
                            suffixe = " Points"

                if i + 1 == len(players):
                    embed.description += f"{first_message}: {member.mention if not inter.author.is_on_mobile() and member else players[i]['player_infos']['username']} | `{prefixe}{content}{suffixe}`\n\n"
                else:
                    embed.description += f"{first_message}: {member.mention if not inter.author.is_on_mobile() and member else players[i]['player_infos']['username']} | `{prefixe}{content}{suffixe}`\n┣┅┅┅┅┅┅┅┅┅┅┅\n"

            if next_page >= pages:
                buttons = [
                    Button(custom_id="begin_ranking", emoji="⏪"),
                    Button(custom_id="previous_ranking", emoji="⬅️"),
                    Button(custom_id="next_ranking", emoji="➡️", disabled=True),
                    Button(custom_id="final_ranking", emoji="⏩", disabled=True)
                ]
            else:
                buttons = [
                    Button(custom_id="begin_ranking", emoji="⏪"),
                    Button(custom_id="previous_ranking", emoji="⬅️"),
                    Button(custom_id="next_ranking", emoji="➡️"),
                    Button(custom_id="final_ranking", emoji="⏩")
                ]

            components.append(buttons)
            
            bottom_button = Button(style=disnake.ButtonStyle.success, label="Mon classement", custom_id="my_rank_ranking")
            components.append(bottom_button)

            select_menu = None
            rows = ActionRow.rows_from_message(inter.message)
            for _, component in ActionRow.walk_components(rows):
                if component.type == disnake.ComponentType.string_select:
                    components.append(component)
            
            await inter.response.edit_message(embed=embed, components=components)

        elif custom_id == "final_ranking":
            city = inter.message.embeds[0].title.split("EVA")[1].split("(")[0].strip()
            components = []

            if not city:
                players = copy.deepcopy(self.bot.get_cog("Variables").guilds_ranking["all_players"])
                embed_title = "Classement mondial des meilleurs joueurs EVA"
            else:
                players = copy.deepcopy(self.bot.get_cog("Variables").guilds_ranking[inter.guild_id])
                embed_title = f"Classement des meilleurs joueurs de EVA {city}"
            pages = ceil(len(players)/MAX_PLAYERS_SCOREBOARD)
            reverse = True
            stat = ""

            for k, v in STATS.items():
                if v in inter.message.embeds[0].title:
                    if k in ["deaths", "gameDefeatCount"]:
                        reverse = False
                    if k == "experience":
                        players.sort(key=lambda x: x["player_infos"]["experience"][k] or 0, reverse=reverse)
                    else:
                        players.sort(key=lambda x: x["player_stats"][k] or 0, reverse=reverse)
                    stat = k
                    if not city:
                        embed_title = f"Classement mondial par {v} des meilleurs joueurs EVA"
                    else:
                        embed_title = f"Classement par {v} des meilleurs joueurs de EVA {city}"

            embed = disnake.Embed(title=embed_title, color=functions.perfectGrey(), timestamp=functions.getTimeStamp())
            embed.set_author(name=inter.guild.name, icon_url=inter.guild.icon.url if inter.guild.icon else None)
            embed.set_footer(text=f"Page {pages}/{pages}")
            embed.description = ""

            for i in range(MAX_PLAYERS_SCOREBOARD * pages - MAX_PLAYERS_SCOREBOARD, len(players)):
                if i == MAX_PLAYERS_SCOREBOARD * pages:
                    break

                member = inter.guild.get_member(players[i]['player_infos']['memberId'])

                if i == 0:
                    first_message = ":first_place:"
                elif i == 1:
                    first_message = ":second_place:"
                elif i == 2:
                    first_message = ":third_place:"
                else:
                    number = str(i+1)
                    new_number = ""
                    for n in number:
                        new_number += numbers[int(n)]
                    first_message =  f"{new_number}"

                # Définitions des prefixes et des suffixes

                content, suffixe, prefixe = "", "", ""

                if stat == "experience":
                    content = players[i]['player_infos']['experience']["level"] or 0
                    prefixe="Niveau "
                else:
                    if stat == "gameCount":
                        suffixe = " Parties"
                    elif stat == "gameTime":
                        suffixe = " Heures"
                    elif stat == "gameVictoryCount":
                        suffixe = " Victoires"
                    elif stat == "gameDefeatCount":
                        suffixe = " Défaites"
                    elif stat == "kills":
                        suffixe = " Tués"
                    elif stat == "deaths":
                        suffixe = " Morts"
                    elif stat == "assists":
                        suffixe = " Assistances"
                    elif stat == "killsByDeaths":
                        suffixe = " K/D"
                    elif stat == "traveledDistance":
                        suffixe = " Mètres"
                    elif stat == "traveledDistanceAverage":
                        suffixe = " Mètres"
                    elif stat == "bestKillStreak":
                        suffixe = " Tués"
                    elif stat == "inflictedDamage":
                        suffixe = " Dégats infligés"
                    
                    if stat == "gameTime":
                        content = round(players[i]['player_stats'][stat] / 3600, 1) or 0
                    elif stat == "killsByDeaths":
                        content = round(players[i]['player_stats'][stat], 3) or 0
                    elif stat in ["traveledDistanceAverage", "traveledDistance"]:
                        content = round(players[i]['player_stats'][stat])
                    else:
                        if stat:
                            content = players[i]['player_stats'][stat] or 0
                        else:
                            content = players[i]["rank"] or 0
                            suffixe = " Points"

                if i + 1 == len(players):
                    embed.description += f"{first_message}: {member.mention if not inter.author.is_on_mobile() and member else players[i]['player_infos']['username']} | `{prefixe}{content}{suffixe}`\n\n"
                else:
                    embed.description += f"{first_message}: {member.mention if not inter.author.is_on_mobile() and member else players[i]['player_infos']['username']} | `{prefixe}{content}{suffixe}`\n┣┅┅┅┅┅┅┅┅┅┅┅\n"

            buttons = [
                Button(custom_id="begin_ranking", emoji="⏪"),
                Button(custom_id="previous_ranking", emoji="⬅️"),
                Button(custom_id="next_ranking", emoji="➡️", disabled=True),
                Button(custom_id="final_ranking", emoji="⏩", disabled=True)
            ]

            components.append(buttons)
            
            bottom_button = Button(style=disnake.ButtonStyle.success, label="Mon classement", custom_id="my_rank_ranking")
            components.append(bottom_button)

            select_menu = None
            rows = ActionRow.rows_from_message(inter.message)
            for _, component in ActionRow.walk_components(rows):
                if component.type == disnake.ComponentType.string_select:
                    components.append(component)
            
            await inter.response.edit_message(embed=embed, components=components)
        
        elif custom_id == "my_rank_ranking":
            try:
                city = inter.message.embeds[0].title.split("EVA")[1].split("(")[0].strip()
            except IndexError:
                city = inter.message.embeds[0].author.name.split("EVA")[1].split("(")[0].strip()
                players = copy.deepcopy(self.bot.get_cog("Variables").guilds_ranking[inter.guild_id])
            else:
                if not city:
                    players = copy.deepcopy(self.bot.get_cog("Variables").guilds_ranking["all_players"])
                else:
                    players = copy.deepcopy(self.bot.get_cog("Variables").guilds_ranking[inter.guild_id])

            await inter.response.defer(with_message=True, ephemeral=True)
            reverse, is_general = True, True
            style_scoreboarding = ""
            stat = ""

            embed = disnake.Embed(color=EVA_COLOR, timestamp=functions.getTimeStamp())
            embed.set_author(name=inter.guild.name, icon_url=inter.guild.icon.url if inter.guild.icon else None)

            for k, v in STATS.items():
                if v in inter.message.embeds[0].title:
                    if k in ["deaths", "gameDefeatCount"]:
                        reverse = False
                    if k == "experience":
                        players.sort(key=lambda x: x["player_infos"]["experience"][k] or 0, reverse=reverse)
                    else:
                        players.sort(key=lambda x: x["player_stats"][k] or 0, reverse=reverse)
                    stat = k

                    is_general = False
                    style_scoreboarding = v

            for i in range(len(players)):
                if players[i]["player_infos"]["memberId"] == inter.author.id:
                    # Définitions des prefixes et des suffixes

                    content, suffixe, prefixe = "", "", ""

                    if not stat:
                        pass
                    elif stat == "experience":
                        content = players[i]['player_infos']['experience']["level"] or 0
                        prefixe="Niveau "
                    else:
                        if stat == "gameCount":
                            suffixe = " Parties"
                        elif stat == "gameTime":
                            suffixe = " Heures"
                        elif stat == "gameVictoryCount":
                            suffixe = " Victoires"
                        elif stat == "gameDefeatCount":
                            suffixe = " Défaites"
                        elif stat == "kills":
                            suffixe = " Tués"
                        elif stat == "deaths":
                            suffixe = " Morts"
                        elif stat == "assists":
                            suffixe = " Assistances"
                        elif stat == "killsByDeaths":
                            suffixe = " K/D"
                        elif stat == "traveledDistance":
                            suffixe = " Mètres"
                        elif stat == "traveledDistanceAverage":
                            suffixe = " Mètres"
                        elif stat == "bestKillStreak":
                            suffixe = " Tués"
                        elif stat == "inflictedDamage":
                            suffixe = " Dégats infligés"
                        
                        if stat == "gameTime":
                            content = round(players[i]['player_stats'][stat] / 3600, 1) or 0
                        elif stat == "killsByDeaths":
                            content = round(players[i]['player_stats'][stat], 3) or 0
                        elif stat in ["traveledDistanceAverage", "traveledDistance"]:
                            content = round(players[i]['player_stats'][stat])
                        else:
                            content = players[i]['player_stats'][stat] or 0
                    
                    if not city:
                        if i == 0:
                            if is_general:
                                embed.description = f"Vous êtes **{i+1}er** dans le classement mondial avec un total de {players[i]['rank']} points."
                            else:
                                embed.description = f"Vous êtes **{i+1}er** dans le classement mondial par __{style_scoreboarding}__ | `{prefixe}{content}{suffixe}`"
                        else:
                            if is_general:
                                embed.description = f"Vous êtes **{i+1}ème** dans le classement mondial avec un total de {players[i]['rank']} points."
                            else:
                                embed.description = f"Vous êtes **{i+1}ème** dans le classement mondial par __{style_scoreboarding}__ | `{prefixe}{content}{suffixe}`"
                    else:
                        if i == 0:
                            if is_general:
                                embed.description = f"Vous êtes **{i+1}er** dans le classement avec un total de {players[i]['rank']} points."
                            else:
                                embed.description = f"Vous êtes **{i+1}er** dans le classement par __{style_scoreboarding}__ | `{prefixe}{content}{suffixe}`"
                        else:
                            if is_general:
                                embed.description = f"Vous êtes **{i+1}ème** dans le classement avec un total de {players[i]['rank']} points."
                            else:
                                embed.description = f"Vous êtes **{i+1}ème** dans le classement par __{style_scoreboarding}__ | `{prefixe}{content}{suffixe}`"
            
                    await inter.followup.send(embed=embed)
                    return
            
            embed.title = functions.getLocalization(self.bot, "NOT_LINKED_EMBED_TITLE", inter.locale, displayName=inter.author.display_name)
            embed.description = functions.getLocalization(self.bot, "NOT_LINKED_EMBED_DESCRIPTION", inter.locale, playerMention=inter.author.mention, commandName=functions.getLocalization(self.bot, 'LINK_NAME', inter.locale), clientMention=inter.guild.me.mention)
            embed_player = disnake.Embed(title=functions.getLocalization(self.bot, "NOT_LINKED_PLAYER_EMBED_TITLE", inter.locale), color=EVA_COLOR, timestamp=functions.getTimeStamp())
            if inter.author.avatar:
                embed_player.set_author(name=inter.author.display_name, icon_url=inter.author.display_avatar.url)
            else:
                embed_player.set_author(name=inter.author.display_name)
            if self.bot.user.avatar:
                embed_player.set_thumbnail(url=self.bot.user.display_avatar.url)
            embed_player.description = functions.getLocalization(self.bot, "NOT_LINKED_PLAYER_EMBED_DESCRIPTION", inter.locale, playerMention=inter.author.mention, commandName=functions.getLocalization(self.bot, 'LINK_NAME', inter.locale))
            await inter.author.send(embed=embed_player)
            await inter.followup.send(embed=embed)

        elif custom_id == "remove_role":
            await inter.response.defer(with_message=True, ephemeral=True)
            embed = disnake.Embed(timestamp=functions.getTimeStamp(), color=disnake.Color.red())
            embed.description = ""
            any_role = True
            select_menu = inter.message.components[0].children[0]
            for option in select_menu.options:
                role = inter.guild.get_role(int(option.value))
                if role in inter.author.roles:
                    await inter.author.remove_roles(role)
                    embed.description += f":white_check_mark: Le Rôle {role.mention} vous a bien été retiré!\n"
                    any_role = False
            if any_role:
                embed.description = ":x: Vous n'avez aucun rôle de la liste !"
            await inter.followup.send(embed=embed)

        elif custom_id == "global_ranking":
            players: typing.List[typing.Dict[typing.Dict, typing.Dict]] = copy.deepcopy(self.bot.get_cog("Variables").guilds_ranking["all_players"])
            await inter.response.defer(with_message=True, ephemeral=True)
            reverse = True
            embed_title = "Classement mondial des meilleurs joueurs EVA"

            for k, v in STATS.items():
                if v in inter.message.embeds[0].title:
                    if k in ["deaths", "gameDefeatCount"]:
                        reverse = False
                    if k == "experience":
                        players.sort(key=lambda x: x["player_infos"]["experience"][k] or 0, reverse=reverse)
                    else:
                        players.sort(key=lambda x: x["player_stats"][k] or 0, reverse=reverse)
                    embed_title = f"Classement mondial par {v} des meilleurs joueurs EVA"

            embed = disnake.Embed(title=embed_title, color=functions.perfectGrey(), timestamp=functions.getTimeStamp())
            embed.set_author(name=inter.guild.name, icon_url=inter.guild.icon.url if inter.guild.icon else None)
            
            embed.set_footer(text=f"Page 1/{ceil(len(players)/MAX_PLAYERS_SCOREBOARD)}")
            embed.description = ""
            select_options = []

            for stat in players[0]["player_stats"].keys():
                reverse = True

                if stat in ["bestInflictedDamage", "killDeathRatio", "gameDrawCount"]:
                    continue

                elif stat in ["deaths", "gameDefeatCount"]:
                    reverse = False
                
                if stat == "experience":
                    players.sort(key=lambda x: x["player_infos"]["experience"][stat] or 0, reverse=reverse)
                else:
                    players.sort(key=lambda x: x["player_stats"][stat] or 0, reverse=reverse)
                select_options.append(SelectOption(label=STATS[stat], value=stat, description=f"Voir le classement mondial par {STATS[stat]}"))

                for i in range(len(players)):
                    try:
                        players[i]["rank"] += i + 1
                    except:
                        players[i]["rank"] = 0

            players.sort(key=lambda x: x["rank"])

            self.bot.get_cog("Variables").guilds_ranking["all_players"] = copy.deepcopy(players)

            for i in range(len(players)):
                if i == MAX_PLAYERS_SCOREBOARD:
                    break

                member = inter.guild.get_member(players[i]['player_infos']['memberId'])

                if i == 0:
                    first_message = ":first_place:"
                elif i == 1:
                    first_message = ":second_place:"
                elif i == 2:
                    first_message = ":third_place:"
                else:
                    number = str(i+1)
                    new_number = ""
                    for n in number:
                        new_number += numbers[int(n)]
                    first_message =  f"{new_number}"

                if i + 1 == len(players):
                    embed.description += f"{first_message}: {member.mention if not inter.author.is_on_mobile() and member else players[i]['player_infos']['username']} | `{players[i]['rank']} Points`\n\n"
                else:
                    embed.description += f"{first_message}: {member.mention if not inter.author.is_on_mobile() and member else players[i]['player_infos']['username']} | `{players[i]['rank']} Points`\n┣┅┅┅┅┅┅┅┅┅┅┅\n"

            buttons = [
                Button(custom_id="begin_ranking", emoji="⏪", disabled=True),
                Button(custom_id="previous_ranking", emoji="⬅️", disabled=True),
                Button(custom_id="next_ranking", emoji="➡️"),
                Button(custom_id="final_ranking", emoji="⏩")
            ]
            
            select_options.append(SelectOption(label=STATS["experience"], value="experience", description=f"Voir le classement mondial par {STATS['experience']}"))

            select = Select(placeholder="Choisir un autre classement", options=select_options, custom_id="other_ranking")

            bottom_button = Button(style=disnake.ButtonStyle.success, label="Mon classement", custom_id="my_rank_ranking")
            
            await inter.followup.send(embed=embed, components=[buttons, bottom_button, select], ephemeral=True)

    @commands.Cog.listener()
    async def on_slash_command_error(self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError):
        """
            Gestionnaire d'erreur général pour toutes les commandes slash.
            
            Gère toutes les erreurs non gérées par leurs gestionnaires respectifs.
        """
        if inter.application_command.has_error_handler():
            return

        error_formated = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        logging.error(error_formated)
        embed = disnake.Embed(color=EVA_COLOR, timestamp=functions.getTimeStamp())
        params = inter.filled_options

        if "player" in params.keys():
            player: disnake.User = params['player']
            if player.bot:
                embed.description = f"Bien essayé ! Mais {player.mention} est juste un Bot et ne peut donc pas jouer à Eva !"
                await inter.send(embed=embed)
                return
        else:
            player = None        

        if isinstance(error, commands.CommandInvokeError):
            original = error.original
            error_formated = "".join(traceback.format_exception(type(original), original, original.__traceback__))
            
            if isinstance(original, errors.HTTPException):
                embed.description = "Je ne peux pas envoyer de messages privés à cet utilisateur ! Il doit autoriser les messages privés provenant des membres du serveur !"
            elif isinstance(original, TypeError):
                if player:
                    embed.title = f":x: {player.display_name} n'est pas encore relié à Eva"
                    embed.description = f"L'utilisateur {player.mention} n'a pas de compte Eva relié à Discord.\nIl doit taper la commande `/link` en message privé à {self.bot.user.mention} pour associer son compte.\nUn message privé lui a été envoyé pour qu'il associe son compte."
                    player_embed = disnake.Embed(title=f"Association de votre compte Eva à Discord")
                    player_embed.set_author(name=player.display_name, icon_url=player.display_avatar.url)
                    player_embed.set_thumbnail(url=self.bot.user.display_avatar.url)
                    player_embed.description = f"{inter.author.mention} vous invite à associer votre compte Eva à votre compte Discord, pour que tout le monde puisse voir l'historique de vos parties ainsi que vos statistiques **publiques** uniquement !\nPour cela rien de plus simple: Tapez ci-dessous la commande `/link` pour associer votre compte!"
                    await player.send(embed=player_embed)
                    await inter.send(embed)
                    return
                else:
                    embed.description = "Une erreur est survenue, elle a bien été signalée."
            elif isinstance(original, AttributeError):
                embed.description = "Une des valeurs nécessaires au fonctionnement du bot est nulle."
        elif isinstance(error, commandsErrors.PrivateMessageOnly):
            return
        elif isinstance(error, commandsErrors.CheckFailure):
            logging.error(inter.application_command.qualified_name, inter.application_command.has_error_handler())
            if inter.application_command.has_error_handler():
                return
        else:
            embed.description = f"Une erreur est survenue, elle a bien été signalée."
        
        admin = self.bot.get_user(ADMIN_USER)
        user_embed = embed.copy()
        if inter.guild:
            user_embed.title = f"Une erreur est survenue dans le serveur {inter.guild.name}"
            user_embed.url = inter.channel.jump_url
            if not inter.author.avatar:
                user_embed.set_author(name=f"{inter.author.display_name}#{inter.author.discriminator}")
            else:
                user_embed.set_author(name=f"{inter.author.display_name}#{inter.author.discriminator}", icon_url=inter.author.display_avatar.url)
            user_embed.set_footer(text=f"#{inter.channel.name}", icon_url=inter.guild.icon.url if inter.guild.icon else None)
            user_embed.description = f"```py\n{error_formated}\n```"
            user_embed.add_field(name="Message original", value=f"`/{inter.application_command.name} {' '.join(str(o) for o in inter.filled_options.values())}`", inline=False)
            await admin.send(embed=user_embed)
        else:
            user_embed.title = f"Une erreur est survenue dans les messages privés avec {inter.author.mention}"
            if not inter.author.avatar:
                user_embed.set_author(name=f"{inter.author.display_name}#{inter.author.discriminator}")
            else:
                user_embed.set_author(name=f"{inter.author.display_name}#{inter.author.discriminator}", icon_url=inter.author.display_avatar.url)
            user_embed.description = f"```py\n{error_formated}\n```"
            user_embed.add_field(name="Message original", value=f"`/{inter.application_command.name} {' '.join(str(o) for o in inter.filled_options.values())}`", inline=False)
            await admin.send(embed=user_embed)
        
        if embed.description:
            await inter.send(embed=embed, ephemeral=True)

def setup(bot: commands.InteractionBot):
    bot.add_cog(Listeners(bot))