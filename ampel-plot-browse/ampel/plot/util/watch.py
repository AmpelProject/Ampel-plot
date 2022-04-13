#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot-browse/ampel/plot/util/watch.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                13.04.2022
# Last Modified Date:  13.04.2022
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

import gc
from time import sleep, time
from pymongo.collection import Collection # type: ignore[import]
from ampel.util.recursion import walk_and_process_dict
from ampel.plot.SVGCollection import SVGCollection
from ampel.model.PlotBrowseOptions import PlotBrowseOptions
from ampel.plot.util.load import print_func, _gather_plots, _handle_json


def read_from_db(col: Collection, pbo: PlotBrowseOptions) -> None:

	try:

		print_func(f"Waching {col.database.name}->{col.name}")
		last_doc = next(col.find({'_id': -1}).limit(1), None)
		latest_ts = last_doc['meta']['ts'] if last_doc else time()

		while True:

			for doc in col.find({'meta.ts': {'$gt': latest_ts}}):

				print_func("*"*20)
				if doc['meta']['ts'] > latest_ts:
					latest_ts = doc['meta']['ts']

				scol = SVGCollection()
				plots: list[dict] = []

				walk_and_process_dict(
					arg = doc,
					callback = _gather_plots,
					match = ['plot'],
					plots = plots,
					debug = pbo.debug
				)

				_handle_json(
					plots if plots else doc,
					pbo, scol, concatenate = False
				)

			gc.collect()
			sleep(1)


	except KeyboardInterrupt:
		import sys
		print_func("\nUntil next time...\n")
		sys.exit(0)
