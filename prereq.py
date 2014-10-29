# prereq.py

import os
import ConfigParser
from eulfedora.server import Repository

def Get_Configs(server):
    config = ConfigParser.ConfigParser()
    cwd = os.path.dirname(os.path.abspath(__file__))
    config_file = "default.cfg"
            
    config.read(cwd+"/"+config_file)
    username = config.get(server, "username")
    password = config.get(server, "password")
    root = config.get(server, "root")

    return username,password,root

def RepoConnect(server):
    username,password,root = Get_Configs(server)
    repo = Repository(root=root,username=username, password=password)
    return repo

def Get_Pid(xml, repo):
    localID = u'local:\xa0'+xml[:-9]
    pid_check = list(repo.find_objects(identifier=localID))
    if len(pid_check) == 0:
        pid_check = list(repo.find_objects(identifier=localID.replace("\xa0", "")))
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
