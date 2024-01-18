import pathlib


def transcode(directory: pathlib.Path) -> None:
    for item in sorted(directory.iterdir()):
        if not item.exists():
            continue
        if item.is_dir():
            transcode(item)
        if item.suffix == ".mp4":
            # convert the name to an integer
            # then subtract 1 and convert back to a string with 0 padding to make it the same length
            previous_item_name = (
                str(int(item.stem) - 1).zfill(len(item.stem)) + item.suffix
            )

            if (directory / previous_item_name).exists():
                # add the current item to the previous item
                with open(directory / previous_item_name, "ab") as f:
                    f.write(item.read_bytes())
                # delete the current item
                item.unlink()
                # rename the previous item to the current item
                (directory / previous_item_name).rename(item)
