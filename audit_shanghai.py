#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
In this file, we will audit:

For the "name" part :
- "name:en" : check if its value contains Chinese characters.
              check if the street type or direction (north, south...) inside 
              the name is in the expected lists.
- "name:zh" : check if its value contains alphabetic letters.

For the "address" part:
- "addr:city" : check if the city is Shanghai 
- "addr:street" : check if it contains numbers. If there are numbers,
                  maybe the value is not a street, but street + housenumber
- "addr:postcode" : check if the value is only numbers and be length of 6
                    (all Chinese postcode is composed of 6 numbers)
- "addr:housenumber" : check if the value contains only numbers or
                       in format of numbers-numbers

"""
import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

# REGULAR EXPRESSIONS
street_type_re = re.compile(r'\S+[\.?|\D]$', re.IGNORECASE)
chinese_char_re = re.compile(ur'[\u4e00-\u9fff]+')
number_re = re.compile(r'\d+\-*\d*')
alphabet_re = re.compile(r'[a-zA-Z]+')

expected_street = ["Street", "Avenue", "Boulevard", "Drive", "Court",
                   "Place", "Square", "Lane", "Road", "Trail",
                   "Parkway", "Commons", "Highway", "Expressway"]
expected_direction = ["North", "South", "East", "West"]
expected_city = ["上海".decode('utf-8'), "Shanghai"]

########################### CHECK FUNCTIONS ################################
def is_street(elem):
    return (elem.attrib["k"] == "addr:street")

def is_city_name(elem):
    return (elem.attrib["k"] == "addr:city")

def is_postcode(elem):
    return(elem.attrib["k"] == "addr:postcode")

def is_housenumber(elem):
    return(elem.attrib["k"] == "addr:housenumber")

def is_name_en(elem):
    return(elem.attrib["k"] == "name:en")

def is_name_zh(elem):
    return(elem.attrib["k"] == "name:zh")

########################### AUDIT FUNCTIONS ################################

def audit_name_zh(pb_names_zh, name_value):
    m = chinese_char_re.search(name_value)
    # if can find chinese characters
    if m:
        # check if can find letters
         m = alphabet_re.search(name_value)
         if m:
             pb_names_zh[name_value].add(name_value)
    # if no chinese characters
    else:
        pb_names_zh[name_value].add(name_value)
   
def audit_name_en(pb_names_en, name_value):
    m = chinese_char_re.search(name_value)
    # if can find chinese characters
    if m:
        pb_names_en[name_value].add(name_value)
    else:
    # if no chinese characters, check the street type and direction
        m = street_type_re.search(name_value)
        if m:
            street_type = m.group()
            if (street_type not in expected_street) and (street_type not in expected_direction):
                pb_names_en[street_type].add(name_value)

def audit_city(pb_cities, city_name):
    if city_name not in expected_city:
        pb_cities[city_name].add(city_name)
    

def audit_street(pb_streets, street_name):
    m = number_re.search(street_name)
    if m:
        pb_streets[street_name].add(street_name)
            
def audit_postcode(pb_postcodes, postcode_value):
    m = number_re.search(postcode_value)
    if m:
        number = m.group()
        if (number != postcode_value) or (len(number) != 6):
            pb_postcodes[postcode_value].add(postcode_value)

def audit_housenumber(pb_housenumbers, housenumber_value):
    m = number_re.search(housenumber_value)
    if m:
        number = m.group()
        if (number != housenumber_value) :
            pb_housenumbers[housenumber_value].add(housenumber_value)
    
        
def audit(osmfile):
    # open osm file
    osm_file = open(osmfile, "r")
    # initialize dictionaries
    pb_names_zh = defaultdict(set)
    pb_names_en = defaultdict(set)
    pb_cities = defaultdict(set)
    pb_streets = defaultdict(set)
    pb_postcodes = defaultdict(set)
    pb_housenumbers = defaultdict(set)
    
    # iterative parsing
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way" :
            for tag in elem.iter("tag"):
                # audit name:zh
                if is_name_zh(tag):
                    audit_name_zh(pb_names_zh, tag.attrib["v"])
                # audit name:en
                if is_name_en(tag):
                    audit_name_en(pb_names_en, tag.attrib["v"])
                # audit city
                if is_city_name(tag):
                    audit_city(pb_cities, tag.attrib["v"])
                # audit street name
                if is_street(tag):
                    audit_street(pb_streets, tag.attrib["v"])
                # audit postcode
                if is_postcode(tag):
                    audit_postcode(pb_postcodes, tag.attrib["v"])
                # audit housenumber
                if is_housenumber(tag):
                    audit_housenumber(pb_housenumbers, tag.attrib["v"])
        
                    
    # print results
    print "######## Problem Names in Chinese ###########"
    for name in pb_names_zh:
        print name
    print "######## Problem Names in English ###########"
    for name in pb_names_en:
        print name 
    print "######## Problem Cities #####################"
    for city in pb_cities:
        print city 
    print "######## Problem Streets #########"
    for street in pb_streets:
        print street 
    print "######## Problem Postcodes ##################"
    for postcode in pb_postcodes:
        print postcode
    print "######## Problem Housenumbers ###############"
    for housenumber in pb_housenumbers:
        print housenumber

if __name__ == '__main__':
    st_types = audit("example.osm")

