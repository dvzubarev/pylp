import os
from setuptools import setup, find_packages

setup(
    name='pylp',
    version=os.environ.get('version', '0'),
    description='linguistic',
    author='dvzubarev',
    author_email='zubarev@isa.ru',
    license='MIT',
    packages=find_packages(),
    install_requires=['ujson', 'libpyexbase'],
)
