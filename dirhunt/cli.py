# -*- coding: utf-8 -*-

#     Ref: https://stackoverflow.com/questions/2685435/cooler-ascii-spinners
import random

SPINNERS = dict(
    BASIC=['-', '/', '|', '\\'],
    ARROW=['←', '↖', '↑', '↗', '→', '↘', '↓', '↙'],
    VERT_BAR=['▁', '▃', '▄', '▅', '▆', '▇', '█', '▇', '▆', '▅', '▄', '▃'],
    HORIZ_BAR=['▉', '▊', '▋', '▌', '▍', '▎', '▏', '▎', '▍', '▌', '▋', '▊', '▉'],
    SPIN_RECT=['▖', '▘', '▝', '▗'],
    ELAST_BAR=['▌', '▀', '▐▄'],
    TETRIS=['┤', '┘', '┴', '└', '├', '┌', '┬', '┐'],
    TRIANGLE=['◢', '◣', '◤', '◥'],
    SQUARE_QRT=['◰', '◳', '◲', '◱'],
    CIRCLE_QRT=['◴', '◷', '◶', '◵'],
    CIRCLE_HLF=['◐', '◓', '◑', '◒'],
    BALLOON=['.', 'o', 'O', '@', '*'],
    BLINK=['◡◡', '⊙⊙', '◠◠'],
    TURN=['◜ ', ' ◝', ' ◞', '◟ '],
    LOSANGE=['◇', '◈', '◆'],
    BRAILLE=['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'],
)


def spinner(spinner_list):
    i = 0
    while True:
        yield spinner_list[i % len(spinner_list)]
        i += 1


def random_spinner():
    return spinner(random.choice(list(SPINNERS.values())))
