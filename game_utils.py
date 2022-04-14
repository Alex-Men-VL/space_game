import asyncio
import os.path
import random


def get_symbol_coordinates(max_row, max_column):
    coordinates = {
        'row': random.randint(1, max_row - 2),
        'column': random.randint(1, max_column - 2)
    }
    return coordinates


async def make_delay(delay):
    for _ in range(delay):
        await asyncio.sleep(0)


def get_frames(frame_folder):
    frames = []
    if not os.path.isdir(frame_folder):
        return frames
    for file_name in os.listdir(frame_folder):
        file_path = os.path.join(frame_folder, file_name)
        if not os.path.isfile(file_path):
            continue

        with open(file_path) as frame_file:
            frame = frame_file.read()
            frames.append(frame)
    return frames
