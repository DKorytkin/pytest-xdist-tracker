import os
import pytest


def is_master(config):
    """
    True if the code running the given pytest.config object is running in a xdist master
    node or not running xdist at all.
    """
    return not hasattr(config, 'workerinput')


class TestRunTracker(object):
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
        with open(self.path, "w") as f:
            f.write("\n".join(self.storage))

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
    def __init__(self, config):
        self.config = config
        self.file_path = config.getoption("--from-xdist-stats")
        self._target_tests = None

    def read_target_tests(self):
        with open(self.file_path) as f:
            data = f.read().split()
        return data

    @property
    def target_tests(self):
        if self._target_tests is None:
            self._target_tests = self.read_target_tests()
        return self._target_tests

    def get_only_necessary_items(self, items):
        return (item for item in items if item.nodeid in self.target_tests)

    def sorted_as_target_tests(self, items):
        return sorted(items, key=lambda x: self.target_tests.index(x.nodeid))

    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(self, session, config, items):
        items[:] = self.sorted_as_target_tests(self.get_only_necessary_items(items))
