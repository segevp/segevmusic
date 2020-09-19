BOOL_DICT = {'y': True, 'Y': True, 'yes': True, 'Yes': True,
             'n': False, 'N': False, 'no': False, 'No': False}


def ask(question, bool_dict=BOOL_DICT):
    answer = None
    while answer not in bool_dict:
        answer = input(question)
    return BOOL_DICT[answer]


def has_hebrew(name):
    return any("\u0590" <= letter <= "\u05EA" for letter in name)


def get_lines(song_names_path):
    with open(song_names_path, 'r') as f:
        song_names = f.read().split('\n')
        return filter(None, song_names)
