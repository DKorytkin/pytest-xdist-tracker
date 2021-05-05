def test_execute_xdist_tracker_plugin(testdir):
    config = testdir.parseconfigure("-n1")
    assert config.option.xdist_stats == "xdist_stats"
    assert config.pluginmanager.hasplugin("xdist_tracker")
    assert not config.pluginmanager.hasplugin("xdist_runner")


def test_execute_xdist_tracker_plugin_with_custom_options(testdir):
    config = testdir.parseconfigure("-n2", "--xdist-stats", "xXx")
    assert config.option.xdist_stats == "xXx"
    assert config.pluginmanager.hasplugin("xdist_tracker")
    assert not config.pluginmanager.hasplugin("xdist_runner")


def test_execute_xdist_tracker_plugin_without_xdist(testdir):
    config = testdir.parseconfigure("--xdist-stats", "xXx")
    assert config.option.xdist_stats == "xXx"
    assert not config.pluginmanager.hasplugin("xdist_tracker")
    assert not config.pluginmanager.hasplugin("xdist_runner")


def test_execute_xdist_runner(testdir):
    config = testdir.parseconfigure("--from-xdist-stats", "xXx")
    assert config.option.from_xdist_stats == "xXx"
    assert not config.pluginmanager.hasplugin("xdist_tracker")
    assert config.pluginmanager.hasplugin("xdist_runner")


def test_execute_xdist_runner_with_xdist(testdir):
    config = testdir.parseconfigure("--from-xdist-stats", "xXx", "-n 2")
    assert config.option.from_xdist_stats == "xXx"
    assert not config.pluginmanager.hasplugin("xdist_tracker")
    assert not config.pluginmanager.hasplugin("xdist_runner")


def test_execute_both_plugins(testdir):
    config = testdir.parseconfigure(
        "--from-xdist-stats", "x1", "-n 2", "--xdist-stats", "x2"
    )
    assert config.option.from_xdist_stats == "x1"
    assert config.option.xdist_stats == "x2"
    assert not config.pluginmanager.hasplugin("xdist_tracker")
    assert not config.pluginmanager.hasplugin("xdist_runner")
