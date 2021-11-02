import pytest


@pytest.fixture
def default_test_nodeid():
    return "tests/test_xxx.py::test_xxx"


@pytest.fixture
def file_name():
    # can be overwritten via local fixture
    return "xdist_stats_worker_gw2.txt"


@pytest.fixture
def expected_file_path(tmpdir, file_name):
    return str(tmpdir / file_name)


@pytest.fixture
def expected_file(expected_file_path, default_test_nodeid):
    with open(expected_file_path, "w") as f:
        f.write(default_test_nodeid)
    return expected_file_path
