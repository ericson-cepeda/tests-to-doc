# Check git repos and upload them to bitbucket

This script check git repositories into the gived path and upload them to bitbucket, Additionally if any repo is dirty, the repo is uploaded to bitbucket with an `uncommited` branch

## Installation

```
$ mkvirtualenv check-git-repos
$ pip install -r requirements.txt
```

## Usage

It is necessary to have an `.env` file located where you want with bitbucket credentials as shown below

```
BITBUCKET_USER="myUser"
BITBUCKET_PASSWORD="myPassword"
```

after that you can run the script

```
python script.py -path [working/tree/directory] -owner [myTeam]
```

For more info about the params execute 

```
python script.py -help
```


