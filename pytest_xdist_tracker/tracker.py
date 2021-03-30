import os

import pytest


def is_master(config):
    """
    True if the code running the given pytest.config object is running in a xdist master
    node or not running xdist at all.
    """
    return not hasattr(config, "workerinput")


class TestRunTracker(object):
    """
    Plugin track tests which run in particular xdist node
    As result save artefact with with these tests
    In case when have some flaky test it could be helpful to reproduce it
    """

    def __init__(self, config):
        self.config = config
        self.is_master = is_master(self.config)
        self.worker_id = os.getenv("PYTEST_XDIST_WORKER")
        _path = config.getoption("--xdist-stats") or "xdist_stats"
        self.path = "{}_worker_{}.txt".format(_path, self.worker_id)
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

    def store(self):
        """
        Save as artefact all tests which were run inside particular xdist node
        tests separate by new line
        """
        with open(self.path, "w") as file:
            file.write("\n".join(self.storage))

    @pytest.hookimpl(hookwrapper=True, trylast=True)
    def pytest_sessionfinish(self):
        """
        Storing all test modules which were executed on this xdist node
        Sometimes needs to debugging coupled tests when failure happens
        This list of test modules sorted as they were executed,
        then can help to reproduce an issue
        """
        yield
        if not self.is_master:
            self.store()

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
    This plugin help to run particular tests from artefact which was generated via `TestRunTracker`
    """

    def __init__(self, config):
        self.config = config
        self.file_path = config.getoption("--from-xdist-stats")
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
        with open(self.file_path) as file:
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
        Generator
        """
        # FIXME track undefined items
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
    def pytest_collection_modifyitems(self, session, config, items):
        """
        Parameters
        ----------
        session : pytest.Session
        config : _pytest.config.Config
        items : [pytest.Item]
        """
        items[:] = self.sorted_as_target_tests(self.find_necessary(items))
