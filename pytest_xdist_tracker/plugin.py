import os

from pytest_xdist_tracker.tracker import TestRunner, TestRunTracker


def pytest_addoption(parser):
    """
    Command line options for our plugin
    Parameters
    ----------
    parser: _pytest.config.Parser
    """
    group = parser.getgroup("xdist_tracker")
    group.addoption(
        "--xdist-stats",
        action="store",
        default="xdist_stats",
        dest="xdist_stats",
        help=(
            "File pattern to save tests which were run on the xdist node (by default %(default)s). "
            "As result if will run with `-n2` will generated 2 artefacts like:"
            "xdist_stats_worker_gw0.txt and xdist_stats_worker_gw1.txt"
        ),
    )
    group.addoption(
        "--from-xdist-stats",
        action="store",
        default=None,
        dest="from_xdist_stats",
        help=(
            "File with tests(nodeid) to run in single thread, could be helpful to reproduce issues "
            "related to coupled tests which corrupted or doesn't clear some state after self"
        ),
    )


def pytest_configure(config):
    """
    Enable this reporter when tests run with XDIST
    """
    if int(os.getenv("PYTEST_XDIST_WORKER_COUNT") or 0) > 0:
        reporter = TestRunTracker(config)
        config.pluginmanager.register(reporter)
    elif config.getoption("--from-xdist-stats"):
        runner = TestRunner(config)
        config.pluginmanager.register(runner)
