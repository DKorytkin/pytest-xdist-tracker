import pytest


ENCODING = "utf-8"


def is_xdist_worker(config):
    """
    Parameters
    ----------
    config: _pytest.config.Config

    Return
    ------
    bool
        `True` if this is an xdist worker, `False` otherwise
    """
    return hasattr(config, "workerinput")


def get_xdist_worker_id(config):
    """
    Parameters
    ----------
    config: _pytest.config.Config

    Returns
    -------
    str
        the id of the current worker ('gw0', 'gw1', etc) or 'master'
        if running on the 'master' node.

        If not distributing tests (for example passing `-n0` or not passing `-n` at all)
        also return 'master'.
    """
    worker_input = getattr(config, "workerinput", None)
    if worker_input:
        return worker_input["workerid"]
    return "master"


class TestTracker(object):
    """
    Plugin track tests which run in particular xdist node
    As result save artifact with with these tests
    In case when have some flaky test it could be helpful to reproduce it
    """

    def __init__(self, config):
        self.config = config
        self.storage = []

    def add(self, item):
        """
        Parameters
        -----------
        item : _pytest.main.Item
        """
        node_id = item.nodeid
        if node_id not in self.storage:
            self.storage.append(node_id)

    @property
    def file_path(self):
        """
        Making path base on passed patter and worker id

        Returns
        -------
        str
            "xdist_stats_worker_gw1.txt"
            "xdist_stats_worker_gw2.txt"
            ...
        """
        worker_id = get_xdist_worker_id(self.config)
        file_path = str(
            self.config.rootdir / "xdist_stats_worker_{}.txt".format(worker_id)
        )
        return file_path

    def store(self):
        """
        Save as artifact all tests which were run inside particular xdist node
        tests separate by new line
        """

        with open(self.file_path, "w", encoding=ENCODING) as file:
            file.write("\n".join(self.storage))

    @pytest.hookimpl(hookwrapper=True, trylast=True)
    def pytest_sessionfinish(self):
        """
        Storing all test modules which were executed on this xdist node
        Sometimes needs to debugging coupled tests when failure happens
        This list of test modules sorted as they were executed,
        then can help to reproduce an issue
        """
        if is_xdist_worker(self.config):
            self.store()
        yield

    @pytest.hookimpl(hookwrapper=True, trylast=True)
    def pytest_runtest_call(self, item):
        """
        Parameters
        ----------
        item : _pytest.main.Item
        """
        self.add(item)
        yield


class TestRunner(object):
    """
    This plugin help to run particular tests from artifact which was generated via `TestRunTracker`
    """

    def __init__(self, config):
        self.config = config
        self._target_tests = None

    def read_target_tests(self):
        """
        Reads artifact which was generated via `TestRunTracker` plugin

        Returns
        -------
        list[str]
            [
                "tests/backend/test_one.py::test_one",
                "tests/backend/test_one.py::test_two",
                ...
            ]
        """
        file_path = self.config.getoption("--from-xdist-stats")
        with open(file_path, encoding=ENCODING) as file:
            data = file.read().split()
        return data

    @property
    def target_tests(self):
        """
        Returns
        -------
        list[str]
            [
                "tests/backend/test_one.py::test_one",
                "tests/backend/test_one.py::test_two",
                ...
            ]
        """
        if self._target_tests is None:
            self._target_tests = self.read_target_tests()
        return self._target_tests

    def find_necessary(self, items):
        """
        Parameters
        ----------
        items: [_pytest.main.Item]

        Returns
        -------
        Generator[pytest.Item]
        """
        return (item for item in items if item.nodeid in self.target_tests)

    def sorted_as_target_tests(self, items):
        """
        Parameters
        ----------
        items: [_pytest.main.Item]

        Returns
        -------
        Generator
        """
        return sorted(items, key=lambda x: self.target_tests.index(x.nodeid))

    @pytest.hookimpl(hookwrapper=True, trylast=True)
    def pytest_collection_modifyitems(self, items):
        """
        Parameters
        ----------
        items : [pytest.Item]
        """
        items[:] = self.sorted_as_target_tests(self.find_necessary(items))
        yield
