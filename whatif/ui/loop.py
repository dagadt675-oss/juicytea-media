"""Loop helper. The last frame matches frame 0. The camera never rewinds."""

from __future__ import annotations

from PIL import Image


def dissolve_to_frame(image: Image.Image, opening: Image.Image, amount: float) -> Image.Image:
    """Crossfade toward the opening plate. ``amount`` 1 is exactly frame 0."""
    amount = max(0.0, min(1.0, amount))
    if amount <= 0:
        return image
    if amount >= 1:
        return opening.copy()
    return Image.blend(image.convert("RGB"), opening.convert("RGB"), amount)


def pingpong_index(frame: int, one_way: int) -> tuple[int, bool]:
    """Map a frame onto a forward-then-back index.

    ``one_way`` is the number of unique pictures. The way back uses those
    same pictures in reverse so the shot ends where it started.
    """
    if one_way <= 1:
        return 0, False
    cycle = 2 * (one_way - 1)
    pos = frame % cycle
    if pos < one_way:
        return pos, False
    return cycle - pos, True
