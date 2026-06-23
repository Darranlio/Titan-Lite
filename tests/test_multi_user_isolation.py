import pytest
import os
import shutil
from portfolio_manager import PortfolioManager
from archive_manager import ArchiveManager
from orchestrator.context import UserContext

@pytest.fixture
def clean_test_env():
    """Cleanup users test directory before and after."""
    test_root = "docs/projects/titan-lite/users_test"
    if os.path.exists(test_root):
        shutil.rmtree(test_root)
    os.makedirs(test_root, exist_ok=True)
    yield test_root
    if os.path.exists(test_root):
        shutil.rmtree(test_root)

def test_user_data_isolation(clean_test_env):
    """
    Verify that two different users have isolated portfolios and archives.
    """
    user_a = UserContext(user_id="user_a", storage_root="docs/projects/titan-lite/users_test/user_a")
    user_b = UserContext(user_id="user_b", storage_root="docs/projects/titan-lite/users_test/user_b")
    
    # Initialize managers for User A
    pm_a = PortfolioManager(storage_root=user_a.storage_root)
    am_a = ArchiveManager(storage_root=user_a.storage_root)
    
    # Initialize managers for User B
    pm_b = PortfolioManager(storage_root=user_b.storage_root)
    am_b = ArchiveManager(storage_root=user_b.storage_root)
    
    # 1. Action: User A deposits money
    pm_a.record_transaction("USD", "DEPOSIT", 10000, 1.0)
    
    # 2. Validation: User A has 10000, User B has 0
    status_a = pm_a.calculate_nav()
    status_b = pm_b.calculate_nav()
    
    assert status_a['total_value_usd'] == 10000.0
    assert status_b['total_value_usd'] == 0.0
    
    # 3. Action: User B buys stock
    # Mock data provider is not used here, we just record a transaction
    pm_b.record_transaction("TSLA", "INITIAL", 10, 200.0)
    
    # 4. Validation: User B has TSLA, User A does not
    status_a_new = pm_a.calculate_nav()
    status_b_new = pm_b.calculate_nav()
    
    assert len(status_a_new['us_equities']) == 0
    assert any(s['symbol'] == 'TSLA' for s in status_b_new['us_equities'])
    
    # 5. Physical Path Check
    assert os.path.exists(os.path.join(user_a.storage_root, "data/portfolio/vault.db"))
    assert os.path.exists(os.path.join(user_b.storage_root, "data/portfolio/vault.db"))
    assert pm_a.db_path != pm_b.db_path

def test_archive_isolation(clean_test_env):
    """Verify archive isolation."""
    user_a_root = "docs/projects/titan-lite/users_test/user_a"
    user_b_root = "docs/projects/titan-lite/users_test/user_b"
    
    # Manually create a dummy report for User A
    report_dir_a = os.path.join(user_a_root, "reports/AAPL")
    os.makedirs(report_dir_a, exist_ok=True)
    import json
    with open(os.path.join(report_dir_a, "metadata.json"), "w") as f:
        json.dump([{"date": "2026-06-02", "price": 150}], f)
        
    am_a = ArchiveManager(storage_root=user_a_root)
    am_b = ArchiveManager(storage_root=user_b_root)
    
    assert len(am_a.get_all_reports()) == 1
    assert len(am_b.get_all_reports()) == 0
