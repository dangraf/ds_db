from setuptools import setup, find_packages
import os

def read_requirements(filepath):
    with open(filepath, 'r') as f:
        content = f.read().strip()
    return content.split('\n')

setup(
    name='ds_db',
    version='0.0.1',
    packages=find_packages(where='src'),
    package_dir={"":"src"},
    url='',
    license='Apache 2.0',
    author='Daniel Grafstroem',
    author_email='dangraf@hotmail.com',
    description='',
    install_requires=read_requirements('requirements.txt')
)