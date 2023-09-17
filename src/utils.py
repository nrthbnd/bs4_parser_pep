import logging

from constants import EXPECTED_STATUS
from exceptions import ParserFindTagException
from requests import RequestException


def get_response(session, url):
    """Перехват ошибки RequestException."""
    try:
        response = session.get(url)
        response.encoding = 'utf-8'
        return response
    except RequestException:
        logging.exception(
            f'Возникла ошибка при загрузке страницы {url}',
            stack_info=True
        )


def find_tag(soup, tag, attrs=None):
    """Перехват ошибки поиска тегов."""
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        error_msg = f'Не найден тег {tag} {attrs}'
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tag


def get_correct_status(status, real_status, pep_link):
    """Проверяет соответствие статуса PEP:
    на главной странице и странице PEP."""
    if status != real_status:
        if real_status not in EXPECTED_STATUS.values():
            real_status = 'Some unknown status'
        expected_status = EXPECTED_STATUS[status]
        message = (
            f'Несовпадающие статусы: \n{pep_link}\nСтатус в карточке: '
            f'{real_status}\nОжидаемые статусы: {expected_status}')
        logging.warning(message)
