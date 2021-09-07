#! /usr/bin/env python
"""
Copyright (c) Facebook, Inc. and its affiliates.
All rights reserved.

This source code is licensed under the license found in the
LICENSE file in the root directory of this source tree.

Computes the dependency between turns in stitched dialog, using source dialog.

Author(s): Satwik Kottur
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import json
import numpy as np


def main(args):
    print("Saving: {}".format(args["input_clevr_path"]))
    with open(args["input_clevr_path"]) as file_id:
        data = json.load(file_id)
    clevr = {}
    for datum in data:
        key = datum["image_filename"]
        for dialog_index, dialog_datum in enumerate(datum["dialogs"]):
            key = "{}_{}".format(datum["image_filename"], dialog_index)
            clevr[key] = dialog_datum

    print("Saving: {}".format(args["input_deep_clevr_path"]))
    with open(args["input_deep_clevr_path"]) as file_id:
        deep_data = json.load(file_id)

    NUM_CONTEXTS = 3
    clevr_lens = []
    deep_clevr_lens = []
    for dialog_datum in deep_data:
        # Deep index to original index map.
        index_map = {}
        index_counts = [0] * NUM_CONTEXTS
        # CLEVR-Dialog data for each contexts.
        context_data = {
            ii: clevr[
                "{}_{}".format(
                    dialog_datum["image_filename"][ii], dialog_datum["dialog_index"][ii]
                )
            ]
            for ii in range(NUM_CONTEXTS)
        }

        # Construct mapping between CLEVR-Dialog and CLEVR-Dialog+.
        for index, datum in enumerate(dialog_datum["data"]):
            context_index = datum["context_index"]
            index_map[index] = (context_index, index_counts[context_index])
            index_counts[context_index] += 1
        reverse_index_map = {
            context_index: [
                (deep_index, mm[1])
                for deep_index, mm in index_map.items()
                if mm[0] == context_index
            ]
            for context_index in range(NUM_CONTEXTS)
        }

        # Go through each datum and map dependence lengths.
        for index, datum in enumerate(dialog_datum["data"]):
            context_index = datum["context_index"]
            clevr_datum = context_data[context_index]
            if "caption" in datum:
                continue

            history_item = clevr_datum["graph"]["history"][index_map[index][1]]
            focus_id = history_item.get("dependence", None)
            if focus_id is None:
                continue
            deep_focus_id = reverse_index_map[context_index][focus_id + 1][0]

            clevr_lens.append(index_map[index][1] - 1 - focus_id)
            deep_clevr_lens.append(index - deep_focus_id)
            assert clevr_lens[-1] <= deep_clevr_lens[-1], "Something wrong!"
    print(np.mean(clevr_lens))
    print(np.mean(deep_clevr_lens))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input_clevr_path", default=None, help="JSON CLEVR-Dialog file"
    )
    parser.add_argument(
        "--input_deep_clevr_path", default=None, help="JSON Deep CLEVR-Dialog file"
    )
    try:
        parsed_args = vars(parser.parse_args())
    except (IOError) as msg:
        parser.error(str(msg))
    main(parsed_args)
