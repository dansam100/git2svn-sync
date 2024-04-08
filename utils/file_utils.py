import os
import errno
import unicodedata
import time
import difflib


def wait_until(predicate, timeout=False, period=0.25, *args, **kwargs):
    must_end = time.time() + (timeout if timeout else 0)
    while not timeout or time.time() < must_end:
        if predicate(*args, **kwargs):
            return True
        time.sleep(period)
    return False


def remove_control_characters(s):
    result = ""
    for ch in s:
        if unicodedata.category(ch)[0] != "C":
            result += ch
        else:
            result += ';'

    return result


def is_content_identical(content1: str, content2: str):
    diff = list(difflib.unified_diff(content1.splitlines(keepends=False), content2.splitlines(keepends=False)))
    diff_str = "\n".join(diff)
    has_no_diff = "" == diff_str
    print(f"No diff={has_no_diff}: Compare diff is:" + diff_str)
    # return "" == "\n".join(filter(lambda l: l.strip(), diff))
    return has_no_diff


def overwrite_file(file_path, contents, encoding="utf-8-sig"):
    binary = False if isinstance(contents, str) else True
    create_folders(file_path)
    if binary:
        print(f"Writing '{file_path}' with mode 'binary'")
        with open(file_path, "wb") as file_to_write:
            file_to_write.write(contents)
            file_to_write.flush()
            file_to_write.close()
    else:
        print(f"Writing '{file_path}' with mode 'text', encoding={encoding}")
        with open(file_path, "w", encoding=encoding) as file_to_write:
            file_to_write.write(contents)
            file_to_write.flush()
            file_to_write.close()


def create_folders(path):
    if not os.path.exists(os.path.dirname(path)):
        try:
            os.makedirs(os.path.dirname(path))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise


def folder_exists(path):
    return os.path.exists(os.path.dirname(path))


def file_exists(path):
    return os.path.exists(path)


def is_svn_to_git_mode(mode):
    return mode == "svn=>git"


def is_git_to_svn_mode(mode):
    return mode == "git=>svn"
