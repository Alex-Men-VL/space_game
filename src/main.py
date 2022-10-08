import asyncio
import curses
import random
import time
from itertools import cycle
from statistics import median

import config
from curses_tools import draw_frame
from curses_tools import get_frame_size
from curses_tools import get_max_frames_size
from curses_tools import read_controls
from explosion import explode
from game_scenario import get_garbage_delay_tics
from game_scenario import PHRASES
from game_utils import get_frame_per_tic
from game_utils import get_frames
from game_utils import get_symbol_coordinates
from game_utils import make_delay
from obstacles import Obstacle
from physics import update_speed

COROUTINES = []
OBSTACLES = []
OBSTACLES_IN_LAST_COLLISIONS = []
YEAR = 1957


async def animate_star_blink(
    canvas: curses.window,
    row: int,
    column: int,
    symbol: str = '*',
    delay: int = 0,
) -> None:
    """Animate twinkling star.

    Args:
        canvas: Main window;
        row: Current row position of star;
        column: Current column position of star
        symbol: Star symbol;
        delay: Delay in star twinkling.
    """

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
    canvas: curses.window,
    start_row: int,
    start_column: int,
    rows_speed: int = -0.3,
    columns_speed: int = 0,
) -> None:
    """Animate spaceship fire.

    Args:
        canvas: Main window;
        start_row: Start row position of fire;
        start_column: Start column position of fire;
        rows_speed: Vertical speed;
        columns_speed: Horizontal speed.
    """

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    # legacy curses feature, returns wrong values
    rows, columns = canvas.getmaxyx()

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
            # Handle collision with obstacles
            if obstacle.has_collision(row, column):
                OBSTACLES_IN_LAST_COLLISIONS.append(obstacle)
                return


async def animate_spaceship(
    canvas: curses.window,
    row: int,
    column: int,
    spaceship_frames: list[str],
    gameover_frame: str,
) -> None:
    """Animate spaceship in current position.

    Args:
        canvas: Main window;
        row: Current position row;
        column: Current position column;
        spaceship_frames: List of spaceship animations;
        gameover_frame: Frame for gameover inscription.
    """

    current_row, current_column = row, column
    min_row = min_column = 1

    # legacy curses feature, returns wrong values
    rows, columns = canvas.getmaxyx()

    max_row, max_column = (
        rows - 1,
        columns - 1,
    )  # the coordinates of the last cell are 1 smaller
    frame_rows, frame_columns = get_max_frames_size(spaceship_frames)
    max_row -= frame_rows
    max_column -= frame_columns
    row_speed = column_speed = 0

    for frame in cycle(get_frame_per_tic(spaceship_frames)):
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
            # Handle collision with obstacles
            if obstacle.has_collision(
                current_row, current_column, frame_rows, frame_columns
            ):
                COROUTINES.append(show_gameover(canvas, gameover_frame))
                return


async def fill_orbit_with_garbage(
    canvas: curses.window,
    garbage_frames: list[str],
    explosion_frames: list[str],
) -> None:
    """Animate stream of garbage

    Args:
        canvas: Main window;
        garbage_frames: List of garbage animations;
        explosion_frames: List of garbage explosion animations.
    """

    # legacy curses feature, returns wrong values
    rows_number, columns_number = canvas.getmaxyx()

    max_row, max_column = (
        rows_number - 1,
        columns_number - 1,
    )  # the coordinates of the last cell are 1 smaller

    while True:
        column = get_symbol_coordinates(max_row, max_column)['column']
        frame = random.choice(garbage_frames)
        delay = get_garbage_delay_tics(YEAR)
        if not delay:
            await make_delay(1)
            continue

        COROUTINES.append(
            animate_garbage(canvas, column, frame, explosion_frames)
        )
        await make_delay(delay)


async def animate_garbage(
    canvas: curses.window,
    column: int,
    garbage_frame: str,
    explosion_frames: list[str],
    speed: int = 0.5,
) -> None:
    """Animate garbage, flying from top to bottom.
    Column position will stay same, as specified on start.

    Args:
        canvas: Main window;
        column: Current column position;
        garbage_frame: Frame for garbage animation;
        explosion_frames: List of garbage explosion animations;
        speed: Speed for garbage animation.
    """

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


async def show_gameover(canvas: curses.window, gameover_frame: str) -> None:
    """Display gameover inscription.

    Args:
        canvas: Main window;
        gameover_frame: Frame for inscription.
    """

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


async def show_game_description(canvas: curses.window) -> None:
    """Display game description.

    Args:
        canvas: Main window.
    """

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


async def change_year() -> None:
    """Change game year."""

    global YEAR

    while True:
        YEAR += 1
        await make_delay(config.CHANGE_YEAR_DELAY)


def draw(canvas: curses.window) -> None:
    """Draw game.

    Args:
        canvas: Main window.
    """

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
