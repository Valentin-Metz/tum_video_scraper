# Deduplicate a list
# Source: https://stackoverflow.com/questions/18113835/python-list-of-tuples-deduplication
def dedup(lst: []) -> []:
    seen = set()
    result = []
    for item in lst:
        fs = frozenset(item)
        if fs not in seen:
            result.append(item)
            seen.add(fs)
    return result


# Prepend the index of a list item to the first string in its tuple
def enumerate_list(list_of_tuples: [(str, str)]) -> [(str, str)]:
    return [(f'{index:03d}_{name}', url) for index, (name, url) in enumerate(list_of_tuples)]
