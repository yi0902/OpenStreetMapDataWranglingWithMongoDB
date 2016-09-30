#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file is to wrangle the data and transform the shape of the data
into the model. The output should be a list of dictionaries
that look like this:

{
"id": "2406124091",
"type: "node",
"visible":"true",
"created": {
          "version":"2",
          "changeset":"17206049",
          "timestamp":"2013-08-03T16:43:42Z",
          "user":"linuxUser16",
          "uid":"1219059"
        },
"pos": [41.9757030, -87.6921867],
"address": {
          "housenumber": "5157",
          "postcode": "60625",
          "street": "North Lincoln Ave"
        },
"name": {
           "main" : "新白鹿酒店 New White Deer Restaurant",
           "en" : "New White Deer Restaurant",
           "zh" : "新白鹿酒店"
        },
"amenity": "restaurant",
"cuisine": "mexican",
"phone": "1 (773)-271-5176"
}

****Following things will be done for reshapping*************

- process only 2 types of top level tags: "node" and "way"
- all attributes of "node" and "way" will be turned into regular key/value pairs, except:
    - attributes in the CREATED array will be added under a key "created"
    - attributes for latitude and longitude will be added to a "pos" array,
      for use in geospacial indexing. The values inside "pos" array are floats
      and not strings. 
- if second level tag "k" value contains problematic characters, it will be ignored
- if second level tag "k" value starts with "addr:", it will be added to a dictionary "address"
- if second level tag "k" value starts with "name:", it will be added to a dictionary "name"
- if second level tag "k" value does not start with "addr:" or "name:",
  but contains ":", process it same as any other tag.
- if there is a second ":" after "addr:" or "name:", the tag will be ignored
- if second level tag "v" value for "name:zh" doesn't contain Chinese, the tag will be ignored
- if second level tag "v" value for "addr:city" isn't Shanghai, the tag will be ignored
- if second level tag "v" value for "addr:postcode" doesn't a number of 6 characters, the tag will be ignored
- for "way" specifically:
  <nd ref="305896090"/>
  <nd ref="1719825889"/>
  will be turned into "node_refs": ["305896090", "1719825889"]

****Following things will be done for updating certain values*****
- for name:en: update the street type and direction type to the expected ones
- for addr:city: if expected value is one part of the city value, set the city value to expected one
- for addr:street:
    if the value contain numbers, if the value contains Chinese,
        set the value to the part before number, if the value contains English,
        set the value to the part after number. For example:
            浦建路207弄 => 浦建路
            NO.588 binhe road => binhe road
    update the street type and direction type to the expected ones
- for addr:housenumber:
    if the value is of format numbers;numbers or numbers～numbers, set it to numbers-numbers
    if the value is of format numbersChineseCharacters, set it to just numbers
    for other formats, ignore the tag

