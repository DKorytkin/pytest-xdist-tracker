import codecs

from setuptools import find_packages, setup

VERSION_FILE = "pytest_xdist_tracker/_version.py"


with codecs.open("README.md", "r", "utf-8") as fh:
    long_description = fh.read()


setup(
    name="pytest-xdist-tracker",
    use_scm_version={
        "write_to": VERSION_FILE,
        "local_scheme": "dirty-tag",
    },
    setup_requires=["setuptools_scm==5.0.2"],
    author="Denis Korytkin",
    author_email="dkorytkin@gmail.comm",
    description="pytest plugin helps to reproduce failures for particular xdist node",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DKorytkin/pytest-xdist-tracker",
    keywords=["py.test", "pytest", "xdist plugin", "tracker", "failed tests"],
    py_modules=[
        "pytest_xdist_tracker.plugin",
        "pytest_xdist_tracker.tracker",
    ],
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        "pytest>=3.5.1",
        "pytest-xdist>=1.23.2",
        "pytest-forked>=1.0.1",
        "six>=1.15.0",
    ],
    entry_points={"pytest11": ["tracker = pytest_xdist_tracker.plugin"]},
    license="MIT license",
    python_requires=">=2.7",
    classifiers=[
        "Framework :: Pytest",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: Utilities",
    ],
)
