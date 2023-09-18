class ParserFindTagException(Exception):
    """Вызывается, когда парсер не может найти тег."""
    pass


class ParserFindAllVersionsException(Exception):
    """Вызывается, когда в блоке ul не содержится заданный текст."""
    pass
