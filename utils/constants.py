import datetime

PERMS_EVABOT = 399364975665

ADMIN_USER = 440141443877830656
EVA_COLOR = int("0x7562d9", base=16)
# EVA_COLOR = int("0xff7825", base=16) # Halloween
OFF_PEAK_HOURS_COLOR = int("0x779bed", base=16)
PEAK_HOURS_COLOR = int("0xbc48b8", base=16)
PERFECT_GREY = (47, 49, 54)

COGS_NAMES = {"Admin": "Administrateur",
              "Mod": "Modérateur", "Eva": "Public", "Help": "Aide"}
HIDDEN_COMMANDS = ["fix", "send"]

# Variables de temps
YEARS = [y for y in range(datetime.datetime.now().year,
                          datetime.datetime.now().year + 24, 1)]
MONTHS = {"Janvier": "01", "Février": "02", "Mars": "03", "Avril": "04", "Mai": "05", "Juin": "06",
          "Juillet": "07", "Août": "08", "Septembre": "09", "Octobre": "10", "Novembre": "11", "Décembre": "12"}
DAYS = {0: "Lundi", 1: "Mardi", 2: "Mercredi",
        3: "Jeudi", 4: "Vendredi", 5: "Samedi", 6: "Dimanche"}
HOURS = [h for h in range(1, 24, 1)]
MINUTES = [m for m in range(0, 60, 20)]

NUMBERS = [":zero:", ":one:", ":two:", ":three:", ":four:",
           ":five:", ":six:", ":seven:", ":eight:", ":nine:"]

RATIO_RESIZE = 150/128
MAX_PLAYERS_SCOREBOARD = 10
FFA = "FREE_FOR_ALL"
ZB = "ZOMBIES"
DOM = "DOMINATION"
TDM = "TDM"
SKM = "SKIRMISH"

STATS = {'experience': 'Niveau', 'gameCount': 'Nombre de parties jouées', 'gameTime': 'Temps de jeu', 'gameVictoryCount': 'Nombre de victoires', 'gameDefeatCount': 'Nombre de défaites', 'inflictedDamage': 'Dégats infligés',
         'kills': 'Tués (K)', 'deaths': 'Morts (D)', 'assists': 'Assistances (A)', 'killsByDeaths': 'Ratio Tués/Morts (K/D)', 'traveledDistance': 'Distance parcourue', 'traveledDistanceAverage': 'Distance moyenne parcourue', 'bestKillStreak': "Meilleur série d'éliminations"}

IMGUR_API_ENTRYPOINT = "https://api.imgur.com"
IMGUR_IMAGE_ID = "WGoIXtu"
