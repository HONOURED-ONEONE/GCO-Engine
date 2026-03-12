def next_version(current: str) -> str:
    # Assumes vN format
    if not current.startswith("v"):
        return "v2"
    try:
        num = int(current[1:])
        return f"v{num + 1}"
    except ValueError:
        return current + "_new"
