def get_last_revision():
    with open("last", "r") as infile:
        git_rev, svn_rev = infile.read().split('=>')
        infile.close()

    return git_rev, svn_rev


def get_last_git_revision():
    with open("last", "r") as infile:
        git_rev, svn_rev = infile.read().split('=>')
        infile.close()

    return git_rev


def get_last_svn_revision():
    with open("last", "r") as infile:
        git_rev, svn_rev = infile.read().split('=>')
        infile.close()

    return svn_rev


def set_last_revision(git_rev, svn_rev):
    print(f"Saving last revision {git_rev} => {svn_rev}")
    with open("last", "r") as infile, open("last.bk", "w") as outfile:
        rev = infile.read()
        outfile.write(rev)
        outfile.flush()
        infile.close()
        outfile.close()

    with open("last", "w") as save_file:
        save_file.write(f"{git_rev}=>{svn_rev}")
        save_file.flush()
        save_file.close()


def save_pending_revisions(pending_revs):
    if not pending_revs or len(pending_revs) <= 0:
        print("No revs to write")
        return

    print(f"Writing {len(pending_revs)} revs to 'pending' file")
    with open("pending", "w") as pending_file:
        pending_file.write("\n".join(pending_revs))
        pending_file.flush()
        pending_file.close()
