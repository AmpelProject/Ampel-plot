#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot-browse/ampel/plot/util/load.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                17.05.2019
# Last Modified Date:  20.04.2022
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

import base64
from typing import Any
from bson import ObjectId # type: ignore[import]
from pymongo.collection import Collection # type: ignore[import]
from ampel.plot.SVGCollection import SVGCollection
from ampel.plot.SVGPlot import SVGPlot
from ampel.model.PlotBrowseOptions import PlotBrowseOptions
from ampel.plot.util.show import show_collection, show_svg_plot


print_func = print
def set_print(pf: Any) -> None:
	global print_func
	print_func = pf


def _handle_json(
	j: dict | list[dict],
	svg_col: SVGCollection,
	plots_col: Collection,
	pbo: PlotBrowseOptions,
	concatenate: bool = False
) -> SVGCollection:

	if pbo.stack < 2:
		if isinstance(j, dict):
			_load_and_show_plot(j, plots_col, pbo)
		elif isinstance(j, list):
			for d in j:
				_load_and_show_plot(d, plots_col, pbo)
		return svg_col

	if isinstance(j, dict):
		svg_col = _load_and_add_plot(j, svg_col, plots_col, pbo)
	elif isinstance(j, list):
		for d in j:
			_load_and_add_plot(d, svg_col, plots_col, pbo)

	if concatenate:
		return svg_col

	show_collection(svg_col, pbo)
	return SVGCollection()


def _load_and_add_plot(
	j: Any,
	svg_col: SVGCollection,
	plots_col: Collection,
	pbo: PlotBrowseOptions
) -> SVGCollection:
	""" will display and reset collection if number of plots exceeds pbo.stack """

	_check_side_load(j, plots_col)
	if (d := _check_adapt(j)):
		splot = SVGPlot(d) # type: ignore
		print_func("Adding", splot._record['name'])
		svg_col.add_svg_plot(splot)
		if (len(svg_col._svgs) % pbo.stack) == 0:
			print_func(f"Displaying plot stack ({len(svg_col._svgs)} figures)")
			show_collection(svg_col, pbo)
			svg_col = SVGCollection()

	return svg_col


def _load_and_show_plot(j: Any, plots_col: Collection, pbo: PlotBrowseOptions) -> None:

	_check_side_load(j, plots_col)
	if (d := _check_adapt(j)):
		splot = SVGPlot(d) # type: ignore
		print_func("Displaying", splot._record['name'])
		show_svg_plot(splot, pbo) # type: ignore


def _gather_plots(path, k, d, **kwargs) -> None:
	""" Used by walk_and_process_dict(...) """

	if isinstance(d[k], dict):
		if kwargs.get('debug'):
			print_func(f"Found {path}.{k}: {d[k]['name']}")
		kwargs['plots'].append(d[k])

	elif isinstance(d[k], list):
		for i, el in enumerate(d[k]):
			if kwargs.get('debug'):
				print_func(f"Found {path}.{k}.{i}: {d[k][i]['name']}")
			kwargs['plots'].append(el)
	

def _check_adapt(j: Any) -> None | SVGPlot:
	if not isinstance(j, dict) or 'svg' not in j:
		return None
	if isinstance(j['svg'], dict) and '$binary' in j['svg']:
		j['svg'] = base64.b64decode(j['svg']['$binary'])
	return j # type: ignore


def _check_side_load(j: Any, col: Collection) -> None:

	if isinstance(j, dict) and 'svg' in j:
		if isinstance(j['svg'], str) and len(j['svg']) == 24:
			print_func(f"Side-loading {j['name']}")
			j['svg'] = next(col.find({'_id': ObjectId(j['svg'])}))['svg']
		if isinstance(j['svg'], ObjectId):
			print_func(f"Side-loading {j['name']}")
			j['svg'] = next(col.find({'_id': j['svg']}))['svg']

	elif isinstance(j, list):

		ids = []
		for i, el in enumerate(j):

			if isinstance(el['svg'], str) and len(el['svg']) == 24:
				ids.append((i, ObjectId(el['svg'])))

			elif isinstance(el['svg'], ObjectId):
				ids.append((i, el['svg']))

		if ids:
			resolved = {
				doc['_id']: doc['svg']
				for doc in col.find({'_id': {'$in': [x[1] for x in ids]}})
			}

			for i, el in ids:
				print_func(f"Side-loading {j[i]['name']}")
				j[i] = resolved[el]
