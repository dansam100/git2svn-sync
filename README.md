# git2svn-sync
Syncs changes in git with svn by tracking diffs over time

# Config
Config.py allows you to configure your local git repo that is to be synced along with the local SVN repo.
To sync commits using the orignal commit authors, your svn repo must have the pre-revprop-hook enabled for 'svn:author' and 'svn:log'.
Sample below (only allows "subversionUser" to change authors on commits and anyone to change logs)

```
REM Only allow log messages or author to be changed.
if "%4" == "svn:log" exit 0
if "%4" == "svn:author" (
	if "%3" == "subversionUser" (
		exit 0
	)
)
echo "Property '%4' cannot be changed by '%3' on revision '%2'" >&2
exit 1
```

# Setup
Create a file called `sync_last` which contain the last git-svn revision that has been synced over to your svn repo.
NOTE: This requires that you have moved over the base SVN repo to Git at least once, or vice versa.

A sample "sync_last" file looks like the following, when syncing from git to svn:
```
e8fb8b3f42b9b0329c53c83bc29103dbc195df23=>23040
```
This is a 'git' sha mapped to an 'svn' revision using '=>'.
Conversely, the `sync_last` file looks like the following when syncing from svn to git
```
23040=>e8fb8b3f42b9b0329c53c83bc29103dbc195df23
```

# Run
Use `python app.py` to run the application once everything has been setup

# Docker
You may create a docker container using the associated docker file to run this as a standalone app
You will need to mount the svn and git repos into the docker container as volumes
