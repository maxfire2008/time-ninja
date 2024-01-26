import pathlib
import random
import sys


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
    out_file = directory / "all.mp4"

    if not out_file.exists():
        out_file.touch()

    with open(out_file, "ab") as out:
        with open(next_file, "rb") as next:
            out.write(next.read())

    # delete the next file
    # next_file.unlink()

    # increment the next tracker
    next_tracker += 1
    next_tracker_file.write_text(str(next_tracker))

    lock_file.unlink()
    return True


def concat_all(directory: pathlib.Path) -> None:
    while concat(directory):
        pass


def transcode(directory: pathlib.Path) -> None:
    # ffmpeg -i all.mp4 -c:v h264_videotoolbox -c:a aac -b:v 25M  -hls_time 10 -hls_flags append_list -hls_list_size 0 -f hls output.m3u8
    # or perhaps ffmpeg -i all.mp4 -ss 0 -to 10 -c:v h264_videotoolbox -c:a aac -b:v 25M enc00000000.ts

    pass


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python transcode.py <directory>")
        sys.exit(1)

    dir = pathlib.Path(sys.argv[1])
    concat_all(dir)
