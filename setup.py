import os

from setuptools import setup

install_requires = [
    "requests"
]

setup(
    name="cloud_storage_handler",
    version="0.0.1",
    packages=["cloud_storage_handler/"],
    install_requires=install_requires,
    include_package_data=True,
)