import re

from setuptools import setup

version = ""
with open("sythe/__init__.py") as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

requirements = []
with open("requirements.txt") as f:
    requirements = f.read().splitlines()


setup(
    name="sythe.py",
    author="AlexFlipnote",
    url="https://github.com/AlexFlipnote/Sythe.py",
    version=version,
    packages=["sythe"],
    description="A script that interacts with the Sythe website using Chrome drivers",
    include_package_data=True,
    install_requires=requirements
)
