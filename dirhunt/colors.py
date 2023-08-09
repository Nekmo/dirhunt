from colorama import Fore


def status_code_colors(status_code):
    if 100 <= status_code < 200:
        return "white"
    elif 200 == status_code:
        return "green1"
    elif 200 < status_code < 300:
        return "green3"
    elif 300 <= status_code < 400:
        return "deep_sky_blue1"
    elif 500 == status_code:
        return "magenta1"
    else:
        return "medium_orchid1"
