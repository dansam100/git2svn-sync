import os

DUMMY_SVN = False
TRACE_LOGS = False
SWITCH_USER_FOR_COMMITS = False
USE_PATCH_TOOL = True
USE_SVN_PATCH_FORMAT = False

root_dir = os.getcwd().replace("\\", "/")
patches_dir = f"{root_dir}/patches/"

git_url = "C:/work/git_repo"
git_branch = "master"
git_pull_timeout = 60000

svn_url = 'C:/work/svnroot'
svn_branch = "trunk"
svn_remote_url = "https://svn.company.com/svn/branches/trunk"

print(f"Sys args: TRACE_LOGS={TRACE_LOGS}, USE_PATCH_TOOL={USE_PATCH_TOOL}")
print(f"SVN args: SWITCH_USER_FOR_COMMITS={SWITCH_USER_FOR_COMMITS}, DUMMY_SVN={DUMMY_SVN}, USE_SVN_PATCH_FORMAT={USE_SVN_PATCH_FORMAT}")

print(f"Git repo: {git_url}, branch: {git_branch}, pull timeout: {git_pull_timeout}")
print(f"SVN repo: {svn_url}, branch: {svn_branch} remote: {svn_remote_url}")
print("\n\n")
