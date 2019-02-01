
m __future__ import print_function
from __future__ import division
import os
import json
import argparse
from lxml import etree
import requests
import networkx as nx
from networkx.readwrite import json_graph 
import itertools
from pprint import pprint


class SolrDoc:
    def __init__(self, solr_doc):
        self.solr_doc = solr_doc
        self.solr_metadata = {}

    def BuildRecord(self):
        self.solr_metadata["id"] = self.solr_doc["id"]
        self.solr_metadata["title"] = self.solr_doc["title_label"]
        self.solr_metadata["author"] = self.BuildAuthor()
        self.solr_metadata["date1"] = self.BuildDate("date1")
        self.solr_metadata["date2"] = self.BuildDate("date2")
        self.solr_metadata["added_author"] = self.AddedAuthors()
        self.solr_metadata["series"] = self.GetSeries()
        self.solr_metadata["extent"] = self.GetExtent()
        self.solr_metadata["filename_txt"] = self.TruncateTitle(".txt")
        self.solr_metadata["filename_xml"] = self.TruncateTitle(".xml")

    @staticmethod
    def get_etd_graph_fields():
        """Store and return set of standard fields for etd graph.

        returns:
            graph_fields(dict): return set of standard graph fields.
        """
        graph_fields = {
            "Program": "custom.program_ss",
            "Authors": "dc.creator",
            "Committee/Advisors": "custom.committee_ss",
            "Topics": "custom.category_ss",
            "Keywords": "custom.keyword_ss",
            "Subjects": "custom.subject_ss",
            "FullSubjects": "custom.full_subject_ss",
            "College": "custom.college_ss",
            "Department": "custom.department_ss"
        }
        return graph_fields

    def build_graph_record(self):
        """Select significant fields from solr record.

        returns:
            self.solr_metadata(dict): dictionary of selected solr fields.
        """
        graph_fields = SolrDoc.get_etd_graph_fields()

        for key, value in graph_fields.items():
            if value in self.solr_doc:
                if key == "Program":
                    self.solr_metadata[key] = self.solr_doc[value][0]

                else:
                    self.solr_metadata[key] = self.solr_doc[value]

        return self.solr_metadata

        """
        self.solr_metadata["Program"] = self.solr_doc["custom.program_ss"]
        self.solr_metadata["Authors"] = self.solr_doc["dc.creator"]
        self.solr_metadata["Committee/Advisors"] = self.solr_doc["custom.committee_ss"]
        self.solr_metadata["Topics"] = self.solr_doc["custom.category_ss"]
        self.solr_metadata["Keywords"] = self.solr_doc["custom.keyword_ss"]
        self.solr_metadata["Subjects"] = self.solr_doc["custom.subject_ss"]
        self.solr_metadata["FullSubjects"] = self.solr_doc["custom.full_subject_ss"]
        self.solr_metadata["College"] = self.solr_doc["custom.college_ss"]
        self.solr_metadata["Department"] = self.solr_doc["custom.department_ss"]
        """

    def BuildFullRecord(self):
        self.solr_metadata["id"] = self.solr_doc.get("id", "None")
        self.solr_metadata["title"] = self.solr_doc["title_label"]
        self.solr_metadata["author"] = self.BuildAuthor()
        self.solr_metadata["date1"] = self.BuildDate("date1")
        self.solr_metadata["date2"] = self.BuildDate("date2")
        self.solr_metadata["added_author"] = self.AddedAuthors()
        self.solr_metadata["series"] = self.GetSeries()
        self.solr_metadata["extent"] = self.GetExtent()
        self.solr_metadata["filename_txt"] = self.TruncateTitle(".txt")
        self.solr_metadata["filename_xml"] = self.TruncateTitle(".xml")
        self.solr_metadata["publishing"] = self.GetPublishingValues()
        self.solr_metadata["full_extent"] = self.GetExtentValues()
        self.solr_metadata["oclc_num"] = self.solr_doc.get("oclc_num", "")
        self.solr_metadata["short_title"] = self.BuildTitle()

    def TruncateTitle(self, file_ending):
        """Test to see if title is too long to use as a filename."""
        filename_author = self.solr_metadata["author"]
        if len(filename_author) > 75:
            filename_author = filename_author[:75] + "+"

        self.full_filename = "_".join([filename_author, self.solr_metadata["title"], self.solr_metadata["id"].replace("/", "")])+file_ending
        self.max_length = 200
        if len(self.full_filename) > self.max_length:
            excise_length = len(self.full_filename) - self.max_length
            self.truncated_title = self.solr_metadata["title"][:len(self.solr_metadata["title"])-excise_length-2]
            self.truncated_title += "+"
            self.full_filename = "_".join([filename_author, self.truncated_title, self.solr_metadata["id"].replace("/", "")])+file_ending
        self._MakeFilename()
        return self.new_filename

    def _MakeFilename(self):
        chars = ['/',':','*','?','<','>','|']
        self.new_filename = self.full_filename.translate(dict((ord(c), u'') for c in chars))

    def BuildTitle(self):
        if "marc245b" in self.solr_doc:
            title = " ".join([self.solr_doc["marc245a"][0], self.solr_doc["marc245b"][0]])
        else:
            title = self.solr_doc["marc245a"][0]

        return title

    def AddedAuthors(self):
        added_authors = []
        if "added_authors" in self.solr_doc:
            for aa in self.solr_doc["added_authors"]:
                if aa != "":
                    added_authors.append(aa)

        return added_authors

    def GetFieldValues(self, field):
        values = ""
        if field in self.solr_doc:
            values = self.solr_doc[field]
        return values

    def GetPublishingValues(self):
        pubs = []
        if "marc260a" in self.solr_doc:
            for e in zip_longest(self.GetFieldValues("marc260a"), self.GetFieldValues("marc260b"), self.GetFieldValues("marc260c")):
                 pubs.append(" ".join(unicode(i) for i in e))
        return pubs

    def GetExtentValues(self):
        extents = []
        if "marc300a" in self.solr_doc:
            for e in zip_longest(self.GetFieldValues("marc300a"), self.GetFieldValues("marc300b"), self.GetFieldValues("marc300c")):
                 extents.append(" ".join(unicode(i) for i in e))
        return extents

    def GetSeries(self):
        series = []
        if "series" in self.solr_doc:
            for s in self.solr_doc["series"]:
                series.append(s)
        return series

    def GetExtent(self):
        extent = ()
        if "multivolume" in self.solr_doc and "total_volumes" in self.solr_doc:
            extent = ("volumes", self.solr_doc["total_volumes"])
        elif "total_pages" in self.solr_doc:
            extent = ("pages", self.solr_doc["total_pages"])
        return extent

    def BuildAuthor(self):
        if "main_entry" in self.solr_doc:
            author = self.solr_doc["main_entry"][0]
        else:
            author = ""
        return author

    def BuildDate(self, field):
        if field in self.solr_doc:
            date = self.solr_doc[field]
        else:
            date = ""
        return date

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
    print(str(len(g.edges()))+ " connections out of a possible " + str(i))
    print(len(g.nodes()), "nodes")
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
    print(str(len(g.edges()))+ " connections out of a possible " + str(i))
    print(len(g.nodes()), "nodes")
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
            print("Request failed")

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
        data = json.dumps(json_graph.node_link_data(g))
        f.write(data)
    print("Wrote file at "+os.path.join(output_path,filename))
           
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


