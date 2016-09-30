#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This code uses the iterative parsing to process the map file and
find out not only what tags are there, but also how many, to get the
feeling on how much of which data we can expect to have in the map.

The output is a dictionary with the tag name as the key
and number of times this tag can be encountered in the map as value.
"""

import xml.etree.ElementTree as ET
import pprint

def count_tags(filename):
    tags = {}
    # iterative parsing
    for event, elem in ET.iterparse(filename):
        tag_name = elem.tag
        # if the tag exsits, increment the counter
        if tag_name in tags:
            tags[tag_name] = tags[tag_name]+ 1
        # if not, add the tag in the dictionary
        else:
            tags[tag_name] = 1
    return tags


if __name__ == "__main__":
    # count tags
    tags = count_tags('example.osm')
    # print results
    pprint.pprint(tags)
