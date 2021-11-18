import os

try:
    from unittest import mock
except ImportError:
    from mock import mock

import pytest
from _pytest.config import Config
from six.moves import urllib_parse

from pytest_xdist_tracker.tracker import TestRunner as Runner
from pytest_xdist_tracker.tracker import TestTracker as Tracker

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError  # python2


def create_pytest_test_item(name):
    node = mock.create_autospec(pytest.Item, spec_set=True)
    node.nodeid = u"tests/backend/unit/test_awesome.py::test_one_{}".format(name)
    return node


@pytest.fixture
def config(tmpdir):
    c = mock.create_autospec(Config)
    c.getoption.return_value = None
    c.workerinput = {"workerid": "gw2"}
    c.rootdir = tmpdir
    c.args = ["tests/backend/unit"]
    return c


@pytest.fixture
def node():
    return create_pytest_test_item(0)


class TestTracker(object):
    FILE_NAME = "my_super_name"

    @pytest.fixture
    def file_name(self):
        return "{}_worker_gw2.txt".format(self.FILE_NAME)

    @pytest.fixture
    def tracker(self, config):
        config.getoption.return_value = self.FILE_NAME
        return Tracker(config=config)

    def test_instance(self, tracker, config):
        assert tracker.config == config
        assert tracker.storage == []

    def test_add(self, tracker, node):
        tracker.add(node)
        assert tracker.storage == [urllib_parse.quote(node.nodeid)]

    def test_add_multiply_times(self, tracker, node):
        tracker.add(node)
        tracker.add(node)
        tracker.add(node)
        assert len(tracker.storage) == 1
        assert tracker.storage == [urllib_parse.quote(node.nodeid)]

    def test_file_path(self, tracker, expected_file_path):
        assert tracker.file_path.endswith("{}_worker_gw2.txt".format(self.FILE_NAME))
        assert tracker.file_path == expected_file_path

    def test_store(self, tracker, node, expected_file_path):
        tracker.add(node)
        tracker.store()
        assert os.path.isfile(expected_file_path), "File not exist"
        with open(expected_file_path) as file_content:
            content = file_content.read().strip()
        assert urllib_parse.unquote(content) == node.nodeid

    def test_store_with_file_pattern(self, tracker, node, expected_file_path):
        tracker.add(node)
        tracker.store()
        assert os.path.isfile(expected_file_path), "File not exist"
        with open(expected_file_path) as file_content:
            content = file_content.read().strip()
        assert urllib_parse.unquote(content) == node.nodeid

    def test_store_empty(self, tracker, expected_file_path):
        tracker.store()
        assert os.path.isfile(expected_file_path), "File not exist"
        with open(expected_file_path) as file_content:
            content = file_content.read().strip()
        assert content == ""

    def test_pytest_sessionfinish(self, expected_file_path, tracker):
        next(tracker.pytest_sessionfinish())
        assert os.path.isfile(expected_file_path), "File not exist"

    def test_pytest_sessionfinish_for_master_node(self, tracker):
        delattr(tracker.config, "workerinput")
        next(tracker.pytest_sessionfinish())
        assert not os.path.isfile(tracker.file_path), "File exists"

    def test_pytest_runtest_call(self, node, tracker):
        next(tracker.pytest_runtest_call(node))
        assert tracker.storage == [urllib_parse.quote(node.nodeid)]


class TestRunner(object):
    FILE_NAME = "my_awesome_name"

    @pytest.fixture
    def file_name(self):
        return "{}_worker_gw2.txt".format(self.FILE_NAME)

    @pytest.fixture
    def runner(self, config, expected_file):
        config.getoption.return_value = expected_file
        assert config.args == ["tests/backend/unit"]
        r = Runner(config=config)
        assert config.args != ["tests/backend/unit"] and config.args
        return r

    @pytest.fixture
    def target_items(self, node):
        """
        Emulate failed test nodes
        Parameters
        ----------
        node: pytest.Item
            "tests/backend/unit/test_awesome.py::test_one_0"

        Returns
        -------
        List[pytest.Item]
            [
                "tests/backend/unit/test_awesome.py::test_one_0",
                "tests/backend/unit/test_awesome.py::test_one_12",
                "tests/backend/unit/test_awesome.py::test_one_11",
            ]
        """
        return [node, create_pytest_test_item(12), create_pytest_test_item(11)]

    @pytest.fixture
    def items(self, node, target_items):
        """
        Returns
        -------
        List[str]
            [
                "tests/backend/unit/test_awesome.py::test_one_1",
                "tests/backend/unit/test_awesome.py::test_one_2",
                "tests/backend/unit/test_awesome.py::test_one_3",
                "tests/backend/unit/test_awesome.py::test_one_4",
                "tests/backend/unit/test_awesome.py::test_one_5",
                "tests/backend/unit/test_awesome.py::test_one_6",
                "tests/backend/unit/test_awesome.py::test_one_7",
                "tests/backend/unit/test_awesome.py::test_one_8",
                "tests/backend/unit/test_awesome.py::test_one_9",
                "tests/backend/unit/test_awesome.py::test_one_10",
                "tests/backend/unit/test_awesome.py::test_one_0",
                "tests/backend/unit/test_awesome.py::test_one_12",
                "tests/backend/unit/test_awesome.py::test_one_11",
            ]
        """
        items = []
        for idx in range(1, 11):
            items.append(create_pytest_test_item(idx))
        # emulates shuffling of tests (diff between run with xdist and without)
        items.extend(target_items)
        return items

    @pytest.fixture
    def target_tests(self, target_items):
        """
        Parameters
        ----------
        List[pytest.Item]
            [
                "tests/backend/unit/test_awesome.py::test_one_0",
                "tests/backend/unit/test_awesome.py::test_one_12",
                "tests/backend/unit/test_awesome.py::test_one_11",
            ]

        Returns
        -------
        List[str]
            [
                "tests/backend/unit/test_awesome.py::test_one_0",
                "tests/backend/unit/test_awesome.py::test_one_11",
                "tests/backend/unit/test_awesome.py::test_one_12",
            ]
        """
        return sorted([node.nodeid for node in target_items])

    def test_instance(self, runner, config, default_test_nodeid):
        assert runner.config == config
        assert runner._target_tests is not None
        assert runner.target_tests == runner._target_tests
        assert runner.target_tests == [default_test_nodeid]

    def test_read_target_tests(self, expected_file_path, runner, default_test_nodeid):
        tests = runner.read_target_tests()
        assert tests == [default_test_nodeid]

    def test_read_target_tests_file_absent(self, runner):
        runner.config.getoption.side_effect = "file_not_exist.txt"
        with pytest.raises(FileNotFoundError):
            runner.read_target_tests()

    def test_target_tests(self, runner, node, default_test_nodeid):
        assert runner.target_tests == [default_test_nodeid]

    def test_find_necessary(self, runner, target_tests, items):
        runner._target_tests = target_tests
        assert sorted(i.nodeid for i in runner.find_necessary(items)) == sorted(
            target_tests
        )

    def test_sorted_as_target_tests(self, runner, target_tests, items):
        runner._target_tests = target_tests
        target_items = runner.find_necessary(items)
        assert [
            i.nodeid for i in runner.sorted_as_target_tests(target_items)
        ] == target_tests

    def test_pytest_collection_modifyitems(self, runner, items, target_tests):
        runner._target_tests = target_tests
        assert len(items) != len(target_tests)
        next(runner.pytest_collection_modifyitems(items))
        assert len(items) == len(target_tests), "Was not filter target test items"
        assert [i.nodeid for i in items] == target_tests
