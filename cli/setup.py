#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-plots/cli/setup.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 29.06.2021
# Last Modified Date: 29.06.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from setuptools import setup, find_namespace_packages # type: ignore

setup(
	name='ampel-plots-cli',
	version='0.8.0',
	packages=find_namespace_packages(),
	install_requires = ["ampel-core"],
	entry_points = {'cli': ['plot Show or extract selected plots from the database = ampel.cli.PlotCommand']}
)
