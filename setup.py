import os
from setuptools import setup, find_packages

import versioneer

with open(os.path.join('./', 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt') as f:
    requires = f.read().splitlines()
    
setup(
    name='halq',
    url='https://github.com/arinyaho/halq',
    license='MIT',
    author='arinyaho',
    description='Package for quant investment',
    long_description=long_description,
    packages=find_packages(exclude=['halq.test']),
    keyword=['quant', 'investment', 'stock'],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only'
    ],
    python_requires='>=3.7',
    install_requires=requires
)