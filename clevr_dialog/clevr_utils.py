#! /usr/bin/env python
"""
Copyright (c) Facebook, Inc. and its affiliates.
All rights reserved.

This source code is licensed under the license found in the
LICENSE file in the root directory of this source tree.

Utilities to stitch CLEVR-Dialog instances.

Author(s): Satwik Kottur
"""

from __future__ import absolute_import, division, print_function, unicode_literals
import argparse


def pretty_print_dialog(dialog):
    """Pretty prints generated dialogs.

    Args:
        dialog: Generated dialog to print
    """
    for dialog in dialog_datum["dialogs"]:
        print(dialog["caption"])
        for round_id, ii in enumerate(dialog["dialog"]):
            coref_id = dialog["graph"]["history"][round_id + 1]["dependence"]
            in_tuple = (
                round_id,
                ii["question"],
                str(ii["answer"]),
                ii["template"],
                str(coref_id),
            )
            print("\t[Q-%d: %s] [A: %s] [%s] [%s]" % in_tuple)


def merge_update_scene_graph(orig_graph, graph_item):
    """Merges two scene graphs into one.

    Args:
        orig_graph: Original scene graph
        graph_item: New graph item to add to the scene graph

    Returns:
        graph: Deep copy of the original scene graph after merging
    """
    graph = copy.deepcopy(orig_graph)
    # Local alias.
    objects = graph["objects"]

    # If not mergeable, return the same scene graph.
    if not graph_item["mergeable"]:
        return graph

    # 1. Go through each new object
    # 2. Find its batch in objects
    #   a. If found, assert for a clash of attributes, update
    #   b. If novel, just add the object as is
    for new_obj in graph_item["objects"]:
        match_found = False
        obj = objects.get(new_obj["id"], None)

        if obj:
            # Assert for existing entries.
            for attr in new_obj:
                try:
                    assert new_obj[attr] == obj.get(
                        attr, new_obj[attr]
                    ), "Some of the attributes do not match!"
                except:
                    pdb.set_trace()

            # Add additional keys.
            objects[new_obj["id"]].update(new_obj)
        else:
            # Add the new object.
            objects[new_obj["id"]] = new_obj

    # if a relation, update it
    if "relation" in graph_item:
        rel = graph_item["relation"]
        ## update it with object 2 id
        id1 = graph_item["objects"][0]["id"]
        id2 = graph_item["objects"][1]["id"]
        rel_objs = graph["relationships"][rel][id1]
        rel_objs.append(id2)
        graph["relationships"][rel][id1] = rel_objs

    # update objects in graph
    graph["objects"] = objects
    return graph
