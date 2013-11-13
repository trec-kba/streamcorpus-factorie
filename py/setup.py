#!/usr/bin/env python

import os
import sys
import fnmatch
import subprocess

## prepare to run PyTest as a command
from distutils.core import Command

from setuptools import setup, find_packages

from version import get_git_version
VERSION, SOURCE_LABEL = get_git_version()
PROJECT = 'streamcorpus_factorie'
AUTHOR = 'Diffeo, Inc.'
AUTHOR_EMAIL = 'support@diffeo.com'
DESC = 'Tools for building streamcorpus objects for particular collections of text used in TREC KBA.'

def read_file(file_name):
    file_path = os.path.join(
        os.path.dirname(__file__),
        file_name
        )
    return open(file_path).read()

def recursive_glob(treeroot, pattern):
    results = []
    for base, dirs, files in os.walk(treeroot):
        goodfiles = fnmatch.filter(files, pattern)
        results.extend(os.path.join(base, f) for f in goodfiles)
    return results

def recursive_glob_with_tree(treeroot, pattern):
    results = []
    for base, dirs, files in os.walk(treeroot):
        goodfiles = fnmatch.filter(files, pattern)
        one_dir_results = []
        for f in goodfiles:
            one_dir_results.append(os.path.join(base, f))
        results.append((base, one_dir_results))
    return results


def _myinstall(pkgspec):
    setup(
        script_args = ['-q', 'easy_install', '-v', pkgspec],
        script_name = 'easy_install'
    )


class PyTest(Command):
    '''run py.test'''

    description = 'runs py.test to execute all tests'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        _myinstall('pytest>2.3')
        if self.distribution.install_requires:
            for ir in self.distribution.install_requires:
                _myinstall(ir)

        # reload sys.path for any new libraries installed
        import site
        site.main()
        print sys.path
        # use pytest to run tests
        pytest = __import__('pytest')
        pytest.main(['-s', 'src'])


setup(
    name=PROJECT,
    version=VERSION,
    description=DESC,
    license='MIT/X11 license http://opensource.org/licenses/MIT',
    #long_description=read_file('README.md'),
    source_label=SOURCE_LABEL,
    long_description="",
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url='',
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    entry_points= {'streamcorpus.pipeline.stages': 'factorie_batch = streamcorpus_factorie:factorie_batch'},
    cmdclass={'test': PyTest},
    # We can select proper classifiers later
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',  ## MIT/X11 license http://opensource.org/licenses/MIT
    ],
    install_requires=[
        'streamcorpus-dev>=0.3.5',
        'streamcorpus_pipeline>=0.3.28',
    ],
    data_files = [
        ## this does not appear to actually put anything into the egg...
        ('configs', recursive_glob('configs', '*.yaml')),
    ]
)
