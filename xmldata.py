#!/usr/bin/env python
#-*- coding: utf-8 -*-
# xmldata.py
# From local machine, run Graph_Builder("[metadata-files-location","Program")
# [Provide location of metadata files and key by which to organize comparison: here, that will always be "Program"]
# Run g = Graph_Builder("[metadata-files-location","Program") at the python shell to work with the
# graph object g.

from __future__ import division
import os
import json
from lxml import etree
import requests
import networkx as nx
from networkx.readwrite import json_graph 
import itertools
from pprint import pprint
from msu_programs import College_Sort
from pclean import Program_Clean
from repo import get_pid, repo_connect

# The list of dictionaries (data_list) should have one dictionary for each program.
# This function checks to see whether a new program dictionary exists or not, then, if it does,
# combines the new dictionary with the old one.

def dict_update(xml_dict, program, data_list):
    if not any (d["Program"] == program for d in data_list):
        data_list.append(xml_dict)
    else:
        for dictionary in data_list:
            if dictionary["Program"] == program:
                for item in dictionary:
                    if item == "Program":
                        pass
                    else:
                        if item in xml_dict:
                            dictionary[item] = list(set(dictionary[item]) | set(xml_dict[item]))


def Get_Names(tree, xpath):
    r = tree.xpath(xpath)
    names = []
    for i in range(len(r)):
        name = []
        for j in r[i].iterchildren():
            if j.text:
                name.append(j.text)
        full_name = name[0].capitalize() + ", " + name[1].capitalize()
        names.append(full_name) # Some names come back unicode, others not. What to do?
    return names

def Get_Terms(tree, xpath):
    r = tree.xpath(xpath)
    terms = []
    if r[0].text is not None and len(r) == 1 and "," in r[0].text:
        terms = [x.lstrip().capitalize().rstrip() for x in r[0].text.split(',')]
    else:
        for i in range(len(r)):
            terms.append(r[i].text)
    return terms

def MARC_Geo(path, item):
    new_path = path+item.replace("DATA.xml","MARCXML.xml")
    geo = []
    if os.path.exists(new_path):
        path_geo = "/marc:record/marc:datafield[@tag='651']/marc:subfield[@code='a']"
        path_geo_2 = "/marc:record/marc:datafield[@tag='650']/marc:subfield[@code='z']"
        tree = etree.parse(path+item.replace("DATA.xml","MARCXML.xml"))
        r_geo = tree.xpath(path_geo, namespaces={"marc": "http://www.loc.gov/MARC21/slim"})
        for i,j in enumerate(r_geo):
            if r_geo[i] <> None:
                geo.append(str(r_geo[i].text).strip(".").rstrip())
           
        r_geo_2 = tree.xpath(path_geo_2, namespaces={"marc": "http://www.loc.gov/MARC21/slim"})
    	for i,j in enumerate(r_geo_2):
            if r_geo_2[i] <> None:
                geo.append(str(r_geo_2[i].text).strip(".").rstrip())
		    
    return geo


def MARC_Data(path, item):
    new_path = path+item.replace("DATA.xml","MARCXML.xml")
    subjects = []
    path_subject = "/marc:record/marc:datafield[@tag='650']/marc:subfield[@code='a']"
    if os.path.exists(new_path):
        tree = etree.parse(path+item.replace("DATA.xml","MARCXML.xml"))
        r_subjects = tree.xpath(path_subject, namespaces={"marc": "http://www.loc.gov/MARC21/slim"})
    else:
    	# Connect to repository to get MARC XML.
        repo = RepoConnect("Development")
        pid = Get_Pid(item, repo)
        if pid is not None:
        	digital_object = repo.get_object(pid)
        	marc_ds = digital_object.getDatastreamObject("MARCXML")
        	tree = etree.fromstring(marc_ds.content.serialize())
        
        	
        if pid is not None:	
        	r_subjects = tree.xpath(path_subject, namespaces={"marc": "http://www.loc.gov/MARC21/slim"})
        else:
    	   r_subjects = []
    if r_subjects != []:
        for i,j in enumerate(r_subjects):
            if r_subjects[i] <> None:
                subjects.append(str(r_subjects[i].text).strip(".").rstrip())
    return subjects

# Takes parameter called data which should be a list of dictionaries.The "Key" parameter is the dictionary key that uniquely specifies
# each dictionary, and is the basis for comparison.

def GraphBuilder(path, key, json_output=False, output_path=None, repo=None):

    g = nx.Graph()
    dataset = XML_Data(path)
    
    for d in dataset:
    	if "College" in d:
        	g.add_node(d[key], strength=len(d["Authors"]), college=d["College"])
        else:
        	g.add_node(d[key], strength=len(d["Authors"]), college="Not specified")
    combos = itertools.combinations(dataset,2)
    i = 0
    for combo in combos:
        i += 1
        for item in combo[0]:
            if item in combo[0] and item in combo[1] and item <> "Program":
                intersect = set(combo[0][item]).intersection(set(combo[1][item]))
                if list(intersect) <> []:
                    g.add_edge(combo[0]["Program"],combo[1]["Program"],{item: list(intersect)})

    for x,y in g.edges():
        g[x][y]['strength'] = sum(len(v) for v in g[x][y].itervalues())          
    print str(len(g.edges()))+ " connections out of a possible " + str(i)
    print len(g.nodes()), "nodes"
    #for x in g.edges():
    #   print x,g[x][0]]g[x][1]]
    
    if json_output == True:
    	Write_JSON(g, path, output_path)
    
    return g

