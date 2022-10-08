import math


def _limit(
    value: float,
    min_value: int,
    max_value: int,
) -> int | float:
    """Limit value by min_value and max_value.

    Args:
        value: Considered value;
        min_value: Left limit;
        max_value: Right limit.

    Returns:
        Considered value or limit value.
    """

    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value


def _apply_acceleration(
    speed: float,
    speed_limit: int,
    forward: bool = True,
) -> int | float:
    """Change speed — accelerate or brake — according to force direction.

    Args:
        speed: Current ship speed;
        speed_limit: Limit of ship speed;
        forward: Force direction.

    Returns:
        Final speed.
    """

    speed_limit = abs(speed_limit)
    speed_fraction = speed / speed_limit

    # if the ship is standing still, pull sharply
    # if the ship is already flying fast, add slowly
    delta = math.cos(speed_fraction) * 0.75

    if forward:
        result_speed = speed + delta
    else:
        result_speed = speed - delta

    result_speed = _limit(result_speed, -speed_limit, speed_limit)

    # if the speed is close to zero, then we stop the ship
    if abs(result_speed) < 0.1:
        result_speed = 0

    return result_speed


def update_speed(
    row_speed: int,
    column_speed: int,
    rows_direction: int,
    columns_direction: int,
    row_speed_limit: int = 2,
    column_speed_limit: int = 2,
    fading: float = 0.8,
) -> tuple[float, float]:
    """Update speed smoothly to make control handy for player.

    rows_direction — is a force direction by rows' axis. Possible values:
       -1 — if force pulls up
       0  — if force has no effect
       1  — if force pulls down

    columns_direction — is a force direction by columns` axis. Possible values:
       -1 — if force pulls left
       0  — if force has no effect
       1  — if force pulls right

    Args:
        row_speed: Current row speed;
        column_speed: Current column speed;
        rows_direction: Horizontal direction of movement;
        columns_direction: Vertical direction of movement;
        row_speed_limit: Horizontal speed limit;
        column_speed_limit: Vertical speed limit;
        fading: Speed attenuation coefficient.

    Returns:
        New speed value (row_speed, column_speed).
    """

    if rows_direction not in (-1, 0, 1):
        raise ValueError(
            f'Wrong rows_direction value {rows_direction}. Expects -1, 0 or 1.'
        )

    if columns_direction not in (-1, 0, 1):
        raise ValueError(
            f'Wrong columns_direction value {columns_direction}. '
            'Expects -1, 0 or 1.'
        )

    if fading < 0 or fading > 1:
        raise ValueError(
            f'Wrong columns_direction value {fading}. '
            'Expects float between 0 and 1.'
        )

    # extinguish the speed so that the ship stops over time
    row_speed *= fading
    column_speed *= fading

    row_speed_limit, column_speed_limit = (
        abs(row_speed_limit),
        abs(column_speed_limit),
    )

    if rows_direction != 0:
        row_speed = _apply_acceleration(
            row_speed, row_speed_limit, rows_direction > 0
        )

    if columns_direction != 0:
        column_speed = _apply_acceleration(
            column_speed, column_speed_limit, columns_direction > 0
        )

    return row_speed, column_speed
