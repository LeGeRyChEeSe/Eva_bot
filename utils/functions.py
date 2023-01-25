import os
import typing
import disnake
import asyncpg
from disnake.ext import commands
from typing import Dict, Tuple, Union
from gql import gql, Client
from gql.transport.exceptions import TransportQueryError
from gql.transport.aiohttp import AIOHTTPTransport
from PIL import Image, ImageDraw, ImageFont
import random
import datetime
from utils.constants import *
# Fonctions asynchrones

async def getPlayerInfos(bot: commands.InteractionBot, player: disnake.User or disnake.Member = None) -> asyncpg.Record:
  """
    Fonction qui récupère les informations d'un joueur contenues dans la base de données.
    
    Parameters
    ----------
    player: :class:`disnake.User` or :class:`disnake.Member`
      Indiquer un ``User`` ou ``Member`` Discord.
    
    Returns
    -------
    player_id: :class:`int`
      Id du joueur Eva.
    player_username: :class:`str`
      Nom complet du joueur Eva avec le discriminant.
    user_id: :class:`int`
      Id du membre du serveur.
  """
  if player:
    try:
      async with bot.pool.acquire() as con:
        user = await con.fetch("""
        SELECT player_id, player_username, user_id
        FROM players
        WHERE user_id = $1
        """, player.id)
    except:
      raise
    else:
      if user:
        return user[0]
  
async def setCities():
  eva_cities = await getCitiesGQL()
  eva_cities["cities"] = []
  for city in eva_cities["locations"]["nodes"]:
    if city['playgroundName']:
      eva_cities["cities"].append(f"{city['name']} (Alias: {city['playgroundName']})")
    else:
      eva_cities["cities"].append(city['name'])
  return eva_cities

def getCities(self) -> Dict:
  return self.bot.get_cog("Variables").eva_cities

async def setGuildsResaChannels(pool: asyncpg.Pool):
  async with pool.acquire() as con:
    resa_channels = await con.fetch('''
    SELECT guild_id, resa_channel_id
    FROM global_config
    ''')
  return resa_channels

# Fonctions synchrones

def perfectGrey() -> disnake.Color:
  return disnake.Color.from_rgb(*PERFECT_GREY)

def getResaChannel(resa_channels: typing.List, guild: disnake.Guild):
  for record in resa_channels:
    if guild.id == record["guild_id"]:
      return guild.get_channel(record["resa_channel_id"])

def getTimeStamp() -> datetime.datetime:
  """
      Fonction qui retourne le timestamp utilisable pour un :class:`disnake.Embed`
  """
  return datetime.datetime.now()

def getLocalization(bot: commands.InteractionBot, key: str, locale: disnake.Locale, **kwargs) -> str:
  """
      Récupère du texte en fonction de la langue de l'utilisateur.

      Paramètres
      ----------
      key: :class:`str`
          Le nom de la clé à récupérer.
      locale: :class:`disnake.Locale`
          `inter.locale` dans la plupart des cas.
      **kwargs: :class:`dict`
          Peut contenir les arguments suivants:
          levelProgressionPercentage: :class:`int`
          level: :class:`int`
          experience: :class:`int`
          experienceForNextLevel: :class:`int`
          gameTime: :class:`int`
          traveledDistance: :class:`int`
          displayName: :class:`str`
          playerMention: :class:`str`
          commandName: :class:`str`
          subCommandName1: :class:`str`
          subCommandName2: :class:`str`
          position: :class:`int`
          channelMention: :class:`str`
          roleMention: :class:`str`
          season: :class:`int`
          username: :class:`str`,
          clientMention: :class:`str`
          jumpUrl: :class:`str`

  """
  text_localized = bot.i18n.get(key).get(str(locale))

  for k, value in kwargs.items():
      k_formatted = "{" + k + "}"
      text_localized = text_localized.replace(k_formatted, str(value))
      
  return text_localized

def getRoomSize(cities: Dict, city_name: str, mode: int) -> int:
  cities = cities["locations"]["nodes"]

  for city in cities:
    if city_name in city["name"]:
      for game in city["details"]["games"]:
        if game["id"] == mode:
            return game["maxPlayer"]

