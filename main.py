import asyncio
import curses
import random
import time
from itertools import cycle

from curses_tools import draw_frame
from game_utils import get_symbol_coordinates, make_delay, get_frames


async def blink(canvas, row, column, symbol='*', delay=0):
    await make_delay(delay)

    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await make_delay(20)

        canvas.addstr(row, column, symbol)
        await make_delay(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await make_delay(5)

        canvas.addstr(row, column, symbol)
        await make_delay(3)


async def fire(canvas, start_row, start_column,
               rows_speed=-0.3, columns_speed=0):
    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def spaceship(canvas, row, column, frames):
    for frame in cycle(frames):
        draw_frame(canvas, row, column, frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, frame, negative=True)


def draw(canvas):
    canvas.border()
    curses.curs_set(False)

    symbols = '+*.:'
    tic_timeout = 0.1
    stars_count = 100

    max_row, max_column = canvas.getmaxyx()
    frames = get_frames('frames')
    coroutines = [fire(canvas, max_row // 2, max_column // 2),
                  spaceship(canvas, max_row // 2, max_column // 2, frames)]
    coroutines.extend([
        blink(canvas,
              **get_symbol_coordinates(max_row, max_column),
              symbol=random.choice(symbols),
              delay=random.randint(1, 5)) for _ in range(stars_count)
    ])

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(tic_timeout)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
