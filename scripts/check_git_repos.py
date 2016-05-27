import sys
import os
import argparse
from git import Repo, cmd
from bitbucket.bitbucket import Bitbucket

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
	pwd = cmdargs.pwd
	user = cmdargs.pwd

	# Bitbucket Login
	bb = Bitbucket(user, pwd)

	if(os.path.exists(cmdargs.path)):
		formated_root = os.path.abspath(root)

		#get the repos dirs
		repo_dirs = get_repos_dirs(formated_root)

		for repo_dir in repo_dirs:
			# generate the URL based on folder 
			g = cmd.Git(repo_dir)
			
			# get the repo name from remote origin url as <name>.git
			repo_name = g.execute(["git", "config", "--get", "remote.origin.url"]).split('/')[-1]

			# @TODO: Maybe picorb could be replaced with a sysargv
			url = 'git@bitbucket.org:picorb/%s'%(repo_name)

			repo = Repo(repo_dir)
			# check if repo has uncommited changes
			if (repo.is_dirty()):
				remote_check = repo.create_remote('check_repo',url)
				# @TODO: Implement this 
				repo.delete_remote(remote_check)

	else:
		sys.stderr.write('Please enter a valid path. \n')


def main(argv=None):
	description = "This script check git repositories into the gived path and upload them to bitbucket"
	parser = argparse.ArgumentParser(description=description, add_help=True)
	parser.add_argument('-path', dest='path', type=str, help='The path to check', required=True)
	parser.add_argument('-user', dest='user', type=str, help='Bitbucket username', required=True)
	parser.add_argument('-pwd', dest='pwd', type=str, help='Bitbucket password', required=True)
	cmdargs = parser.parse_args()
	check_git_repos(cmdargs)
	

if __name__ == '__main__':
  status = main(sys.argv[1:])
  sys.exit(status)