def getCityfromDict(cities: Dict, city_name: str = None, city_id: int = None) -> Dict:
  cities = cities["locations"]["nodes"]

  if city_name and not city_id:
    city_name = city_name.split(" (")[0]
  elif city_name and city_id:
    raise Exception

  for city in cities:
    if (city_name and city_name in city["name"]) or city_id == city["id"]:
      return city

# Fonctions manipulant des images

def getHeight(original_height: float) -> int:
  """
    Retourne une Hauteur par rapport à un ratio constant ``RATIO_RESIZE``.

    Paramètres
    ----------
    original_height: :class:`float`
      Hauteur initiale.
  """
  return int(original_height * RATIO_RESIZE)

def setImage(game: Dict, mode: str, map: str):
  """
    Construit l'image d'une partie en fonction des paramètres entrés.

    Paramètres
    ----------
    game: :class:`Dict`
      Dictionnaire contenant toutes les données de la partie.
    mode: :class:`str`
      Indique le mode de jeu de la partie.
    map: :class:`str`
      Indique la carte de la partie.
  """
  players = game['players']

  if mode == ZB:
    mode_path = "assets/Images/after_h_zombies_logo.png"
    map_path = "assets/Images/after_h_zombies_band.png"
  else:
    mode_path = "assets/Images/afterh.png"
    map_path = f"assets/Images/{map.lower()}.png"

  columns_images = getColumnsImages()

  mode_base = Image.open(mode_path)
  mode_base = mode_base.resize((280, getHeight(128)), Image.ANTIALIAS)
  mode_image = Image.new('RGBA', mode_base.size, "BLACK")
  mode_image.paste(mode_base, (0,0), mode_base)
  scoreboard_title_image = Image.new('RGB', (838, getHeight(32)), "#0b0d13")
  if mode == ZB:
    score_general_image = Image.new('RGB', (838, getHeight(112)), "#161a26")
  elif mode in [DOM, SKM, TDM]:
    score_general_image = Image.new('RGB', (838, getHeight(112)), "#161a26")

  map_image = Image.open(map_path)
  map_image = map_image.resize((558, getHeight(128)), Image.ANTIALIAS)

  text_font = ImageFont.truetype("assets/Fonts/gotham_condensed_bold.otf", 100)
  column_font = ImageFont.truetype("assets/Fonts/AlteHaasGroteskBold.ttf", 22)
  element_font = ImageFont.truetype("assets/Fonts/AlteHaasGroteskRegular.ttf", 30)

  text = "Détails de partie".upper()
  
  base = Image.open("assets/Images/background.png")
  
  tmp_file = ""
  for _ in range(0,25):
    tmp_file = f"{tmp_file}{random.randint(0,9)}"
  tmp_file = f"{tmp_file}.png"

  base.paste(mode_image, (45,150), mode_image)
  base.paste(map_image, (325, 150))
  if mode == FFA:
    players.sort(key=lambda x: x['data']['rank'])
    base.paste(scoreboard_title_image, (45, 320))
    y = 357
    for p in players:
      x = 45
      i = 0
      p = p["data"]

      rank: str = str(p["rank"])
      name: str = p["niceName"]
      kda: str = f"{p['kills']}/{p['deaths']}/{p['assists']}"
      score: str = str(p["score"])
      data = [rank, name, kda, score]

      for element in columns_images:
        tmp_element = element.copy()
        column_editable = ImageDraw.Draw(tmp_element)
        w, h = column_editable.textsize(data[i], font=element_font)
        column_editable.text(((element.width-w)/2, (element.height-h)/2), data[i], "#c3beb5", font=element_font)
        base.paste(tmp_element, (x, y))
        x = x + element.width
        i += 1
      y += getHeight(55)
  if mode == ZB:
    y = 487

    base.paste(score_general_image, (45, 300))
    base.paste(scoreboard_title_image, (45, 450))
    players.sort(key=lambda x: x['data']['rank'])
    for p in players:
      x = 45
      i = 0
      p = p["data"]

      rank: str = str(p["rank"])
      name: str = p["niceName"]
      kda: str = f"{p['kills']}/{p['deaths']}/{p['assists']}"
      score: str = str(p["score"])
      data = [rank, name, kda, score]

      for element in columns_images:
        tmp_element = element.copy()
        column_editable = ImageDraw.Draw(tmp_element)
        w, h = column_editable.textsize(data[i], font=element_font)
        column_editable.text(((element.width-w)/2, (element.height-h)/2), data[i], "#c3beb5", font=element_font)
        base.paste(tmp_element, (x, y))
        x = x + element.width
        i += 1
      y += getHeight(55)
  elif mode in [DOM, SKM, TDM]:
    y = 487

    base.paste(score_general_image, (45, 300))
    base.paste(scoreboard_title_image, (45, 450)) # +20px
    first_team = game['data']['teamOne']['name'].upper()
    second_team = game['data']['teamTwo']['name'].upper()
    alliance = [p for p in players if p["data"]["team"].upper() == first_team]
    rebels = [p for p in players if p["data"]["team"].upper() == second_team]
    rebels.sort(key=lambda x: x['data']['rank'])
    alliance.sort(key=lambda x: x['data']['rank'])

    for p in alliance:
      x = 45
      i = 0
      p = p["data"]

      rank: str = str(p["rank"])
      name: str = p["niceName"]
      kda: str = f"{p['kills']}/{p['deaths']}/{p['assists']}"
      score: str = str(p["score"])
      data = [rank, name, kda, score]

      for element in columns_images:
        tmp_element = element.copy()
        column_editable = ImageDraw.Draw(tmp_element)
        w, h = column_editable.textsize(data[i], font=element_font)
        column_editable.text(((element.width-w)/2, (element.height-h)/2), data[i], "#c3beb5", font=element_font)
        base.paste(tmp_element, (x, y))
        x = x + element.width
        i += 1
      y += getHeight(55)
    
    y += 20
    rebels_y = y
    y += getHeight(32)
    base.paste(scoreboard_title_image, (45, rebels_y))

    for p in rebels:
      x = 45
      i = 0
      p = p["data"]


      rank: str = str(p["rank"])
      name: str = p["niceName"]
      kda: str = f"{p['kills']}/{p['deaths']}/{p['assists']}"
      score: str = str(p["score"])
      data = [rank, name, kda, score]

      for element in columns_images:
        tmp_element = element.copy()
        column_editable = ImageDraw.Draw(tmp_element)
        w, h = column_editable.textsize(data[i], font=element_font)
        column_editable.text(((element.width-w)/2, (element.height-h)/2), data[i], "#c3beb5", font=element_font)
        base.paste(tmp_element, (x, y))
        x = x + element.width
        i += 1
      y += getHeight(55)

  base_editable = ImageDraw.Draw(base)
  base_editable.text((45, 25), text, (255, 255, 255), font=text_font)
  
  if mode == FFA:
    base_editable.text((92, 323), "RANG", "#e0c89f", font=column_font)
    base_editable.text((290,323), "PSEUDO", "#e0c89f", font=column_font)
    base_editable.text((542,323), "K/D/A", "#e0c89f", font=column_font)
    base_editable.text((742,323), "SCORE", "#e0c89f", font=column_font)
  elif mode == ZB:
    base_editable.text((92, 453), "RANG", "#e0c89f", font=column_font)
    base_editable.text((290,453), "PSEUDO", "#e0c89f", font=column_font)
    base_editable.text((542,453), "K/D/A", "#e0c89f", font=column_font)
    base_editable.text((742,453), "SCORE", "#e0c89f", font=column_font)
  elif mode in [DOM, SKM, TDM]:
    # Alliance
    base_editable.text((92, 453), "RANG", "#e0c89f", font=column_font)
    base_editable.text((290,453), "PSEUDO", "#e0c89f", font=column_font)
    base_editable.text((542,453), "K/D/A", "#e0c89f", font=column_font)
    base_editable.text((742,453), "SCORE", "#e0c89f", font=column_font)

    # Rebels
    base_editable.text((92, rebels_y + 3), "RANG", "#e0c89f", font=column_font)
    base_editable.text((290,rebels_y + 3), "PSEUDO", "#e0c89f", font=column_font)
    base_editable.text((542,rebels_y + 3), "K/D/A", "#e0c89f", font=column_font)
    base_editable.text((742,rebels_y + 3), "SCORE", "#e0c89f", font=column_font)

  base.save(f"assets/Images/tmp/{tmp_file}")

  return base, tmp_file

