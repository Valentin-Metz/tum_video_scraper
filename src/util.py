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


# Append numbers to duplicate strings in [(duplicate, str)]
# Source: https://stackoverflow.com/questions/65679401/rename-duplicates-in-python-list
def rename_duplicates(list_of_tuples: [(str, str)]) -> [(str, str)]:
    seen = {}
    for i, (a, b) in enumerate(list_of_tuples):
        if a not in seen:
            seen[a] = 0
        else:
            seen[a] += 1
            list_of_tuples[i] = (list_of_tuples[i][0] + f'_{seen[a]}', b)
    return list_of_tuples
