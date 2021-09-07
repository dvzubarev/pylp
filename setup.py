from setuptools import setup, find_packages

setup(
    name='pylp',
    version='0.1',
    description='linguistic',
    author='dvzubarev',
    author_email='zubarev@isa.ru',
    license='MIT',
    packages=find_packages(),
    install_requires=['ujson', 'libpyexbase'],
)
