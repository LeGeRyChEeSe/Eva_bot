import json
import disnake
import re
from disnake import SelectOption, errors
from disnake.ext import commands, tasks
from disnake.ui import ActionRow, Button, Select
from disnake.utils import format_dt
import typing
from utils.constants import *
import utils.functions as functions

class Tasks(commands.Cog):
    def __init__(self, bot: commands.InteractionBot) -> None:
        self.bot = bot
        self.start_tasks.start()

    @tasks.loop(minutes=15)
    async def set_best_players_ranking(self):

        async with self.bot.pool.acquire() as con:
            best_players_ranking_channels_id = await con.fetch('''
            SELECT best_players_ranking_channel_id, guild_id
            FROM global_config
            ''')

        best_players_ranking_channels = []
        
        for record in best_players_ranking_channels_id:
            if record["best_players_ranking_channel_id"] is not None:
                try:
                    channel = await self.bot.fetch_channel(record["best_players_ranking_channel_id"])
                except:
                    async with self.bot.pool.acquire() as con:
                        await con.execute("""
                        UPDATE global_config
                        SET best_players_ranking_channel_id = NULL
                        WHERE global_config.best_players_ranking_channel_id = $1
                        """, record["best_players_ranking_channel_id"])
                else:
                    best_players_ranking_channels.append(channel)

        for channel in best_players_ranking_channels:
            guild = self.bot.get_guild(channel.guild.id)
            edited = False
            more = False

            if not channel.permissions_for(guild.me).send_messages or not channel.permissions_for(guild.me).embed_links:
                continue
            
            players: typing.List[typing.Dict[typing.Dict, typing.Dict]] = []

            embed = disnake.Embed(title=f"Actualisation {format_dt(functions.getTimeStamp() + datetime.timedelta(minutes=15), style='R')}", color=EVA_COLOR, timestamp=functions.getTimeStamp())
            embed.set_author(name=f"Classement général des meilleurs joueurs Eva de {guild.name}", icon_url=guild.icon.url if guild.icon else None)
            embed.description = ""
            embed.add_field(name="Le classement général est calculé en fonction de tous les classements suivants", value="Nombre de parties jouées\nTemps de jeu\nNombre de victoires\nNombre de défaites\nNombre de parties\nDégats infligés\nTués (K)\nMorts (D)\nAssistances (A)\nRatio Tués/Morts (K/D)\nDistance parcourue\nDistance moyenne parcourue\nMeilleur série d'éliminations\nNiveau", inline=False)
            embed.add_field(name="Vous ne voyez pas votre pseudo dans le classement ?", value=f"Tapez la commande `/{functions.getLocalization(self.bot, 'LINK_NAME', guild.preferred_locale)}` en message privé à {guild.me.mention} pour associer votre compte Eva à votre compte Discord !\nUne fois l'association terminée patientez le temps indiqué plus haut pour voir votre position dans le classement !\nCliquez sur `Mon classement` si vous ne vous trouvez pas pour afficher votre position !", inline=False)
            embed.add_field(name="Vous ne voyez toujours pas votre pseudo dans le classement après avoir associé votre compte Eva ?",value=f"Vérifiez bien sur le site [EVA.GG](https://www.eva.gg) que la case __**Profil public**__ est cochée pour que {guild.me.mention} puisse récupérer les infos de votre profil !", inline=False)

            for member in guild.members:
                user_infos = await functions.getPlayerInfos(self.bot, member)

                if user_infos:
                    try:
                        player_infos, player_stats = await functions.getStats(user_infos["player_id"], self.bot.get_cog("Variables").seasons_list[-1])
                    except:
                        continue
                    player_infos["player"]["memberId"] = member.id
                    players.append({"player_infos": player_infos["player"], "player_stats": player_stats["player"]["statistics"]["data"]})
            
            select_options = []
            
            for stat in players[0]["player_stats"].keys():
                reverse = True

                if stat in ["bestInflictedDamage", "killDeathRatio"]:
                    continue

                elif stat in ["deaths", "gameDefeatCount"]:
                    reverse = False
                
                if stat == "experience":
                    players.sort(key=lambda x: x["player_infos"]["experience"][stat] or 0, reverse=reverse)
                else:
                    players.sort(key=lambda x: x["player_stats"][stat] or 0, reverse=reverse)
                select_options.append(SelectOption(label=STATS[stat], value=stat, description=f"Voir le classement par {STATS[stat]}"))

                for i in range(len(players)):
                    try:
                        players[i]["rank"] += i + 1
                    except:
                        players[i]["rank"] = 0
            
            select_options.append(SelectOption(label=STATS["experience"], value="experience", description=f"Voir le classement par {STATS['experience']}"))

            select = Select(placeholder="Choisir un autre classement", options=select_options, custom_id="other_ranking")

            players.sort(key=lambda x: x["rank"])

            self.bot.get_cog("Variables").guilds_ranking[guild.id] = players

            for i in range(len(players)):
                if i == MAX_PLAYERS_SCOREBOARD:
                    embed.description += "**.**\n**.**\n**Cliquez sur le bouton `Plus` pour afficher le reste du classement.**"
                    more = True
                    break

                member = guild.get_member(players[i]['player_infos']['memberId'])
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

                embed.description += f"{first_message}: {member.mention}\n┣┅┅┅┅┅┅┅┅┅┅┅\n"

            if more:
                buttons = [
                    Button(style=disnake.ButtonStyle.blurple, label="Plus", custom_id="more_ranking"),
                    Button(style=disnake.ButtonStyle.success, label="Mon classement", custom_id="my_rank_ranking")
                ]
            else:
                buttons = [
                    Button(style=disnake.ButtonStyle.success, label="Mon classement", custom_id="my_rank_ranking")
                ]

            async for message in channel.history(limit=5, oldest_first=True):
                if message.author != guild.me:
                    continue
                if len(message.embeds) < 1:
                    continue

                if message.embeds[0].title.startswith("Actualisation"):
                    await message.edit(embed=embed, components=[buttons, select])
                    edited = True
                    break
            
            if not edited:
                await channel.send(embed=embed, components=[buttons, select])

    @tasks.loop(minutes=1)
    async def deadline_resa_channel(self):
        for record in self.bot.get_cog("Variables").resa_channels:
            guild = self.bot.get_guild(record["guild_id"])
            resa_channel: disnake.ForumChannel = guild.get_channel(record["resa_channel_id"])

            if not resa_channel or resa_channel.type != disnake.ChannelType.forum:
                continue
            elif not resa_channel.permissions_for(guild.me).send_messages or not resa_channel.permissions_for(guild.me).send_messages_in_threads or not resa_channel.permissions_for(guild.me).embed_links or not resa_channel.permissions_for(guild.me).manage_threads:
                continue

            for thread in resa_channel.threads:
                try:
                    async for message in thread.history(oldest_first=False, limit=None):
                        if not message.embeds or message.author != self.bot.user:
                            continue
                        elif message.embeds[0].description.startswith("La réservation s'autodétruira à la fin de la session"):
                            try:
                                deadline = datetime.datetime.fromtimestamp(int(re.search("[0-9]+", message.embeds[0].description).group()))
                            except ValueError:
                                pass
                            else:
                                actual_time = functions.getTimeStamp()
                                if deadline < actual_time:
                                    await message.delete()
                        try:
                            deadline = datetime.datetime.fromtimestamp(int(re.search("[0-9]+", message.embeds[0].fields[1].value).group()))
                        except ValueError:
                            pass
                        else:
                            extend_deadline = deadline + datetime.timedelta(minutes=40)
                            actual_time = functions.getTimeStamp()

                            if extend_deadline < actual_time:
                                await message.delete()
                            elif actual_time.timestamp() - deadline.timestamp() <= 60 and actual_time.timestamp() - deadline.timestamp() > 0:
                                embed = disnake.Embed(title=f"La session de {deadline.time().strftime('%H:%M')} vient de commencer ! Vous ne pouvez plus vous y inscrire.", description=f"La réservation s'autodétruira à la fin de la session {format_dt(extend_deadline, style='R')}.", color=EVA_COLOR, timestamp=functions.getTimeStamp())
                                
                                rows = ActionRow.rows_from_message(message)
                                for _, component in ActionRow.walk_components(rows):
                                    component.disabled = True
                                
                                await thread.send(embed=embed)
                                await message.edit(components=rows, delete_after=(extend_deadline.timestamp() - actual_time.timestamp()))
                except:
                    continue

    @tasks.loop(minutes=1)
    async def alert_resa(self):
        for record in self.bot.get_cog("Variables").resa_channels:
            guild = self.bot.get_guild(record["guild_id"])
            resa_channel: disnake.ForumChannel = guild.get_channel(record["resa_channel_id"])

            if not resa_channel or resa_channel.type != disnake.ChannelType.forum:
                continue
            elif not resa_channel.permissions_for(guild.me).send_messages or not resa_channel.permissions_for(guild.me).send_messages_in_threads or not resa_channel.permissions_for(guild.me).embed_links:
                continue

            for thread in resa_channel.threads:
                try:
                    async for message in thread.history(oldest_first=True):
                        if (message.embeds and not message.embeds[0].fields) or not message.embeds:
                            continue

                        try:
                            players_list = message.embeds[0].description.split("\n")[1:]
                        except AttributeError:
                            players_list = None
                        except IndexError:
                            players_list = None
                        else:
                            players_list = ", ".join(players_list)

                        try:
                            deadline = datetime.datetime.fromtimestamp(int(re.search("[0-9]+", message.embeds[0].fields[1].value).group()))
                        except ValueError:
                            pass
                        else:
                            alert_deadline = deadline - datetime.timedelta(minutes=40)
                            actual_time = functions.getTimeStamp()

                            if alert_deadline < actual_time and actual_time < deadline and actual_time.timestamp() - alert_deadline.timestamp() <= 60:
                                embed = disnake.Embed(title=f"La session commence {format_dt(deadline, style='R')} !", color=EVA_COLOR, timestamp=functions.getTimeStamp())
                                original_embed = message.embeds[0]

                                await message.edit(embed=original_embed)
                                await thread.send(content=players_list, embed=embed, delete_after=(deadline.timestamp() - actual_time.timestamp()))
                except:
                    continue

    @tasks.loop(minutes=1)
    async def updateDaysResa(self):
        """
            Met à jour tous les fils (threads) de chaque forum de réservation de chaque serveur
            
            en fonction de la date actuelle jusqu'à J+6.
        """
        for record in self.bot.get_cog("Variables").resa_channels:
            guild = self.bot.get_guild(record["guild_id"])
            resa_channel: disnake.ForumChannel = guild.get_channel(record["resa_channel_id"])
            days_with_dates = await functions.getEachDayInTheWeek()
            days_with_dates = sorted(days_with_dates.items(), key=lambda x: x[1], reverse=True)

            if not resa_channel or resa_channel.type != disnake.ChannelType.forum:
                continue
            elif not resa_channel.permissions_for(guild.me).send_messages or not resa_channel.permissions_for(guild.me).send_messages_in_threads or not resa_channel.permissions_for(guild.me).embed_links:
                continue

            async with self.bot.pool.acquire() as con:
                location_id = await con.fetch("""
                SELECT city_id
                FROM global_config
                WHERE global_config.guild_id = $1
                """, guild.id)

            cities = functions.getCities(self)
            city = functions.getCityfromDict(cities, city_id=location_id[0]["city_id"])
            threads: typing.List[disnake.Thread] = []
            next_day = False

            for thread in resa_channel.threads:
                if not thread or not thread.applied_tags:
                    continue

                try:
                    thread_date = datetime.datetime.strptime(thread.name, "%A %d %B %Y")
                except:
                    continue
                
                days_with_dates_formated: typing.List[datetime.date] = []

                for _, date in days_with_dates:
                    days_with_dates_formated.append(date.date())
                    
                if thread_date.date() not in days_with_dates_formated:
                    for t in days_with_dates:
                        k, v = t[0], t[1]
                        day_tag = DAYS[v.weekday()]
                        tag = [tag for tag in resa_channel.available_tags if day_tag == tag.name]
                        if tag:
                            tag = tag[0]
                            calendar = await functions.getCalendar(self, v, city_name=city["name"])
                            calendar = calendar["calendar"]
                            forum_embed = disnake.Embed(title=f"Réservations du {v.strftime('%A %d %B %Y')}", color=disnake.Color.red())
                            forum_embed.set_image(file=disnake.File("assets/Images/reservation.gif"))
                            select_options = []

                            for day in calendar["sessionList"]["list"]:
                                select_options.append(SelectOption(label=f"{day['startTime']}", value=json.dumps({
                                    "loc": day["slot"]["locationId"],
                                    "date": day["slot"]["date"],
                                    "start": day["slot"]["startTime"],
                                    "end": day["slot"]["endTime"]
                                }), description=f"{day['startTime']} ➡️ {day['endTime']}"))

                            select = Select(placeholder="Choisir un horaire", options=select_options, custom_id="reservation")
                            button = Button(style=disnake.ButtonStyle.url, label="Réserver sur EVA.GG", url=f"https://www.eva.gg/fr/calendrier?locationId={city['id']}&gameId=1&currentDate={v.strftime('%Y-%m-%d')}")
                            
                            await resa_channel.create_thread(name=f"{v.strftime('%A %d %B %Y')}", applied_tags=[tag], embed=forum_embed, components=[button, select])
                            next_day = True
                            await thread.delete()
                            break
                else:
                    threads.append(thread)

                if thread_date.date() == datetime.datetime.now(thread_date.tzinfo).date():
                    if not thread:
                        continue

                    messages = await thread.history(limit=1, oldest_first=True).flatten()
                    message = messages[0]
                    empty = False
                    rows = ActionRow.rows_from_message(message)
                    
                    for _, component in ActionRow.walk_components(rows):
                        if component.type == disnake.ComponentType.string_select:
                            for option in component.options:
                                datetime_option = datetime.datetime.strptime(f"{thread.name} {option.label}", "%A %d %B %Y %H:%M")
                                if datetime_option < datetime.datetime.now(datetime_option.tzinfo):
                                    component.options.remove(option)
                                    if not component.options:
                                        empty = True

                    await message.edit(components=rows if not empty else None)

            if next_day:
                threads.sort(key=lambda x: x.created_at)
                for thread in threads:
                    history = await thread.history(oldest_first=True).flatten()
                    first_message = history[0]
                    first_message.embeds[0].set_image(file=disnake.File("assets/Images/reservation.gif"))
                    new_thread, _ = await resa_channel.create_thread(name=thread.name, applied_tags=thread.applied_tags, embeds=first_message.embeds, components=ActionRow.rows_from_message(first_message))

                    if len(history) > 1:
                        other_messages = history[1:]
                        for message in other_messages:
                            if message.author != self.bot.user:
                                content = f"**{message.author.display_name} le {format_dt(message.created_at)}**:\n>>> {message.content}"
                            else:
                                content = message.content
                            await new_thread.send(content=content, embeds=message.embeds, components=ActionRow.rows_from_message(message))
                    await thread.delete()

    @tasks.loop(hours=1)
    async def set_variables(self):
        # Seasons List
        self.bot.get_cog("Variables").seasons_list = await functions.getSeasonsList()

        # Eva Cities
        self.bot.get_cog("Variables").eva_cities = await functions.setCities()

    @tasks.loop(count=1)
    async def set_resa_channels(self):
        self.bot.get_cog("Variables").resa_channels = await functions.setGuildsResaChannels(self.bot.pool)
    
    # Les 2 fonctions ci-dessous doivent impérativement rester à la fin de la liste des tâches
    @tasks.loop(count=1)
    async def start_tasks(self):
        self.set_variables.start()
        self.set_best_players_ranking.start()
        self.deadline_resa_channel.start()
        self.alert_resa.start()
        self.set_resa_channels.start()
        self.updateDaysResa.start()
    
    @start_tasks.before_loop
    async def before_start_tasks(self):
        await self.bot.wait_until_ready()

    def cog_unload(self) -> None:
        self.start_tasks.stop()
        self.set_variables.stop()
        self.set_best_players_ranking.stop()
        self.deadline_resa_channel.stop()
        self.alert_resa.stop()
        self.set_resa_channels.stop()
        self.updateDaysResa.stop()

def setup(bot: commands.InteractionBot):
    bot.add_cog(Tasks(bot))