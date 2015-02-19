from eulfedora.server import Repository
from eulfedora.models import DigitalObject, XmlDatastream, DatastreamObject
from eulxml.xmlmap import XmlObject
from eulxml import xmlmap
from lxml import etree
from datetime import datetime, date
import os
import xmldata
from eulfedora import api
from msu_programs import College_Sort
import pdfdates
import pclean
import prereq

class CustomEtd():
    def __init__(self, data_xml, repo=None, server="Development"):
        if not repo:
            repo = prereq.RepoConnect(server)
        self.data_xml = data_xml
        self.tree = etree.parse(self.data_xml)

    def CreateXmlFile(self):
        root = self.CustomDs()
        custom_xml = self.data_xml[:-9]+"_CUSTOM.xml"
        with open(custom_xml, "w") as f:
            f.write(etree.tostring(root, pretty_print=True, encoding='utf-8', xml_declaration=True))
        return custom_xml

    def GetProgram(self):
        path_program = "/DISS_submission/DISS_description/DISS_institution/DISS_inst_contact"
        r_program = self.tree.xpath(path_program)
        program_text = r_program[0].text
        return pclean.Program_Clean(program_text)

    def GetKeywords(self):
        path_keywords = "/DISS_submission/DISS_description/DISS_categorization/DISS_keyword"
        keywords = xmldata.Get_Terms(self.tree, path_keywords)
        return keywords

    def GetCategory(self):
        path_category = "/DISS_submission/DISS_description/DISS_categorization/DISS_category/DISS_cat_desc"
        categories = xmldata.Get_Terms(self.tree, path_category)
        return categories

    def GetSubjects(self):
        self.AddMarcXml()
        all_subjects = []
        subject_fields = ["600","610","611","630","648","650","651"]
        for field in subject_fields:
            path_subjects = "/marc:record/marc:datafield[@tag='subject_field' and @ind2='0']/marc:subfield[@code='a']".replace("subject_field",field)
            subjects = self.marc_tree.xpath(path_subjects, namespaces={"marc": "http://www.loc.gov/MARC21/slim"})
            all_subjects += subjects
        return all_subjects

    def GetFullSubjects(self):
        if not self.marc_tree:
            self.AddMarcXml()
        full_subjects = []
        subject_fields = ["600","610","611","630","648","650","651"]
        for field in subject_fields:
            xpath = "/marc:record/marc:datafield[@tag='subject_field' and @ind2!='7']".replace("subject_field",field)
            s_head = self.marc_tree.xpath(xpath, namespaces={"marc": "http://www.loc.gov/MARC21/slim"})
            for subject in s_head:
                subject = []
                for subject_field in subject:
                    subject.append((subject_field.tag, subject_field.text))
                full_subjects.append(CombineFields(subject, field))

        return full_subjects

    def GetInstitutionData(self):
        """
        Return dictionary with key as program (clean) and value as a tuple containing (college, dept).
        Dept is None if not found.
        """
        int_data = College_Sort()
        return int_data

    def GetProgramAffiliations(program):
        
        program_affiliations = self.GetInstitutionData().get(program_name, (None, None))
        return program_affiliations

    @staticmethod
    def CombineFields(subject, field):
        name_fields = ["600", "610", "611","630"]
        if len(subject) == 1:
            subject_string = subject[0][1].rstrip().lstrip()
        elif field in name_fields:
            print field
            subdivisions = ["v", "x", "y", "z"]
            name_content = [s[1].rstrip().lstrip() for s in subject if s[0] not in subdivisions]
            name = " ".join(name_content)
            subdivision_content = "--".join([s[1].rstrip().lstrip() for s in subject if s[0] in subdivisions])
            if subdivision_content is True:
                subject_string = "--".join([name, subdivision_content])
            else:
                subject_string = name
        else:
            subject_content = [s[1].rstrip().lstrip() for s in subject]
            subject_string = "--".join(subject_content)

        return subject_string.rstrip().lstrip()


    def AddMarcXml(self):
        self.marc_tree = None
        marc_path = self.data_xml[:-9]+"_MARCXML.xml"
        if os.path.isfile(marc_path):
            self.marc_tree = etree.parse(self.data_xml[:-9]+"_MARCXML.xml")
        else:
            pass
            #TODOex


    def GetCodes(self):
        sr = pdfdates.ETDData("", self.data_xml)
        rcodes = sr.SearchRestrictions()
        return rcodes

    def CustomDs(self):
        root = etree.Element("custom")
        program = etree.SubElement(root, "program")
        program_name = pclean.Program_Clean(self.GetProgram())
        program.text = program_name

        keywords = self.GetKeywords()
        if keywords <> [None]:
            for key in keywords:
                keyword = etree.SubElement(root,"keyword")
                keyword.text = key

        categories = self.GetCategory()
        for cat in categories:
            category = etree.SubElement(root,"category")
            category.text = cat

        subjects = self.GetSubjects()
        if subjects != []:
            for i,sub in enumerate(subjects):
                if subjects[i] <> None:
                    subject = etree.SubElement(root, "subject")
                    subject.text = sub[i].text.strip(".").rstrip()

        full_subjects = self.GetFullSubjects()
        if full_subjects != []:
            for sub in full_subjects:
                full_subject = etree.SubElement(root, "full_subject")
                full_subject.text = sub

        rcodes = self.GetCodes()
        for key in rcodes:
            value = rcodes[key]
            new_field = etree.SubElement(root, key)
            if key == "third_party_search":
                datecls = pdfdates.DocumentDates(self.data_xml)
                mdate = datecls.FileModifiedDate()
                marker = datetime.strptime("20130507", "%Y%m%d").date()
                if mdate < marker and rcodes[key] == "N":
                    value = "YN"
            new_field.text = value
            self.third_party_search = value
        return root