def getScoreboard(game: Dict) -> str:
  """
    Retourne le chemin de l'image créée en fonction des données indiquées en paramètres.

    Paramètres
    ----------
    game: :class:`Dict`
      Dictionnaire contenant toutes les données de la partie.
  """
  mode = game['data']['mode']
  map = game['data']['map']
  first_team = game['data']['teamOne']['name'].upper()
  second_team = game['data']['teamTwo']['name'].upper()
  alliance_score = game['data']['teamOne']['score']
  rebels_score = game['data']['teamTwo']['score']

  original_date = datetime.datetime.fromisoformat(game['createdAt']+'+00:00') + datetime.timedelta(hours=2)
  date_format = original_date.strftime("%d/%m/%Y")
  clock_format = original_date.strftime("%H:%M")
  
  scoreboard_base, image_path = setImage(game, mode, map)

  mode_font = ImageFont.truetype("assets/Fonts/gotham_condensed_bold.otf", 75)
  map_font = ImageFont.truetype("assets/Fonts/gotham_condensed_bold.otf", 50)
  date_font = ImageFont.truetype("assets/Fonts/gotham_condensed_medium.otf", 50)
  clock_font = ImageFont.truetype("assets/Fonts/gotham_condensed_medium.otf", 65)
  
  score_font = ImageFont.truetype("assets/Fonts/gotham_condensed_bold.otf", 75)
  score_text_font = ImageFont.truetype("assets/Fonts/gotham_condensed_bold.otf", 50)
  team_font = ImageFont.truetype("assets/Fonts/gotham_condensed_bold.otf", 35)

  # Mode, Map and Time Band on Top
  scoreboard_editable = ImageDraw.Draw(scoreboard_base)
  scoreboard_editable.text((330, 155), map.replace('_', ' '), (255, 255, 255), font=map_font)
  scoreboard_editable.text((330, 200), mode.replace('_', ' '), (255, 255, 255), font=mode_font)
  scoreboard_editable.text((700, 155), date_format, (255, 255, 255), font=date_font)
  scoreboard_editable.text((745, 200), clock_format, (255, 255, 255), font=clock_font)
  
  if mode == ZB:
    scoreboard_editable.text((140, 320), "Fin de la mission".upper(), "#c3beb5", font=score_font)
    scoreboard_editable.text((640, 305), "Score".upper(), "#c3beb5", font=score_text_font)
    scoreboard_editable.text((625, 345), str(alliance_score), "#c3beb5", font=score_font)
  elif mode in [DOM, SKM, TDM]:
    alliance_image = Image.open("assets/Images/alliance_logo.png")
    alliance_image = alliance_image.resize((getHeight(65), getHeight(65)))
    rebels_image = Image.open("assets/Images/rebels_logo.png")
    rebels_image = rebels_image.resize((getHeight(65), getHeight(65)))
    scoreboard_base.paste(alliance_image, (50, 310))
    scoreboard_base.paste(rebels_image, (878 - rebels_image.width, 310))
    scoreboard_editable.text((50, 390), first_team, "#c3beb5", font=team_font)
    _, _, w, h = scoreboard_editable.textbbox((0, 0), second_team, font=team_font)
    scoreboard_editable.text((878 - w, 390), second_team, "#c3beb5", font=team_font)
    #scoreboard_editable.text((771, 390), second_team, "#c3beb5", font=team_font)
    scoreboard_editable.text((220, 320), str(alliance_score), "#c3beb5", font=score_font)
    scoreboard_editable.text((640, 320), str(rebels_score), "#c3beb5", font=score_font)
    scoreboard_editable.text((450, 330), "VS", "#c3beb5", font=score_text_font)

  scoreboard_base.save(f"assets/Images/tmp/{image_path}")

  return image_path

