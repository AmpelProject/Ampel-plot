#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot-cli/setup.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                29.06.2021
# Last Modified Date:  11.01.2023
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

from setuptools import setup, find_namespace_packages # type: ignore

setup(
	name='ampel-plot-cli',
	version='0.8.3',
	packages=find_namespace_packages(),
	install_requires = ["ampel-core", "ampel-plot", "ampel-plot-browse"],
	python_requires = '>=3.10,<3.12',
	entry_points = {'cli': ['plot Show or export selected plots from the database = ampel.cli.PlotCommand']}
)
