from pathlib import Path
import subprocess
from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QCoreApplication
import logging
from datetime import datetime
import git
from git import Repo, GitCommandError, InvalidGitRepositoryError, NoSuchPathError

class FileStatus(Enum):
    """Git file status types."""
    UNMODIFIED = ' '
    MODIFIED = 'M'
    ADDED = 'A'
    DELETED = 'D'
    RENAMED = 'R'
    COPIED = 'C'
    UNMERGED = 'U'
    UNTRACKED = '?'
    IGNORED = '!'

@dataclass
class GitFile:
    """Represents a file tracked by Git.
    
    Attributes:
        path: Path to the file
        status: Current Git status of the file
        staged: Whether the file is staged for commit
    """
    path: Path
    status: FileStatus
    staged: bool

class GitError(Exception):
    """Custom exception for Git-related errors."""
    pass

class GitRepositoryError(Exception):
    """Custom exception for Git repository-related errors."""
    pass

class GitCommandError(Exception):
    """Custom exception for errors during Git command execution."""
    pass

class GitManager(QObject):
    """Manager for Git operations.
    
    Attributes:
        project_path: Path to the Git repository
        repo: The Git repository instance
        status_changed: Signal emitted when repository status changes
        error_occurred: Signal emitted when an error occurs
        operation_success: Signal emitted when an operation is successful
    """
    
    operation_success = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    status_changed = pyqtSignal()
    
    def __init__(self, project_path: Union[str, Path], parent: Optional[QObject] = None):
        """Initialize Git manager.
        
        Args:
            project_path: Path to the project directory
            parent: Parent QObject for proper Qt ownership
        """
        super().__init__(parent)
        
        # Ensure we're in the main thread
        if QThread.currentThread() != QCoreApplication.instance().thread():
            raise RuntimeError("GitManager must be created in the main thread")
        
        self.project_path = Path(project_path)
        self.logger = logging.getLogger(__name__)
        self._repo: Optional[Repo] = None
        
        try:
            self._ensure_repo()
        except GitError as e:
            self.error_occurred.emit(str(e))
            
    @property
    def repo(self) -> Optional[Repo]:
        """Get the Git repository instance.
        
        Returns:
            The Git repository instance or None if not initialized
        """
        return self._repo

    def moveToThread(self, thread: QThread):
        """Override moveToThread to ensure proper thread affinity for timers."""
        super().moveToThread(thread)
        # If we have any timers, they should be recreated here
        
    def _ensure_repo(self) -> None:
        """Ensure Git repository exists and is properly initialized."""
        try:
            if not self.project_path.exists():
                raise GitRepositoryError(f"Repository path does not exist: {self.project_path}")
            
            try:
                self._repo = Repo(str(self.project_path))
            except (InvalidGitRepositoryError, NoSuchPathError) as e:
                if isinstance(e, NoSuchPathError):
                    raise GitRepositoryError(f"Repository path does not exist: {self.project_path}")
                # Initialize new repo if it's not a Git repo yet
                self._ensure_git_repo()
                self._repo = Repo(str(self.project_path))
                
            if not self._repo:
                raise GitRepositoryError("Failed to initialize repository")
                
            # Ensure we have an initial commit
            if not any(self._repo.heads):
                self._run_git_command('add', '.')
                try:
                    self._run_git_command('commit', '-m', 'Initial commit')
                except GitCommandError as e:
                    if 'nothing to commit' not in str(e):
                        raise
                
        except GitRepositoryError:
            raise
        except Exception as e:
            raise GitRepositoryError(f"Failed to initialize Git repository: {str(e)}")
                
    def _ensure_git_repo(self) -> None:
        """Ensure the project directory is a Git repository.

        This method checks if the project directory contains a .git folder.
        If not, it initializes a new Git repository in the project directory
        and creates an initial commit if there are files to commit.

        Raises:
            GitError: If Git repository initialization fails
        """
        try:
            if not (self.project_path / '.git').is_dir():
                # Initialize repository
                self._run_git_command('init')
                
                # Configure Git user if not already configured
                try:
                    self._run_git_command('config', 'user.email')
                except GitCommandError:
                    self._run_git_command('config', '--local', 'user.email', 'neuralforge@example.com')
                try:
                    self._run_git_command('config', 'user.name')
                except GitCommandError:
                    self._run_git_command('config', '--local', 'user.name', 'NeuralForge')
                    
                # Add all files and create initial commit
                files = list(self.project_path.glob('*'))
                if files:  # Only commit if there are files
                    self._run_git_command('add', '.')
                    try:
                        self._run_git_command('commit', '-m', 'Initial commit')
                    except GitCommandError as e:
                        if 'nothing to commit' not in str(e):
                            raise
                
                self.operation_success.emit("Git repository initialized")
                
        except GitCommandError as e:
            raise GitError(f"Failed to initialize Git repository: {str(e)}")

    def _run_git_command(self, *args: str) -> Tuple[str, str]:
        """Run a Git command.
        
        Args:
            *args: Command arguments
        
        Returns:
            Tuple of (stdout, stderr)
        
        Raises:
            GitCommandError: If the Git command fails
        """
        # Skip repository check for init command
        if args[0] != 'init':
            # Ensure repository exists before running command
            if not (self.project_path / '.git').is_dir():
                raise GitCommandError("Not a Git repository")
        
        try:
            process = subprocess.Popen(
                ['git'] + list(args),
                cwd=str(self.project_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise GitCommandError(f"Git command failed: {stderr.strip()}")
                
            return stdout.strip(), stderr.strip()
            
        except subprocess.CalledProcessError as e:
            raise GitCommandError(f"Git command failed: {e.stderr.strip() if hasattr(e, 'stderr') else str(e)}")
        except Exception as e:
            raise GitCommandError(f"Failed to execute Git command: {str(e)}")

    def get_status(self) -> List[GitFile]:
        """Get repository status.
        
        Returns:
            List of GitFile objects representing the status of files in the repository
            
        Raises:
            GitError: If operation fails or repository is not initialized
        """
        self._ensure_repo()
        
        try:
            files = []
            
            # Get modified files
            for item in self._repo.index.diff(None):
                status = FileStatus.MODIFIED if item.change_type == 'M' else \
                        FileStatus.ADDED if item.change_type == 'A' else \
                        FileStatus.DELETED if item.change_type == 'D' else \
                        FileStatus.RENAMED if item.change_type == 'R' else \
                        FileStatus.UNMODIFIED
                
                files.append(GitFile(
                    path=Path(item.a_path),
                    status=status,
                    staged=False
                ))
            
            # Get untracked files
            for path in self._repo.untracked_files:
                files.append(GitFile(
                    path=Path(path),
                    status=FileStatus.UNTRACKED,
                    staged=False
                ))
            
            # Get staged files
            for item in self._repo.index.diff('HEAD'):
                status = FileStatus.MODIFIED if item.change_type == 'M' else \
                        FileStatus.ADDED if item.change_type == 'A' else \
                        FileStatus.DELETED if item.change_type == 'D' else \
                        FileStatus.RENAMED if item.change_type == 'R' else \
                        FileStatus.UNMODIFIED
                
                files.append(GitFile(
                    path=Path(item.a_path),
                    status=status,
                    staged=True
                ))
            
            return files
            
        except Exception as e:
            raise GitError(f"Failed to get repository status: {str(e)}")
            
    def stage_file(self, file_path: Union[str, Path]) -> None:
        """Stage a file for commit.
        
        Args:
            file_path: Path to file to stage
        """
        try:
            file_path = Path(file_path) if isinstance(file_path, str) else file_path
            self._run_git_command('add', str(file_path.relative_to(self.project_path)))
            self.status_changed.emit()
        except GitCommandError as e:
            self.error_occurred.emit(f"Failed to stage file: {str(e)}")
            
    def unstage_file(self, file_path: Union[str, Path]) -> None:
        """Unstage a file from commit.
        
        Args:
            file_path: Path to file to unstage
        """
        try:
            file_path = Path(file_path) if isinstance(file_path, str) else file_path
            self._run_git_command('reset', 'HEAD', str(file_path.relative_to(self.project_path)))
            self.status_changed.emit()
        except GitCommandError as e:
            self.error_occurred.emit(f"Failed to unstage file: {str(e)}")
            
    def commit(self, message: str) -> None:
        """Create a new commit.
        
        Args:
            message: Commit message
        """
        try:
            self._run_git_command('commit', '-m', message)
            self.status_changed.emit()
        except GitCommandError as e:
            self.error_occurred.emit(f"Failed to commit: {str(e)}")
            
    def push(self, remote: str = 'origin', branch: str = 'main') -> None:
        """Push commits to remote repository.
        
        Args:
            remote: Remote repository name
            branch: Branch to push to
        """
        try:
            self._run_git_command('push', remote, branch)
        except GitCommandError as e:
            self.error_occurred.emit(f"Failed to push: {str(e)}")
            
    def pull(self, remote: str = 'origin', branch: str = 'main') -> None:
        """Pull changes from remote repository.
        
        Args:
            remote: Remote repository name
            branch: Branch to pull from
        """
        try:
            self._run_git_command('pull', remote, branch)
            self.status_changed.emit()
        except GitCommandError as e:
            self.error_occurred.emit(f"Failed to pull: {str(e)}")
            
    def get_remotes(self) -> Dict[str, str]:
        """Get configured remote repositories.
        
        Returns:
            Dictionary mapping remote names to URLs
        """
        try:
            output, _ = self._run_git_command('remote', '-v')
            remotes = {}
            
            for line in output.splitlines():
                if not line:
                    continue
                    
                parts = line.split()
                if len(parts) >= 2 and '(fetch)' in line:
                    remotes[parts[0]] = parts[1]
                    
            return remotes
        except GitCommandError as e:
            self.error_occurred.emit(f"Failed to get remotes: {str(e)}")
            return {}
            
    def add_remote(self, name: str, url: str) -> None:
        """Add a new remote repository.
        
        Args:
            name: Remote name
            url: Remote repository URL
        """
        try:
            self._run_git_command('remote', 'add', name, url)
        except GitCommandError as e:
            self.error_occurred.emit(f"Failed to add remote: {str(e)}")
            
    def remove_remote(self, name: str) -> None:
        """Remove a remote repository.
        
        Args:
            name: Remote name to remove
        """
        try:
            self._run_git_command('remote', 'remove', name)
        except GitCommandError as e:
            self.error_occurred.emit(f"Failed to remove remote: {str(e)}")
            
    def create_branch(self, name: str):
        """Create a new branch."""
        try:
            self._run_git_command('checkout', '-b', name)
            self.status_changed.emit()
        except GitCommandError as e:
            self.error_occurred.emit(f"Failed to create branch: {str(e)}")
            
    def switch_branch(self, name: str):
        """Switch to an existing branch."""
        try:
            self._run_git_command('checkout', name)
            self.status_changed.emit()
        except GitCommandError as e:
            self.error_occurred.emit(f"Failed to switch branch: {str(e)}")
            
    def get_branches(self) -> List[str]:
        """Get list of all branches."""
        try:
            output, _ = self._run_git_command('branch')
            branches = []
            
            for line in output.splitlines():
                if line.startswith('*'):
                    branches.append(line[2:])
                else:
                    branches.append(line.strip())
                    
            return branches
        except GitCommandError as e:
            self.error_occurred.emit(f"Failed to get branches: {str(e)}")
            return []
            
    def get_current_branch(self) -> str:
        """Get name of current branch.
        
        Returns:
            Name of current branch or 'main' if no branch exists
        """
        try:
            self._ensure_repo()
            if not self._repo.head.is_valid():
                # If no commits exist yet, create initial commit
                self._run_git_command('add', '.')
                self._run_git_command('commit', '-m', 'Initial commit')
                self._run_git_command('branch', '-M', 'main')
                return 'main'
            return self._repo.active_branch.name
        except (GitCommandError, ValueError) as e:
            self.error_occurred.emit(f"Failed to get current branch: {str(e)}")
            return 'main'  # Default to main if we can't get the branch name

    def get_file_diff(self, file_path: Union[str, Path]) -> str:
        """Get diff for a specific file."""
        try:
            file_path = Path(file_path) if isinstance(file_path, str) else file_path
            output, _ = self._run_git_command('diff', str(file_path.relative_to(self.project_path)))
            return output
        except GitCommandError as e:
            self.error_occurred.emit(f"Failed to get file diff: {str(e)}")
            return ""
            
    def discard_changes(self, file_path: Union[str, Path]) -> None:
        """Discard changes in a file."""
        try:
            file_path = Path(file_path) if isinstance(file_path, str) else file_path
            self._run_git_command('checkout', '--', str(file_path.relative_to(self.project_path)))
            self.status_changed.emit()
        except GitCommandError as e:
            self.error_occurred.emit(f"Failed to discard changes: {str(e)}")
            
    def get_commit_history(self, max_count: int = 100) -> List[Dict]:
        """Get commit history."""
        try:
            output, _ = self._run_git_command([
                'log',
                f'-{max_count}',
                '--pretty=format:%H%n%an%n%ae%n%at%n%s%n%b%n---'
            ])
            commits = []
            current_commit = {}
            current_field = None
            fields = ['hash', 'author', 'email', 'timestamp', 'subject', 'body']
            
            for line in output.splitlines():
                if line == '---':
                    if current_commit:
                        commits.append(current_commit)
                    current_commit = {}
                    current_field = None
                elif not current_field:
                    current_field = fields.pop(0)
                    current_commit[current_field] = line
                else:
                    if current_field == 'body':
                        if 'body' not in current_commit:
                            current_commit['body'] = line
                        else:
                            current_commit['body'] += '\n' + line
                            
            return commits
        except GitCommandError as e:
            self.error_occurred.emit(f"Failed to get commit history: {str(e)}")
            return []
            
    def clone_repository(self, url: str, directory: str = None, branch: str = None) -> bool:
        """Clone a repository from URL."""
        try:
            cmd = ['clone', url]
            if directory:
                cmd.append(directory)
            if branch:
                cmd.extend(['--branch', branch])
                
            result = subprocess.run(
                ['git'] + cmd,
                cwd=self.project_path.parent if directory else self.project_path,
                capture_output=True,
                text=True,
                check=True
            )
            self.error_occurred.emit(f"Successfully cloned repository from {url}")
            return True
        except subprocess.CalledProcessError as e:
            self.error_occurred.emit(f"Failed to clone repository: {str(e)}")
            return False
            
    def fetch(self, remote: str = None) -> bool:
        """Fetch changes from remote without merging."""
        try:
            cmd = ['fetch']
            if remote:
                cmd.append(remote)
                
            self._run_git_command(cmd)
            self.error_occurred.emit(f"Fetched changes from {remote or 'all remotes'}")
            return True
        except GitCommandError as e:
            self.error_occurred.emit(f"Failed to fetch: {str(e)}")
            return False
            
    def get_remote_branches(self, remote: str = None) -> List[str]:
        """Get list of remote branches."""
        try:
            output, _ = self._run_git_command('branch', '-r')
            branches = []
            
            for line in output.splitlines():
                line = line.strip()
                if not line:
                    continue
                if remote:
                    if line.startswith(f"{remote}/"):
                        branches.append(line.split('/', 1)[1])
                else:
                    branches.append(line)
                    
            return branches
        except GitCommandError as e:
            self.error_occurred.emit(f"Failed to get remote branches: {str(e)}")
            return []
            
    def push_to_remote(self, remote: str, branch: str, force: bool = False) -> bool:
        """Push changes to remote branch."""
        try:
            cmd = ['push', remote, branch]
            if force:
                cmd.append('--force')
                
            self._run_git_command(cmd)
            self.error_occurred.emit(
                f"Force pushed to {remote}/{branch}" if force else f"Pushed to {remote}/{branch}"
            )
            return True
        except GitCommandError as e:
            self.error_occurred.emit(f"Failed to push to remote: {str(e)}")
            return False
            
    def pull_from_remote(self, remote: str, branch: str) -> bool:
        """Pull changes from remote branch."""
        try:
            self._run_git_command('pull', remote, branch)
            self.status_changed.emit()
            self.error_occurred.emit(f"Pulled from {remote}/{branch}")
            return True
        except GitCommandError as e:
            self.error_occurred.emit(f"Failed to pull from remote: {str(e)}")
            return False
            
    def get_tracking_status(self) -> Tuple[int, int]:
        """Get number of commits ahead and behind remote branch."""
        try:
            output, _ = self._run_git_command('rev-list', '--left-right', '--count', 'HEAD...@{upstream}')
            ahead, behind = map(int, output.split())
            return (ahead, behind)
        except GitCommandError as e:
            self.error_occurred.emit(f"Failed to get tracking status: {str(e)}")
            return (0, 0)
            
    def set_upstream_branch(self, remote: str, branch: str) -> bool:
        """Set upstream branch for current branch."""
        try:
            self._run_git_command('branch', '--set-upstream-to', f'{remote}/{branch}')
            self.error_occurred.emit(f"Set upstream to {remote}/{branch}")
            return True
        except GitCommandError as e:
            self.error_occurred.emit(f"Failed to set upstream branch: {str(e)}")
            return False
            
    def rename_remote(self, old_name: str, new_name: str) -> bool:
        """Rename a remote."""
        try:
            self._run_git_command('remote', 'rename', old_name, new_name)
            self.error_occurred.emit(f"Renamed remote '{old_name}' to '{new_name}'")
            return True
        except GitCommandError as e:
            self.error_occurred.emit(f"Failed to rename remote: {str(e)}")
            return False
            
    def delete_remote_branch(self, remote: str, branch: str) -> bool:
        """Delete a remote branch."""
        try:
            self._run_git_command('push', remote, '--delete', branch)
            self.error_occurred.emit(f"Deleted remote branch {remote}/{branch}")
            return True
        except GitCommandError as e:
            self.error_occurred.emit(f"Failed to delete remote branch: {str(e)}")
            return False
            
    def checkout_branch(self, branch_name: str, create: bool = False) -> None:
        """Checkout or create a branch.
        
        Args:
            branch_name: Name of the branch to checkout
            create: If True, create the branch if it doesn't exist
            
        Raises:
            GitError: If checkout fails or repository is not initialized
        """
        self._ensure_repo()
        
        try:
            if create and branch_name not in self._repo.heads:
                self._repo.create_head(branch_name)
                
            self._repo.heads[branch_name].checkout()
            self.logger.info(f"Checked out branch: {branch_name}")
            
        except Exception as e:
            raise GitError(f"Failed to checkout branch '{branch_name}': {str(e)}")
            
    def commit_changes(self, message: str, 
                      files: Optional[List[Union[str, Path]]] = None) -> None:
        """Commit changes to the repository.
        
        Args:
            message: Commit message
            files: List of files to commit. If None, commits all changes.
            
        Raises:
            GitError: If commit fails or repository is not initialized
        """
        self._ensure_repo()
        
        try:
            if files:
                # Convert all paths to strings relative to repo root
                repo_root = Path(self._repo.working_dir)
                relative_files = [
                    str(Path(f).relative_to(repo_root)) for f in files
                ]
                self._repo.index.add(relative_files)
            else:
                self._repo.index.add('*')
                
            if self._repo.index.diff('HEAD'):
                self._repo.index.commit(message)
                self.logger.info(f"Changes committed: {message}")
            else:
                self.logger.info("No changes to commit")
                
        except Exception as e:
            raise GitError(f"Failed to commit changes: {str(e)}")
            
    def push_changes(self, remote: str = 'origin', 
                    branch: Optional[str] = None) -> None:
        """Push commits to remote repository.
        
        Args:
            remote: Name of the remote (default: 'origin')
            branch: Branch to push. If None, pushes current branch.
            
        Raises:
            GitError: If push fails or repository is not initialized
        """
        self._ensure_repo()
        
        try:
            if not branch:
                branch = self._repo.active_branch.name
                
            self._repo.remote(remote).push(branch)
            self.logger.info(f"Changes pushed to {remote}/{branch}")
            
        except Exception as e:
            raise GitError(f"Failed to push changes: {str(e)}")
            
    def pull_changes(self, remote: str = 'origin', 
                    branch: Optional[str] = None) -> None:
        """Pull changes from remote repository.
        
        Args:
            remote: Name of the remote (default: 'origin')
            branch: Branch to pull. If None, pulls current branch.
            
        Raises:
            GitError: If pull fails or repository is not initialized
        """
        self._ensure_repo()
        
        try:
            if not branch:
                branch = self._repo.active_branch.name
                
            self._repo.remote(remote).pull(branch)
            self.logger.info(f"Changes pulled from {remote}/{branch}")
            
        except Exception as e:
            raise GitError(f"Failed to pull changes: {str(e)}")
            
    def get_commit_history(self, max_count: int = 50) -> List[Dict[str, str]]:
        """Get repository commit history.
        
        Args:
            max_count: Maximum number of commits to retrieve
            
        Returns:
            List of dictionaries containing commit information
            
        Raises:
            GitError: If operation fails or repository is not initialized
        """
        self._ensure_repo()
        
        try:
            commits = []
            for commit in self._repo.iter_commits(max_count=max_count):
                commits.append({
                    'hash': commit.hexsha,
                    'author': str(commit.author),
                    'date': datetime.fromtimestamp(commit.committed_date).isoformat(),
                    'message': commit.message.strip(),
                    'branch': self._repo.active_branch.name
                })
            return commits
            
        except Exception as e:
            raise GitError(f"Failed to get commit history: {str(e)}")

    def __del__(self):
        """Clean up Git repository when manager is destroyed."""
        try:
            if self._repo:
                self._repo.close()
                self._repo = None
        except:
            pass  # Ignore cleanup errors
