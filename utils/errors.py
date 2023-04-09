from gql.transport.exceptions import TransportQueryError


class UserIsPrivate(TransportQueryError):
    pass


class UserNotFound(TransportQueryError):
    pass


class UserNotLinked(TransportQueryError):
    pass
