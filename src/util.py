# Prepend the index of a list item to the first string in its tuple
def enumerate_list(list_of_tuples: [(str, str)]) -> [(str, str)]:
    return [(f'{index:03d}_{name}', url) for index, (name, url) in enumerate(list_of_tuples)]
