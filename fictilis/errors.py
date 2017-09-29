class BaseFictilisException(Exception):
    pass


class AlreadyExistsError(BaseFictilisException):
    pass


class NotExistsError(BaseFictilisException):
    pass


class InvalidParams(BaseFictilisException):
    pass


class InvalidDeclaration(BaseFictilisException):
    pass


class InvalidType(BaseFictilisException):
    pass


class UnexpectedError(BaseFictilisException):
    pass
