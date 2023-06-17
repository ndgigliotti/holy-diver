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
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    description="A dot-accessible configuration manager for deeply nested configuration files.",
    install_requires=requirements,
    license="MIT license",
    long_description=readme,
    long_description_content_type="text/x-rst",
    include_package_data=True,
    keywords=[
        "holy_diver",
        "holy-diver",
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
    name="holy-diver",
    packages=find_packages(include=["holy_diver", "holy_diver.*"]),
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/ndgigliotti/holy-diver",
    download_url="https://github.com/ndgigliotti/holy-diver/archive/refs/tags/v0.1.0-alpha.3.tar.gz",
    version="v0.1.0-alpha.3",
    zip_safe=False,
)