def translate_to_graph(dataset, key, json_output=False, output_path=None, repo=None):

    g = nx.Graph()
    
    for d in dataset:
        if "College" in d and "Department" in d:
            g.add_node(d[key], strength=len(d["Authors"]), college=d["College"], department=d["Department"])
        elif "College" in d:
            g.add_node(d[key], strength=len(d["Authors"]), college=d["College"], department="Not Specified")

        else:
            g.add_node(d[key], strength=len(d["Authors"]), college="Not Specified", department="Not Specified")          

    combos = itertools.combinations(dataset,2)
    i = 0
    for combo in combos:
        i += 1
        for item in combo[0]:
            if item in combo[0] and item in combo[1] and item <> "Program":
                intersect = set(combo[0][item]).intersection(set(combo[1][item]))
                if list(intersect) <> []:
                    g.add_edge(combo[0]["Program"],combo[1]["Program"],{item: list(intersect)})

    for x,y in g.edges():
        g[x][y]['strength'] = sum(len(v) for v in g[x][y].itervalues())          
    print str(len(g.edges()))+ " connections out of a possible " + str(i)
    print len(g.nodes()), "nodes"
    #for x in g.edges():
    #   print x,g[x][0]]g[x][1]]
    
    if json_output == True:
        Write_JSON(g, output_path)
    
    return g

class SolrData():
    def __init__(self, url):
        self.url = url
        self._RunQuery()
        self.program_dict = {}

    def _RunQuery():
        r = requests.get(self.url)
        if r.ok:
            self.data = r.json()
            self._PrepareData()
        else:
            print "Request failed"

    def _PrepareData():
        documents = self.data["response"]["docs"]
        for doc in documents:
            self._GetSubjects()

    

def XML_Data(path):
    xmlBBList = [item for item in os.listdir(path) if "DATA.xml" in item]

    path_advisor = "/DISS_submission/DISS_description/DISS_advisor/DISS_name"
    path_committee = "/DISS_submission/DISS_description/DISS_cmte_member/DISS_name"
    path_author = "/DISS_submission/DISS_authorship/DISS_author[@type='primary']/DISS_name"
    path_category = "/DISS_submission/DISS_description/DISS_categorization/DISS_category/DISS_cat_desc"
    path_program = "/DISS_submission/DISS_description/DISS_institution/DISS_inst_contact"
    path_keywords = "/DISS_submission/DISS_description/DISS_categorization/DISS_keyword"
  
    college_data = College_Sort()
    

    data_list = []
    
    for item in xmlBBList:
        xml_dict = {}

        tree = etree.parse(path+item)
        r_program = tree.xpath(path_program)
        program = r_program[0].text

        clean_program = Program_Clean(program)
        xml_dict["Program"] = clean_program

        # Call Get_Names function to pull names from XML files and convert them to standard form.        
        xml_dict["Authors"] = Get_Names(tree, path_author)           
        advisors_list = Get_Names(tree, path_advisor)
        committee_list = Get_Names(tree, path_committee)
        xml_dict["Committee/Advisors"] = list(set(advisors_list) | set(committee_list)) 

        # Call Get_Terms function to pull keywords and topics from XML.               
        xml_dict["Topics"] = Get_Terms(tree, path_category)
        keywords = Get_Terms(tree, path_keywords)
        
        if keywords <> [None]:
            xml_dict["Keywords"] = keywords
        # Get subjects from MARC.xml file
        xml_dict["Subjects"] = MARC_Data(path, item)
        
        # Get geographical LCSH from MARC.xml file
        # xml_dict["GeoHeadings"] = MARC_Geo(path, item)
        
        if clean_program in college_data:
        	if college_data[clean_program][0] is not None:
        		xml_dict["Department"] = [college_data[clean_program][1]]
        	if college_data[clean_program][1] is not None:
        		xml_dict["College"] = [college_data[clean_program][0]]
     
            
        dict_update(xml_dict, clean_program, data_list)
    return data_list

def Write_JSON(g, output_path):
    filename = "etddata.json"
    with open(os.path.join(output_path,filename), "w") as f:
        data = json_graph.dumps(g)
        f.write(data)
	print "Wrote file at "+os.path.join(output_path,filename)
           
#    output = open("/Users/higgi135/Documents/etdDataJSON_3", "wb")
#    outputData = json.dumps(etds, indent=4, separators=(',',':'))
#    output.write(outputData)
#    output.close()
#    pprint(etds)
#    print len(data_list)
#    program_list = []
#    for x in data_list:
#        program_list.append(x["Program"])        
#    pprint(sorted(set(program_list)))
#    pprint(data_list)
