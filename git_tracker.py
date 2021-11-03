from config import git_url, TRACE_LOGS
from git import Repo

repo = Repo(git_url)
print(repo.git._version_info)


def get_last_commit(with_pull=True):
    origin = repo.remote('origin')

    if with_pull:
        origin.pull(kill_after_timeout=60000)

    return repo.head.commit


def get_revisions_since(rev):
    cmd = repo.git
    rev_str = cmd.rev_list(f"{rev}..HEAD")

    return reversed(rev_str.split("\n")) if rev_str else []


def get_diff(rev):
    cmd = repo.git
    diff = cmd.diff("--no-prefix", "-p", "--raw", f"{rev}~1..{rev}")
    files = cmd.diff("--name-only", f"{rev}~1..{rev}")
    msg = cmd.log("--pretty=format:%B", f"{rev}~1..{rev}")
    author = cmd.log("--pretty=format:%aN", f"{rev}~1..{rev}")

    if TRACE_LOGS:
        print(f"Diff (revision = {rev})\n\n{diff}")
        print(f"Files (revision = {rev})\n\n{files}")

    return msg, author, diff, files.split("\n") if files else []
