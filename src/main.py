import asyncio
import curses
import random
import time
from itertools import cycle
from statistics import median

import config
from curses_tools import (
    draw_frame,
    read_controls,
    get_max_frames_size,
    get_frame_size,
)
from explosion import explode
from game_scenario import PHRASES, get_garbage_delay_tics
from game_utils import (
    get_symbol_coordinates,
    make_delay,
    get_frames,
    get_frame_per_tic,
)
from obstacles import Obstacle
from physics import update_speed

COROUTINES = []
OBSTACLES = []
OBSTACLES_IN_LAST_COLLISIONS = []
YEAR = 1957


async def animate_star_blink(canvas, row, column, symbol='*', delay=0):
    await make_delay(delay)

    brightness_per_delay = [
        (curses.A_DIM, 20),
        (curses.A_NORMAL, 3),
        (curses.A_BOLD, 5),
        (curses.A_NORMAL, 3),
    ]

    while True:
        for brightness, delay in brightness_per_delay:
            canvas.addstr(row, column, symbol, brightness)
            await make_delay(delay)


async def animate_fire(
    canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0
):
    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    (
        rows,
        columns,
    ) = canvas.getmaxyx()  # legacy curses feature, returns wrong values
    max_row, max_column = (
        rows - 1,
        columns - 1,
    )  # the coordinates of the last cell are 1 smaller

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed

        for obstacle in OBSTACLES:
            if obstacle.has_collision(row, column):
                OBSTACLES_IN_LAST_COLLISIONS.append(obstacle)
                return


async def animate_spaceship(canvas, row, column, frames, gameover_frame):
    current_row, current_column = row, column
    min_row = min_column = 1
    (
        rows,
        columns,
    ) = canvas.getmaxyx()  # legacy curses feature, returns wrong values
    max_row, max_column = (
        rows - 1,
        columns - 1,
    )  # the coordinates of the last cell are 1 smaller
    frame_rows, frame_columns = get_max_frames_size(frames)
    max_row -= frame_rows
    max_column -= frame_columns
    row_speed = column_speed = 0

    for frame in cycle(get_frame_per_tic(frames)):
        row_offset, column_offset, space_pressed = read_controls(canvas)
        row_speed, column_speed = update_speed(
            row_speed, column_speed, row_offset, column_offset
        )

        current_row = median([min_row, current_row + row_speed, max_row])
        current_column = median(
            [min_column, current_column + column_speed, max_column]
        )

        if space_pressed and YEAR > config.FIRE_START_YEAR:
            fire_column = (
                current_column + frame_columns // 2
            )  # as current_column points to the left edge of the frame
            COROUTINES.append(animate_fire(canvas, current_row, fire_column))

        draw_frame(canvas, current_row, current_column, frame)
        await asyncio.sleep(0)
        draw_frame(canvas, current_row, current_column, frame, negative=True)

        for obstacle in OBSTACLES:
            if obstacle.has_collision(
                current_row, current_column, frame_rows, frame_columns
            ):
                COROUTINES.append(show_gameover(canvas, gameover_frame))
                return


async def fill_orbit_with_garbage(canvas, frames, explosion_frames):
    (
        rows_number,
        columns_number,
    ) = canvas.getmaxyx()  # legacy curses feature, returns wrong values
    max_row, max_column = (
        rows_number - 1,
        columns_number - 1,
    )  # the coordinates of the last cell are 1 smaller

    while True:
        column = get_symbol_coordinates(max_row, max_column)['column']
        frame = random.choice(frames)
        delay = get_garbage_delay_tics(YEAR)
        if not delay:
            await make_delay(1)
            continue

        COROUTINES.append(
            animate_garbage(canvas, column, frame, explosion_frames)
        )
        await make_delay(delay)


async def animate_garbage(
    canvas, column, garbage_frame, explosion_frames, speed=0.5
):
    """Animate garbage, flying from top to bottom.
    Сolumn position will stay same, as specified on start."""

    # legacy curses feature, returns wrong values
    rows_number, columns_number = canvas.getmaxyx()

    columns_number -= 1  # the coordinates of the last cell are 1 smaller
    frame_rows, frame_columns = get_frame_size(garbage_frame)

    column = median([0, column, columns_number - frame_columns])
    row = 0

    obstacle = Obstacle(row, column, frame_rows, frame_columns)
    OBSTACLES.append(obstacle)
    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed
        obstacle.row = row

        if obstacle in OBSTACLES_IN_LAST_COLLISIONS:
            OBSTACLES.remove(obstacle)
            center_row = row + frame_rows // 2
            center_column = column + frame_columns // 2
            await explode(canvas, center_row, center_column, explosion_frames)
            return
    OBSTACLES.remove(obstacle)


async def show_gameover(canvas, gameover_frame):
    # legacy curses feature, returns wrong values
    rows_number, columns_number = canvas.getmaxyx()

    max_row, max_column = (
        rows_number - 1,
        columns_number - 1,
    )  # the coordinates of the last cell are 1 smaller
    frame_rows, frame_columns = get_frame_size(gameover_frame)

    row = (max_row - frame_rows) // 2
    column = (max_column - frame_columns) // 2
    while True:
        draw_frame(canvas, row, column, gameover_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, gameover_frame, negative=True)


async def show_game_description(canvas):
    row = column = 1
    while True:
        phrase = PHRASES.get(YEAR)
        if phrase:
            frame = f'{YEAR} - {phrase}'
        else:
            frame = str(YEAR)
        draw_frame(canvas, row, column, frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, frame, negative=True)


async def change_year():
    global YEAR

    while True:
        YEAR += 1
        await make_delay(config.CHANGE_YEAR_DELAY)


def draw(canvas):
    canvas.border()
    canvas.nodelay(True)
    curses.curs_set(False)

    # legacy curses feature, returns wrong values
    rows, columns = canvas.getmaxyx()

    max_row, max_column = (
        rows - 1,
        columns - 1,
    )  # the coordinates of the last cell are 1 smaller

    frames = get_frames(config.FRAMES_FOLDER_PATH)
    COROUTINES.extend(
        [
            animate_spaceship(
                canvas,
                max_row // 2,
                max_column // 2,
                frames['rocket'],
                frames['gameover'][0],
            ),
            fill_orbit_with_garbage(
                canvas,
                frames['trash'],
                frames['explosion'],
            ),
            show_game_description(canvas),
            change_year(),
        ]
    )
    COROUTINES.extend(
        [
            animate_star_blink(
                canvas,
                **get_symbol_coordinates(max_row, max_column),
                symbol=random.choice(config.STAR_SYMBOLS),
                delay=random.randint(
                    config.MIN_BLINK_DELAY,
                    config.MAX_BLINK_DELAY,
                ),
            )
            for _ in range(config.STARS_COUNT)
        ]
    )

    while True:
        for coroutine in COROUTINES.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                COROUTINES.remove(coroutine)
        canvas.refresh()
        canvas.border()  # To fix bug with broken border
        canvas.refresh()

        time.sleep(config.TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
