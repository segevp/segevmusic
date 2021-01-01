from typing import List
from requests import get
from urllib.parse import quote
from re import search

BOOL_DICT = {'y': True, 'Y': True, 'yes': True, 'Yes': True, '': True,
             'n': False, 'N': False, 'no': False, 'No': False}

ODESLI_URL = "https://api.song.link/v1-alpha.1/links?url={url}"


def ask(question: str, bool_dict: dict = BOOL_DICT, on_interrupt=False):
    """
    Prints a given question on stdout and waits for user input.
    Keeps doing so until the answer is in the given dict's keys,
    and then returns the given key's value from the dict.
    """
    answer = None
    while answer not in bool_dict:
        try:
            answer = input(question)
        except KeyboardInterrupt:
            return on_interrupt
    return bool_dict[answer]


def choose_item(items: List):
    items_dict = {str(index): item for index, item in enumerate(items, start=1)}
    for index, item in items_dict.items():
        print(f"{index}) {item}")
    chosen_item = ask(f"\n--> What is your choice (1-{len(items_dict)})? ", bool_dict=items_dict)
    return chosen_item


def has_hebrew(name: str) -> bool:
    """
    Returns whether the given 'name' contains hebrew chars in it (bool).
    """
    return any("\u0590" <= letter <= "\u05EA" for letter in name)


def get_language(name):
    return 'he' if has_hebrew(name) else 'en'


def get_lines(song_names_path: str) -> List[str]:
    """
    Returns the lines that are not empty of a given file path.
    """
    with open(song_names_path, 'r') as f:
        song_names = f.read().split('\n')
        return list(filter(None, song_names))


def get_indexes(max_index, min_index=1) -> List[int]:
    """
    Asking user for indexes input until they are in the min/max range.
    Returns user chosen indexes.
    """
    correct_input = False
    range_check = range(min_index, max_index + 1)
    user_input = []
    newline()
    while not correct_input:
        user_input = input(
            f"--> Enter songs ({min_index}-{max_index}), space/comma separated, or Return-key to continue: ")
        user_input = set(int(index) for index in user_input.replace(',', ' ').split())
        correct_input = all(index in range_check for index in user_input)
    return user_input


def newline():
    print("\n", end='')


def convert_platform_link(link: str, wanted_platform: str):
    url = quote(link)
    json = get(ODESLI_URL.format(url=url)).json()
    return json['linksByPlatform'][wanted_platform]['url']


def get_url_param_value(url: str, param: str):
    re_match = search(r"[?&](" + param + "=[^&]+).*$", url)
    if re_match:
        param_value = re_match.group(1)
        return param_value.split('=')[1]
    print(f"--> WARNING: The parameter {param} was not found in the url.")
    return None


def update_url_param(url: str, param: str, value: str):
    url_split = url.split('?')
    re_match = search(r"[?&](" + param + "=[^&]+).*$", url)
    param_value = f"{param}={quote(value)}"
    if len(url_split) == 1:
        new_url = url + f'?{param_value}'
    elif re_match:
        new_url = url.replace(re_match.group(1), param_value)
    else:
        new_url = url + f'&{param_value}'
    return new_url
