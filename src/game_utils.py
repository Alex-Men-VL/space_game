import asyncio
import os
import random
import typing


def get_symbol_coordinates(
    max_row: int,
    max_column: int,
) -> dict[str, int]:
    """Get random coordinates on game window.

    Args:
        max_row: Window width;
        max_column: Window height.

    Returns:
        Dict with random coordinates.
    """

    coordinates = {
        'row': random.randint(
            1, max_row - 1
        ),  # subtract 1 so as not to get the coordinate of the border
        'column': random.randint(1, max_column - 1),
    }
    return coordinates


async def make_delay(delay: int) -> None:
    """Make animation delay.

    Args:
        delay: Delay value.
    """

    for _ in range(delay):
        await asyncio.sleep(0)


def get_frames(frames_folder_path: str) -> dict[str, list[str]]:
    """Get game frames.

    Args:
        frames_folder_path: Path to folder with game frames.

    Returns:
        Dict with list of frames for each animation.
    """

    frames = {}
    for file_name in os.listdir(frames_folder_path):
        file_path = os.path.join(frames_folder_path, file_name)
        if not os.path.isfile(file_path):
            continue

        with open(file_path) as frame_file:
            frame = frame_file.read()
        frame_type, *_ = file_name.split('_')
        frames.setdefault(frame_type, []).append(frame)
    return frames


def get_frame_per_tic(
    frames: list[str],
    tic_count: int = 2,
) -> typing.Generator[str, None, None]:
    """Get frame per tic.

    Args:
        frames: List of frames;
        tic_count: Delay each frame in animation.
    """

    for frame in frames:
        for _ in range(tic_count):
            yield frame
