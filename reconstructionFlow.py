import os
import pathlib
import subprocess
import logging

import argparse
import cv2
import numpy as np

import ml.flo_util as flo_util
import scripts.analysis.image_utils

READER_PATHS = {
    "disparity_x": f"_x_stereo.left.{{width}}.{{height}}.1.float",
    "disparity_y": f"_y_stereo.left.{{width}}.{{height}}.1.float",
}

def get_path(movie, chapter, field, frame_id=None):
    path = pathlib.Path(field) / movie / f"chapter{chapter}"
    if frame_id is None:
        return path

    if field in ["image_left", "image_right"]:
        filename = f"out{str(frame_id+1).zfill(8)}.jpg"
    elif field in ["flow_forward", "flow_backward"]:
        filename = f"out{str(frame_id+1).zfill(8)}.flo"
    else:
        raise
    return pathlib.Path(field) / movie / f"chapter{chapter}" / filename


def load_readers(movie, chapter):
    image_left_path = get_path(movie, chapter, "image_left", 0)
    assert image_left_path.exists()
    dummy_img = cv2.imread(str(image_left_path))
    # should be in format h, w, c (or h, w if greyscale)
    height = dummy_img.shape[0]
    width = dummy_img.shape[1]
    readers_filenames = {
        reader: get_path(movie, chapter, "reconstructions")
        / reader_path.format(width=width, height=height)
        for reader, reader_path in READER_PATHS.items()
    }
    readers = {
        reader: scripts.analysis.image_utils.RawReader(reader_filename)
        for reader, reader_filename in readers_filenames.items()
    }
    return readers


def forward_flow_to_backward_flow(forward, ignore_value=-1):
    h, w = forward.shape[0:2]
    coord_x, coord_y = np.meshgrid(range(w), range(h))
    left_coord = np.stack([coord_x, coord_y], axis=2)
    assert left_coord.shape == forward.shape, f"{left_coord.shape} != {forward.shape}"
    right_coord = np.round(left_coord + forward).astype(np.int32)
    left_coord = left_coord.astype(np.int32)
    valid = np.logical_and(right_coord[:, :, 0] < w, right_coord[:, :, 1] < h)
    valid = np.logical_and(right_coord[:, :, 0] >= 0, valid)
    valid = np.logical_and(right_coord[:, :, 1] >= 0, valid)
    backward = np.full_like(forward, ignore_value)
    # it is assumed that forward_flow is injective mapping
    right_idx = (right_coord[valid, 1], right_coord[valid, 0])
    left_idx = (left_coord[valid, 1], left_coord[valid, 0])
    for c in range(2):
        backward[(right_idx[0], right_idx[1], c)] = -forward[
            (left_idx[0], left_idx[0], c)
        ]
    return backward


def run_reconstruction(movie, chapter, ce_repo):
    movies_repo_dir = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
    ce_repo = pathlib.Path(os.path.realpath(ce_repo))
    assert ce_repo.exists()
    reconstruction_path = movies_repo_dir / get_path(movie, chapter, "reconstructions")
    reconstruction_path.mkdir(parents=True, exist_ok=True)
    cmd = [
        "env/build/run.sh",
        "./build/stereo/save_disparity",
        "-Simage_dim_scale=1.0",
        "-Skind=1",
        f"-Sdir=/host/{reconstruction_path}",
        f"--movies-base-dir=/host/{movies_repo_dir}",
        f"--movie={movie}",
        f"--chapter={chapter}"
    ]
    print(' '.join(cmd))
    p = subprocess.Popen(
        cmd,
        cwd=ce_repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False
    )
    out, err = p.communicate()
    ret_code = p.returncode   # ret_code != 0, indicates an error occured in execution.
    if ret_code:
        logging.error(err)
        return False
    logging.info(out)
    return True

def write_frame(movie, chapter, frame_id, readers):
    forward_flow_path = get_path(movie, chapter, "flow_forward", frame_id)
    backward_flow_path = get_path(movie, chapter, "flow_backward", frame_id)
    # reconstruction_
    data = {
        reader_name: np.array(reader.get_frames(frame_id, 1))[0]
        for reader_name, reader in readers.items()
    }
    forward_flow = np.concatenate([-data["disparity_x"], data["disparity_y"]], 2)
    backward_flow = forward_flow_to_backward_flow(forward_flow)
    flo_util.writeFlow(forward_flow_path, forward_flow)
    flo_util.writeFlow(backward_flow_path, backward_flow)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="create .flo files for forward and backward flow"
    )
    parser.add_argument("--movie", type=str, help="movie name", required=True)
    parser.add_argument("--chapter", type=int, help="chapter number", required=True)
    parser.add_argument(
        "--ce_repo", type=str, help="ce repo for reconstruction", required=True
    )
    args = parser.parse_args()

    run_reconstruction(args.movie, args.chapter, args.ce_repo)
    num_frames = len(os.listdir(get_path(args.movie, args.chapter, "image_left")))
    readers = load_readers(args.movie, 10)
    get_path(args.movie, args.chapter, "flow_forward").mkdir(
        parents=True, exist_ok=True
    )
    get_path(args.movie, args.chapter, "flow_backward").mkdir(
        parents=True, exist_ok=True
    )
    for frame_id in range(num_frames):
        write_frame(args.movie, args.chapter, frame_id, readers)
