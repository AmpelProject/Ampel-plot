#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-plot/ampel-plot-cli/setup.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 29.06.2021
# Last Modified Date: 19.11.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from setuptools import setup, find_namespace_packages # type: ignore

setup(
	name='ampel-plot-cli',
	version='0.8.1',
	packages=find_namespace_packages(),
	install_requires = ["ampel-core", "ampel-plot", "ampel-plot-browse"],
	entry_points = {'cli': ['plot Show or extract selected plots from the database = ampel.cli.PlotCommand']}
)
