import asyncio
import curses

from curses_tools import draw_frame, get_max_frames_size


async def explode(canvas, center_row, center_column, frames):
    rows, columns = get_max_frames_size(frames)
    corner_row = center_row - rows / 2
    corner_column = center_column - columns / 2

    curses.beep()
    for frame in frames:
        draw_frame(canvas, corner_row, corner_column, frame)

        await asyncio.sleep(0)
        draw_frame(canvas, corner_row, corner_column, frame, negative=True)
        await asyncio.sleep(0)
