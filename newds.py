from eulfedora.server import Repository
from eulfedora.models import DigitalObject, XmlDatastream, DatastreamObject
from eulxml.xmlmap import XmlObject
from eulxml import xmlmap
from lxml import etree
import os, ConfigParser
import xmldata
from eulfedora import api

def Repo_Connect(server):
    username,password,root = Get_Configs(server)
    repo = Repository(root=root,username=username, password=password)
    return repo


def Update_Custom(server, filepath, purge=False):

    i = 0
    path = filepath
    username,password,root = Get_Configs(server)
    repo = Repository(root=root,username=username, password=password)
    
    xml_files = [x for x in os.listdir(path) if "DATA.xml" in x]

    for xml in xml_files:
    
        tree = etree.parse(path+xml)

        path_program = "/DISS_submission/DISS_description/DISS_institution/DISS_inst_contact"
        path_keywords = "/DISS_submission/DISS_description/DISS_categorization/DISS_keyword"
        path_category = "/DISS_submission/DISS_description/DISS_categorization/DISS_category/DISS_cat_desc"

        r_program = tree.xpath(path_program)
        root = etree.Element("custom")
        program = etree.SubElement(root, "program")
        program.text = Program_Clean(r_program[0].text)

        categories = Get_Terms(tree, path_category)
        for cat in categories:
            category = etree.SubElement(root,"category")
            category.text = cat

        keywords = Get_Terms(tree, path_keywords)
        if keywords <> [None]:
            for key in keywords:
                keyword = etree.SubElement(root,"keyword")
                keyword.text = key

        pid = Get_Pid(xml, repo)

        if pid is not None:
            i+=1
            custom_xml = "/Volumes/archivematica/ETD-Custom_Datastream/"+xml[:-9]+"_CUSTOM.xml"
            with open(custom_xml, "w") as f:
                f.write(etree.tostring(root, pretty_print=True, encoding='utf-8', xml_declaration=True))
                    
            xml_object = xmlmap.load_xmlobject_from_file(custom_xml)

            digital_object = repo.get_object(pid)

            if purge is True:
                digital_object.api.purgeDatastream(pid,"CUSTOM")

            new_datastream = DatastreamObject(digital_object,"CUSTOM","Custom metadata compiled by MSUL",mimetype="text/xml",control_group="X")
            new_datastream.content = xml_object
            new_datastream.label = "Custom metadata compiled by MSUL"
            new_datastream.save()
            print i, " saved "+pid
        


def Get_Pid(xml, repo):
    localID = u'local:\xa0'+xml[:-9]
    pid_check = list(repo.find_objects(identifier=localID))
    if len(pid_check) == 1:
        pid = str(pid_check[0])
    elif len(pid_check) == 0:
        print "No object found for "+ xml
        pid = None
    else:
        print "Error for "+ xml
        print [x for x in pid_check]
        pid = None

    return pid

def Get_Configs(server):
    config = ConfigParser.ConfigParser()
    cwd = os.path.dirname(os.path.abspath(__file__))
    for f in os.listdir(cwd):
        if f.endswith(".cfg"):
            config_file = f
            
    config.read(cwd+"/"+config_file)
    username = config.get(server, "username")
    password = config.get(server, "password")
    root = config.get(server, "root")

    return username,password,root
    


    
