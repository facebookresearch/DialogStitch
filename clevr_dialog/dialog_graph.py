#! /usr/bin/env python
"""Copyright (c) Facebook, Inc. and its affiliates.
All rights reserved.

This source code is licensed under the license found in the
LICENSE file in the root directory of this source tree.

Class structure for a dialog graph.

Author(s): Satwik Kottur
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import collections
import copy


class DialogGraph:
    def __init__(self):
        self.current_graph = self.get_empty_graph()
        self.turn_graphs = [self.current_graph]

    def get_empty_graph(self):
        """Generate an empty scene graph.
        """
        default_list = lambda: collections.defaultdict(list)
        graph = {
            "relationships": collections.defaultdict(default_list),
            "counts": {},
            "exists": {},
            "history": [],
            "objects": {},
        }
        return graph

    # Adapted from:
    # https://github.com/satwikkottur/clevr-dialog/blob/master/clevr_utils.py
    def merge_update_scene_graph(self, graph_item):
        """Merges two scene graphs into one.

        Args:
            graph_item: New graph item to add to the scene graph

        Returns:
            graph: Deep copy of the original scene graph after merging
        """
        graph = copy.deepcopy(self.current_graph)
        # Local alias.
        objects = graph["objects"]

        # If not mergeable, return the same scene graph.
        if not graph_item["mergeable"]:
            self.turn_graphs.append(graph)
            self.current_graph = graph

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
        self.turn_graphs.append(graph)
        self.current_graph = graph

    def get_known_attributes(self, graph):
        """Extract known attributes from a graph.
        """
        known_objs = graph["objects"]
        known_attrs = set()
        for obj_id, obj_attrs in known_objs.items():
            # NOTE: Fix this later.
            for attr_key in ("shape", "size", "material", "color"):
                known_attrs.add(obj_attrs.get(attr_key, "N/A"))
        # Remove N/A.
        if "N/A" in known_attrs:
            known_attrs.remove("N/A")
        return known_attrs


if __name__ == "__main__":
    pass
