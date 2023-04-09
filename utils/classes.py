import typing
import asyncpg
from disnake.ext import commands


class EvaBot(commands.InteractionBot):
    """
    Represents disnake.ext.commands.InteractionBot with some
    needed attributes added.

    Attributes
    ----------
    guilds_ranking: :class:`Dict`
        Guilds where there is a EVA ranking system.
    resa_channels: :class:`List`
        Channels where there is a EVA booking system.
    seasons_list: :class:`List`
        List of every EVA seasons.
    eva_cities: :class:`Dict`
        Every EVA cities.
    pool: :class:`asyncpg.Pool`
        Connection pool to the database.
    sondages: :class:`Dict`
        All sondages messages.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
            
        self.guilds_ranking = {}
        self.resa_channels = []
        self.seasons_list = []
        self.eva_cities = {}
        self.pool: asyncpg.Pool
        self.sondages = {}


class Player:
    def __init__(self, player: typing.Dict) -> None:
        if 'data' in player.keys():
            player = player['data']

        self._player = player
        self._userId: int = player['userId']
        self._username: str = player['username']
        self._displayName: str = player['displayName']
        self._experience: typing.Dict = player['experience']
        self._statistics: typing.Dict = player['statistics']['data']

    @property
    def player(self):
        return self._player

    @player.setter
    def player(self):
        raise ValueError('No edit is allowed.')

    @property
    def userId(self):
        return self._userId

    @userId.setter
    def userId(self):
        raise ValueError('No edit is allowed.')

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self):
        raise ValueError('No edit is allowed.')

    @property
    def displayName(self):
        return self._displayName

    @displayName.setter
    def displayName(self):
        raise ValueError('No edit is allowed.')

    @property
    def experience(self):
        return self._experience

    @experience.setter
    def experience(self):
        raise ValueError('No edit is allowed.')

    @property
    def statistics(self):
        return self._statistics

    @statistics.setter
    def statistics(self):
        raise ValueError('No edit is allowed.')
