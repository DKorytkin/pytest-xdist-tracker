import pytest


@pytest.fixture
def default_test_nodeid():
    return "tests/test_xxx.py::test_xxx"


@pytest.fixture
def expected_file_path(tmpdir, default_test_nodeid):
    path = tmpdir / "xdist_stats_worker_gw2.txt"
    path.write(default_test_nodeid)
    return str(path)
