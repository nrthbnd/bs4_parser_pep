import logging
import re
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import (BASE_DIR, EXPECTED_STATUS,
                       MAIN_DOC_URL, PEP_DOC_URL, STATUS_LIST)
from outputs import control_output
from utils import find_tag, get_response, get_correct_status


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
        'li',
        attrs={'class': 'toctree-l1'}
    )
    result = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]

    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if response is None:
            continue

        soup = BeautifulSoup(response.text, features='lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        result.append((version_link, h1.text, dl_text))
    return result


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise Exception('Ничего не нашлось')
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append((link, version, status))
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    soup = BeautifulSoup(response.text, features='lxml')

    main_tag = find_tag(soup, 'div', {'role': 'main'})
    table = find_tag(main_tag, 'table', attrs={'class': 'docutils'})

    for _ in table:
        pdf_a4_tag = find_tag(
            table,
            'a',
            {'href': re.compile(r'.+pdf-a4\.zip$')}
        )
        pdf_a4_link = pdf_a4_tag['href']
        archive_url = urljoin(downloads_url, pdf_a4_link)
        filename = archive_url.split('/')[-1]

        downloads_dir = BASE_DIR / 'downloads'
        downloads_dir.mkdir(exist_ok=True)
        archive_path = downloads_dir / filename

        response = session.get(archive_url)
        with open(archive_path, 'wb') as file:
            file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    """Парсинг странички PEP."""
    response = get_response(session, PEP_DOC_URL)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    main_section = soup.find('section', attrs={'id': 'index-by-category'})
    tbody = main_section.find_all('tbody')
    status_list_counted = [0] * len(STATUS_LIST)

    for item in tqdm(tbody):
        tr = item.find_all('tr')
        for tr_tag in tr:
            status = find_tag(tr_tag, 'td').text[1:]
            a_tag = find_tag(tr_tag, 'a', attrs={'class': 'reference'})
            href = a_tag['href']

            pep_link = urljoin(PEP_DOC_URL, href)
            pep_response = get_response(session, pep_link)
            pep_soup = BeautifulSoup(pep_response.text, features='lxml')
            pep_section = find_tag(
                pep_soup,
                'section',
                attrs={'id': 'pep-content'}
            )
            headers = find_tag(
                pep_section,
                'dl',
                attrs={'class': 'field-list'}
            )

            pattern = r'.*?Status:\n(?P<status>.*?)\n'
            status_match = re.search(pattern, headers.get_text())
            full_status = status_match.group('status')
            real_status = (
                [keys for keys, values in EXPECTED_STATUS.items()
                    if full_status in values][0] if any(
                        full_status in values for values in (
                            EXPECTED_STATUS.values())
                    ) else None)
            get_correct_status(status, real_status, pep_link)

            if real_status is not None:
                status_index = STATUS_LIST.index(real_status)
                status_list_counted[status_index] += 1

    results = [('Статус', 'Количество')]
    total = 0
    for item, status in enumerate(STATUS_LIST):
        count = status_list_counted[item]
        total += count
        results.append((status, count))
    results.append(('Total', total))

    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()

    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results is not None:
        control_output(results, args)
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
