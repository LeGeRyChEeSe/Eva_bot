import asyncio
import json
import disnake
import logging
from disnake import Localized
from disnake import SelectOption
from disnake.ext import commands
from disnake.ext.commands import errors as commandsErrors
from disnake.ui import StringSelect, ActionRow, Button
from disnake.utils import format_dt
import utils.functions as functions
from utils.constants import *
import utils.classes as classes


class Admin(commands.Cog):
    def __init__(self, bot: classes.EvaBot) -> None:
        self.bot = bot

    @commands.slash_command(name="reload")
    @commands.default_member_permissions(administrator=True)
    @commands.check(lambda x: x.author.id == ADMIN_USER and x.guild.id == 748856777105211423)
    async def reload(self, inter: disnake.ApplicationCommandInteraction, cog: str):
        """
            Reload a Cog.

            Parameters
            ----------
            cog: :class:`str`
                The cog name.
        """
        self.bot.reload_extension(f"cogs.{cog.lower()}")
        await inter.response.send_message(f"> {cog.title()}\n```diff\n+Successfuly Reloaded\n```", ephemeral=True)

    @reload.autocomplete("cog")
    async def cog_autocomplete(self, inter: disnake.ApplicationCommandInteraction, cog: str):
        return [c for c in self.bot.cogs.keys() if cog.lower() in c.lower()]

    @commands.slash_command(name="setup")
    @commands.default_member_permissions(manage_guild=True)
    async def _setup(self, inter: disnake.ApplicationCommandInteraction, ville: str, create_command_channel: str = commands.Param("No", choices=[Localized("No", key="BOOL_NO"), Localized("Yes", key="BOOL_YES")])):
        """
            Configurez tous les paramètres du bot ! (A n'éxécuter qu'une fois à l'arrivée du bot)

            Parameters
            ----------
            ville: :class:`str`
                La ville par défaut de ce serveur Discord.
            create_command_channel: :class:`bool`
                Voulez-vous créer un salon dédié aux commandes du bot ?
        """
        if inter.guild.me.guild_permissions.value < int(PERMS_EVABOT):
            embed = disnake.Embed(title="Permissions manquantes",
                                  color=EVA_COLOR, timestamp=functions.getTimeStamp())
            embed.description = f"Certaines permissions sont manquantes et empêchent le bon fonctionnement de {inter.guild.me.mention}.\nCliquez sur le bouton ci-dessous pour ajouter de nouveau {inter.guild.me.mention} au serveur avec les nouvelles permissions.\n\nRetapez la commande `/setup` pour définir les paramètres du bot automatiquement."
            button = disnake.ui.Button(style=disnake.ButtonStyle.url, label="Ajouter",
                                       url=f"https://discord.com/api/oauth2/authorize?client_id=1007056236019204136&permissions={PERMS_EVABOT}&scope=bot%20applications.commands")
            await inter.response.send_message(embed=embed, components=button, ephemeral=True)
            return

        await inter.response.defer(with_message=True, ephemeral=True)
        embeds = []
        city_exists = True
        cities = functions.getCities(self.bot)
        city = functions.getCityfromDict(cities, city_name=ville)
        location = await functions.getLocation(city["id"])
        location = location["location"]
        current_season_number = functions.getCurrentSeasonNumber(self.bot)

        if not "COMMUNITY" in inter.guild.features:
            await inter.edit_original_response("**Activation de la communauté de serveur...**")
            embed = disnake.Embed(title="Activer la communauté",
                                  color=EVA_COLOR, timestamp=functions.getTimeStamp())
            rules_channel = await inter.guild.create_text_channel("règles", reason="Activation de la communauté")
            public_updates_channel = await inter.guild.create_text_channel("moderator-only", reason="Activation de la communauté", overwrites={
                inter.guild.default_role: disnake.PermissionOverwrite(
                    view_channel=False),
                inter.guild.me: disnake.PermissionOverwrite(
                    view_channel=True)
            })
            await inter.guild.edit(community=True, verification_level=disnake.VerificationLevel.low, explicit_content_filter=disnake.ContentFilter.all_members, rules_channel=rules_channel, public_updates_channel=public_updates_channel, reason=f"Utile au fonctionnement de {inter.guild.me.mention}")
            embed.description = f"Pour assurer le bon fonctionnement du bot, la communauté a été activé sur ce serveur, voici les fonctionnalités qui ont été ajoutées/modifiées:\n```diff\n+ Communauté: Activé\n\n+ Niveau de vérification: Faible\n\n+ Filtre de contenus médias explicites: Analyser les contenus médias de tous les membres.\n\n+ Création d'un salon des règles du serveur\n\n+ Création d'un salon de mises à jour de la communauté\n```"
            embeds.append(embed)

        async with self.bot.pool.acquire() as con:
            guild_config = await con.fetch("""
            SELECT logs_channel_id, resa_channel_id, best_players_ranking_channel_id
            FROM global_config
            WHERE global_config.guild_id = $1
            """, inter.guild.id)

        try:
            logs_channel = await self.bot.fetch_channel(guild_config[0]["logs_channel_id"])
        except:
            logs_channel_id = None
        else:
            logs_channel_id = logs_channel.id

        try:
            resa_channel: disnake.ForumChannel = await self.bot.fetch_channel(guild_config[0]["resa_channel_id"])
        except:
            resa_channel_id = None
        else:
            resa_channel_id = resa_channel.id

        try:
            best_players_ranking_channel = await self.bot.fetch_channel(guild_config[0]["best_players_ranking_channel_id"])
        except:
            best_players_ranking_channel_id = None
        else:
            best_players_ranking_channel_id = best_players_ranking_channel.id

        embed = disnake.Embed(title=":white_check_mark: Paramétrage terminé :white_check_mark:",
                              color=EVA_COLOR, timestamp=functions.getTimeStamp())
        embed.description = f"Tous les paramètres ont été correctement mis en place. Voici un récapitulatif de ce qui a été ajouté:\n```diff\n"

        if not logs_channel_id:
            await inter.edit_original_response("**Création du salon des logs...**")
            logs_channel = await inter.guild.create_text_channel("evabot_logs", reason=f"Création des salons utiles à {inter.guild.me.display_name}", overwrites={
                inter.guild.default_role: disnake.PermissionOverwrite(
                    view_channel=False),
                inter.guild.me: disnake.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    embed_links=True)
            })
            logs_channel_id = logs_channel.id

            embed.description += f"+ Création d'un salon regroupant les logs de {inter.guild.me.display_name}\n\n"

        calendar = await functions.getCalendar(self.bot, datetime.datetime.now(), city_name=ville)
        calendar = calendar["calendar"]

        if not calendar["sessionList"]["list"]:
            embed.description += f"- La salle de {ville} n'a pas encore ouverte ses portes au public, vous ne pouvez donc pas choisir cette ville pour configurer le forum des réservations pour le moment. Merci pour votre compréhension.\n\n"
            city_exists = False

        if city_exists:
            if not resa_channel_id:
                await inter.edit_original_response("**Création du forum des réservations...**")
                date = await functions.setDateTags(calendar)
                resa_channel = await inter.guild.create_forum_channel("evabot_resa", topic=f"Salon des réservations à {ville} uniquement. Choisissez le jour où vous voulez réserver une session en cliquant sur l'un des salons ci-dessous, puis choisissez votre horaire en cliquant sur le bouton \"Choisir un horaire\"", reason=f"Création des salons utiles à {inter.guild.me.display_name}", overwrites={
                    inter.guild.default_role: disnake.PermissionOverwrite(
                        create_forum_threads=False,
                        view_channel=True),
                    inter.guild.me: disnake.PermissionOverwrite(
                        view_channel=True,
                        create_forum_threads=True,
                        send_messages_in_threads=True,
                        send_messages=True,
                        manage_threads=True,
                        manage_messages=True,
                        read_message_history=True
                    )
                },
                    available_tags=[disnake.ForumTag(
                        name=day) for weekday, day in DAYS.items() if weekday != date],
                    default_sort_order=disnake.ThreadSortOrder.creation_date
                )
                resa_channel_id = resa_channel.id
                embed.description += "+ Création d'un salon pour les réservations\n\n"
            else:
                await inter.edit_original_response("**Vérifications/Modifications des paramètres du forum des réservations...**")
                date = await functions.setDateTags(calendar)
                resa_channel = await resa_channel.edit(available_tags=[disnake.ForumTag(name=day) for weekday, day in DAYS.items() if weekday != date], topic=f"Salon des réservations à {ville} uniquement. Choisissez le jour où vous voulez réserver une session en cliquant sur l'un des salons ci-dessous, puis choisissez votre horaire en cliquant sur le bouton \"Choisir un horaire\"", default_layout=disnake.utils.MISSING)

                for thread in resa_channel.threads:
                    await thread.delete(reason="Setup")

                async for archived_thread in resa_channel.archived_threads():
                    await archived_thread.delete(reason="Setup")

            days_with_dates = await functions.getEachDayInTheWeek()
            days_with_dates = sorted(
                days_with_dates.items(), key=lambda x: x[1], reverse=True)
            peak_hours_emoji = [
                emoji for emoji in inter.guild.emojis if emoji.name == "peak_hours"]
            off_peak_hours_emoji = [
                emoji for emoji in inter.guild.emojis if emoji.name == "off_peak_hours"]

            if not peak_hours_emoji:
                with open("./assets/Images/peak_hours.png", "rb") as image:
                    try:
                        peak_hours_emoji = await inter.guild.create_custom_emoji(name="peak_hours", image=bytearray(image.read()))
                    except disnake.errors.Forbidden:
                        peak_hours_emoji = ":purple_square:"
                        off_peak_hours_emoji = ":blue_square:"
            else:
                peak_hours_emoji = peak_hours_emoji[0]
            if not off_peak_hours_emoji:
                with open("./assets/Images/off_peak_hours.png", "rb") as image:
                    try:
                        off_peak_hours_emoji = await inter.guild.create_custom_emoji(name="off_peak_hours", image=bytearray(image.read()))
                    except disnake.errors.Forbidden:
                        peak_hours_emoji = ":purple_square:"
                        off_peak_hours_emoji = ":blue_square:"
            else:
                off_peak_hours_emoji = off_peak_hours_emoji[0]

            for t in days_with_dates:
                k, v = t[0], t[1]
                day_tag = DAYS[v.weekday()]
                await inter.edit_original_response(f"**Création du salon des réservations de {day_tag}...**")
                tag = [
                    tag for tag in resa_channel.available_tags if day_tag == tag.name]
                if tag:
                    tag = tag[0]
                    calendar = await functions.getCalendar(self.bot, v, city_name=ville)
                    calendar = calendar["calendar"]
                    forum_embed = disnake.Embed(
                        title=f"Réservations du {v.strftime('%A %d %B %Y')}", color=disnake.Color.red())
                    forum_embed.description = f"{peak_hours_emoji} Heures pleines\n{off_peak_hours_emoji} Heures creuses"
                    forum_embed.set_image(file=disnake.File(
                        "assets/Images/reservation.gif"))

                    buttons = []
                    buttons.append(Button(style=disnake.ButtonStyle.url, label="Réserver sur EVA.GG",
                                   url=f"https://www.eva.gg/fr/calendrier?locationId={calendar['location']['id']}&gameId=1&currentDate={v.strftime('%Y-%m-%d')}"))
                    buttons.append(Button(
                        style=disnake.ButtonStyle.danger, label="Associer compte EVA", custom_id="link_button", emoji="🪢"))

                    new_thread, _ = await resa_channel.create_thread(name=f"{v.strftime('%A %d %B %Y')}", applied_tags=[tag], embed=forum_embed, components=buttons)

                    for day in calendar["sessionList"]["list"]:
                        slot_id = day["slot"]["id"]
                        for terrain in day["availabilities"]:
                            if terrain["taken"] == 0:
                                continue
                            terrain_id = terrain["terrainId"]
                            terrain_name = [
                                i["name"] for i in location["details"]["terrains"] if i["id"] == terrain_id]
                            date = datetime.datetime.fromisoformat(
                                day["slot"]["datetime"])
                            session = await functions.getSession(slot_id, terrain_id)
                            session = session["getSession"]
                            players_list = []

                            for booking_list in session["bookingList"]:
                                player_count = booking_list["playerCount"]
                                for i in range(player_count):
                                    if i < len(booking_list["playerList"]) and booking_list["playerList"][i]["username"]:
                                        players_list.append(
                                            booking_list["playerList"][i])
                                    else:
                                        players_list.append(None)

                            members_list = [(await functions.getStats(player["username"], seasonId=current_season_number), await functions.getMember(self.bot, player["username"])) if player and player["username"] else (None, None) for player in players_list]

                            resa_embed = disnake.Embed(
                                title=f"Réservation à {day['slot']['startTime']}", color=PEAK_HOURS_COLOR if day["isPeakHour"] else OFF_PEAK_HOURS_COLOR)
                            resa_embed.description = f"__**Liste des joueurs**__:\n" + '\n'.join([f"[{member[0]['player']['displayName']}](https://www.eva.gg/profile/public/{member[0]['player']['username']}) | {member[1].mention}" if member[1] else (f"[{member[0]['player']['displayName']}](https://www.eva.gg/profile/public/{member[0]['player']['username']})" if member[0] else "Anonyme") for member in members_list])
                            resa_embed.add_field(
                                name="Ville", value=city["name"], inline=False)
                            resa_embed.add_field(
                                name="Terrain", value=terrain_name[0], inline=False)
                            resa_embed.add_field(
                                name="Horaire choisi", value=f"{format_dt(date)} | {format_dt(date, style='R')}", inline=False)
                            resa_embed.add_field(
                                name="Nombre de joueurs", value=f"{terrain['taken']}/{terrain['total']}", inline=False)

                            buttons = [
                                Button(style=disnake.ButtonStyle.url, label="Réserver (EVA.GG)",
                                       url=f"https://www.eva.gg/fr/calendrier?locationId={city['id']}&gameId=1&currentDate={day['slot']['date']}"),
                                Button(
                                    style=disnake.ButtonStyle.secondary, label="Rafraîchir", emoji="🔃", custom_id="refresh_reservation")
                            ]

                            await new_thread.send(embed=resa_embed, components=buttons)

            embed.description += "+ Ajout des espaces de réservations par jour dans le salon pour les réservations\n\n"

        if not best_players_ranking_channel_id:
            await inter.edit_original_response("**Création du salon du classement des joueurs...**")
            best_players_ranking_channel = await inter.guild.create_text_channel("evabot_ranking", reason=f"Création des salons utiles à {inter.guild.me.display_name}", overwrites={
                inter.guild.default_role: disnake.PermissionOverwrite(
                    view_channel=True,
                    send_messages=False),
                inter.guild.me: disnake.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    manage_messages=True,
                    read_message_history=True,
                    embed_links=True
                )})
            best_players_ranking_channel_id = best_players_ranking_channel.id
            embed.description += "+ Création d'un salon où sera placé automatiquement un classement des meilleurs joueurs du serveur\n\n"

        if create_command_channel == "Yes":
            await inter.edit_original_response("**Création d'un salon des commandes...**")
            await inter.guild.create_text_channel("evabot_commandes", reason=f"Création des salons utiles à {inter.guild.me.display_name}")
            embed.description += f"+ Création du salon où TOUTES les commandes relatives à {inter.guild.me.display_name} devront être tapées."

        async with self.bot.pool.acquire() as con:
            await con.execute("""
            INSERT INTO global_config
            VALUES($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (guild_id)
            DO UPDATE
            SET logs_channel_id = $4, resa_channel_id = $5, best_players_ranking_channel_id = $6, city_id = $7
            WHERE global_config.guild_id = $1
            """, inter.guild.id, inter.guild.name, inter.guild.owner_id, logs_channel_id, resa_channel_id, best_players_ranking_channel_id, calendar["location"]["id"] if city_exists else None)

        if embed.description.endswith("```diff\n"):
            embed.description = "Aucun paramètre n'a été modifié, tout est déjà correctement configuré ! :partying_face:"
        else:
            embed.description += "```"

        embed.description += f"\n\n:warning: Attention si jamais vous supprimez l'un des 3 salons suivants: **evabot_resa**, **evabot_logs** et **evabot_ranking** ; Vous devrez en définir de nouveaux via la commande `/config` suivis du type de salon que vous voulez définir.\n\n\n__**Pour refaire une configuration au propre:**__\n\n:one: - Supprimez tous les salons en lien avec {inter.guild.me.mention}\n:two: - Ajouter de nouveau {inter.guild.me.mention} au serveur via le bouton **Ajouter au serveur** quand vous cliquez sur son profil\n:three: - Retapez la commande `/setup`"
        embeds.append(embed)

        await inter.edit_original_response(content=None, embeds=embeds)

        await self.bot.get_cog("Tasks").set_variables()

    @_setup.autocomplete("ville")
    async def ville_autocomplete(self, inter: disnake.ApplicationCommandInteraction, ville: str):
        return [c for c in self.bot.eva_cities["cities"] if ville.lower() in c.lower()]

    @commands.slash_command(name="config")
    @commands.default_member_permissions(manage_guild=True)
    async def config(self, inter: disnake.ApplicationCommandInteraction):
        """
            Configurez les paramètres du bot ! {{CONFIG}}
        """

    @config.sub_command(name="logs")
    async def logs(self, inter: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel):
        """
            Configurez le salon où sera accueilli tous les logs ! {{CONFIG_LOGS}}

            Parameters
            ----------
            channel: :class:`disnake.TextChannel`
                Le salon où seront envoyés les logs d'Eva Bot. {{CONFIG_LOGS_CHANNEL}}
        """
        async with self.bot.pool.acquire() as con:
            old_logs_channel_id = await con.fetch("""
            SELECT logs_channel_id
            FROM global_config
            WHERE global_config.guild_id = $1
            """, inter.guild.id)
            old_logs_channel_id = old_logs_channel_id[0]["logs_channel_id"]

            await con.execute("""
            UPDATE global_config
            SET logs_channel_id = $2
            WHERE global_config.guild_id = $1
            """, inter.guild.id, channel.id)

        if not old_logs_channel_id:
            old_logs_channel_text = "Aucun salon n'a été défini auparavant !"
        else:
            old_logs_channel = inter.guild.get_channel(old_logs_channel_id)
            if old_logs_channel:
                old_logs_channel_text = old_logs_channel.mention
            else:
                old_logs_channel_text = "Aucun salon"

        embed = disnake.Embed(title="Modification du salon des Logs",
                              color=EVA_COLOR, timestamp=functions.getTimeStamp())
        embed.set_footer(text=inter.guild.name,
                         icon_url=inter.guild.icon.url if inter.guild.icon else None)
        embed.add_field(name="Ancien Salon",
                        value=old_logs_channel_text, inline=False)
        embed.add_field(name="Nouveau Salon",
                        value=channel.mention, inline=False)

        await inter.response.send_message(embed=embed, ephemeral=True)

    @config.sub_command(name="resa")
    async def resa(self, inter: disnake.ApplicationCommandInteraction, channel: disnake.ForumChannel):
        """
            Configurez le salon où seront créés tous les fils de réservations ! {{CONFIG_RESA}}

            Parameters
            ----------
            channel: :class:`disnake.ForumChannel`
                Le salon qui regroupera tous les fils de réservations. {{CONFIG_RESA_CHANNEL}}
        """
        async with self.bot.pool.acquire() as con:
            old_resa_channel_id = await con.fetch("""
            SELECT resa_channel_id
            FROM global_config
            WHERE global_config.guild_id = $1
            """, inter.guild.id)

            old_resa_channel_id = old_resa_channel_id[0]["resa_channel_id"]

            await con.execute("""
            UPDATE global_config
            SET resa_channel_id = $2
            WHERE global_config.guild_id = $1
            """, inter.guild.id, channel.id)

        if not old_resa_channel_id:
            old_resa_channel_text = "Aucun salon n'a été défini auparavant !"
        else:
            old_resa_channel = inter.guild.get_channel(old_resa_channel_id)
            if old_resa_channel:
                old_resa_channel_text = old_resa_channel.mention
            else:
                old_resa_channel_text = "Aucun salon"

        embed = disnake.Embed(title="Modification du salon des réservations.",
                              color=EVA_COLOR, timestamp=functions.getTimeStamp())
        embed.set_footer(text=inter.guild.name,
                         icon_url=inter.guild.icon.url if inter.guild.icon else None)
        embed.add_field(name="Ancien Salon",
                        value=old_resa_channel_text, inline=False)
        embed.add_field(name="Nouveau Salon",
                        value=channel.mention, inline=False)

        await inter.response.send_message(embed=embed, ephemeral=True)

    @config.sub_command(name="ranking")
    async def ranking(self, inter: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel):
        """
            Configurez le salon où sera envoyé le classement des meilleurs joueurs du serveur !

            Parameters
            ----------
            channel: :class:`disnake.ForumChannel`
                Le salon où sera envoyé le classement.
        """
        async with self.bot.pool.acquire() as con:
            old_best_players_ranking_channel_id = await con.fetch("""
            SELECT best_players_ranking_channel_id
            FROM global_config
            WHERE global_config.guild_id = $1
            """, inter.guild.id)

            old_best_players_ranking_channel_id = old_best_players_ranking_channel_id[
                0]["best_players_ranking_channel_id"]

            await con.execute("""
            UPDATE global_config
            SET best_players_ranking_channel_id = $2
            WHERE global_config.guild_id = $1
            """, inter.guild.id, channel.id)

        if not old_best_players_ranking_channel_id:
            old_resa_channel_text = "Aucun salon n'a été défini auparavant !"
        else:
            old_resa_channel = inter.guild.get_channel(
                old_best_players_ranking_channel_id)
            if old_resa_channel:
                old_resa_channel_text = old_resa_channel.mention
            else:
                old_resa_channel_text = "Aucun salon"

        embed = disnake.Embed(title="Modification du salon du classement des meilleurs joueurs.",
                              color=EVA_COLOR, timestamp=functions.getTimeStamp())
        embed.set_footer(text=inter.guild.name,
                         icon_url=inter.guild.icon.url if inter.guild.icon else None)
        embed.add_field(name="Ancien Salon",
                        value=old_resa_channel_text, inline=False)
        embed.add_field(name="Nouveau Salon",
                        value=channel.mention, inline=False)

        await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(name="fix", guild_ids=[748856777105211423])
    @commands.default_member_permissions(administrator=True)
    @commands.check(lambda x: x.author.id == ADMIN_USER)
    async def fix(self, inter: disnake.ApplicationCommandInteraction, resa_threads: bool = False, resa_topic: bool = False, message_select_id: str = None, horaire: str = None, setup_city_name: str = None, forum_resa_id: str = None, get_all_channels: str = None):
        await inter.response.defer(with_message=True, ephemeral=True)

        async with self.bot.pool.acquire() as con:
            guilds_config = await con.fetch("""
            SELECT resa_channel_id, city_id
            FROM global_config
            """)

        if message_select_id and horaire:
            channel: disnake.Thread = self.bot.get_channel(1061086976029237380)
            message = await channel.fetch_message(int(message_select_id))
            rows = ActionRow.rows_from_message(message)
            for _, component in ActionRow.walk_components(rows):
                logging.warning(component.type ==
                                disnake.ComponentType.string_select)
                if component.type == disnake.ComponentType.string_select:
                    component.add_option(label=horaire)
            await message.edit(components=rows)
            await inter.edit_original_message("OK")
            return

        elif setup_city_name and forum_resa_id:
            calendar = await functions.getCalendar(self.bot, datetime.datetime.now(), city_name=setup_city_name)
            calendar = calendar["calendar"]
            cities = functions.getCities(self.bot)
            city = functions.getCityfromDict(cities, city_name=setup_city_name)
            location = await functions.getLocation(city["id"])
            location = location["location"]
            current_season_number = functions.getCurrentSeasonNumber(self.bot)

            if calendar["sessionList"]["list"]:
                resa_channel = await self.bot.fetch_channel(forum_resa_id)
                date = await functions.setDateTags(calendar)
                resa_channel = await resa_channel.edit(available_tags=[disnake.ForumTag(name=day) for weekday, day in DAYS.items() if weekday != date], topic=f"Salon des réservations à {setup_city_name} uniquement. Choisissez le jour où vous voulez réserver une session en cliquant sur l'un des salons ci-dessous, puis choisissez votre horaire en cliquant sur le bouton \"Choisir un horaire\"", default_sort_order=disnake.ThreadSortOrder.creation_date, default_layout=disnake.utils.MISSING)

                for thread in resa_channel.threads:
                    await thread.delete(reason="Fix Setup")

                async for archived_thread in resa_channel.archived_threads():
                    await archived_thread.delete(reason="Fix Setup")

                days_with_dates = await functions.getEachDayInTheWeek()
                days_with_dates = sorted(
                    days_with_dates.items(), key=lambda x: x[1], reverse=True)
                peak_hours_emoji = [
                    emoji for emoji in inter.guild.emojis if emoji.name == "peak_hours"]
                off_peak_hours_emoji = [
                    emoji for emoji in inter.guild.emojis if emoji.name == "off_peak_hours"]

                if not peak_hours_emoji:
                    with open("./assets/Images/peak_hours.png", "rb") as image:
                        try:
                            peak_hours_emoji = await inter.guild.create_custom_emoji(name="peak_hours", image=bytearray(image.read()))
                        except disnake.errors.Forbidden:
                            peak_hours_emoji = ":purple_square:"
                            off_peak_hours_emoji = ":blue_square:"
                else:
                    peak_hours_emoji = peak_hours_emoji[0]
                if not off_peak_hours_emoji:
                    with open("./assets/Images/off_peak_hours.png", "rb") as image:
                        try:
                            off_peak_hours_emoji = await inter.guild.create_custom_emoji(name="off_peak_hours", image=bytearray(image.read()))
                        except disnake.errors.Forbidden:
                            peak_hours_emoji = ":purple_square:"
                            off_peak_hours_emoji = ":blue_square:"
                else:
                    off_peak_hours_emoji = off_peak_hours_emoji[0]

                for t in days_with_dates:
                    k, v = t[0], t[1]
                    day_tag = DAYS[v.weekday()]
                    await inter.edit_original_response(f"**Création du salon des réservations de {day_tag}...**")
                    tag = [
                        tag for tag in resa_channel.available_tags if day_tag == tag.name]
                    if tag:
                        tag = tag[0]
                        calendar = await functions.getCalendar(self.bot, v, city_name=setup_city_name)
                        calendar = calendar["calendar"]
                        forum_embed = disnake.Embed(
                            title=f"Réservations du {v.strftime('%A %d %B %Y')}", color=disnake.Color.red())
                        forum_embed.description = f"{peak_hours_emoji} Heures pleines\n{off_peak_hours_emoji} Heures creuses"
                        forum_embed.set_image(file=disnake.File(
                            "assets/Images/reservation.gif"))

                        buttons = []
                        buttons.append(Button(style=disnake.ButtonStyle.url, label="Réserver sur EVA.GG",
                                       url=f"https://www.eva.gg/fr/calendrier?locationId={calendar['location']['id']}&gameId=1&currentDate={v.strftime('%Y-%m-%d')}"))
                        buttons.append(Button(
                            style=disnake.ButtonStyle.danger, label="Associer compte EVA", custom_id="link_button", emoji="🪢"))

                        new_thread, _ = await resa_channel.create_thread(name=f"{v.strftime('%A %d %B %Y')}", applied_tags=[tag], embed=forum_embed, components=buttons)
                        for day in calendar["sessionList"]["list"]:
                            slot_id = day["slot"]["id"]
                            for terrain in day["availabilities"]:
                                if terrain["taken"] == 0:
                                    continue
                                terrain_id = terrain["terrainId"]
                                terrain_name = [
                                    i["name"] for i in location["details"]["terrains"] if i["id"] == terrain_id]
                                date = datetime.datetime.fromisoformat(
                                    day["slot"]["datetime"])
                                session = await functions.getSession(slot_id, terrain_id)
                                session = session["getSession"]
                                players_list = []

                                for booking_list in session["bookingList"]:
                                    player_count = booking_list["playerCount"]
                                    for i in range(player_count):
                                        if i < len(booking_list["playerList"]) and booking_list["playerList"][i]["username"]:
                                            players_list.append(
                                                booking_list["playerList"][i])
                                        else:
                                            players_list.append(None)

                                members_list = [[await functions.getStats(player["username"], seasonId=current_season_number), await functions.getMember(self.bot, player["username"])] if player and player["username"] else [None, None] for player in players_list]

                                resa_embed = disnake.Embed(
                                    title=f"Réservation à {day['slot']['startTime']}", color=PEAK_HOURS_COLOR if day["isPeakHour"] else OFF_PEAK_HOURS_COLOR)
                                resa_embed.description = f"__**Liste des joueurs**__:\n" + '\n'.join([f"[{member[0]['player']['displayName']}](https://www.eva.gg/profile/public/{member[0]['player']['username']}) | {member[1].mention}" if member[1] else (f"[{member[0]['player']['displayName']}](https://www.eva.gg/profile/public/{member[0]['player']['username']})" if member[0] else "Anonyme") for member in members_list])
                                resa_embed.add_field(
                                    name="Ville", value=city["name"], inline=False)
                                resa_embed.add_field(
                                    name="Terrain", value=terrain_name[0], inline=False)
                                resa_embed.add_field(
                                    name="Horaire choisi", value=f"{format_dt(date)} | {format_dt(date, style='R')}", inline=False)
                                resa_embed.add_field(
                                    name="Nombre de joueurs", value=f"{terrain['taken']}/{terrain['total']}", inline=False)

                                buttons = [
                                    Button(style=disnake.ButtonStyle.url, label="Réserver (EVA.GG)",
                                           url=f"https://www.eva.gg/fr/calendrier?locationId={city['id']}&gameId=1&currentDate={day['slot']['date']}"),
                                    Button(
                                        style=disnake.ButtonStyle.secondary, label="Rafraîchir", emoji="🔃", custom_id="refresh_reservation")
                                ]

                                await new_thread.send(embed=resa_embed, components=buttons)

                async with self.bot.pool.acquire() as con:
                    await con.execute("""
                    UPDATE global_config
                    SET city_id = $2
                    WHERE global_config.guild_id = $1
                    """, resa_channel.guild.id, calendar["location"]["id"])

                await inter.edit_original_response(f"**Le forum des réservations dans le serveur {resa_channel.guild.name} a bien été réparé.**")
            else:
                await inter.edit_original_message(f"La salle de **{setup_city_name}** __n'a pas encore ouverte ses portes au public__, vous ne pouvez donc pas choisir cette ville pour configurer le forum des réservations pour le moment.\nMerci pour votre compréhension.")
            return

        elif get_all_channels:
            guild = self.bot.get_guild(int(get_all_channels))
            await inter.edit_original_response("\n".join((f"{c.name} : {c.id}" for c in guild.channels)))
            return

        for guild_config in guilds_config:
            try:
                resa_channel: disnake.ForumChannel = await self.bot.fetch_channel(guild_config["resa_channel_id"])
            except:
                continue

            if resa_threads:
                is_present = False
                for tag in resa_channel.available_tags:
                    is_present = False
                    for thread in resa_channel.threads:
                        if tag.name.lower() in thread.name:
                            is_present = True
                            break
                    if not is_present:
                        day_tag = tag
                        break

                if not is_present:
                    days_with_dates = await functions.getEachDayInTheWeek()

                    for k, v in sorted(DAYS.items(), reverse=True):
                        if day_tag.name in v:
                            if not guild_config["city_id"]:
                                break
                            calendar = await functions.getCalendar(self.bot, days_with_dates[k], city_id=guild_config["city_id"])
                            calendar = calendar["calendar"]
                            forum_embed = disnake.Embed(
                                title=f"Réservations du {days_with_dates[k].strftime('%A %d %B %Y')}", color=disnake.Color.red())
                            forum_embed.set_image(file=disnake.File(
                                "assets/Images/reservation.gif"))
                            select_options = []

                            for day in calendar["sessionList"]["list"]:
                                select_options.append(SelectOption(label=f"{day['startTime']}", value=json.dumps({
                                    "loc": day["slot"]["locationId"],
                                    "date": day["slot"]["date"],
                                    "start": day["slot"]["startTime"],
                                    "end": day["slot"]["endTime"]
                                }), description=f"{day['startTime']} ➡️ {day['endTime']}"))

                            select = StringSelect(
                                placeholder="Choisir un horaire", options=select_options, custom_id="reservation")

                            await resa_channel.create_thread(name=f"{days_with_dates[k].strftime('%A %d %B %Y')}", applied_tags=[tag], embed=forum_embed, components=select)

            if resa_topic:
                if guild_config["city_id"]:
                    await resa_channel.edit(topic=f"Salon des réservations à {functions.getCityfromDict(functions.getCities(self.bot), city_id=guild_config['city_id'])['name']} uniquement. Choisissez le jour où vous voulez réserver une session en cliquant sur l'un des salons ci-dessous, puis choisissez votre horaire en cliquant sur le bouton \"Choisir un horaire\"", default_sort_order=disnake.ThreadSortOrder.creation_date, default_layout=disnake.utils.MISSING)

        await inter.edit_original_message("**Les forums des réservations ont bien été réparé.**")

    @commands.slash_command(name="test", guild_ids=[748856777105211423])
    @commands.default_member_permissions(administrator=True)
    @commands.check(lambda x: x.author.id == ADMIN_USER)
    async def test(self, inter: disnake.ApplicationCommandInteraction):
        print(inter.guild.get_role(1010978821966671985).permissions.value >
              inter.guild.me.guild_permissions.value)

    @fix.autocomplete("setup_city_name")
    async def ville_autocomplete(self, inter: disnake.ApplicationCommandInteraction, ville: str):
        return [c for c in self.bot.eva_cities["cities"] if ville.lower() in c.lower()]

    @commands.slash_command(name="send")
    @commands.check(lambda x: x.author.id == ADMIN_USER)
    async def _send(self, inter: disnake.ApplicationCommandInteraction, content: str):
        await inter.response.defer(with_message=False)
        await inter.channel.send(content.replace("\\n", "\n"))

    # Errors

    @reload.error
    async def reload_error(self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError):
        if isinstance(error, commandsErrors.CheckFailure):
            await inter.response.send_message("```diff\n-Vous ne pouvez pas utiliser cette commande !\n```", ephemeral=True)


def setup(bot: classes.EvaBot):
    bot.add_cog(Admin(bot))
