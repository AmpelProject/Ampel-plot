#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot/ampel/demo/T3DemoSavePlot.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                25.07.2022
# Last Modified Date:  25.07.2022
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

import matplotlib.pyplot as plt
from random import random, randrange
from ampel.types import UBson
from ampel.struct.UnitResult import UnitResult
from ampel.view.T3Store import T3Store
from ampel.abstract.AbsT3PlainUnit import AbsT3PlainUnit
from ampel.model.PlotProperties import PlotProperties
from ampel.plot.create import create_plot_record


class T3DemoSavePlot(AbsT3PlainUnit):

	plot: PlotProperties = PlotProperties(
		tags = ["DEMO_PLOT"],
		file_name = {
			"format_str": "plot_%s_%s.svg",
			"arg_keys": ["first_suffix", "second_suffix"]
		},
		title = {
			"format_str": "A title - %s\n%s",
			"arg_keys": ["first_arg", "second_arg"]
		}
	)


	def process(self, t3s: T3Store) -> UBson | UnitResult:

		fig, ax = plt.subplots()
		x = [random() for i in range(20)]
		y = [randrange(-50, 50) / 100 for i in range(20)]
		dy = [randrange(0, 10) / 100 for i in range(20)]
		plt.scatter(x, y, s=10, zorder=20)
		plt.errorbar(x, y, yerr=dy, fmt="o", ms=0, zorder=10, color='darkgrey')
		ax.axhline(y=0, color='black', linestyle='-')
		ax.set_xlabel('Demo x-label')
		ax.set_ylabel('Demo y-label')

		return {
			'plot': create_plot_record(
				fig, self.plot,
				logger = self.logger,
				extra = {
					"first_suffix": "one",
					"second_suffix": "two",
					"first_arg": "foo",
					"second_arg": "bar",
				}
			)
		}
