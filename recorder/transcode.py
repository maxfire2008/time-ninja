import pathlib
import random
import sys
import subprocess
import time
import m3u8
import shutil


def concat(directory: pathlib.Path) -> bool:
    next_tracker_file = directory / "next"
    if not next_tracker_file.exists():
        next_tracker = 0
    else:
        next_tracker = int(next_tracker_file.read_text())

    next_file = directory / f"{next_tracker:08d}.mp4"

    if not next_file.exists():
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

    return True


def concat_all(directory: pathlib.Path) -> None:
    while concat(directory):
        pass


def transcode_all(directory: pathlib.Path) -> None:
    # ffmpeg -i all.mp4 -c:v h264_videotoolbox -c:a aac -b:v 25M -hls_time 10 -hls_playlist_type event -hls_flags append_list -f hls tc.m3u8

    all_file = directory / "all.mp4"
    all_file_size = all_file.stat().st_size

    all_file_size_tracker = directory / "all_size"

    if all_file_size_tracker.exists():
        if all_file_size == int(all_file_size_tracker.read_text()):
            print("No new data for transcoding")
            return
    else:
        all_file_size_tracker.touch()

    all_file_size_tracker.write_text(str(all_file_size))

    try:
        ffprobe_duration = subprocess.run(
            [
                "ffprobe",
                "-show_entries",
                "format=duration",
                "-v",
                "error",
                "-of",
                "csv=p=0",
                "tc.m3u8",
            ],
            cwd=directory,
            capture_output=True,
            check=True,
        )

        duration = float(ffprobe_duration.stdout)
    except subprocess.CalledProcessError:
        duration = 0.0

    print(duration)

    subprocess.run(
        [
            "ffmpeg",
            "-i",
            "all.mp4",
            "-ss",
            str(duration),
            "-c:v",
            "h264_videotoolbox",
            "-c:a",
            "aac",
            "-b:v",
            "25M",
            "-hls_time",
            "10",
            "-hls_playlist_type",
            "event",
            "-hls_flags",
            "append_list",
            "-f",
            "hls",
            "tc.m3u8",
        ],
        cwd=directory,
        check=True,
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python transcode.py <directory>")
        sys.exit(1)

    dir = pathlib.Path(sys.argv[1])

    recording_dirs = set()

    while True:
        pstart = time.time()
        print("Checking for new recordings...")
        recording_dirs_before = len(recording_dirs)
        files = list(dir.glob("**/*.mp4"))

        for file in files:
            try:
                int(file.stem)
            except ValueError:
                continue

            recording_dirs.add(file.parent)

        print(f"Found {len(recording_dirs) - recording_dirs_before} new recordings")

        for recording_dir in recording_dirs:
            print(f"Processing {recording_dir}")
            try:
                print("Concatenating...")
                cstart = time.time()
                concat_all(recording_dir)
                print(f"Concatenated in {time.time() - cstart:.2f}s\n")

                print("Transcoding...")
                tstart = time.time()
                transcode_all(recording_dir)
                print(f"Transcoded in {time.time() - tstart:.2f}s")
            except Exception as e:
                print(f"Error: {e}")
            print("========\n\n")
        time.sleep(max(2, 30 - (time.time() - pstart)))
