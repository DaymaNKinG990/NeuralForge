import pytest
from pathlib import Path
from src.utils.git_manager import GitManager, GitRepositoryError, GitCommandError

@pytest.fixture
def git_manager(tmp_path: Path):
    # Setup a temporary directory as a Git repository
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    git_manager = GitManager(str(repo_path))
    git_manager._run_git_command('init')
    return git_manager


def test_initialize_git_manager(git_manager):
    assert git_manager.repo is not None, "Git repository should be initialized"


def test_invalid_git_repository():
    with pytest.raises(GitRepositoryError):
        GitManager("invalid/path")


def test_run_git_command_success(git_manager):
    stdout, stderr = git_manager._run_git_command('status')
    assert "On branch" in stdout, "Git status should indicate the current branch"


def test_run_git_command_failure(git_manager):
    with pytest.raises(GitCommandError):
        git_manager._run_git_command('nonexistent-command')
