# git2svn-sync
Syncs changes in git with svn by tracking diffs over time

# Config
Config.py allows you to configure your local git repo that is to be synced along with the local SVN repo.
The remote SVN url is needed for switching users when commits are to be synced as the original authors

# Setup
Create a file called `last` which contain the last git-svn revision that has been synced over to your svn repo.
NOTE: This requires that you have moved over the base SVN repo to Git at least once, or vice versa.

A sample "last" file looks like the following:
```
e8fb8b3f42b9b0329c53c83bc29103dbc195df23=>-1
```
This is a 'git' revision number mapped to an 'svn' revision number using '=>'

# Run
Use `python app.py` to run the application once everything has been setup

# Docker
You may create a docker container using the associated docker file to run this as a standalone app
