from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
from collections import OrderedDict

import yaml
import yamlordereddictloader
from maya import cmds

SHELVES = [
    "Curves",
    "Surfaces",
    "Polygons",
    "Sculpting",
    "UVEditing",
    "Rigging",
    "Animation",
    "Rendering",
    "FX",
]


def gen(path):
    tab = OrderedDict()
    tab["name"] = "maya"
    tab["load"] = True
    tab["categories"] = []

    for shelf in SHELVES:
        category = OrderedDict()
        category["name"] = shelf
        category["open"] = True
        category["commands"] = []
        tab["categories"].append(category)

        for child in cmds.shelfLayout(shelf, query=True, childArray=True):
            if "separator" in child:
                continue

            label = cmds.shelfButton(
                child,
                query=True,
                label=True,
            )
            image = cmds.shelfButton(
                child,
                query=True,
                image=True,
            )
            command = cmds.shelfButton(
                child,
                query=True,
                command=True,
            )
            options = cmds.shelfButton(
                child,
                query=True,
                doubleClickCommand=True,
            )

            if not hasattr(cmds, command):
                continue

            cmd = OrderedDict()
            category["commands"].append(cmd)

            if not os.path.exists(image):
                image = ":{}".format(image)

            cmd["name"] = label
            cmd["callback"] = "maya.cmds:{}".format(command)
            cmd["icon"] = image

            if options and hasattr(cmds, options):
                menu = OrderedDict()
                cmd["menu"] = menu
                menu["items"] = []

                item = OrderedDict()
                menu["items"].append(item)
                item["name"] = "Options"
                item["callback"] = "maya.cmds:{}".format(options)

    with open(path, "w") as f:
        yaml.dump(
            tab,
            f,
            Dumper=yamlordereddictloader.Dumper,
            default_flow_style=False,
        )
