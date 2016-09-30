#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This file checks the "k" value for each "<tag>" and see if they can be valid keys in MongoDB,
as well as see if there are any other potential problems.

We use 3 regular expressions to check for certain patterns in the tags.
We would like to see if we have tags like "addr:street", "name:en" and
if we have any tags with problematic characters.
"""
import xml.etree.ElementTree as ET
import pprint
import re

#regular expression
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

def key_type(element, keys):
    # check for tag element
    if element.tag == "tag":
        # get key 
        k = element.attrib["k"]
        # count for lower cases
        if re.search(lower, k):
            keys["lower"] =  keys["lower"] + 1
        # count for lower colon cases
        elif re.search(lower_colon, k):
            keys["lower_colon"] =  keys["lower_colon"] + 1
        # count for problem character cases
        elif re.search(problemchars, k):
            keys["problemchars"] =  keys["problemchars"] + 1
        # count for all other cases
        else:
            keys["other"] =  keys["other"]+ 1
            
    return keys

def process_map(filename):
    # initialise the keys dictionary
    keys = {"lower": 0,
            "lower_colon": 0,
            "problemchars": 0,
            "other": 0}
    # iterative parsing
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)

    return keys   

if __name__ == "__main__":
    # process the osm map
    keys = process_map('example.osm')
    # print the results
    pprint.pprint(keys)
