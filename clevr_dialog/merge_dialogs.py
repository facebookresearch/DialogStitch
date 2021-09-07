#! /usr/bin/env python
"""
Copyright (c) Facebook, Inc. and its affiliates.
All rights reserved.

This source code is licensed under the license found in the
LICENSE file in the root directory of this source tree.

Merge dialogs from CLEVR-Dialog.

Author(s): Satwik Kottur
"""

from __future__ import absolute_import, division, print_function, unicode_literals
import argparse
import json
import multiprocessing
import os
import random
from tqdm import tqdm as progressbar
import sys

import dialog


NUM_VAL_IMGS = 500


def main(args):
    print("Reading: {}".format(args["input_json_path"]))
    with open(args["input_json_path"], "r") as file_id:
        raw_data = json.load(file_id)

    dialogs = [dialog.Dialog(ii, jj) for ii in raw_data for jj in range(5)]
    for ii in dialogs:
        ii.segment_dialog()

    # Get triplets randomly sampled.
    triplets = {}
    while len(triplets) < args["num_dialogs"]:
        dialog_triple = random.sample(dialogs, 3)
        merged_id = str([(ii.image_index, ii.dialog_index) for ii in dialog_triple])
        if (
            dialog.Dialog.check_mergeability(*dialog_triple)
            and merged_id not in triplets
        ):
            triplets[merged_id] = dialog.Dialog.merge_dialogs(*dialog_triple)

            if len(triplets) % 100 == 0:
                print("Progress: {} / {}".format(len(triplets), args["num_dialogs"]))

    num_dialog = len(dialogs)
    print("# instances: {}".format(num_dialog))
    print("# triples: {}".format(
        num_dialog * (num_dialog - 1) * (num_dialog - 2) // 6)
    )
    print("# triples matches: {}".format(len(triplets)))

    # Save JSON files.
    print("Saving triplets: {}".format(args["save_json_path"]))
    with open(args["save_json_path"], "w") as file_id:
        json.dump(list(triplets.values()), file_id)


def merge_dialogs(dialogs, num_dialogs, random_seed=None):
    """Given a list of dialogs, randomly sample and merge.
    """
    dialogs = [dialog.Dialog(ii, jj) for ii in dialogs for jj in range(5)]
    for ii in dialogs:
        ii.segment_dialog()
    if random_seed:
        random.seed(random_seed)

    # Get triplets randomly sampled.
    triplets = {}
    with progressbar(total=num_dialogs) as pbar:
        while len(triplets) < num_dialogs:
            dialog_triple = random.sample(dialogs, 3)
            merged_id = str([(ii.image_index, ii.dialog_index) for ii in dialog_triple])
            # merged_id not in triplets
            if dialog.Dialog.check_mergeability(*dialog_triple):
                triplets[merged_id] = dialog.Dialog.merge_dialogs(*dialog_triple)
                pbar.update(1)
    print("# instances: {}".format(len(dialogs)))
    print("# triples matches: {}".format(len(triplets)))
    return list(triplets.values())


def worker(dialogs, num_dialogs, worker_seed, worker_id, out_queue):
    out_queue.put({worker_id: merge_dialogs(dialogs, num_dialogs, worker_seed)})


def merge_dialog_wrapper(source_data, num_dialogs, args):
    """Wrapper around merging dialogs.
    """

    def get_label(dialog):
        return "_".join(
            [str(ii) for ii in dialog["image_index"]]
            + [str(ii) for ii in dialog["dialog_index"]]
        )

    print("Starting the threads:")
    # Multithread version.
    output_q = multiprocessing.Queue()
    jobs = []
    for worker_id in range(args["num_workers"]):
        num_dialogs_worker = num_dialogs // args["num_workers"]
        inputs = (
            source_data,
            num_dialogs_worker,
            random.randrange(sys.maxsize),
            worker_id,
            output_q,
        )
        process = multiprocessing.Process(target=worker, args=inputs)
        jobs.append(process)
        process.start()
    # Wait for all the jobs to finish and collect the output.
    final_results = {}
    for _ in jobs:
        final_results.update(output_q.get())
    for job in jobs:
        job.join()

    concat_dialogs = [jj for ii in final_results.values() for jj in ii]
    total_dials = len(concat_dialogs)
    unique_dials = len(set(get_label(ii) for ii in concat_dialogs))
    overlap_percent = (total_dials - unique_dials) / total_dials * 100
    print("Generated: {}".format(total_dials))
    print("Overlap: {} \%".format(overlap_percent))
    return concat_dialogs


def generate_dataset(args):
    print("Reading: {}".format(args["clevr_train_json"]))
    with open(args["clevr_train_json"], "r") as file_id:
        train_data = json.load(file_id)

    print("Reading: {}".format(args["clevr_val_json"]))
    with open(args["clevr_val_json"], "r") as file_id:
        val_data = json.load(file_id)

    # Each image contains 5 dialogs, 3 dialogs are merged together.
    collection = [
        {
            "split": "val",
            "source": train_data[:NUM_VAL_IMGS],
            "num_dialogs": NUM_VAL_IMGS * 5 // 3,
        },
        {
            "split": "test",
            "source": val_data,
            "num_dialogs": len(val_data) * 5 // 3,
        },
        {
            "split": "train",
            "source": train_data[NUM_VAL_IMGS:],
            "num_dialogs": (len(train_data) - NUM_VAL_IMGS) * 5 // 3,
        },
    ]
    for split_info in collection:
        if args["num_workers"] > 1:
            data_triplets = merge_dialog_wrapper(
                split_info["source"], split_info["num_dialogs"], args
            )
        else:
            data_triplets = merge_dialogs(
                split_info["source"], split_info["num_dialogs"]
            )
        # Save JSON files.
        save_path = os.path.join(
            args["save_root"], "deep_clevr_dialog_{}.json".format(split_info["split"])
        )
        print("Saving triplets: {}".format(save_path))
        with open(save_path, "w") as file_id:
            json.dump(data_triplets, file_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--clevr_train_json", default=None, help="Path to CLEVR-Dialog train"
    )
    parser.add_argument(
        "--clevr_val_json", default=None, help="Path to CLEVR-Dialog val"
    )
    parser.add_argument("--save_root", default=None, help="Path to save the files")
    parser.add_argument(
        "--num_workers", type=int, default=4, help="Number of workers to merge"
    )

    try:
        parsed_args = vars(parser.parse_args())
    except (IOError) as msg:
        parser.error(str(msg))
    generate_dataset(parsed_args)
