import os
from pdfminer.pdfparser import PDFParser, PDFDocument
from datetime import datetime, time, date
from lxml import etree
from pprint import pprint
import json
from . import newds

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
    def __init__(self, directory):
        self.directory = directory

    def SearchAuth(self, xml):
        path_search = "/DISS_submission/@third_party_search"
        tree = etree.parse(self.directory+xml)
        r_search = tree.xpath(path_search)
        return r_search[0]

    def FindRestricted(self, date, json=False):
        files = (x for x in os.listdir(self.directory) if x.endswith(".xml"))
        marker = datetime.strptime(date, "%Y%m%d").date()
        pids = []
        for xfile in files:
            d = DocumentDates(self.directory+xfile)
            filedate = d.FileModifiedDate()

            e = ETDData(self.directory)
            thirdparty = e.SearchAuth(xfile)


            if filedate > marker and thirdparty == "N":
                repo = newds.Repo_Connect("Development")
                pid = newds.Get_Pid(xfile,repo)
                if pid is not None:
                    pids.append(pid)
        if json == True:
            with open("pids.json", "w") as f:
                data = json.dump(pids, f)

        return pids

                                        
    

        

        
