#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-plot/ampel-plot-browse/ampel/plot/util/clipboard.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 16.11.2021
# Last Modified Date: 19.11.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

import base64, json, time, pyperclip, re  # type: ignore
from typing import Any, Optional, Union
from ampel.util.recursion import walk_and_process_dict
from ampel.plot.SVGCollection import SVGCollection
from ampel.plot.SVGPlot import SVGPlot
from ampel.model.PlotBrowseOptions import PlotBrowseOptions
from ampel.plot.util.show import show_collection, show_svg_plot

print_func = print
def set_print(pf: Any) -> None:
	global print_func
	print_func = pf


def read_from_clipboard(
	pbo: PlotBrowseOptions,
	keyboard_callback: Any,
	gui_callback: Any = None,
	exit_on_interrupt: bool = True
) -> None:
	"""
	Note: method never returns unless CTRL-C is pressed or gui_callback raises KeyboardInterrupt
	"""

	recent_value = ""
	scol = _new_col(pbo)

	pyperclip.copy('')
	pattern = re.compile(r"(?:NumberLong|ObjectId)\((.*?)\)", re.DOTALL)
	#from bson.json_util import loads

	if gui_callback is None:
		gui_callback = lambda: None

	gui_callback()
	print_func("Monitoring clipboard...")

	try:
		while True:

			tmp_value = pyperclip.paste()
			gui_callback()

			if tmp_value != recent_value:

				recent_value = tmp_value

				try:

					# if pattern.match(tmp_value): # no time to check why it doesn't work
					if tmp_value and "NumberLong" in tmp_value or "ObjectId" in tmp_value:
						j = json.loads(
							re.sub(pattern, r"\1", tmp_value)
						)
					else:
						j = json.loads(tmp_value)

					ctrl_pressed = keyboard_callback()
					if pbo.debug and ctrl_pressed:
						print_func("CTRL is pressed")

					if (
						(isinstance(j, dict) and 'svg' not in j) or
						(isinstance(j, list) and len(j) > 0 and 'svg' not in j[0])
					):
						plots: list[dict] = []
						walk_and_process_dict(
							arg = j,
							callback = _gather_plots,
							match = ['plot'],
							plots = plots,
							debug = pbo.debug
						)
						if plots:
							scol = _handle_json(plots, pbo, scol, ctrl_pressed)
					else:
						scol = _handle_json(j, pbo, scol, ctrl_pressed)
				except KeyboardInterrupt:
					raise
				except json.decoder.JSONDecodeError:
					if pbo.debug:
						import traceback
						print_func("JSONDecodeError")
						print_func(traceback.format_exc())
						print_func(tmp_value)
				except Exception:
					import traceback
					with open('error.log', 'w') as f:
						traceback.print_exc(file=f)
					print_func(traceback.format_exc())

			time.sleep(0.1)

	except KeyboardInterrupt:
		if exit_on_interrupt:
			import sys
			print_func("\nUntil next time...\n")
			sys.exit(0)


def _handle_json(
	j: Union[dict, list[dict]], pbo: PlotBrowseOptions,
	scol: SVGCollection, ctrl_pressed: bool = False
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

	if ctrl_pressed:
		return scol

	show_collection(scol, pbo)
	return _new_col(pbo)


def _load_and_add_plot(j: Any, scol: SVGCollection, pbo: PlotBrowseOptions) -> SVGCollection:
	""" will display and reset collection if number of plots exceeds pbo.stack """
	if (d := _check_adapt(j)):
		splot = SVGPlot(d) # type: ignore
		print_func("Adding", splot._record['name'])
		scol.add_svg_plot(splot)
		if (len(scol._svgs) % pbo.stack) == 0:
			print_func(f"Displaying plot stack ({len(scol._svgs)} figures)")
			show_collection(scol, pbo)
			scol = _new_col(pbo)
	return scol


def _load_and_show_plot(j: Any, pbo: PlotBrowseOptions) -> None:
	if (d := _check_adapt(j)): # type: ignore[assignment]
		splot = SVGPlot(d) # type: ignore
		print_func("Displaying", splot._record['name'])
		show_svg_plot(splot, pbo) # type: ignore


def _new_col(pbo: PlotBrowseOptions) -> SVGCollection:
	return SVGCollection(
		inter_padding = 0 if pbo.tight else 100
	)


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
	

def _check_adapt(j: Any) -> Optional[SVGPlot]:
	if not isinstance(j, dict) or 'svg' not in j:
		return None
	if isinstance(j['svg'], dict) and '$binary' in j['svg']:
		j['svg'] = base64.b64decode(j['svg']['$binary'])
	return j # type: ignore