import sys
import re

import utils

re_head_svn = re.compile('^Index:')
re_diff_git = re.compile('^diff --git ([^ ]+) ([^ ]+$)')
re_diff_file_mode = re.compile('.+ file mode [0-9]+$')
re_diff_stat = re.compile('^(@@ -[^ ]+ \\+[^ ]+ @@).*$')
re_sim_index = re.compile('^similarity index [0-9]+%$')


def is_git_diff_header(line, i):
    if re_diff_git.match(line[i]):
        if re_diff_file_mode.match(line[i + 1]):
            i += 1
        if line[i + 1].startswith('index ') and \
                line[i + 2].startswith('--- ') and \
                line[i + 3].startswith('+++ '):
            return True
    return False


def is_git_diff_rename_header(line, i):
    if re_diff_git.match(line[i]):
        if line[i + 1].startswith('similarity index ') and line[i + 2].startswith('rename from '):
            if line[i + 1][len('similarity index '):].startswith("100%"):
                return True, True
            else:
                return True, False
    return False, False


def is_svn_diff_header(line, i):
    if re_diff_git.match(line[i]):
        if re_diff_file_mode.match(line[i + 1]):
            i += 1
        if line[i + 1].startswith('--- ') and line[i + 2].startswith('+++ '):
            return True
    return False


def svn_convert_print_diff_header(line, i, revision):
    lines = []
    num_line = 4
    print(re_diff_git.sub(r'Index: \2', line[i]))
    lines.append(re_diff_git.sub(r'Index: \2', line[i]))

    if re_diff_file_mode.match(line[i + 1]):
        i += 1
        num_line += 1

    print('===================================================================')
    lines.append('===================================================================')
    if line[i + 2] == '--- /dev/null':
        filename = line[i + 3][len('+++ '):]
        print('--- %s\t(revision 0)' % filename)
        lines.append('--- %s\t(revision 0)' % filename)
    else:
        print('%s\t(revision %s)' % (line[i + 2], revision))
        lines.append('%s\t(revision %s)' % (line[i + 2], revision))

    if line[i + 3] == '+++ /dev/null':
        filename = line[i + 2][len('--- '):]
        print('+++ %s\t(working copy)' % filename)
        lines.append('+++ %s\t(working copy)' % filename)
    else:
        print('%s\t(working copy)' % line[i + 3])
        lines.append('%s\t(working copy)' % line[i + 3])

    return num_line, lines


def svn_convert_rename_header(line, i, revision):
    lines = []
    num_line = 6

    if len(line) > i + 3 and not line[i+3].startswith("rename to "):
        num_line = 5

    filename = re_diff_git.match(line[i]).group(1)
    rename = re_diff_git.match(line[i]).group(2)

    print(re_diff_git.sub(r'Index: \1', line[i]))
    lines.append(re_diff_git.sub(r'Index: \1', line[i]))

    print('===================================================================')
    lines.append('===================================================================')
    lines.append(f'--- {filename}\t(revision {revision}, rename: {rename})')
    lines.append(f'+++ {filename}\t(working copy)')

    return num_line, lines


def svn_format_diff(diff, revision=""):
    i = 0
    lines = []
    diff_lines = diff.split("\n")

    while i < len(diff_lines):
        if is_git_diff_header(diff_lines, i):
            num, out = svn_convert_print_diff_header(diff_lines, i, revision)
            i += num
            lines += out
        elif re_diff_stat.match(diff_lines[i]):
            print(re_diff_stat.sub(r'\1', diff_lines[i]))
            lines.append("\n" + re_diff_stat.sub(r'\1', diff_lines[i]))
            i += 1
        else:
            is_rename, no_changes = is_git_diff_rename_header(diff_lines, i)
            if is_rename and not no_changes:
                num, out = svn_convert_rename_header(diff_lines, i, revision)
                i += num
                lines += out
            elif i == (len(diff_lines) - 1):
                # last line
                sys.stdout.write(diff_lines[i])
                # output += diff_lines[i] + '\n'
            else:
                print(diff_lines[i])
                lines.append(diff_lines[i])
            i += 1

    return lines


