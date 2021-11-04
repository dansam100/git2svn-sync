from config import git_url, git_branch, git_pull_timeout, TRACE_LOGS
from git import Repo

repo = Repo(git_url)
print("GIT version", repo.git.version_info, "\n")

branch_exists = False
for ref in repo.references:
    if git_branch == ref.name:
        print(f"Checking out branch: {git_branch}\n")
        repo.git.checkout(git_branch)
        branch_exists = True
        break

if not branch_exists:
    print(f"Checking out NEW branch: {git_branch}\n")
    repo.git.checkout('-b', git_branch)


def get_last_commit(with_pull=True):
    origin = repo.remote('origin')

    if with_pull:
        origin.pull(kill_after_timeout=git_pull_timeout)

    return repo.head.commit


def get_revisions_since(rev):
    cmd = repo.git
    rev_str = cmd.rev_list(f"{rev}..HEAD")

    return reversed(rev_str.split("\n")) if rev_str else []


def get_diff(rev):
    cmd = repo.git
    diff = cmd.diff("--no-prefix", f"{rev}~1..{rev}")
    files = cmd.diff("--name-only", f"{rev}~1..{rev}")
    msg = cmd.log("--pretty=format:%B", f"{rev}~1..{rev}")
    author = cmd.log("--pretty=format:%ce", f"{rev}~1..{rev}")

    if TRACE_LOGS:
        print(f"Diff (revision = {rev})\n\n{diff}")
        print(f"Files (revision = {rev})\n\n{files}")

    return msg, author, diff, files.split("\n") if files else []
