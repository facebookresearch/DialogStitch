#! /usr/bin/env python
"""Copyright (c) Facebook, Inc. and its affiliates.
All rights reserved.

This source code is licensed under the license found in the
LICENSE file in the root directory of this source tree.

Class structure for a dialog.

Author(s): Satwik Kottur
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import copy
import itertools
import random

from dialog_graph import DialogGraph


class Dialog:
    def __init__(self, dialog_bundle, index):
        # Add attributes.
        for key in ("image_filename", "image_index", "split"):
            setattr(self, key, dialog_bundle[key])
        self.data = dialog_bundle["dialogs"][index]
        self.dialog_index = index
        self.context_recaller = []
        self.dialog_graph = DialogGraph()

    def add_context_index(self, index):
        """Adds index to turns of the dialog.

        Args:
            index: Context index to add for each turn
        """
        for datum in self.data["dialog"]:
            datum["context_index"] = index

    def clear_context_index(self):
        """Deletes index to turns of the dialog.
        """
        for datum in self.data["dialog"]:
            del datum["context_index"]

    def segment_dialog(self):
        """Segment the dialog based on dependencies.

        Identify following types of questions:
        (a) Context recaller
        (b) Independent questions
        """
        # Update the graphs.
        for round_id, round_datum in enumerate(self.data["graph"]["history"]):
            self.dialog_graph.merge_update_scene_graph(round_datum)

        focus_attrs = []
        dialog_history = self.data["graph"]["history"]
        for round_id, round_datum in enumerate(self.data["dialog"]):
            # Context recaller.
            template = round_datum["template"]
            if "early" in template and "sim" not in template:
                # Ignore the first round.
                if round_id == 0:
                    continue
                # Check known attributes.
                turn_graph = self.dialog_graph.turn_graphs[round_id + 1]
                known_attrs = self.dialog_graph.get_known_attributes(turn_graph)
                focus_attrs = [
                    ii["focus_desc"]
                    for ii in dialog_history[: round_id + 2]
                    if "focus_desc" in ii
                ]
                all_focus_attrs = set(
                    ii[jj]
                    for ii in focus_attrs
                    if ii is not None
                    for jj in ii["required"]
                )
                new_context_datum = {
                    "round_id": round_id,
                    "known_attrs": copy.deepcopy(known_attrs),
                    "focus_attrs": copy.deepcopy(all_focus_attrs),
                    "turn_focus_attrs": dialog_history[round_id + 1]["focus_desc"],
                }
                self.context_recaller.append(new_context_datum)

    @staticmethod
    def check_mergeability(first_dialog, second_dialog, third_dialog=None):
        """Check if a dialog is mergeable with self.

        Args:
            first_dialog, second_dialog, third_dialog: the sequence of dialogs
        """
        dialogs = (first_dialog, second_dialog)
        if third_dialog is not None:
            dialogs += (third_dialog,)

        focus = [dd.context_recaller[-1]["focus_attrs"] for dd in dialogs]
        known = [dd.context_recaller[-1]["known_attrs"] for dd in dialogs]
        compatible = True
        for id1, id2 in itertools.permutations(range(len(dialogs)), 2):
            compatible = compatible and len(known[id1].intersection(focus[id2])) == 0
        if compatible:
            Dialog.merge_dialogs(*dialogs)
        return compatible

    @staticmethod
    def merge_dialogs(*dialogs):
        """Merging dialogs (two or three at a time).
        """
        if len(dialogs) == 2:
            merged_data = Dialog.merge_two_dialogs(*dialogs)
        elif len(dialogs) == 3:
            merged_data = Dialog.merge_three_dialogs(*dialogs)
        else:
            raise ValueError("Dialogs need to be of length 2 or 3!")

        # Get the merged dialog.
        merged_dialog = {"data": merged_data}
        for key in ("image_filename", "image_index", "split", "dialog_index"):
            merged_dialog[key] = [getattr(dd, key) for dd in dialogs]
        return merged_dialog

    @staticmethod
    def merge_two_dialogs(first_dialog, second_dialog, merge_type="ABAB"):
        """Merging two dialogs that are compatible.

        Args:
            first_dialog, second_dialog: the sequence of dialogs (A, B)
            merge_type: One of the ABA or ABAB merge types
        """
        if merge_type == "ABA":
            # A-B-A stitching.
            first_split = random.choice(first_dialog.context_recaller)
            second_split = None
        elif merge_type == "ABAB":
            # A-B-A-B stitching.
            first_split = random.choice(first_dialog.context_recaller)
            second_split = random.choice(second_dialog.context_recaller)
        else:
            raise ValueError("Mergetype invalid!")

        # Add dialog indices.
        first_dialog.add_context_index(0)
        second_dialog.add_context_index(1)
        new_dialog = [{"context_index": 0, "caption": first_dialog.data["caption"]}]
        new_dialog.extend(first_dialog.data["dialog"][: first_split["round_id"]])
        new_dialog.append(
            {"context_index": 1, "caption": second_dialog.data["caption"]}
        )
        if second_split is None:
            new_dialog.extend(second_dialog.data["dialog"])
        else:
            new_dialog.extend(second_dialog.data["dialog"][: second_split["round_id"]])
        new_dialog.extend(first_dialog.data["dialog"][first_split["round_id"] :])
        if second_split is not None:
            new_dialog.extend(second_dialog.data["dialog"][second_split["round_id"] :])
        new_dialog = copy.deepcopy(new_dialog)
        # Remove dialog indices.
        first_dialog.clear_context_index()
        second_dialog.clear_context_index()
        # Debug.
        # print(Dialog.print_merged_dialog(new_dialog))
        return new_dialog

    @staticmethod
    def merge_three_dialogs(first_dialog, second_dialog, third_dialog):
        """Merging three dialogs that are compatible.

        Args:
            first_dialog, second_dialog, third_dialog: the sequence of dialogs
        """
        dialogs = {0: first_dialog, 1: second_dialog, 2: third_dialog}
        splits = {
            ii: random.choice(dd.context_recaller)["round_id"]
            for ii, dd in dialogs.items()
        }
        # Add dialog indices.
        for index, dialog in dialogs.items():
            dialog.add_context_index(index)

        seen_dialogs = []
        new_dialog = []
        # Randomly select a dialog.
        current_id = -1
        while len(seen_dialogs) < 6:
            candidate_ids = [
                ii
                for ii in dialogs
                if (ii != current_id and seen_dialogs.count(ii) < 2)
            ]
            if len(candidate_ids) > 0:
                current_id = random.choice(candidate_ids)

            if current_id not in seen_dialogs:
                new_dialog.append(
                    {
                        "context_index": current_id,
                        "caption": dialogs[current_id].data["caption"],
                    }
                )
                new_dialog.extend(
                    dialogs[current_id].data["dialog"][: splits[current_id]]
                )
            else:
                new_dialog.extend(
                    dialogs[current_id].data["dialog"][splits[current_id] :]
                )
            seen_dialogs.append(current_id)

        new_dialog = copy.deepcopy(new_dialog)
        # Remove dialog indices.
        for index, dialog in dialogs.items():
            dialog.clear_context_index()
        # Debug.
        # print(Dialog.print_merged_dialog(new_dialog))
        return new_dialog

    @staticmethod
    def print_merged_dialog(merged_dialog):
        """Prints the merged dialog.

        Args:
            merged_dialog: Dialog after stitching
        """
        string = "-" * 80 + "\n"
        string += "\n".join(merged_dialog["image_filename"]) + "\n"
        for turn in merged_dialog["data"]:
            if "question" in turn:
                string += "({}) Q: {}\n\t[A: {}] [{}]\n".format(
                    turn["context_index"],
                    turn["question"],
                    turn["answer"],
                    turn["template"],
                )
            else:
                string += "({}) C: {}\n".format(turn["context_index"], turn["caption"])
        string += "\n" + "-" * 80 + "\n"
        return string

    def print_dialog(self, show_history=False):
        string = "-" * 80 + "\n"
        string += "C: {}\n".format(self.data["caption"])
        string += "\t{}\n".format(self.data["graph"]["history"][0])
        for round_id, ii in enumerate(self.data["dialog"]):
            string += "Q-{}: {}\n\t[A: {}] [{}]\n".format(
                round_id, ii["question"], ii["answer"], ii["template"]
            )
            if show_history:
                string += "\t{}\n".format(self.data["graph"]["history"][round_id + 1])
        string += "\n" + "-" * 80 + "\n"
        return string

    def __str__(self, show_history=False):
        string = "-" * 80 + "\n"
        string += "C: {}\n".format(self.data["caption"])
        for round_id, ii in enumerate(self.data["dialog"]):
            string += "Q-{}: {}\n\t[A: {}] [{}]\n".format(
                round_id, ii["question"], ii["answer"], ii["template"]
            )
            if show_history:
                string += "\t{}\n".format(self.data["graph"]["history"][round_id + 1])
        string += "\n" + "-" * 80 + "\n"
        return string


if __name__ == "__main__":
    pass