def git_convert_print_diff_header(line, i, revision):
    lines = []
    num_line = 2

    filename = line[i][len('Index: '):]

    # diff --git node
    if line[i + 1].startswith("========="):
        i += 1
    if re_diff_git.match(line[i + 1]):
        i += 1
        lines.append(f"diff --git a/{filename} b/{filename}")
        num_line += 1

    if re_diff_file_mode.match(line[i + 1]):
        i += 1
        lines.append(line[i])
        num_line += 1

    if line[i].startswith("deleted"):
        lines.append(f"index {revision}..0000000 100644")
        lines.append(f"--- a/{filename}")
        lines.append('+++ /dev/null')
        num_line += 2
    elif line[i].startswith("new"):
        lines.append(f"index 0000000..{revision} 100644")
        lines.append('--- /dev/null')
        lines.append(f"+++ b/{filename}")
        if line[i + 1].startswith("GIT binary patch"):
            lines.append(line[i + 1])
            lines.append(line[i + 2])
        num_line += 2
    else:
        lines.append(f"index {revision}..1111111 100644")
        lines.append(f"--- a/{filename}")
        lines.append(f"+++ b/{filename}")
        num_line += 2

    return num_line, lines


def git_format_diff(diff: str, revision=""):
    i = 0
    lines = []
    diff_lines = diff.replace("\r", "").split("\n")
    skip_node = False

    while i < len(diff_lines):
        if re_head_svn.match(diff_lines[i]):
            skip_node = False
            num, out = git_convert_print_diff_header(diff_lines, i, revision)
            # print("\n".join(out))
            if len(diff_lines) > (i + 8) and diff_lines[i + 6].startswith("Property changes on:") \
                    and diff_lines[i + 8].startswith("Deleted: svn:ignore"):
                print("Skipping garbage lines")
                skip_node = True
                i += num
            else:
                i += num
                lines += out
        elif skip_node:
            if i == (len(diff_lines) - 1):
                # last line
                lines.append("")
            i += 1
        elif re_diff_stat.match(diff_lines[i]):
            # print(re_diff_stat.sub(r'\1', diff_lines[i]))
            lines.append(re_diff_stat.sub(r'\1', diff_lines[i]))
            i += 1
        else:
            if i == (len(diff_lines) - 1):
                # last line
                sys.stdout.write(diff_lines[i])
                lines.append(diff_lines[i] + '\n')
            else:
                # print(diff_lines[i])
                lines.append(diff_lines[i])
            i += 1

    return lines


def git_get_binary_files(diff: str):
    i = 0
    files = []
    diff_lines = diff.replace("\r", "").split("\n")

    while i < len(diff_lines):
        if re_diff_git.match(diff_lines[i]):
            if re_diff_file_mode.match(diff_lines[i + 1]) and diff_lines[i + 1].startswith("new file"):
                if len(diff_lines) > (i + 5) and diff_lines[i + 5].startswith("GIT binary patch"):
                    files.append(diff_lines[i + 4][len("+++ b/"):])
                elif len(diff_lines) > (i + 3) and diff_lines[i + 3].startswith("GIT binary patch"):
                    files.append(re_diff_git.match(diff_lines[i]).group(2))
            elif diff_lines[i + 1].startswith("index "):
                if len(diff_lines) > (i + 4) and diff_lines[i + 4].startswith("GIT binary patch"):
                    files.append(diff_lines[i + 3][len("+++ "):])

        i += 1

    return files


def git_get_rename_files(diff: str):
    i = 0
    files = []
    diff_lines = diff.replace("\r", "").split("\n")

    while i < len(diff_lines):
        if re_diff_git.match(diff_lines[i]):
            if re_sim_index.match(diff_lines[i + 1]):
                if len(diff_lines) > (i + 2) and diff_lines[i + 2].startswith("rename from"):
                    from_file = diff_lines[i + 2][len("rename from "):]
                    if len(diff_lines) > (i + 3):
                        to_file = diff_lines[i + 3][len("rename to "):]
                    else:
                        to_file = diff_lines[i][len(f"diff --git {from_file} "):]
                    files.append(
                        {
                            'from': from_file,
                            'to': to_file
                         }
                    )

        i += 1

    return files