def getColumnsImages():
  """
    Retourne les images construites pour chaque colonne du tableau des scores.
  """
  pos_image = Image.new('RGB', (158, getHeight(55)), "#1e2436")
  name_image = Image.new('RGB', (264, getHeight(55)), "#0a101a")
  kda_image = Image.new('RGB', (214, getHeight(55)), "#1e2436")
  score_image = Image.new('RGB', (202, getHeight(55)), "#0a101a")
  return [pos_image, name_image, kda_image, score_image]

# Fonctions GraphQl qui envoient des requêtes directement sur l'API de https://eva.gg

def getTransport() -> AIOHTTPTransport:
  """
    Construit et retourne un :class:`gql.transport.aiohttp.AIOHTTPTransport`
    
    pour envoyer une requête conforme sur le site Web.
  """
  transport = AIOHTTPTransport(url="https://api.eva.gg/graphql", headers={
          "Accept": "*/*",
          "Accept-Encoding": "gzip, deflate, br",
          "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
          "Connection": "keep-alive",
          "content-type": "application/json",
          "Host": "api.eva.gg",
          "Origin": "https://www.eva.gg",
          "Referer": "https://www.eva.gg/",
          "sec-ch-ua": '"Opera GX";v="89", "Chromium";v="103", "_Not:A-Brand";v="24"',
          "sec-ch-ua-mobile": "?0",
          "sec-ch-ua-platform": "Windows",
          "Sec-Fetch-Dest": "empty",
          "Sec-Fetch-Mode": "cors",
          "Sec-Fetch-Site": "same-site",
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 OPR/89.0.4447.64"
      })

  return transport

