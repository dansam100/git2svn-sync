import sys
import re

re_diff_git = re.compile('^diff --git [^ ]+ ([^ ]+$)')
re_diff_file_mode = re.compile('.+ file mode [0-9]+$')
re_diff_stat = re.compile('^(@@ -[^ ]+ \\+[^ ]+ @@).*$')


def is_diff_header(line, i):
    if re_diff_git.match(line[i]):
        if re_diff_file_mode.match(line[i+1]):
            i += 1
        if line[i+1].startswith('index ') and \
            line[i+2].startswith('--- ') and \
                line[i+3].startswith('+++ '):
            return True
    return False


def convert_print_diff_header(line, i, revision):
    lines = []
    num_line = 4
    print(re_diff_git.sub(r'Index: \1', line[i]))
    lines.append(re_diff_git.sub(r'Index: \1', line[i]))

    if re_diff_file_mode.match(line[i+1]):
        i += 1
        num_line += 1

    print('===================================================================')
    lines.append('\n===================================================================')
    if line[i+2] == '--- /dev/null':
        filename = line[i+3][len('+++ '):]
        print('--- %s\t(revision 0)' % filename)
        lines.append('\n--- %s\t(revision 0)' % filename)
    else:
        print('%s\t(revision %s)' % (line[i+2], revision))
        lines.append('\n%s\t(revision %s)' % (line[i+2], revision))

    if line[i+3] == '+++ /dev/null':
        filename = line[i+2][len('--- '):]
        print('+++ %s\t(working copy)' % filename)
        lines.append('\n+++ %s\t(working copy)' % filename)
    else:
        print('%s\t(working copy)' % line[i+3])
        lines.append('\n%s\t(working copy)' % line[i+3])

    return num_line, lines


def svn_format_diff(diff, revision=""):
    i = 0
    lines = []
    diff_lines = diff.split("\n")

    while i < len(diff_lines):
        if is_diff_header(diff_lines, i):
            num, out = convert_print_diff_header(diff_lines, i, revision)
            i += num
            lines += out
        elif re_diff_stat.match(diff_lines[i]):
            print(re_diff_stat.sub(r'\1', diff_lines[i]))
            lines.append("\n" + re_diff_stat.sub(r'\1', diff_lines[i]))
            i += 1
        else:
            if i == (len(diff_lines) - 1):
                # last line
                sys.stdout.write(diff_lines[i])
                # output += diff_lines[i] + '\n'
            else:
                print(diff_lines[i])
                lines.append(diff_lines[i])
            i += 1

    return lines