class DatastreamXml():
    def __init__(self, pid):
        username,password,root = prereq.Get_Configs(server)
        self.repo = Repository(root=root,username=username, password=password)
        self.pid = pid

    def ReplaceDs(self, dsid, xml_path):
        self.dsid = dsid
        self.xml_path = xml_path
        xml_object = self._MakeXmlObject()
        digital_object = repo.get_object(self.pid)
        datastream = DatastreamObject(digital_object, self.dsid)
        datastream.content = xml_object
        new_datastream.label = "_".join(self.pid.replace(":", ""), dsid)
        new_datastream.save()

    def _MakeXmlObject(self):
        return xmlmap.load_xmlobject_from_file(self.xml_path)


def Update_Custom(server, path, purge=False):
    """
    Function to update custom xml datastream for all existing objects.
    """
    i = 0
    username,password,root = prereq.Get_Configs(server)
    repo = Repository(root=root,username=username, password=password)
    
    xml_files = (x for x in os.listdir(path) if "DATA.xml" in x)

    for xml in xml_files:

        pid = prereq.Get_Pid(xml, repo)

        if pid is not None:
  
            tree = etree.parse(path+xml)

            path_program = "/DISS_submission/DISS_description/DISS_institution/DISS_inst_contact"
            path_keywords = "/DISS_submission/DISS_description/DISS_categorization/DISS_keyword"
            path_category = "/DISS_submission/DISS_description/DISS_categorization/DISS_category/DISS_cat_desc"

            r_program = tree.xpath(path_program)
            root = etree.Element("custom")
            program = etree.SubElement(root, "program")
            program.text = pclean.Program_Clean(r_program[0].text)

            categories = xmldata.Get_Terms(tree, path_category)
            for cat in categories:
                category = etree.SubElement(root,"category")
                category.text = cat

            keywords = xmldata.Get_Terms(tree, path_keywords)
            if keywords <> [None]:
                for key in keywords:
                    keyword = etree.SubElement(root,"keyword")
                    keyword.text = key

            sr = pdfdates.ETDData(path, xml)
            rcodes = sr.SearchRestrictions()
            for key in rcodes:
                value = rcodes[key]
                new_field = etree.SubElement(root, key)
                if key == "third_party_search":
                    datecls = pdfdates.DocumentDates(path+xml)
                    mdate = datecls.FileModifiedDate()
                    marker = datetime.strptime("20130507", "%Y%m%d").date()
                    if mdate < marker and rcodes[key] == "N":
                        value = "YN"
                new_field.text = value

            print "pid", pid

            digital_object = repo.get_object(pid)

            marcxml_object = digital_object.getDatastreamObject("MARCXML")
            marcxml_content = marcxml_object.content.serialize()
            marc_tree = etree.fromstring(marcxml_content)
            subject_fields = ["600","610","611","630","648","650","651"]

            for field in subject_fields:
                path_subjects = "/marc:record/marc:datafield[@tag='[subject_field]' and @ind2!='7']/marc:subfield[@code='a']".replace("[subject_field]", field)
                subjects = marc_tree.xpath(path_subjects, namespaces={"marc": "http://www.loc.gov/MARC21/slim"})
                if len(subjects) != 0:
                    print "===SUBJECTS==="
                    subjects = list(set([s.text.strip().rstrip(".,;") for s in subjects]))
                    for i,sub in enumerate(subjects):
                        if subjects[i] <> None:
                            print sub
                            subject = etree.SubElement(root, "subject")
                            subject.text = sub
            

            full_subjects = []
            
            for field in subject_fields:
                xpath = "/marc:record/marc:datafield[@tag='[subject_field]' and @ind2='0']".replace("[subject_field]",field)
                s_head = marc_tree.xpath(xpath, namespaces={"marc": "http://www.loc.gov/MARC21/slim"})
                for subject in s_head:
                    subject_parts = []
                    for subject_field in subject:
                        subject_parts.append((subject_field.tag, subject_field.text))
                    full_subjects.append(CustomEtd.CombineFields(subject_parts, field))

            if full_subjects != []:
                for sub in full_subjects:
                    full_subject = etree.SubElement(root, "full_subject")
                    full_subject.text = sub.rstrip()



            i+=1
            custom_xml = "/Volumes/fedcom_ingest/ETD-Custom_Datastream/"+xml[:-9]+"_CUSTOM.xml"
            with open(custom_xml, "w") as f:
                f.write(etree.tostring(root, pretty_print=True, encoding='utf-8', xml_declaration=True))
                    
            xml_object = xmlmap.load_xmlobject_from_file(custom_xml)
        
            if purge is True:
                digital_object.api.purgeDatastream(pid,"CUSTOM")
                print "PURGED CUSTOM"

            new_datastream = DatastreamObject(digital_object,"CUSTOM","Custom metadata compiled by MSUL",mimetype="text/xml",control_group="X")
            new_datastream.content = xml_object
            new_datastream.label = "Custom metadata compiled by MSUL"
            new_datastream.save()
            
        


    


    
