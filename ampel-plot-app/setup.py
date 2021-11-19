#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-plot/ampel-plot-app/setup.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 19.11.2021
# Last Modified Date: 19.11.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from setuptools import setup, find_namespace_packages # type: ignore

setup(
	name='ampel-plot-app',
	version='0.8.1',
	packages=find_namespace_packages(),
	package_data = {
		'': ['py.typed'],
		'conf': [
			'*.json', '**/*.json', '**/**/*.json',
			'*.yaml', '**/*.yaml', '**/**/*.yaml',
			'*.yml', '**/*.yml', '**/**/*.yml'
		]
	},
	install_requires = ["ampel-plot", "ampel-plot-browse", "pyinstaller", "pysimplegui", "psutil"]
)
