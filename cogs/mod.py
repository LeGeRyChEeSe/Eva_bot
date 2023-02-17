import disnake
from disnake.ext import commands
from disnake.ui import  Select, ActionRow, Button
from utils.constants import *
import utils.functions as functions

class Mod(commands.Cog):
    def __init__(self, bot: commands.InteractionBot) -> None:
        self.bot = bot

    @commands.slash_command(name="roles")
    @commands.default_member_permissions(manage_roles=True)
    async def roles(self, inter: disnake.ApplicationCommandInteraction):
        """
            Créer une liste de rôles que n'importe qui peut s'ajouter facilement. {{ROLE}}
        """

    @roles.sub_command(name="create")
    async def create(self, inter: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel, titre: str, description: str, unique_role: bool, set_username: bool, placeholder: str = None):
        """
            Créez un message dynamique d'affectation de rôles. {{ROLE_CREATE}}

            Parameters
            ----------
            channel: :class:`disnake.TextChannel`
                Le salon où sera envoyé le message. {{ROLE_CREATE_CHANNEL}}
            titre: :class:`str`
                Le titre de l'encadré du message. {{ROLE_CREATE_TITLE}}
            description :class:`str`
                La description de l'encadré du message. {{ROLE_CREATE_DESC}}
            unique_role: :class:`bool`
                Si l'utilisateur ne peut choisir qu'un seul rôle. {{ROLE_CREATE_UNIQUE}}
            set_username: :class:`bool`
                Si le rôle est ajouté à la fin du pseudo de l'utilisateur. {{ROLE_CREATE_SET_USERNAME}}
            placeholder: :class:`str`
                Le message pour guider l'utilisateur quant au choix des rôles. {{ROLE_CREATE_PLACEHOLDER}}
        """
        if not channel.permissions_for(inter.guild.me).send_messages:
            await inter.response.send_message(functions.getLocalization(self.bot, "ROLE_CREATE_NO_PERMS", inter.locale, channelMention=channel.mention), ephemeral=True)
            return

        if channel.guild != inter.guild:
            await inter.response.send_message(functions.getLocalization(self.bot, "ROLE_CREATE_NOT_IN_SERVER", inter.locale), ephemeral=True)
            return

        if unique_role:
            if set_username:
                custom_id = "unique_role_and_set_username"
            else:
                custom_id = "unique_role"
        else:
            custom_id = "multiple_roles"

        options = [disnake.SelectOption(label=functions.getLocalization(self.bot, "ROLE_CREATE_OPTION_LABEL", inter.guild_locale), value=0, description=functions.getLocalization(self.bot, "ROLE_CREATE_OPTION_DESCRIPTION", inter.guild_locale), emoji="🚮", default=True)]
        select = Select(custom_id=custom_id, placeholder=placeholder or functions.getLocalization(self.bot, "ROLE_CREATE_OPTION_PLACEHOLDER", inter.guild_locale), options=options)
        button = Button(style=disnake.ButtonStyle.secondary, emoji="❌", custom_id="remove_role")

        embed = disnake.Embed(title=titre, description=description, color=EVA_COLOR)
        embed.set_thumbnail(url=inter.guild.icon.url)
        embed.set_footer(text=inter.guild.name)

        target = await channel.send(embed=embed, components=[select, button])
        await inter.response.send_message(functions.getLocalization(self.bot, "ROLE_CREATE_RESPONSE", inter.locale, jumpUrl=target.jump_url, commandName=functions.getLocalization(self.bot, "ROLE_NAME", inter.locale), subCommandName1=functions.getLocalization(self.bot, "ROLE_ADD_NAME", inter.locale), subCommandName2=functions.getLocalization(self.bot, "ROLE_EDIT_NAME", inter.locale)), ephemeral=True)

    @roles.sub_command("edit")
    async def edit(self, inter: disnake.ApplicationCommandInteraction, channel:disnake.TextChannel, message_id : str, titre: str = None, description: str = None):
        """
            Éditer l'encadré du message d'affectation des rôles. {{ROLE_EDIT}}

            Parameters
            ----------
            message_id: :class:`str`
                ID du message. Activer le mode développeur pour accéder à l'ID du message. {{ROLE_EDIT_MESSAGE_ID}}
            titre: :class:`str`
                Le titre de l'encadré du message. {{ROLE_EDIT_TITLE}}
            description :class:`str`
                La description de l'encadré du message. {{ROLE_EDIT_DESC}}
        """
        await inter.response.defer(with_message=True, ephemeral=True)
        message_id = int(message_id)
        
        if not channel in inter.guild.channels:
            await inter.followup.send("Ce salon ne se situe pas dans ce serveur !")
            return

        message = await channel.fetch_message(message_id)

        if not message:
            await inter.followup.send("Ce message n'existe pas ou ne se situe pas dans ce serveur !")
            return

        if message.author != inter.guild.me:
            await inter.followup.send("Je ne peux pas modifier ce message !", ephemeral=True)
            return

        embed = message.embeds[0]
        if titre:
            embed.title = titre
        if description:
            embed.description = description
        
        await message.edit(embed=embed,)
        await inter.followup.send(f"Le message a bien été modifié :point_right: {message.jump_url}", ephemeral=True)

    @roles.sub_command("add")
    async def add(self, inter: disnake.ApplicationCommandInteraction, channel:disnake.TextChannel, message_id: str, role: disnake.Role, description: str = None, emoji: str = None):
        """
            Ajouter un rôle à un message d'affectation des rôles. 25 rôles max par message. {{ROLE_ADD}}

            Parameters
            ----------
            channel: :class:`disnake.TextChannel`
                Salon où se trouve le message. {{ROLE_ADD_CHANNEL}}
            message_id: :class:`str`
                ID du message. Activer le mode développeur pour accéder à l'ID du message. {{ROLE_ADD_MESSAGE_ID}}
            role: :class:`disnake.Role`
                Le rôle à ajouter au message. {{ROLE_ADD_ROLE}}
            description: :class:`str`
                Description du rôle. {{ROLE_ADD_DESC}}
            emoji: :class:`str`
                L'emoji associé au rôle. {{ROLE_ADD_EMOJI}}
        """
        await inter.response.defer(with_message=True, ephemeral=True)
        message_id = int(message_id)

        if not channel in inter.guild.channels:
            await inter.followup.send("Ce salon ne se situe pas dans ce serveur !")
            return

        message = await channel.fetch_message(message_id)

        if not message:
            await inter.followup.send("Ce message n'existe pas ou ne se situe pas dans ce serveur !")
            return

        if inter.author.guild_permissions < role.permissions:
            await inter.followup.send("Vous n'avez pas les permissions pour ajouter ce rôle !")
            return
        
        if message.author != inter.guild.me:
            await inter.followup.send("Je ne peux pas modifier ce message !")
            return

        if message.components:
            rows = ActionRow.rows_from_message(message)
            buttonRow = ActionRow()
            buttonRow.append_item(Button(style=disnake.ButtonStyle.secondary, emoji="❌", custom_id="remove_role"))
            
            for row, component in ActionRow.walk_components(rows):
                if component.type != disnake.ComponentType.select:
                    continue

                if component.options[0].value == "0":
                    component.options.remove(component.options[0])
                try:
                    component.append_option(disnake.SelectOption(label=role.name, value=role.id, description=description, emoji=emoji))
                except ValueError:
                    await inter.followup.send("Le nombre max a été atteint !")
                    return
                except:
                    raise
                else:
                    if component.custom_id == "multiple_roles":
                        component.max_values += len(component.options) - 1

            #rows.append(buttonRow)
            await message.edit(components=rows)

            await inter.followup.send(f"Le rôle {role.mention} a bien été ajouté au message d'affectation des rôles :point_right: {message.jump_url}")

    @roles.sub_command("delete")
    async def delete(self, inter: disnake.ApplicationCommandInteraction, channel:disnake.TextChannel, message_id: str, role: disnake.Role):
        """
            Supprimer un rôle d'un message d'affectation des rôles. {{ROLE_DELETE}}

            Parameters
            ----------
            channel: :class:`disnake.TextChannel`
                Le salon où se trouve le message. {{ROLE_DELETE_CHANNEL}}
            message_id: :class:`str`
                ID du message. Activer le mode développeur pour accéder à l'ID du message. {{ROLE_DELETE_MESSAGE_ID}}
            role: :class:`disnake.Role`
                Le rôle à supprimer du message. {{ROLE_DELETE_ROLE}}
        """
        await inter.response.defer(with_message=True, ephemeral=True)
        message_id = int(message_id)

        if not channel in inter.guild.channels:
            await inter.followup.send("Ce salon ne se situe pas dans ce serveur !")
            return

        message = await channel.fetch_message(message_id)

        if not message:
            await inter.followup.send("Ce message n'existe pas ou ne se situe pas dans ce serveur !")
            return

        if inter.author.guild_permissions < role.permissions:
            await inter.followup.send("Vous n'avez pas les permissions pour ajouter ce rôle !")
            return
        
        if message.author != inter.guild.me:
            await inter.followup.send("Je ne peux pas modifier ce message !")
            return

        if not message.components:
            await inter.followup.send("Ce message ne contient pas d'affectation de rôles.")
            return
        else:
            rows = ActionRow.rows_from_message(message)
            deleted = False

            for row, component in ActionRow.walk_components(rows):
                if not component.type == disnake.ComponentType.select:
                    continue

                for option in component.options:
                    if option.value == str(role.id):
                        component.options.remove(option)
                        if component.custom_id == "multiple_roles" and component.max_values > 1:
                            component.max_values -= 1
                        deleted = True
                if len(component.options) == 0:
                    component.append_option(disnake.SelectOption(label=functions.getLocalization(self.bot, "ROLE_CREATE_OPTION_LABEL", inter.guild_locale), value=0, description=functions.getLocalization(self.bot, "ROLE_CREATE_OPTION_DESCRIPTION", inter.guild_locale), emoji="🚮", default=True))
                    component.max_values = 1
            if deleted:
                await message.edit(components=rows)
                await inter.followup.send(f"Le rôle {role.mention} a bien été supprimé du message d'affectation des rôles :point_right: {message.jump_url}")
            else:
                await inter.followup.send(f"Le rôle {role.mention} n'est pas présent dans la liste d'affectation des rôles de ce message :point_right: {message.jump_url}\nPar conséquent je n'ai pas pu le supprimer !")

    @commands.slash_command(name="sondage")
    @commands.default_member_permissions(manage_messages=True)
    async def sondage(self, inter: disnake.ApplicationCommandInteraction, question: str):
        """
            Créer un sondage avec plusieurs réponses possibles.

            Parameters
            ----------
            question: :class:`str`
                La question du sondage
        """
        await inter.response.defer(with_message=False)
        
        embed = disnake.Embed(title=question, color=disnake.Color.from_rgb(*PERFECT_GREY))
        embed.set_author(name=f"Sondage de {inter.author.display_name}", icon_url=inter.author.display_avatar)

        buttons = []
        buttons.append(Button(style=disnake.ButtonStyle.secondary, label="Ajouter des réponses", custom_id=f"{inter.author.id}_sondage_button"))
        buttons.append(Button(style=disnake.ButtonStyle.danger, label="J'ai ajouté toutes les réponses que je voulais", custom_id=f"{inter.author.id}_sondage_clear_button"))

        await inter.delete_original_response()
        await inter.channel.send(embed=embed, components=buttons)

def setup(bot: commands.InteractionBot):
    bot.add_cog(Mod(bot))