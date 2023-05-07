#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = []

test_requirements = [
    "pytest>=3",
]

setup(
    author="Nick Gigliotti",
    author_email="ndgigliotti@gmail.com",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="A dot-accessible configuration manager for deeply nested configuration files.",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords=[
        "dot_config",
        "dot-config",
        "dot config",
        "config",
        "configuration",
        "config file",
        "configuration file",
        "configuration manager",
        "config manager",
        "configuration management",
        "yaml",
        "json",
        "dot accessible",
        "dot-accessible",
        "attribute",
        "attribute accessible",
        "attribute-accessible",
        "recursive",
        "nested",
        "nested configuration",
        "nested config",
        "deeply nested",
    ],
    name="dot_config",
    packages=find_packages(include=["dot_config", "dot_config.*"]),
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/ndgigliotti/dot-config",
    version="0.1.0",
    zip_safe=False,
)
