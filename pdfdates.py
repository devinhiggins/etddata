import os
from pdfminer.pdfparser import PDFParser
#from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser, PDFDocument
from datetime import datetime, time, date
from lxml import etree
from pprint import pprint
import json
import prereq

class DocumentDates:
    def __init__(self, f):
        self.file = f


    def PDFCreationDate(self):
        if self.file.endswith(".pdf"):
            fp = open(self.file, 'rb')
            parser = PDFParser(fp)
            doc = PDFDocument()
            parser.set_document(doc)
            doc.set_parser(parser)
            doc.initialize()
            cdate = doc.info[0]['CreationDate']
            if isinstance(cdate, str):
                date_format = date(int(cdate[2:6]), int(cdate[6:8]), int(cdate[8:10]))
            else:
                date_format = None
                print "No Creation Date for "+self.file
            return date_format
        else:
            "The file doesn't appear to be a PDF."
            return None

    def FileModifiedDate(self):
        mdate = os.path.getmtime(self.file)
        date_format = date.fromtimestamp(mdate)
        return date_format
        
    def FileCtimeDate(self):
        cdate = os.path.getctime(self.file)
        date_format = date.fromtimestamp(cdate)
        return date_format


class ETDData:
    def __init__(self, directory, xml=None):
        """
        Establishes class instance including file directory and xml file if provided.

        Args:
            directory(str)
        """
        self.directory = directory
        if xml:
            self.xml = xml

    def SearchAuth(self):
        """
        Look up third-party search value XML file.
        self.xml variable must be established.
        """
        path_search = "/DISS_submission/@third_party_search"
        tree = etree.parse(self.directory+self.xml)
        r_search = tree.xpath(path_search)
        return r_search[0]

    def SearchRestrictions(self):
        """
        Looks up publishing restriction codes for each XML document. 
        Return dictionary of attributes and their values.
        self.xml variable must be established.
        """
        path_r = "/DISS_submission"
        tree = etree.parse(self.directory+self.xml)
        r = tree.xpath(path_r)
        return r[0].attrib

    def FindRestricted(self, date, server, jsonize=False):
        """
        Finds pids for restricted ETDs and returns them in a list.
        
        Args:
            date(str): Date after which ETD authors could select to restrict 3-p search.
            server(str): Server to use (must be specified in configuration file).
            jsonize(bool): Create JSON output if True.

        Yields:
            list: all PIDs from a given server which should be restricted.

        """
        files = (x for x in os.listdir(self.directory) if x.endswith(".xml"))
        marker = datetime.strptime(date, "%Y%m%d").date()
        pids = []
        for xfile in files:
            self.xml = xfile
            d = DocumentDates(self.directory+xfile)
            filedate = d.FileModifiedDate()

            thirdparty = self.SearchAuth()


            if filedate > marker and (thirdparty == "N" or thirdparty == "O"):
                repo = prereq.Repo_Connect(server)
                pid = prereq.Get_Pid(xfile,repo)
                if pid is not None:
                    pids.append(pid)

        if jsonize == True:
            with open("pids.json", "w") as f:
                data = json.dump(pids, f)

        return pids

                                        
    

        

        
