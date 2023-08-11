def status_code_colors(status_code):
    """Return a color for a status code."""
    if 100 <= status_code < 200:
        return "white"
    elif 200 == status_code:
        return "green1"
    elif 200 < status_code < 300:
        return "green3"
    elif 300 <= status_code < 400:
        return "deep_sky_blue1"
    elif 400 <= status_code < 404 or 404 < status_code < 500:
        return "deep_pink2"
    elif 404 == status_code:
        return "bright_red"
    elif 500 == status_code:
        return "magenta1"
    else:
        return "medium_orchid1"
