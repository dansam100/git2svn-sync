from config import svn_url, ALLOW_SWITCH_USER, DUMMY_SVN
import svn.local
import pprint

repo = svn.local.LocalClient(svn_url)


def get_last_commit(with_pull=True):
    print("Getting last commit details from svn (svn info)")
    if DUMMY_SVN:
        return

    if with_pull:
        repo.update()

    info = repo.info()
    pprint.pprint(info)

    return info


def switch_user(user):
    print(f"Performing 'svn relocate {user}'")
    if not ALLOW_SWITCH_USER or DUMMY_SVN:
        return

    print(f"Switching to user: {user}")
    repo.run_command(f"relocate svn+ssh//{user}@svn_remote_url")


def commit(message, author, rev, diff, files):
    print(f"Performing 'svn commit --username {author} -m {message} <diff> {','.join(files)}'")
    if DUMMY_SVN:
        return "dummy_commit", -1

    switch_user(author)

    commit_msg = f"{message}\n\nSynced from: {rev}"
    apply(diff)
    repo.commit(commit_msg, files)
    commit_info = get_last_commit(with_pull=False)

    return commit_msg, commit_info['commit_revision']


def apply(rev, diff):
    print("Performing 'svn patch <diff>'")
    if DUMMY_SVN:
        return

    patch = f"./patches/{rev}.txt"
    with open(patch, "r") as patch_file:
        patch_file.write(diff)
        patch_file.close()

    repo.run_command("patch", patch)


def cleanup():
    print("Performing 'svn cleanup'")
    if DUMMY_SVN:
        return

    repo.cleanup()
