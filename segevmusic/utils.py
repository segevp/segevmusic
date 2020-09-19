from typing import Iterator

BOOL_DICT = {'y': True, 'Y': True, 'yes': True, 'Yes': True,
             'n': False, 'N': False, 'no': False, 'No': False}


def ask(question: str, bool_dict: dict = BOOL_DICT):
    """
    Prints a given question on stdout and waits for user input.
    Keeps doing so until the answer is in the given dict's keys,
    and then returns the given key's value from the dict.
    """
    answer = None
    while answer not in bool_dict:
        answer = input(question)
    return BOOL_DICT[answer]


def has_hebrew(name: str) -> bool:
    """
    Returns whether the given 'name' contains hebrew chars in it (bool).
    """
    return any("\u0590" <= letter <= "\u05EA" for letter in name)


def get_lines(song_names_path: str) -> Iterator[str]:
    """
    Returns the lines that are not empty of a given file path.
    """
    with open(song_names_path, 'r') as f:
        song_names = f.read().split('\n')
        return filter(None, song_names)
