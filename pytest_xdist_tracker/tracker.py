from __future__ import absolute_import

import io

import pytest
from six.moves import urllib_parse

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
        self.is_loadfile = self.config.getoption("dist") == "loadfile"
        self.storage = []

    def get_name(self, item):
        """
        Usually returns full test case name
            "tests/path/test_module.py::TestCase::test_one"
        But if was passed dist=loadfile will be enough just test module name
            "tests/path/test_module.py"

        Parameters
        -----------
        item : _pytest.main.Item

        Returns
        -------
        str
        """
        if self.is_loadfile:
            # TODO #7 dist in node always `no`
            # ("test_module_path.py", line number, "test_case")
            return item.location[0]
        return urllib_parse.quote(item.nodeid)

    def add(self, item):
        """
        Parameters
        -----------
        item : _pytest.main.Item
        """
        name = self.get_name(item)
        if name not in self.storage:
            self.storage.append(name)

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
        file_name = "{}_worker_{}.txt".format(
            self.config.getoption("--xdist-stats"), worker_id
        )
        return str(self.config.rootdir / file_name)

    def store(self):
        """
        Save as artifact all tests which were run inside particular xdist node
        tests separate by new line
        """

        with io.open(self.file_path, "wb") as file:
            content = "\n".join(self.storage)
            file.write(content.encode(ENCODING))

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
    This plugin help to run particular tests from artifact which was generated via `TestTracker`
    """

    def __init__(self, config):
        """
        Parameters
        ----------
        config: _pytest.config.Config
        """
        self._target_tests = None
        self.config = config
        # patch of passed arguments `tests/...` to reduce collection runtime
        self.config.args[:] = self.target_test_modules

    def read_target_tests(self):
        """
        Reads artifact which was generated via `TestRunTracker` plugin

        Returns
        -------
        List[str]
            [
                "tests/backend/test_one.py::test_one",
                "tests/backend/test_one.py::test_two",
                ...
            ]
        """
        file_path = self.config.getoption("--from-xdist-stats")
        test_cases = []
        with io.open(file_path, "rb") as file:
            for line in file:
                test_cases.append(
                    urllib_parse.unquote(line.decode(ENCODING).rstrip("\n"))
                )
        return test_cases

    @property
    def target_tests(self):
        """
        Returns
        -------
        List[str]
            [
                "tests/backend/test_one.py::test_one",
                "tests/backend/test_one.py::test_two",
                ...
            ]
        """
        if self._target_tests is None:
            self._target_tests = self.read_target_tests()
        return self._target_tests

    @property
    def target_test_modules(self):
        """
        Returns
        -------
        set[str]
        """
        return list({test_case.split("::")[0] for test_case in self.target_tests})

    def find_necessary(self, items):
        """
        Parameters
        ----------
        items: List[_pytest.main.Item]

        Returns
        -------
        Generator[pytest.Item]
        """
        return (item for item in items if item.nodeid in self.target_tests)

    def sorted_as_target_tests(self, items):
        """
        Parameters
        ----------
        items: List[_pytest.main.Item]

        Returns
        -------
        Generator
        """
        return sorted(items, key=lambda x: self.target_tests.index(x.nodeid))

    @pytest.hookimpl(hookwrapper=True)
    def pytest_collection_modifyitems(self, items):
        """
        Parameters
        ----------
        items : List[pytest.Item]
        """
        items[:] = self.sorted_as_target_tests(self.find_necessary(items))
        yield
