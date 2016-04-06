"""Set of functions to initiate access to FC repo."""
import logging
import os
import ConfigParser
from eulfedora.server import Repository


def get_configs(server):
    config = ConfigParser.ConfigParser()
    cwd = os.path.dirname(os.path.abspath(__file__))
    config_file = "default.cfg"

    config.read(cwd+"/"+config_file)
    username = config.get(server, "username")
    password = config.get(server, "password")
    root = config.get(server, "root")

    return username, password, root


def repo_connect(server):
    username,password,root = get_configs(server)
    repo = Repository(root=root, username=username, password=password)
    return repo


def get_pid(xml, repo):
    localID = u'local:\xa0'+xml[:-9]
    pid_check = list(repo.find_objects(identifier=localID))
    if len(pid_check) == 0:
        pid_check = list(repo.find_objects(identifier=localID.replace(u'\xa0', u'')))
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

def get_pid_by_filename(repo, search_term, namespace, return_all_objects=False):
    """Search repo for objects with filename in identifier field."""
    pid_check = list(repo.find_objects(identifier=search_term))
    logging.info("Found {0} items for {1}".format(len(pid_check), search_term))
    pid = None
    pids = []
    for item in pid_check:
        logging.info("Matching item: {0}".format(item))
        if return_all_objects:
            pids.append(str(item))
        else:
            if str(item).startswith(namespace):
                pid = str(item)
                break
    if return_all_objects:
        return pids
    else:
        return pid

def find_identifier(server, path, pids):
    """
    Iterate through XML files to find source file that matches a given PID.

    Positional arguments:
    server (str) -- name of server to access, e.g. "fedcomd", "fedcomm", etc.
    path (str) -- a path containing ETD xml documents.
    pids (list) -- a list of pids to check for.
    """
    repo = RepoConnect(server)
    xml_files = (x for x in os.listdir(path) if "DATA.xml" in x)
    for xml in xml_files:
        returned_pid = Get_Pid(xml, repo)
        if returned_pid in pids:
            print "{0} matches {1}".format(xml, returned_pid)
