import curses

SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258


def read_controls(canvas: curses.window) -> tuple[int, int, bool]:
    """Read keys pressed.

    Args:
        canvas: Main window.

    Returns:
        Tuple with controls state.
    """

    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            break

        if pressed_key_code == UP_KEY_CODE:
            rows_direction = -1

        if pressed_key_code == DOWN_KEY_CODE:
            rows_direction = 1

        if pressed_key_code == RIGHT_KEY_CODE:
            columns_direction = 1

        if pressed_key_code == LEFT_KEY_CODE:
            columns_direction = -1

        if pressed_key_code == SPACE_KEY_CODE:
            space_pressed = True
    return rows_direction, columns_direction, space_pressed


def draw_frame(
    canvas: curses.window,
    start_row: int | float,
    start_column: int | float,
    text: str,
    negative: bool = False,
) -> None:
    """Draw multiline text fragment on canvas,
    erase text instead of drawing if negative=True is specified.

    Args:
        canvas: Main window;
        start_row: Current position row of frame;
        start_column: Current position column of frame;
        text: Multiline text;
        negative: Flag indicating to draw or erase text.
    """

    rows_number, columns_number = canvas.getmaxyx()

    for row, line in enumerate(text.splitlines(), round(start_row)):
        if row < 0:
            continue

        if row >= rows_number:
            break

        for column, symbol in enumerate(line, round(start_column)):
            if column < 0:
                continue

            if column >= columns_number:
                break

            if symbol == ' ':
                continue

            if row == rows_number - 1 and column == columns_number - 1:
                continue

            symbol = symbol if not negative else ' '
            canvas.addch(row, column, symbol)


def get_frame_size(frame: str) -> tuple[int, int]:
    """Calculate size of multiline text fragment

    Args:
        frame: Multiline text fragment.

    Returns:
        Pair — number of rows and columns.
    """

    lines = frame.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns


def get_max_frames_size(frames: list[str]) -> tuple[int, int]:
    """Calculate max size of multiline text for each of the coordinates.

    Args:
        frames: Multiline text.

    Returns:
        Pair — number of rows and columns.
    """

    sizes = [get_frame_size(frame) for frame in frames]
    max_rows = max(sizes, key=lambda size: size[0])[0]
    max_columns = max(sizes, key=lambda size: size[1])[1]
    return max_rows, max_columns
