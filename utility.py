def append_patch(name, id, count) -> str:
    return f'{name}-{id + 1}-{count}' if count > 1 else name
