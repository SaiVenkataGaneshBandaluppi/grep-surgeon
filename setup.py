# MIT License - see LICENSE file for details
from setuptools import find_packages, setup

setup(
    name="grep-surgeon",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pyyaml>=6.0.2",
        "click>=8.1.7",
    ],
    entry_points={
        "console_scripts": [
            "grep-surgeon=grep_surgeon.cli:main",
        ],
    },
    python_requires=">=3.11",
)
