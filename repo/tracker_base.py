import difflib
from typing import List, NamedTuple

from utils import file_utils, logger, diff_tools

logger = logger.get_logger(__name__)


class IdenticalCheckResult(NamedTuple):
    is_identical: bool
    files: List[str]
    diff_count: int
    identical_count: int


class TrackerMeta(type):
    """A repo tracker metaclass that will be used for tracker creation"""

    def __instancecheck__(cls, instance):
        return cls.__subclasscheck__(type(instance))

    def __subclasscheck__(cls, subclass):
        return (hasattr(subclass, 'get_revisions_since') and
                callable(subclass.get_revisions_since) and
                hasattr(subclass, 'get_last_commit') and
                callable(subclass.get_last_commit) and
                hasattr(subclass, 'get_diff') and
                callable(subclass.get_diff) and
                hasattr(subclass, 'commit') and
                callable(subclass.commit) and
                hasattr(subclass, 'repo_path') and
                callable(subclass.repo_path) and
                hasattr(subclass, 'repo') and
                callable(subclass.repo) and
                hasattr(subclass, 'run_command') and
                callable(subclass.run_command)
                )


class TrackerBase(metaclass=TrackerMeta):
    """A repo tracker that allows reading revisions, diffs and committing changes"""

    def __init__(self, name, tracker_type, repo_path, **kwargs):
        self.name = name
        self.type = tracker_type
        self.repo_path = repo_path
        self.args = kwargs

    def run_command(self, subcommand, args=(), encoding="utf-8-sig", return_binary=False):
        pass

    def overwrite_file(self, file, contents):
        logger.info(f"Overwriting file: {file} with new contents")
        logger.debug(f"Overwrite contents: {contents}")

        file_path = f"{self.repo_path}/{file}"
        file_utils.overwrite_file(file_path, contents)

    def get_file(self, rev, file, is_binary=False, encoding="utf-8-sig"):
        pass

    def get_current_file(self, file, is_binary=False, encoding="utf-8-sig"):
        logger.info(f"Pulling contents of file (local) = {file} and is_binary={is_binary}")

        file_path = f"{self.repo_path}/{file}"
        if not file_utils.file_exists(file_path):
            return ""

        with open(file_path, "r", encoding=encoding) as file:
            file_contents = file.read()

        if is_binary:
            return bytearray(file_contents, encoding=encoding)

        return "\n".join(file_contents.splitlines(keepends=False))

    def format_and_save(self, rev, diff):
        pass

    def get_diff(self, rev: str):
        pass

    def cleanup(self):
        pass

    def get_last_commit(self, with_pull=False):
        pass

    def get_revisions_since(self, rev):
        pass

    def commit(self, date, msg, author, rev, diff, files=(), src=None):
        pass

    def verify_apply(self, rev: str, src, diff: str, files: List[str]) -> bool:
        logger.info(f"Verifying patch apply for {len(files)} files for rev: {rev}")
        binary_files = diff_tools.git_get_binary_files(diff)
        logger.info(f"Binary files will be skipped: {binary_files}")

        files_to_verify = list(filter(lambda f: f not in binary_files, files))
        check_identical = TrackerBase.check_identical_files(rev, src, self, files_to_verify)
        if not check_identical.is_identical:
            logger.info(f"Copy files over manually as last resort, files = {check_identical.files}")
            TrackerBase.try_copy_files(rev, src, self, check_identical.files)
            check_identical = TrackerBase.check_identical_files(rev, src, self, files_to_verify)
            if not check_identical.is_identical:
                logger.error(f"Rev: {rev} differs in {src.type} and {self.type} by {check_identical.diff_count} files")
                return False
        else:
            logger.info(f"Rev: {rev} from {src.type} is identical to HEAD in {self.type}. Skipping...")

        return True

    @staticmethod
    def check_identical_files(rev: str, src, tgt, files: List[str]) -> IdenticalCheckResult:
        diffs = {}
        diff_files = []
        diff_count = 0
        identical_count = 0
        is_identical = len(files) > 0

        for file in files:
            is_file_identical = True
            try:
                src_content: str = src.get_file(rev, file)
                tgt_content: str = tgt.get_current_file(file)
                print(f"Src: {src_content}")
                print(f"Tgt: {tgt_content}")
                if file_utils.is_content_identical(tgt_content, src_content):
                    identical_count += 1
                else:
                    is_file_identical = False
                    diff_count += 1
                    diff_files.append(file)
                    diffs[file] = difflib.unified_diff(tgt_content.splitlines(keepends=False),
                                                       src_content.splitlines(keepends=False))
            except Exception as e:
                logger.error(e, "Failed in 'check_identical_files'")
                is_file_identical = False
                diff_count += 1
                diff_files.append(file)
                diffs[file] = repr(e)
            finally:
                is_identical &= is_file_identical
                result = "contents same" if is_file_identical else "files differ"
                logger.info(f"Checking if {file} is identical ({src.type} => {tgt.type}) => {result}")

        for name, diff in diffs.items():
            logger.info(f"diff({name}):" + '\n'.join(diff))

        return IdenticalCheckResult(is_identical, diff_files, diff_count, identical_count)

    @staticmethod
    def try_copy_files(rev: str, src, tgt, files: List[str]):
        logger.info(f"Overwriting files: {files}")
        for file in files:
            logger.info(f"Attempt to overwrite file ({src.type} => {tgt.type}): {file}")
            contents = src.get_file(rev, file)
            tgt.overwrite_file(file, contents)
