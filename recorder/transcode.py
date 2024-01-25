import pathlib
import subprocess
import random


def transcode(file_path: pathlib.Path) -> None:
    transcode_output = file_path.parent / f"{file_path.stem}.ts"
    if transcode_output.exists():
        return

    M3U8 = f"""#EXTM3U
#EXT-X-VERSION:7
#EXT-X-TARGETDURATION:{15*(int(file_path.stem)+1)}
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:VOD
"""

    for i in range(int(file_path.stem) + 1):
        if not (file_path.parent / f"{i:08d}.mp4").exists():
            return
        else:
            M3U8 += f"""#EXTINF:15.000000,
{i:08d}.mp4
"""

    M3U8 += "#EXT-X-ENDLIST"

    with open(file_path.parent / f"{file_path.stem}_temp.m3u8", "w") as f:
        f.write(M3U8)

    subprocess.run(
        [
            "ffmpeg",
            "-i",
            str(file_path.parent / f"{file_path.stem}_temp.m3u8"),
            "-ss",
            str(int(file_path.stem) * 15),
            "-to",
            str((int(file_path.stem) + 1) * 15),
            "-c",
            "copy",
            str(transcode_output),
        ],
        check=True,
    )

    (file_path.parent / f"{file_path.stem}_temp.m3u8").unlink()