def College_Sort():


    html_list = html.split("</div>")

    college_data = {}
    most_recent = ""

    for line in html_list:
        if "tablehead1b" in line:
            current_college = line[line.index("1b>"):]
            most_recent = "college"
        elif "tablehead2" in line:
            current_dept = line[line.index("px;"):]
            most_recent = "department"
        elif "ProgramDetail" in line:
            program = line[85:line.index("</a>")]
            if "&nbsp" in program:
                program = program[:program.index("&nbsp")]
            if "(" in program:
                program = program[:program.index("(")]
            if "Master of Business" in program:
                program = "Business Administration"

            program = Program_Clean(program)

            if program not in college_data:
                if most_recent == "department":
                    college_data[program] = (current_college[3:].rstrip(), current_dept[5:].rstrip())
                else:
                    college_data[program] = (current_college[3:].rstrip(), None)

    return college_data 


def Program_Clean(program):

    html = """<div class=tablehead1b>College of Agriculture and Natural Resources</div><div class=tablehead2 style='padding-left:50px;'>Department of Agricultural, Food, and Resource Economics</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5321'>Agricultural, Food and Resource Economics - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5320'>Agricultural, Food and Resource Economics - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Animal Science</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0290'>Animal Science - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0291'>Animal Science- Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0472'>Animal Science-Environmental Toxicology</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Biosystems and Agricultural Engineering</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0501'>Biosystems Engineering - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0502'>Biosystems Engineering - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Community, Agriculture, Recreation and Resource Studies</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5209'>Community, Agriculture, Recreation and Resource Studies - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5208'>Community, Agriculture, Recreation and Resource Studies - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5377'>Sustainable Tourism and Protected Area Management - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5376'>Sustainable Tourism and Protected Area Management - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Entomology                                              </div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0537'>Entomology - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0536'>Entomology - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Fisheries and Wildlife</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0347'>Fisheries and Wildlife - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0477'>Fisheries and Wildlife - Environmental Toxicology</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0346'>Fisheries and Wildlife - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Food Science and Human Nutrition</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0354'>Food Science - Master of Science and Doctor of Philosophy&nbsp;&nbsp;<span class=tabledata1>(Master of Science)</span></a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0355'>Food Science - Master of Science and Doctor of Philosophy&nbsp;&nbsp;<span class=tabledata1>(Doctor of Philosophy)</span></a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0474'>Food Science-Environmental Toxicology</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5273'>Human Nutrition - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5274'>Human Nutrition - Environmental Toxicology</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5272'>Human Nutrition - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Forestry                                                </div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0379'>Forestry - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0475'>Forestry - Environmental Toxicology</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0378'>Forestry - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5312'>Plant Breeding, Genetics and Biotechnology - Forestry&nbsp;&nbsp;<span class=tabledata1>(Master of Science)</span></a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5313'>Plant Breeding, Genetics and Biotechnology - Forestry&nbsp;&nbsp;<span class=tabledata1>(Doctor of Philosophy)</span></a></div><div class=tablehead2 style='padding-left:50px;'>Department of Horticulture</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0403'>Horticulture - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0402'>Horticulture - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5314'>Plant Breeding, Genetics and Biotechnology - Horticulture&nbsp;&nbsp;<span class=tabledata1>(Master of Science)</span></a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5315'>Plant Breeding, Genetics and Biotechnology - Horticulture&nbsp;&nbsp;<span class=tabledata1>(Doctor of Philosophy)</span></a></div><div class=tablehead2 style='padding-left:50px;'>School of Packaging</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0486'>Packaging - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0409'>Packaging - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>School of Planning, Design and Construction</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5260'>Construction Management - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5268'>Environmental Design - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5264'>Interior Design and Facilities Management - Master of Arts (this program is in moratorium Spring 2011 through Fall 2014)</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5355'>Planning, Design and Construction - Doctor of Philosophy</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Plant Biology</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5316'>Plant Breeding, Genetics and Biotechnology - Plant Biology&nbsp;&nbsp;<span class=tabledata1>(Master of Science)</span></a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5317'>Plant Breeding, Genetics and Biotechnology - Plant Biology&nbsp;&nbsp;<span class=tabledata1>(Doctor of Philosophy)</span></a></div><div class=tablehead2 style='padding-left:50px;'>Department of Plant, Soil and Microbial Sciences</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5369'>Crop and Soil Sciences - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5370'>Crop and Soil Sciences- Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5371'>Crop and Soil Sciences- Environmental Toxicology</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5372'>Plant Breeding, Genetics and Biotechnology - Crop and Soil Sciences&nbsp;&nbsp;<span class=tabledata1>(Master of Science)</span></a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5373'>Plant Breeding, Genetics and Biotechnology - Crop and Soil Sciences&nbsp;&nbsp;<span class=tabledata1>(Doctor of Philosophy)</span></a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5375'>Plant Pathology - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5374'>Plant Pathology - Master of Science</a></div><br><br><div class=tablehead1b>College of Arts and Letters</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1044'>African American and African Studies - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1043'>African American and African Studies - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1002'>American Studies - Doctor of Philosophy (this program is in moratorium effective Spring 2010 through Summer 2017)</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0639'>American Studies - Master of Arts (this program is in moratorium effective Spring 2010 through Summer 2015)</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5643'>Critical Studies in Literacy and Pedagogy - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5601'>Digital Rhetoric and Professional Writing - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5724'>Foreign Language Teaching - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5600'>Rhetoric and Writing - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5642'>Second Language Studies - Doctor of Philosophy</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Art, Art History, and Design</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0554'>Studio Art - Master of Fine Arts</a></div><div class=tablehead2 style='padding-left:50px;'>Department of English</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0647'>English - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1017'>Literature in English - Master of Arts</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Linguistics and Germanic, Slavic, Asian and African Languages</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1029'>German Studies - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1028'>German Studies - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0714'>Linguistics - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0713'>Linguistics - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1049'>Teaching English to Speakers of Other Languages - Master of Arts</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Philosophy</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0893'>Philosophy - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0891'>Philosophy - Master of Arts</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Romance and Classical Studies</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5732'>Applied Spanish Linguistics - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0913'>French - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0915'>French, Language and Literature - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5734'>Hispanic Cultural Studies - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=5733'>Hispanic Literatures - Master of Arts</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Theatre</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=0979'>Theatre - Master of Fine Arts</a></div><br><br><div class=tablehead1b>Eli Broad College of Business and The Eli Broad Graduate School of Management</div><div class=tablehead2 style='padding-left:50px;'>The Eli Broad College of Business</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=6024'>Business Administration - Doctor of Philosophy&nbsp;&nbsp;<span class=tabledata1>(Business Information Systems)</span></a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=6048'>Business Research - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=6011'>Master of Business Administration</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=6037'>Master of Business Administration Degree: Corporate M.B.A. Program</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=6044'>Master of Business Administration Degree: Executive M.B.A. Program</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1310'>Master of Business Administration Degree: Program in Integrative Management</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Accounting and Information Systems</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=6019'>Accounting - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1054'>Business Administration - Doctor of Philosophy</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Finance</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1139'>Business Administration - Doctor of Philosophy&nbsp;&nbsp;<span class=tabledata1>(Finance)</span></a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=6016'>Finance - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>School of Hospitality Business</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=6046'>Foodservice Business Management - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=6047'>Hospitality Business Management - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Management</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=6007'>Business Administration - Doctor of Philosophy&nbsp;&nbsp;<span class=tabledata1>(Strategic Management)</span></a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=6008'>Business Administration - Doctor of Philosophy&nbsp;&nbsp;<span class=tabledata1>(Org Behav-Human Resource Mgt)</span></a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=6062'>Management, Strategy, and Leadership - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Marketing</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=6057'>Marketing Research - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Supply Chain Management</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1331'>Business Administration - Doctor of Philosophy&nbsp;&nbsp;<span class=tabledata1>(Logistics)</span></a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1350'>Business Administration - Doctor of Philosophy&nbsp;&nbsp;<span class=tabledata1>(Operations and Sourcing Mgt)</span></a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=6035'>Supply Chain Management - Master of Science</a></div><br><br><div class=tablehead1b>College of Communication Arts and Sciences</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1473'>Health and Risk Communication - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1500'>Media and Information Studies - Doctor of Philosophy</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Advertising, Public Relations and Retailing</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1352'>Advertising - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1357'>Public Relations - Master of Arts</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Communication</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1377'>Communication - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1376'>Communication - Master of Arts</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Communicative Sciences and Disorders</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1454'>Communicative Sciences and Disorders - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1453'>Communicative Sciences and Disorders - Master of Arts</a></div><div class=tablehead2 style='padding-left:50px;'>School of Journalism</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1404'>Journalism - Master of Arts</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Telecommunication, Information Studies and Media</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1438'>Telecommunication, Information Studies and Media - Master of Arts</a></div><br><br><div class=tablehead1b>College of Education</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2294'>Education - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2293'>Educational Policy - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=6744'>Health Professions Education - Master of Arts</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Counseling, Educational Psychology, and Special Education</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=6703'>Educational Psychology and Educational Technology - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2299'>Educational Technology - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2251'>Measurement and Quantitative Methods - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1752'>Rehabilitation Counseling - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2279'>Rehabilitation Counselor Education - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2275'>School Psychology - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1742'>School Psychology - Educational Specialist</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=6702'>School Psychology - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1727'>Special Education - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1726'>Special Education - Master of Arts</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Educational Administration</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=6752'>Educational Leadership - Doctor of Education</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2288'>Higher, Adult and Lifelong Education - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2245'>Higher, Adult, and Lifelong Education - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1646'>K-12 Educational Administration - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=1644'>K-12 Educational Administration - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2246'>Student Affairs Administration - Master of Arts</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Kinesiology</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2284'>Kinesiology - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2283'>Kinesiology - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Teacher Education</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=6730'>Curriculum, Instruction, and Teacher Education - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=6727'>Teaching and Curriculum - Master of Arts</a></div><br><br><div class=tablehead1b>College of Engineering</div><div class=tablehead2 style='padding-left:50px;'>Department of Chemical Engineering and Materials Science</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2304'>Chemical Engineering - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2303'>Chemical Engineering - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=8002'>Materials Science and Engineering - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=8001'>Materials Science and Engineering - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Civil and Environmental Engineering</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2312'>Civil Engineering - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2311'>Civil Engineering - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2326'>Environmental Engineering - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2324'>Environmental Engineering - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Computer Science and Engineering</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2336'>Computer Science - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2335'>Computer Science - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Electrical and Computer Engineering</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2349'>Electrical Engineering - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2348'>Electrical Engineering - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Mechanical Engineering</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2495'>Engineering Mechanics - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2494'>Engineering Mechanics - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2402'>Mechanical Engineering - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2401'>Mechanical Engineering - Master of Science</a></div><br><br><div class=tablehead1b>College of Human Medicine</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2837'>Master of Public Health in Public Health</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Epidemiology and Biostatistics</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2847'>Biostatistics - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2831'>Epidemiology - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=2832'>Epidemiology - Master of Science</a></div><br><br><div class=tablehead1b>College of Music</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7331'>Collaborative Piano - Master of Music</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7334'>Jazz Studies - Master of Music</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7324'>Music Composition - Doctor of Musical Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7323'>Music Composition - Master of Music</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7336'>Music Conducting - Doctor of Musical Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7335'>Music Conducting - Master of Music</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7326'>Music Education - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7325'>Music Education - Master of Music</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7329'>Music Performance - Doctor of Musical Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7328'>Music Performance - Master of Music</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7332'>Music Theory - Master of Music</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7327'>Musicology - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7330'>Piano Pedagogy - Master of Music</a></div><br><br><div class=tablehead1b>College of Natural Science</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3782'>Biological Science-Interdepartmental - Master of Science (this program is in moratorium Fall 2013 through Fall 2014)</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3964'>Cell and Molecular Biology - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7071'>Cell and Molecular Biology - Environmental Toxicology - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7011'>Cell and Molecular Biology - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3986'>Ecology, Evolutionary Biology and Behavior - Dual Major</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3935'>General Science - Master of Arts for Teachers (this program is in moratorium Fall 2013 through Fall 2014)</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3788'>Genetics - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7087'>Genetics - Environmental Toxicology - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7020'>Genetics - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7069'>Mathematics Education - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7068'>Mathematics Education - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3987'>Neuroscience - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7098'>Neuroscience - Environmental Toxicology - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7038'>Neuroscience - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3800'>Physical Science - Interdepartmental - Master of Science (this program is in moratorium Fall 2013 through Fall 2014)</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Biochemistry and Molecular Biology</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7028'>Biochemistry and Molecular Biology - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7027'>Biochemistry and Molecular Biology - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7029'>Biochemistry and Molecular Biology-Environmental Toxicology - Doctor of Philosophy</a></div><div class=tablehead2 style='padding-left:50px;'>Biomedical Laboratory Diagnostics Program</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7037'>Biomedical Laboratory Operations - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7104'>Biomedical Laboratory Science - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3793'>Clinical Laboratory Sciences - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Chemistry</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3829'>Chemical Physics - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3575'>Chemistry - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3938'>Chemistry - Environmental Toxicology - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3573'>Chemistry - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Geological Sciences</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3952'>Environmental Geosciences - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3968'>Environmental Geosciences - Environmental Toxicology - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3928'>Environmental Geosciences - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3927'>Geological Sciences - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3925'>Geological Sciences - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Mathematics</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3734'>Applied Mathematics - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3733'>Applied Mathematics - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3994'>Industrial Mathematics - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3741'>Mathematics - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3739'>Mathematics - Master of Arts for Teachers</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3740'>Mathematics - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Microbiology and Molecular Genetics</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7030'>Microbiology and Molecular Genetics - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7043'>Microbiology and Molecular Genetics - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Physics and Astronomy</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3924'>Astrophysics and Astronomy - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3923'>Astrophysics and Astronomy - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3838'>Physics - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3836'>Physics - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Physiology                                              </div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3861'>Physiology - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3860'>Physiology - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Plant Biology</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7019'>Plant Biology - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7018'>Plant Biology - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Statistics and Probability</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3871'>Applied Statistics - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3877'>Statistics - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3875'>Statistics - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Zoology</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3889'>Zoology - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3941'>Zoology - Environmental Toxicology - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=3887'>Zoology - Master of Science</a></div><br><br><div class=tablehead1b>College of Nursing</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4013'>Nursing - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4003'>Nursing - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4030'>Nursing Practice - Doctor of Nursing Practice</a></div><br><br><div class=tablehead1b>College of Osteopathic Medicine</div><div class=tablehead2 style='padding-left:50px;'>Department of Pharmacology and Toxicology</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4216'>Integrative Pharmacology - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4217'>Laboratory Research in Pharmacology and Toxicology - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4178'>Pharmacology and Toxicology - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4176'>Pharmacology and Toxicology - Master of Science</a></div><br><br><div class=tablehead1b>College of Social Science</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7625'>Chicano/Latino Studies, Doctor of Philosophy</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Anthropology</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4308'>Anthropology - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4307'>Anthropology - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4727'>Professional Applications in Anthropology - Master of Arts</a></div><div class=tablehead2 style='padding-left:50px;'>School of Criminal Justice                                            </div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4725'>Criminal Justice - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4318'>Criminal Justice - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4744'>Forensic Science - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7728'>Judicial Administration - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7673'>Law Enforcement Intelligence and Analysis - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Economics                                               </div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4737'>Economics - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4736'>Economics - Master of Arts</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Geography</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4742'>Geographic Information Science - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4347'>Geography - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7669'>Geography - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of History</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7611'>History - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7609'>History - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7610'>History-Secondary School Teaching - Master of Arts (this program is in moratorium effective Spring 2010 through Spring 2015)</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Human Development and Family Studies</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7702'>Child Development - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7722'>Family Community Services - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7692'>Human Development and Family Studies - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7691'>Human Development and Family Studies - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7645'>Youth Development - Master of Arts</a></div><div class=tablehead2 style='padding-left:50px;'>School of Planning, Design and Construction</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7623'>International Planning Studies</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7619'>Urban and Regional Planning - Master of Urban and Regional Planning</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Political Science</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4387'>Political Science - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4385'>Political Science - Master of Arts</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7624'>Public Policy - Master of Public Policy</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Psychology</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4414'>Psychology - Master of Arts and Doctor of Philosophy&nbsp;&nbsp;<span class=tabledata1>(Master of Arts)</span></a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4415'>Psychology - Master of Arts and Doctor of Philosophy&nbsp;&nbsp;<span class=tabledata1>(Doctor of Philosophy)</span></a></div><div class=tablehead2 style='padding-left:50px;'>School of Human Resources and Labor Relations</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7650'>Human Resources and Labor Relations  - Master of Human Resources and Labor Relations</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=7602'>Industrial Relations and Human Resources - Doctor of Philosophy</a></div><div class=tablehead2 style='padding-left:50px;'>School of Social Work</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4746'>Social Work - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4493'>Social Work - Master of Social Work</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Sociology</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4536'>Sociology - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4535'>Sociology - Master of Arts</a></div><br><br><div class=tablehead1b>College of Veterinary Medicine</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4912'>Comparative Medicine and Integrative Biology - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4911'>Comparative Medicine and Integrative Biology - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4914'>Food Safety - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Large Animal Clinical Sciences</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4764'>Large Animal Clinical Sciences - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4763'>Large Animal Clinical Sciences - Master of Science</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Microbiology and Molecular Genetics</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4901'>Microbiology - Environmental Toxicology - Doctor of Philosophy</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Pathobiology and Diagnostic Investigation</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4919'>Pathobiology - Doctor of Philosophy</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4918'>Pathobiology - Master of Science</a></div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4920'>Pathobiology-Environmental Toxicology - Doctor of Philosophy</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Pharmacology and Toxicology</div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4902'>Pharmacology and Toxicology-Environmental Toxicology - Doctor of Philosophy</a></div><div class=tablehead2 style='padding-left:50px;'>Department of Small Animal Clinical Sciences                          </div><div style='padding-left:100px;'><a class=text href='ProgramDetail.asp?Program=4810'>Small Animal Clinical Sciences - Master of Science</a></div><br><hr width='98%' color=#CCCCCC><br></div>"""
        

    if " - Master" in program:
        clean_program = program[:program.index("- Master")].rstrip()
    elif " - Doctor" in program:
        clean_program = program[:program.index("- Doctor")].rstrip()
    elif " -  Master" in program:
        clean_program = program[:program.index(" -  Master")].rstrip()
    elif " -  Doctor" in program:
        clean_program = program[:program.index(" -  Doctor")].rstrip()
    else:
        clean_program = program

    if clean_program == "Pharmacology and Toxicology - Environmental Toxicology":
        clean_program = "Pharmacology and Toxicology-Environmental Toxicology"
    elif clean_program == "Higher, Adult, and Lifelong Education":
        clean_program = "Higher, Adult and Lifelong Education"
    elif clean_program == "Comparative Med & Integr Biol":
        clean_program = "Comparative Medicine and Integrative Biology"
    elif clean_program == "Animal Science- Doctor of Philosophy":
        clean_program = "Animal Science"
    elif clean_program == "Crop and Soil Sciences- Doctor of Philosophy":
        clean_program = "Crop and Soil Sciences"
    elif clean_program == "Business Administration - Organization Behavior - Huamn Resource Management":
        clean_program = "Business Administration - Organization Behavior - Human Resource Management"
    elif clean_program == "English" or clean_program == "Literature in English":
        clean_program = "English & Literature in English"
    elif clean_program == "Biological Science-Interdepartmental":
        clean_program = "Biological Science - Interdepartmental"
    
    return clean_program

