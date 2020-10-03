from typing import List

BOOL_DICT = {'y': True, 'Y': True, 'yes': True, 'Yes': True, '': True,
             'n': False, 'N': False, 'no': False, 'No': False}


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
    return BOOL_DICT[answer]


def has_hebrew(name: str) -> bool:
    """
    Returns whether the given 'name' contains hebrew chars in it (bool).
    """
    return any("\u0590" <= letter <= "\u05EA" for letter in name)


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
    while not correct_input:
        user_input = input(
            f"\n--> Enter songs ({min_index}-{max_index}), space/comma separated, or Return-key to continue: ")
        user_input = set(int(index) for index in user_input.replace(',', ' ').split())
        correct_input = all(index in range_check for index in user_input)
    return user_input


def newline():
    print("\n")
