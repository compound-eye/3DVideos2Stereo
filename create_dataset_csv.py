import pandas as pd
import argparse
import os

EXTENSIONS = {
    "image_left": ".jpg",
    "image_right": ".jpg",
    "flow_forward": ".flo",
    "flow_backward": ".flo",
    "disparity": ".png",
    "uncertainty": ".png"
}

if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(
        description="create a csv file"
    )
    PARSER.add_argument(
        "list",
        type=str,
        help="path to list file"
    )
    PARSER.add_argument(
        "output_dir",
        type=str,
        help="path to write csv file",
    )
    ARGS = PARSER.parse_args()

    with open(ARGS.list, "r") as f:
        FILENAMES = [line.rstrip("\n") for line in f]

    DATASET = [
        {
            field: f"{field}/{sample}{ext}"
            for field, ext in EXTENSIONS.items()
        } for sample in FILENAMES
    ]
    DATASET = pd.DataFrame.from_records(DATASET)
    DATASET.to_csv(ARGS.output_dir)
