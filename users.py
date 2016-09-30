#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file finds out how many unique users
have contributed to the map in this particular area!

The function process_map returns a set of unique user IDs ("uid")
"""
import xml.etree.ElementTree as ET
import pprint
import re

def get_user(element):
    uid = None
    # get the uid value from node, way and relation tags
    if (element.tag == "node") or (element.tag == "way") or (element.tag == "relation"):
            uid = element.attrib["uid"]
    return uid


def process_map(filename):
    users = set()
    # iterative parsing
    for _, element in ET.iterparse(filename):
        user = get_user(element)
        if user != None:
            users.add(user)
        
    return users


if __name__ == "__main__":
    # find users
    users = process_map('example.osm')
    # print results
    pprint.pprint(users)
