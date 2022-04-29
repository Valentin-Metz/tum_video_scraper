import json

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

# filter log of chrome for arbitrary url
# pred: Callable[[str], bool]
def filter_log(logs: list[dict], pred) -> list[str]:
    ret = []
    for l in logs:
        if "message" not in l: continue
        # print(l["message"], ",")
        j = json.loads(l["message"])
        if "message" not in j: continue
        j = j["message"]
        if "params" not in j: continue
        j = j["params"]
        if "request" not in j: continue
        j = j["request"]
        if "url" not in j:
            continue
        url = j["url"]
        if pred(url):
            ret.append(url)
    return ret
