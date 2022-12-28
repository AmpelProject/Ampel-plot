#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot-browse/setup.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                23.02.2021
# Last Modified Date:  28.12.2022
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

from setuptools import setup, find_namespace_packages # type: ignore

setup(
	name='ampel-plot-browse',
	version='0.8.3',
	packages=find_namespace_packages(),
	package_data = {
		'': ['py.typed'],
		'data': ['*.html', '**/*.htm']
	},
	python_requires = '>=3.10,<3.11',
	install_requires = ["ampel-plot", "pyperclip", "pynput", "pyvips", "pygments", "pyyaml"]
)
