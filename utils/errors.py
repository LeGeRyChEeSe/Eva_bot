from gql.transport.exceptions import TransportQueryError


class UserIsPrivate(TransportQueryError):
    pass