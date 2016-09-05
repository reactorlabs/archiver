#! /usr/bin/python3
from datetime import datetime
import sys
import time
import os
import subprocess
import tempfile
import shutil

sys.path.append(".")
import config

# repositories to be checked
repo_info = []
repo_dates = []

def removeRepo():
    """ Removes the repository folder (repo) if it exists. """
    if (os.path.isdir("repo")):
        shutil.remove("repo")

def clone(address, into):
    """ Clone the given repository (assuming passwordless ssh login) into local folder repo. """
    removeRepo();
    subprocess.call(["git", "clone", address, into])

def getRemotes(repo):
    """ Returns set of remote addresses for given repository """
    try:
        raw = subprocess.check_output(["git", "-C", repo, "remote", "-v"], stderr=subprocess.PIPE).decode("utf-8")
        result = set()
        for l in raw.split("\n"):
            l = l.strip()
            if (len(l) == 0):
                continue
            result.add(l.split("\t")[1].split(" ")[0])
        return result
    except:
        return set()

     



def branches():
    """ Returns set of branches for the used repository. """
    raw = subprocess.check_output(["git", "-C", "repo", "branch", "-a"]).decode("utf-8")
    result = set()
    for line in raw.split("\n"):
        line = line.strip()
        if (not line):
            continue
        if (line.find("->") >= 0):
            continue
        if (line[0] == "*"):
            line = line[1:].strip()
        if (line.startswith("remotes/origin/")):
            line = line[15:].strip()
        result.add(line)
    return result
    
def checkout(branchName):
    """ Checkout given branch """
    subprocess.call(["git", "-C", "repo", "checkout", branchName])
    
def getRevisions(date, repo):
    year = date[0]
    month = date[1]
    since = "\"{m}/1/{y}\"".format(m = month, y = year)
    month += 1
    if (month == 13):
        month = 1
        year += 1
    until = "\"{m}/1/{y}\"".format(m = month, y = year)
    raw = subprocess.check_output(["git", "-C", repo, "log", "--pretty=format:%H %ae", "--since", since, "--until", until, "--all"]).decode("utf-8")
    result = []
    for line in raw.split("\n"):
        line = line.strip()
        if (not line):
            continue
        line = line.split(" ")
        if (line[1] in config.useremail):
            result.append(line[0])
    return result

def getPatch(rev, p, repo):
    """ Creates a revision patch. """
    subprocess.call(["git", "-C", repo, "format-patch", "-1", rev, "-o", p]) 
    
def compressDir(folder, name, outdir):
    f = "{0}.tar.gz".format(name)
    old = os.getcwd()
    os.chdir(folder)
    subprocess.call(["tar", "-zcf", os.path.join(outdir, f), "."])
    os.chdir(old)
    shutil.rmtree(folder)
                            
             
    
def repoFilename(repoAddress):
    """ Returns a safe filename created from the repository's address. Replaces all non-standard characters by underscore. """
    return repoAddress.replace("/", "_").replace(":","_").replace("\\","_").replace(".","_")

    
    
def help():
    """ A simple help print procedure. """
    print("""
    Archiver
    

    
    """)    

def loadConfig():
    """ Loads the configuration from the commandline. 

    TODO: Actually implement, as of now, only takes information from the config.py file.  """
    if (config.till == ()):
        y = datetime.now().year
        m = datetime.now().month
        if (m == 1):
            m = 12
            y = y - 1
        config.till = (y, m)
    pass

def loadRepositories():
    """ Loads the repositories into the repository directory. """
    global repo_info
    to_clone = config.repository[:]
    # make sure the repository directory exists
    if (not os.path.isdir(config.repository_dir)):
        print("- repository directory {0} does not exist, creating...".format(config.repository_dir))
        os.makedirs(config.repository_dir)
    # now that we are sure repository dir exists, walk its directories and try to find repositories 
    for d in os.listdir(config.repository_dir):
        print("- checking {0} for git repository...".format(d))
        repo_path = os.path.join(config.repository_dir, d)
        remotes = getRemotes(repo_path)
        if (len(remotes) == 0):
            print("  not a git repository")
        else:
            # it is a git repository, try to find if it is in our list
            for r in config.repository:
                if (r in remotes):
                    print("  matched to {0}".format(r))
                    to_clone.remove(r)
                    repo_info.append((repo_path, False, r)) # false because we should not delete it at the end
                    break
    # now fetch the missing repositories
    if (len(to_clone) > 0):
        print("- fetching missing repositories")
        for r in to_clone:
            print("  {0}...".format(r))
            tf = tempfile.mkdtemp(prefix = "archiver", dir = config.repository_dir)
            print(tf)
            clone(r, tf)
            repo_info.append((tf, True, r)) # true, because we must clean the directory afterwards  

def initializeOutput():
    """ Checks that the output directory exists, creates one, if it does not and sets the list of months to create. """
    global repo_dates
    # make sure the output directory exists
    if (not os.path.isdir(config.output_dir)):
        print("- output directory {0} does not exist, creating...".format(config.output_dir))
        os.makedirs(config.output_dir)
    # now check all months from since date to
    y, m = config.since
    end = config.till[0] * 12 + config.till[1]
    while (y * 12 + m <= end):
        if (not os.path.isdir(os.path.join(config.output_dir, "{0}_{1}".format(y,m)))):
            repo_dates.append((y,m))
        m = m + 1
        if (m == 13):
            m = 1
            y = y + 1

def cleanup():
    """ Deletes temporary files. """
    global repo_info
    print("- cleanup")
    for x in repo_info:
        if (x[1] == True):
            print("  {0}...".format(x[0]))
            shutil.rmtree(x[0])




if (__name__ == "__main__"):
    # load the confifguration
    loadConfig()
    # populate repositories
    loadRepositories()
    # initialize the output directory and the months to archive
    initializeOutput()
    if (len(repo_info) == 0 or len(repo_dates) == 0):
        print("! NOTHING TO DO")
    else:
        # for each repository, for each month output the tarball
        for r in repo_info:
            print("- {0}...".format(r[2]))
            for m in repo_dates:
                revs = getRevisions(m, r[0])
                if (len(revs) > 0):
                    print("  {0}/{1}...{2} revisions".format(m[0], m[1], len(revs)))
                    outdir = os.path.join(config.output_dir, "{0}_{1}".format(m[0], m[1]))
                    os.makedirs(outdir, exist_ok = True)
                    # get all patches
                    outTemp = os.path.join(outdir, repoFilename(r[2]))
                    os.makedirs(outTemp, exist_ok = True)
                    print("    creating patches...")
                    for rev in revs:
                        getPatch(rev, outTemp, r[0])
                    # compress the directory
                    print("    archiving...")
                    compressDir(outTemp, repoFilename(r[2]), outdir)










    # and now the cleanup
    cleanup()







    
#clone("git@github.com:reactorlabs/rjit.git")

#for b in branches():
#    print("Checking branch {0}".format(b))
#month = 2
#year = 2016
#
#tempDir = "{y}_{m}".format(y = year, m = month)
#
#os.mkdir(tempDir)
#
#revs = getRevisions(month, year, ["peta.maj82@gmail.com"])
#print("  {0} commits found".format(len(revs)))
#for rev in revs:
#    getPatch(rev, tempDir)
# now tar the dir
#compressDir(tempDir)

#removeRepo()