def update_graph(solr_url):
    """Update ETD graph data for visualization."""
    etds = []
    etddata_dict = {}

    # Establish solr query data.
    row_count = 1000
    count = 1000
    params = {"q": "PID:etd\:*", "wt": "json", "rows": row_count}
    fields = SolrDoc.get_etd_graph_fields()
    page = 0

    # Request from solr only the fields needed for this process.
    params["fl"] = [v for k, v in fields.items()]

    data_list = []

    # As long as we're getting full results sets, keep getting next page.
    while count == row_count:

        params["start"] = page * 1000

        r_etddata = requests.get(solr_url, params=params)
        r_data = r_etddata.json()
        etds = r_data["response"]["docs"]
        for e in etds:

            etd_doc = SolrDoc(e)
            etd_graph_dict = etd_doc.build_graph_record()

            # Skip documents without programs.
            if "Program" in etd_doc.solr_metadata:
                dict_update(etd_graph_dict, etd_doc.solr_metadata["Program"], data_list)
            else:
                pass

        count = len(etds)
        page += 1
    try:
        etddata_dict["data_list"] = data_list
        output_path = "/var/www/fedora/sites/all/themes/msul-omega-fedcom/js/"
        translate_to_graph(data_list, "Program", json_output=True, output_path=output_path)

    except Exception as e:
        print(e)

if __name__ == "__main__":
    # Parse user input
    parser = argparse.ArgumentParser(description='Updates data for ETD graph visualization.')
    parser.add_argument('-s', '--solrurl', help='URL to send Solr updates to',required=True)
    args = vars(parser.parse_args())

    update_graph(args["solrurl"])

