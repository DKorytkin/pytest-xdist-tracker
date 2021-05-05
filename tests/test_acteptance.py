import pytest


@pytest.fixture
def target_tests(testdir):
    testdir.makepyfile(
        """
            import pytest

            def test_fail0():
                assert 0

            def test_fail1():
                raise ValueError()

            def test_ok():
                pass

            @pytest.mark.skip
            def test_skip():
                assert 0
        """
    )
    return testdir


@pytest.mark.parametrize("numprocesses", (1, 3))
def test_storing_worker_artifacts(target_tests, numprocesses):
    report = target_tests.runpytest("-n", str(numprocesses))
    result = report.parseoutcomes()
    assert result["passed"] == 1
    assert result["skipped"] == 1
    assert result["failed"] == 2
    for n in range(numprocesses):
        generated_artifact = target_tests.tmpdir.join(
            "xdist_stats_worker_gw{}.txt".format(n)
        )
        assert generated_artifact.isfile()


def test_not_run_tracker_without_xdist(target_tests):
    report = target_tests.runpytest("-n0", "-s")
    result = report.parseoutcomes()
    assert result["passed"] == 1
    assert result["skipped"] == 1
    assert result["failed"] == 2
    generated_artifact = target_tests.tmpdir.join("xdist_stats_worker_gw0.txt")
    assert not generated_artifact.isfile()


def test_run_tests_from_artifact(target_tests):
    """
    test_run_tests_from_artifact.py::test_fail0
    test_run_tests_from_artifact.py::test_ok
    test_run_tests_from_artifact.py::test_fail1
    """
    lines = [
        "test_run_tests_from_artifact.py::test_ok",
        "test_run_tests_from_artifact.py::test_fail1",
    ]
    f = target_tests.maketxtfile("\n".join(lines))
    report = target_tests.runpytest("--from-xdist-stats", str(f))
    result = report.parseoutcomes()
    assert result["passed"] == 1
    assert result["failed"] == 1


def test_run_tests_not_from_artifact(target_tests):
    """
    test_run_tests_not_from_artifact.py::test_fail0
    test_run_tests_not_from_artifact.py::test_ok
    test_run_tests_not_from_artifact.py::test_fail1
    """
    lines = [
        "test_run_tests_not_from_artifact.py::test_ok",
        "test_run_tests_not_from_artifact.py::test_fail1",
    ]
    f = target_tests.maketxtfile("\n".join(lines))
    report = target_tests.runpytest("--from-xdist-stats", str(f), "-n1")
    result = report.parseoutcomes()
    assert result["passed"] == 1
    assert result["skipped"] == 1
    assert result["failed"] == 2
