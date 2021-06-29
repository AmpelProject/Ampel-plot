#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-plots/main/setup.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 23.02.2021
# Last Modified Date: 29.06.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from setuptools import setup, find_namespace_packages # type: ignore

setup(
	name='ampel-plots',
	version='0.8.0',
	packages=find_namespace_packages(),
	package_data = {
		'': ['py.typed'],
		'conf': [
			'*.json', '**/*.json', '**/**/*.json',
			'*.yaml', '**/*.yaml', '**/**/*.yaml',
			'*.yml', '**/*.yml', '**/**/*.yml'
		]
	},
	install_requires = ["matplotlib", "svgutils==0.3.0", "cairosvg"]
)