async def getLastGame(userId: int, gameId: int = 1) -> Dict:
  """
    Récupérer les données de la dernière partie d'un joueur.

    Paramètres
    ----------
    userId: :class:`int`
      L'id du compte Eva.
    gameId: :class:`int`
      Le numéro de partie. ``1`` = la dernière partie la plus récente.
  """
  async with Client(
      transport=getTransport(),
      fetch_schema_from_transport=False,
  ) as session:

    query = gql("""   
      query ($userId: Int, $page: PageInput, $mode: [GameModeEnum!]) {
        gameHistories(userId: $userId, page: $page, mode: $mode) {
          totalCount
          pageInfo {
            current
            itemsLimit
            total
          }
          nodes 
      {
        id
        createdAt
        data {
          mode
          map
          outcome
          teamOne {
            score
            name
          }
          teamTwo {
            score
            name
          }
        }
        players {
          id
          userId
          data {
            niceName
            rank
            team
            score
            outcome
            kills
            deaths
            assists
          }
        }
      }
        }
      }
    """)

    params = {"userId": userId, "page": {"page": 1, "itemsLimit": 20}}

    result = await session.execute(query, variable_values=params)
    if result["gameHistories"]["nodes"]:
      return result["gameHistories"]["nodes"][gameId - 1]

async def getmyBattlepass() -> Dict:
  """
    Récupérer les informations privées du BattlePass d'un joueur.

    ``Non Fonctionnel`` actuellement.
  """
  return

  async with Client(
      transport=getTransport(),
      fetch_schema_from_transport=False,
  ) as session:

    # Execute single query
    query = gql("""     
      query {
        myBattlepass {
          id
          active
          amount
          expirationDate
          commitmentDate
          memberFrom
          renew
          status
          withCommitment
          nextPaymentAttempt
          monthsLate
          amountLeftToPay
          paymentMethodId
          locationId
          details {
            futureSessionSlotIds
            sessionLeftCount
          }
          payments {
            id
            amount
            status
            creationDatetime
          }
        }
      }
    """)

    result = await session.execute(query)
    return result

