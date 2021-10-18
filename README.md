# pytest-xdist-tracker

This plugin allows us to keep artifact after running test with xdist (parallel)


## Installation

```shell
pip install pytest-xdist-tracker
```


## Using

For example, we use `pytest-xdist` for running tests in parallel and
we have a test that fails from time to time.
That definitely a flaky/coupled test that fails because 
before were executed tests that keep after self some unexpected state for our failed test

`pytest-xdist-tracker` can help with that case

It stores artifact after execution like this one `xdist_stats_worker_gw1.txt`
where `gw1` is number of xdist node

Then we can reproduce tests which were run in particular node where failure happened

```shell
pytest --from-xdist-stats=xdist_stats_worker_gw1.txt
```
It will collect tests as usual but will filter by our tests

note: this plugin works only with `pytest-xdist`