"""

import xml.etree.ElementTree as ET
import pprint
import re
import codecs
import json
import string
import io

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problem_char_re = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
chinese_char_re = re.compile(ur'[\u4e00-\u9fff]+')
street_type_re = re.compile(r'\S+[\.?|\D]$', re.IGNORECASE)
number_re = re.compile(r'\d+\-*\d*')
number_to_update_re = re.compile(r'\d+[;|～]\d+')
number_chinese_re = re.compile(ur'\d+[\u4e00-\u9fff]+')

mapping = { "St": "Street",
            "St.": "Street",
            "Ave" : "Avenue",
            "Ave." : "Avenue",
            "Rd" : "Road",
            "Rd." : "Road",
            "road" : "Road",
            "Lu" : "Road",
            "Hwy." : "Highway",
            "highway" : "Highway",
            "(N.)" : "North",
            "(S.)" : "South",
            "(E.)" : "East",
            "(W.)" : "West",
            "(N)" : "North",
            "(S)" : "South",
            "(E)" : "East",
            "(W)" : "West"}

expected_street = ["Street", "Avenue", "Boulevard", "Drive", "Court",
                   "Place", "Square", "Lane", "Road", "Trail",
                   "Parkway", "Commons", "Highway"]
expected_direction = ["North", "South", "East", "West"]
expected_city = ["上海".decode('utf-8'), "Shanghai"]

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]

def shape_element(element):

    node = {}
    
    # Treat only node & way tags
    if element.tag == "node" or element.tag == "way" :
        
        node["created"] = {}
        for attr in element.attrib:
            # Set value for id
            if attr == "id":
                node["id"] = element.attrib["id"]
            # Set value for visible
            if attr == "visible":
                node["visible"] = element.attrib["visible"]
            # Set value for created
            if attr in CREATED:
                node["created"][attr] = element.attrib[attr]

        # Set address & name values
        process_address_and_name(node, element)

        if element.tag == "node":
            # Set tag type
            node["type"] = "node"
            # Set position for node tag
            node["pos"] = [float(element.attrib["lat"]), float(element.attrib["lon"])]
        else:
            # Set tag type
            node["type"] = "way"
            # Set node references for way tag
            node["node_refs"] = process_refs(element)
            
        return node
    else:
        return None

def process_address_and_name(node, element):

    address = {}
    name = {}
    
    for tag in element.iter("tag"):
        k = tag.attrib["k"]
        v = tag.attrib["v"]
        if re.search(problem_char_re, k):
            continue
        if len(k.split(":")) > 2:
            continue
        if k.startswith("addr:"):
            key = k[5:]
            # Process address items
            v = process_address(key, v)
            # If not None, set the value
            if v:
                address[key] = v
        elif k.startswith("name:"):
            key = k[5:]
            # Process name items
            v = process_name(key, v)
            # If not None, set the value
            if v:
                name[key] = v
        elif k == "name":
            name["main"] = v
        else:
            node[k] = v
            
    # Assign address and name values 
    if len(address) != 0:
        node["address"] = address
    if len(name) != 0:
        node["name"] = name

def process_address(key, value):

    ######## Treat city #####################
    if key == "city":
        if value not in expected_city:
            is_updated = False
            # Loop on each expected city name
            for city in expected_city:
                # If one part of the value is the expected city name
                if city in value:
                    # Set the value equal to expected city name
                    #print "City before : " + value
                    value = city
                    is_updated = True
                    #print "City after : " + value
            # If value doesn't have relation with the expected city name
            # return None
            if not is_updated:
                value = None

    ####### Treat street type ################
    if key == "street":
        m = re.search(number_re, value)
        # If numbers found
        if m:
            number = m.group()
            # If can find Chinese
            if re.search(chinese_char_re, value):
                # Set the value equal to the part before the numbers
                #print "Chinese street before : " + value
                value = value.split(number)[0]
                #print "Chinese street after : " + value
            else:
                # Set the value equal to the part after the numbers
                #print "English street before : " + value
                value = value.split(number)[1].strip()
                #print "English street after : " + value

        # Treat the street type     
        m = re.search(street_type_re, value)
        if m:
            street_type = m.group()
            # Update the street type or direction
            if street_type in mapping:
                value = value.replace(street_type, mapping[street_type])
            
    ####### Treat postcode ###################
    if key == "postcode":
        m = re.search(number_re, value)
        if m:
            postcode = m.group()
            # If found numbers isn't of length 6
            if len(postcode) != 6:
                value = None
            else:
                # Set the value to postcode found
                # For example : 200100 Shanghai => 200100
                #print "Postcode before : " + value
                value = postcode
                #print "Postcode after : " + value
        # If no numbers found
        else:
            value = None

    ####### Treat housenumber ################
    if key == "housenumber":
        m = re.search(number_re, value)
        if m:
            number = m.group()
            # If the number found is just a part of the value
            if number != value:
                is_updated = False
                # Check if the value is of format numbers;numbers or numbers～numbers
                m = re.search(number_to_update_re, value)
                if m:
                    # Update the value to format numbers-numbers
                    #print "Housenumber before : " + value
                    value = value.replace(";", "-")
                    value = value.replace("～", "-")
                    is_updated = True
                    #print "Housenumber after : " + value
                # Check if the value is of format numbersChineseCharacters
                if re.search(number_chinese_re, value):
                    #print "Housenumber before : " + value
                    value = number
                    is_updated = True
                    #print "Housenumber after : " + value
                # If is not of above two types, return None
                if not is_updated:
                    value = None
        # If no numbers found
        else:
            value = None
                  
    return value

def process_name(key, value):
    if key == "zh":
        # If no Chinese character found, return None
        if not re.search(chinese_char_re, value):
            value = None
    elif key == "en":
        m = re.search(street_type_re, value)
        if m:
            street_type = m.group()
            # Update the street type or direction
            if street_type in mapping:
                #print "Name english before : " + value
                value = value.replace(street_type, mapping[street_type])
                #print "Name english after : " + value
    # For other types of language, no treatment
    return value

def process_refs(element):
    refs = []
    for tag in element.iter("nd"):
        refs.append(tag.attrib["ref"])
    return refs
    
def process_map(file_in):
    # Define output file
    file_out = "{0}.json".format(file_in)
    data = []
    # Iterative parsing
    with io.open(file_out, "w", encoding="utf8") as fo:
        for _, element in ET.iterparse(file_in):
            # Adapt the element to model
            el = shape_element(element)
            if el:
                data.append(el)
                # Make sure the Chinese characters can be correctly written
                jdata = unicode(json.dumps(el, ensure_ascii=False))
                fo.write(jdata + "\n")
    return data


if __name__ == "__main__":
    data = process_map('example.osm')
    #pprint.pprint(data)
