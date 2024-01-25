import pathlib
import subprocess
import random


def concat(directory: pathlib.Path) -> bool:
    lock_file = directory / "lock"
    if lock_file.exists():
        return True

    lock_bytes = random.randbytes(128)
    lock_file.write_bytes(lock_bytes)
    if lock_file.read_bytes() != lock_bytes:
        return True

    next_tracker_file = directory / "next"
    if not next_tracker_file.exists():
        next_tracker = 0
    else:
        next_tracker = int(next_tracker_file.read_text())

    next_file = directory / f"{next_tracker:08d}.mp4"

    if not next_file.exists():
        lock_file.unlink()
        return False

    # append the next file to out.mp4
    out_file = directory / "out.mp4"

    if not out_file.exists():
        out_file.touch()

    with open(out_file, "ab") as out:
        with open(next_file, "rb") as next:
            out.write(next.read())

    # delete the next file
    next_file.unlink()

    # increment the next tracker
    next_tracker += 1
    next_tracker_file.write_text(str(next_tracker))

    lock_file.unlink()
    return True


def concat_all(directory: pathlib.Path) -> None:
    while concat(directory):
        pass