async def getStats(userId: int, seasonId: int) -> Tuple[Dict, Dict]:
  """
    Récupérer les statistiques publiques d'un joueur.

    Parameters
    ----------
    userId: :class:`int`
      L'id du compte Eva.
    seasonId: :class:`int`
      Le numéro de la saison.

    Returns
    -------
    :class:`Tuple`(
      player_infos: :class:`dict`
        Les informations publiques du joueur Eva.
      player_stats: :class:`dict`
        Les stats publiques du joueur Eva.
    )
  """
  async with Client(
      transport=getTransport(),
      fetch_schema_from_transport=False,
  ) as session:

      # Profile Query
      player_query = gql("""
        query ($userId: Int, $username: String, $seasonId: Int) {
          player(userId: $userId, username: $username) {
            ...
        {
          userId
          username
          displayName
          seasonPass(seasonId: $seasonId) {
            active
          }
          experience(gameId: 1, seasonId: $seasonId) {
            experience
            experienceForCurrentLevel
            experienceForNextLevel
            level
            levelProgressionPercentage
          }
        }
          }
        }
      """)

      params = {"userId": userId, "seasonId": seasonId}

      player_result = await session.execute(player_query, variable_values=params)

      # Stats Query
      stats_query = gql("""
        query ($userId: Int, $username: String, $seasonId: Int) {
          player(userId: $userId, username: $username) {
            statistics(gameId: 1, seasonId: $seasonId) {
              data {
                gameCount
                gameTime
                gameVictoryCount
                gameDefeatCount
                gameDrawCount
                inflictedDamage
                bestInflictedDamage
                kills
                deaths
                assists
                killDeathRatio
                killsByDeaths
                traveledDistance
                traveledDistanceAverage
                bestKillStreak
              }
            }
          }
        }
      """)

      params = {"userId": userId, "seasonId": seasonId}

      try:
        stats_result = await session.execute(stats_query, variable_values=params)
      except TransportQueryError:
        raise
      else:
        return player_result, stats_result

async def getSeasonsList() -> typing.List:
  """
    Récupérer la liste des saisons.

    N'est pas censée être appelée manuellement.
  """
  async with Client(
      transport=getTransport(),
      fetch_schema_from_transport=False,
  ) as session:

      query = gql("""
        query {
          listSeasons {
            nodes 
        {
          id
          from
          to
          seasonNumber
          active
          status
        }

            itemCount
          }
        }
      """)

      result = await session.execute(query)

      return result["listSeasons"]["nodes"]

async def getProfile(username: str) -> Dict:
  """
    Récupérer les informations publiques du profil d'un joueur.

    Pour récupérer l'attribut ``username`` d'un membre, utilisez la fonction :meth:`getPlayerInfos(bot, member)`

    Parameters
    ----------
    username: :class:`str`
      Le nom d'utilisateur du joueur.

    Returns
    ------
    userId: :class:`int`
      Id du joueur.
    username: :class:`str`
      Nom complet du joueur avec le discriminant.
    displayName: :class:`str`
      Nom du joueur sans le discriminant.
    seasonPass:
      active: :class:`bool`
    experience:
      experience: :class:`int`
      experienceForCurrentLevel: :class:`int`
      experienceForNextLevel: :class:`int`
      level: :class:`int`
      levelProgressionPercentage: :class:`int`
  """
  async with Client(
      transport=getTransport(),
      fetch_schema_from_transport=False,
  ) as session:

      query = gql("""
        query ($userId: Int, $username: String) {
          player(userId: $userId, username: $username) {
            ...
        {
          userId
          username
          displayName
          seasonPass {
            active
          }
          experience(gameId: 1) {
            experience
            experienceForCurrentLevel
            experienceForNextLevel
            level
            levelProgressionPercentage
          }
        }
          }
        }
      """)

      params = {"username": username}

      result = await session.execute(query, variable_values=params)

      return result

async def getMe() -> Dict:
  """
    Récupérer les informations privées d'un joueur.

    ``Non fonctionnel`` actuellement.
  """
  return
  
  async with Client(
      transport=getTransport(),
      fetch_schema_from_transport=False,
  ) as session:

      query = gql("""   
        query {
          me {
            ...
        {
          id
          username
          displayName
          email
          role
          gender
          phone
          birthdate
          firstName
          lastName
          fullName
          address {
            line1
            postalCode
            city
            country
          }
          newsletter
          isPublic
        }
            player 
        {
          userId
          username
          displayName
          seasonPass {
            active
          }
          experience(gameId: 1) {
            experience
            experienceForCurrentLevel
            experienceForNextLevel
            level
            levelProgressionPercentage
          }
        }
            usernameToken
          }
        }
      """)

      result = await session.execute(query)

      return result

