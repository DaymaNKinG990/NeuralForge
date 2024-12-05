import pytest
from pathlib import Path
from src.utils.git_manager import GitManager, GitRepositoryError, GitCommandError
import shutil
import gc
import time

@pytest.fixture
def git_manager(tmp_path: Path):
    """Create a temporary directory and initialize it as a Git repository."""
    # Setup a temporary directory
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir(parents=True, exist_ok=True)
    
    # Create a test file to ensure we have something to commit
    test_file = repo_path / "test.txt"
    test_file.write_text("Test content")
    
    # Initialize git manager
    manager = GitManager(repo_path)
    
    yield manager
    
    # Cleanup
    try:
        # Close the repo and force garbage collection
        if manager._repo:
            manager._repo.close()
            manager._repo = None
        gc.collect()
        time.sleep(0.1)  # Give Windows time to release file handles
        
        # Remove the directory
        if repo_path.exists():
            # First try to make files writable
            for path in repo_path.rglob('*'):
                try:
                    path.chmod(0o777)
                except:
                    pass
            
            # Now remove the directory
            shutil.rmtree(repo_path, ignore_errors=True)
    except Exception as e:
        print(f"Warning: Cleanup failed - {e}")

def test_initialize_git_manager(git_manager):
    """Test that Git repository is properly initialized."""
    assert git_manager.repo is not None, "Git repository should be initialized"
    assert (git_manager.project_path / ".git").is_dir(), "Git directory should exist"
    
    # Verify initial commit
    history = git_manager.get_commit_history(max_count=1)
    assert len(history) > 0, "Should have at least one commit"
    assert history[0].get('message', '').strip() == 'Initial commit'

def test_invalid_git_repository(tmp_path):
    """Test handling of invalid repository paths."""
    invalid_path = tmp_path / "nonexistent"
    with pytest.raises(GitRepositoryError):
        GitManager(invalid_path)

def test_run_git_command_success(git_manager):
    """Test successful Git command execution."""
    # First ensure Git is initialized
    git_manager._ensure_repo()
    
    # Now run git status
    stdout, stderr = git_manager._run_git_command('status')
    assert "On branch" in stdout, "Git status should indicate the current branch"

def test_run_git_command_failure(git_manager):
    """Test handling of failed Git commands."""
    with pytest.raises(GitCommandError):
        git_manager._run_git_command('nonexistent-command')

def test_git_operations(git_manager):
    """Test basic Git operations."""
    # Create and add a new file
    test_file = git_manager.project_path / "new_file.txt"
    test_file.write_text("New content")
    
    # Stage the file using relative path
    git_manager.stage_file(test_file)
    
    # Verify file is staged
    status = git_manager.get_status()
    staged_files = [f.path for f in status if f.staged]
    assert "new_file.txt" in str(staged_files), "File should be staged"
    
    # Create commit
    git_manager.commit_changes("Test commit")
    
    # Verify commit
    history = git_manager.get_commit_history(max_count=1)
    assert history[0].get('message', '').strip() == 'Test commit'
