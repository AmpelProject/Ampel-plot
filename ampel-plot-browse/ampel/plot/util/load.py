#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot-browse/ampel/plot/util/load.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                17.05.2019
# Last Modified Date:  13.04.2022
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

import base64
from typing import Any
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
	pbo: PlotBrowseOptions,
	scol: SVGCollection,
	concatenate: bool = False
) -> SVGCollection:

	if pbo.stack < 2:
		if isinstance(j, dict):
			_load_and_show_plot(j, pbo)
		elif isinstance(j, list):
			for d in j:
				_load_and_show_plot(d, pbo)
		return scol

	if isinstance(j, dict):
		scol = _load_and_add_plot(j, scol, pbo)
	elif isinstance(j, list):
		for d in j:
			_load_and_add_plot(d, scol, pbo)

	if concatenate:
		return scol

	show_collection(scol, pbo)
	return SVGCollection()


def _load_and_add_plot(
	j: Any,
	scol: SVGCollection,
	pbo: PlotBrowseOptions
) -> SVGCollection:
	""" will display and reset collection if number of plots exceeds pbo.stack """

	if (d := _check_adapt(j)):
		splot = SVGPlot(d) # type: ignore
		print_func("Adding", splot._record['name'])
		scol.add_svg_plot(splot)
		if (len(scol._svgs) % pbo.stack) == 0:
			print_func(f"Displaying plot stack ({len(scol._svgs)} figures)")
			show_collection(scol, pbo)
			scol = SVGCollection()

	return scol


def _load_and_show_plot(j: Any, pbo: PlotBrowseOptions) -> None:

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
