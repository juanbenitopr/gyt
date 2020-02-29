import os
from typing import List, Union, Tuple
from gyt.exceptions import RepositoryNotFoundError, RepositoryEmpty
from gyt.utils import run_git_command


class Repository:

    def __init__(self, path: str):
        self.path = path
        self._global_args = ['-C', self.path]

    @property
    def current_branch(self) -> str:
        branch = self.execute(*'rev-parse --abbrev-ref HEAD'.split(' '))

        branch = branch.strip()

        if not branch:
            raise RepositoryEmpty()

        return branch

    @property
    def local_branches(self) -> List[str]:
        branch = self.execute('branch')

        branch = [b.strip() for b in branch.replace('* ', '').splitlines()]

        if not branch:
            raise RepositoryEmpty()

        return branch

    @property
    def remote(self) -> List[str]:
        remotes = self.execute('remote')

        remote_cleaned = [remote for remote in remotes.splitlines()]

        return remote_cleaned

    @classmethod
    def _create(cls, path: str):
        run_git_command('init', path)

    @classmethod
    def build(cls, path: str = '.', create_repository: bool = False, create_project: bool = False):
        repository_path = os.path.join(path, '.git')

        force_create = create_repository or create_project

        if not os.path.exists(repository_path) and not force_create:
            raise RepositoryNotFoundError()
        elif create_project:
            directory_path = os.path.join(path)
            os.makedirs(directory_path)
            cls._create(directory_path)
        elif create_repository:
            cls._create(path=path)

        return cls(path=path)

    def execute(self, command: str, *args) -> str:
        response = run_git_command(*self._global_args, *command.split(' '), *args)
        return response.stdout.decode('utf8')

    def status(self):
        response = self.execute('status')

        sections = {'branch': None, 'new': [], 'modified': [], 'untracked': []}

        for section in response.splitlines():
            section_cleaned = self._clean_status_line(section)

            if section_cleaned is None:
                continue

            section_cleaned, line_cleaned = section_cleaned

            if isinstance(sections[section_cleaned], list):
                sections[section_cleaned].append(line_cleaned)
            else:
                sections[section_cleaned] = line_cleaned

        return sections

    def _clean_status_line(self, line: str) -> Union[Tuple[str, str], None]:
        if line.startswith('On branch'):
            return 'branch', line.replace('On branch ', '')
        elif 'new file' in line:
            return 'new', line.replace('\tnew file:', '').strip()
        elif'modified' in line:
            return 'modified', line.replace('\tmodified:', '').strip()
        elif line.startswith('\t'):
            return 'untracked', line.strip()
        return None

    def add(self, files: List[str] = list(), all_files: bool = False):
        if all_files:
            self.execute('add -A')
        elif len(files) > 0:
            for file in files:
                self.execute('add', file)
        return self.status()

    def commit(self, message: str):
        self.execute('commit -m', message)
        return self.status()

    def add_remote(self, url: str, name: str='origin'):
        self.execute(f'remote add {name} {url}')
        return self.status()

    def remove_remote(self, name: str='origin'):
        self.execute(f'remote remove {name}')
        return self.status()

    def push(self, remote_name: str='origin', force: bool=False, remote_branch: str=None, local_branch: str=None):

        local_branch = local_branch or self.current_branch

        command = f'push {remote_name} {local_branch}'

        if remote_branch:
            command += f':{remote_branch}'

        if force:
            command += ' -f'

        self.execute(command)
        return self.status()

    def pull(self, remote_name: str='origin', force: bool=False, remote_branch: str=None, local_branch: str=None):
        local_branch = local_branch or self.current_branch

        command = f'pull {remote_name} {local_branch}'

        if remote_branch:
            command += f':{remote_branch}'

        if force:
            command += ' -f'

        self.execute(command)
        return self.status()

