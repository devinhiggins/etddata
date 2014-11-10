# solrdata.py

import requests

class SolrData():
    def __init__(self):
        pass

    @staticmethod
    def ResultCount(self, query_url):
        
        r = requests.get(query_url)
        if r.ok:
            results = r.json()
            item_count = results['response']['numFound']
        else:
            item_count = 0

        return item_count


class SolrEtdData(SolrData):
    def __init__(self, query_url):

        self.query_url = query_url
        self.r = requests.get(query_url)
        if not r.ok:
            print "Faulty URL"
        

    def GetAllUrl(self):
        

    def GetAll(self):
        item_count = self.ResultCount(self.query_url)


