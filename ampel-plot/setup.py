#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot/setup.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                23.02.2021
# Last Modified Date:  21.04.2022
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

from setuptools import setup, find_namespace_packages # type: ignore
from pathlib import Path

setup(
	name='ampel-plot',
	version='0.8.3',
	long_description=(Path(__file__).parent / "README.md").read_text(),
	long_description_content_type="text/markdown",
	packages=find_namespace_packages(),
	package_data = {
		'': ['py.typed'],
		'conf': [
			'*.json', '**/*.json', '**/**/*.json',
			'*.yaml', '**/*.yaml', '**/**/*.yaml',
			'*.yml', '**/*.yml', '**/**/*.yml'
		]
	},
	python_requires = '>=3.10,<3.11',
	extras_require={"MPL": ["matplotlib"]},
)
