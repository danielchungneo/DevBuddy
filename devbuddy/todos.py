"""Single to-do list: item normalization."""


def normalize_item(item) -> dict:
    if isinstance(item, str):
        return {"text": item.strip(), "done": False}
    return {
        "text": str(item.get("text", "")).strip(),
        "done": bool(item.get("done", False)),
    }


def normalize_todo_items(raw) -> list[dict]:
    out = []
    for x in raw or []:
        if not isinstance(x, (dict, str)):
            continue
        it = normalize_item(x)
        if it["text"]:
            out.append(it)
    return out
