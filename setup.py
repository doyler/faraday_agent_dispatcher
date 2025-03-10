#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2019  Infobyte LLC (http://www.infobytesec.com/)

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""The setup script."""

import sys
from setuptools import setup, find_packages

if sys.version_info.major < 3 or sys.version_info.minor < 7:
    print("Python >=3.7 is required to run the dispatcher.")
    print("Install a newer Python version to proceed")
    sys.exit(1)


with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['Click>=6.0', 'websockets', 'aiofiles', 'aiohttp<4.0.0', 'requests',
                'syslog_rfc5424_formatter', 'itsdangerous', 'autobahn', 'twisted']

setup_requirements = ['pytest-runner', 'click', 'setuptools_scm']

test_requirements = ['pytest', 'pytest-aiohttp']

setup(
    author="Eric Horvat",
    author_email='erich@infobytesec.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Faraday agent dispatcher to communicate an agent to faraday",
    entry_points={
        'console_scripts': [
            'faraday-dispatcher=faraday_agent_dispatcher.cli:main_sync',
        ],
    },
    install_requires=requirements,
    license="GNU General Public License v3",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='faraday integration',
    name='faraday_agent_dispatcher',
    packages=find_packages(include=['faraday_agent_dispatcher', 'faraday_agent_dispatcher.*']),
    use_scm_version=False,
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/infobyte/faraday_agent_dispatcher',
    version='1.0',
    zip_safe=False,
)
