import sys
import os
import argparse
import requests
from dotenv import load_dotenv, find_dotenv
from git import Repo, cmd
from slugify import slugify
# load .env
load_dotenv(find_dotenv())

BITBUCKET_USER = os.environ.get("BITBUCKET_USER")
BITBUCKET_PASSWORD = os.environ.get("BITBUCKET_PASSWORD")

# owner can be the user or team
def create_bitbucket_repo(user, pwd, owner, repo_slug):
    data = {"scm": "git", "is_private": "true", "fork_policy": "no_public_forks"}
    url = "https://api.bitbucket.org/2.0/repositories/%s/%s"%(owner, repo_slug)
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=data,headers=headers, auth=(user, pwd))
    if "error" in response.json():
        print response.json()["error"]["message"]

def get_repos_dirs(tree_dir):
    # repos dirs
    repos_dirs = []

    subdirs = [x[0] for x in os.walk(tree_dir)]
    for subdir in subdirs:
        try:
            repo = Repo(subdir)
            # if subfolder does not have the sufix .git then add it
            if(subdir.split('.')[-1] != 'git'):
                repos_dirs.append(subdir)

        except:
            pass

    return repos_dirs

def check_git_repos(cmdargs):
    # path gived by user
    root = cmdargs.path

    # Bitbucket crendentials
    pwd = BITBUCKET_PASSWORD
    user = BITBUCKET_USER
    owner = cmdargs.owner

    if(os.path.exists(cmdargs.path)):
        formated_root = os.path.abspath(root)

        #get the repos dirs
        repo_dirs = get_repos_dirs(formated_root)

        for repo_dir in repo_dirs:
            # get the repo name from remote origin url as <name>.git
            g = cmd.Git(repo_dir)

            # if repo has origin set name based on it
            try:
                repo_name = g.execute(["git", "config", "--get", "remote.origin.url"]).split('/')[-1].split(".")[0]
            except:
                # if repo has not origin set name based on its folder name
                repo_name = repo_dir.split('/')[-1].lower().replace(" ","_")

            repo_name = slugify(repo_name)
            # @TODO: Maybe picorb could be replaced with a sysargv
            url = 'git@bitbucket.org:%s/%s'%(owner,repo_name)

            repo = Repo(repo_dir)

            # create a temporal remote
            try:
                # delete bitbucket_remote if it exists
                repo.delete_remote('bitbucket_remote')
            except:
                pass

            bitbucket_remote = repo.create_remote('bitbucket_remote',url)

            # create the bitbucket repo
            create_bitbucket_repo(user, pwd, owner, repo_name)
            print repo_name

            # check if repo has uncommited changes
            if (repo.is_dirty() or len(repo.untracked_files)>0):
                print "This repo is dirty: ", repo_name
                # create/change branch
                try:
                    g.execute(["git", "checkout", "-b", "uncommited"])
                except:
                    g.execute(["git", "checkout", "uncommited"])
                g.execute(["git", "add", "-A"])
                g.execute(["git", "commit", "-m", '"uncommited changes"'])

            # Push all branches to the new remote
            g.execute(["git", "push", "bitbucket_remote", "--all"])

            # delete temporal remote
            repo.delete_remote(bitbucket_remote)

    else:
        sys.stderr.write('Please enter a valid path. \n')


def main(argv=None):
    description = "This script check git repositories into the gived path and upload the dirty repos to bitbucket"
    parser = argparse.ArgumentParser(description=description, add_help=True)
    parser.add_argument('-path', dest='path', type=str, help='The path to check', required=True)
    parser.add_argument('-owner', dest='owner', type=str, help='Bitbucket team or owner', required=True)
    cmdargs = parser.parse_args()
    check_git_repos(cmdargs)


if __name__ == '__main__':
    status = main(sys.argv[1:])
    sys.exit(status)
