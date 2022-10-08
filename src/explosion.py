import asyncio
import curses

from curses_tools import draw_frame, get_max_frames_size


async def explode(
    canvas: curses.window,
    center_row: int,
    center_column: int,
    frames: list[str],
) -> None:
    """Animate obstacle explosion.

    Args:
        canvas: Main window;
        center_row: Current row position;
        center_column: Current column position
        frames: List of obstacle explosion animations;
    """

    # get the coordinates of the upper left corner for rendering the animation
    rows, columns = get_max_frames_size(frames)
    corner_row = center_row - rows / 2
    corner_column = center_column - columns / 2

    curses.beep()
    for frame in frames:
        draw_frame(canvas, corner_row, corner_column, frame)
        await asyncio.sleep(0)

        draw_frame(canvas, corner_row, corner_column, frame, negative=True)
        await asyncio.sleep(0)