async def getCitiesGQL() -> Dict:
  """
    Retourne toutes les villes où une salle Eva est présente.  
  """
  async with Client(
      transport=getTransport(),
      fetch_schema_from_transport=False,
  ) as session:

      query = gql("""
        
        query($search: String, $country: CountryEnum, $sortOrder: SortOrderLocationsInput) {
          locations(search: $search, country: $country, sortOrder: $sortOrder, includesComingSoon: true) {
            nodes {
              ...
        {
          ...
        {
          id
          name
          playgroundName
          timezone
          emailContact
          department
          fullAddress
          isExternal
          sessionDuration
          sessionPrice
          sessionPriceESport
          currency
          country
          telephone
          url
          geolocationPoint
          geolocationKmDistance
          isComingSoon
          stripe {
            publicKey
          }
        }

          details {
            games {
              id
              maxPlayer
              maxPlayerESport
            }
            terrains {
              id
              name
              areaM2
              maxPlayer
            }
          }
        }

            }
          }
        }
      """)

      params = {
        "search": "",
        "sortOrder": {
          "by": "COUNT_BOOKINGS_MONTHLY",
          "direction": "DESC"
        }
      }

      result = await session.execute(query, variable_values=params)

      return result

async def getCalendar(self, date: datetime.datetime, city_name: str = None, city_id: int = None) -> Dict:
  """
    Retourne le calendrier d'une salle Eva. 
  """
  cities = getCities(self)
  location = getCityfromDict(cities, city_name=city_name, city_id=city_id)
  game_id = 1

  async with Client(
      transport=getTransport(),
      fetch_schema_from_transport=False,
  ) as session:

      query = gql(""" 
  query ($locationId: Int!, $currentDate: Date, $gameId: Int) {
    calendar(locationId: $locationId, currentDate: $currentDate) {
      firstDate
      currentDate
      lastDate
      location {
        id
        name
      }
      closingDays {
        date
        reason
      }
      sessionList(gameId: $gameId) {
        battlepassPercentage
        battlepassOpenSessionCount
        list {
          id
          date
          startTime
          endTime
          duration
          slot {
            ...
  {
    id
    date
    datetime
    startTime
    endTime
    duration
    locationId
  }

          }
          availabilities {
            total
            totalESport
            available
            availableESport
            gameIds
            hasBattlepassPlayer
            isBattlepass
            isESport
            hasESportMode
            taken
            terrainId
            priority
          }
        }
      }
    }
  }
      """)

      params = {
        "locationId": location['id'],
        "currentDate": date.strftime('%Y-%m-%d'),
        "gameId": game_id
      }

      result = await session.execute(query, variable_values=params)

      return result

async def setDateTags(calendar: Dict) -> Union[int, None]:
  dates = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0}
  for day in calendar["closingDays"]:
      date = datetime.datetime.strptime(day["date"], "%Y-%m-%d")
      dates[str(date.weekday())] += 1
  date = sorted(dates.items(), key=lambda x: x[1], reverse=True)[0]
  if date[1] == 0:
      date = None
  else:
      date = int(date[0])
  return date

async def getEachDayInTheWeek() -> Dict[int, datetime.datetime]:
  days_with_dates = {}
  actual_date = datetime.datetime.now()

  for _ in range(0, 7):
    days_with_dates[actual_date.weekday()] = actual_date
    actual_date += datetime.timedelta(days=1)
  return days_with_dates

def getCurrentSeason(self) -> Dict:
  for season in self.bot.get_cog("Variables").seasons_list:
    if season["active"]:
      return season

def getCurrentSeasonNumber(self) -> int:
  for season in self.bot.get_cog("Variables").seasons_list:
    if season["active"]:
      return season["seasonNumber"]