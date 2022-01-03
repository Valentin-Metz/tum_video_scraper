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
