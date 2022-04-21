#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot-browse/ampel/plot/util/clipboard.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                16.11.2021
# Last Modified Date:  22.11.2021
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

import platform, json, time, re, gc # type: ignore[import]

from typing import Any
from pymongo.collection import Collection # type: ignore[import]
from ampel.util.recursion import walk_and_process_dict
from ampel.plot.SVGCollection import SVGCollection
from ampel.model.PlotBrowseOptions import PlotBrowseOptions
from ampel.plot.util.load import print_func, _handle_json, _gather_plots

if platform.system() == 'Darwin':
	import AppKit # type: ignore[import] # noqa
else:
	import pyperclip # type: ignore[import] # noqa


def read_from_clipboard(
	pbo: PlotBrowseOptions,
	plots_col: Collection,
	keyboard_callback: Any,
	gui_callback: Any = None,
	exit_on_interrupt: bool = True
) -> None:
	"""
	Note: method never returns unless CTRL-C is pressed or gui_callback raises KeyboardInterrupt
	"""

	recent_value = ""
	scol = SVGCollection()

	pattern = re.compile(r"(?:NumberLong|ObjectId)\((.*?)\)", re.DOTALL)
	#from bson.json_util import loads

	if gui_callback is None:
		gui_callback = lambda: None

	gui_callback()
	print_func("Monitoring clipboard...")

	if platform.system() == 'Darwin':
		board = AppKit.NSPasteboard.generalPasteboard()
		get_cbc = lambda: board.changeCount()
	else:
		pyperclip.copy('')
		get_cbc = pyperclip.paste()

	try:
		while True:

			tmp_value = get_cbc()
			gui_callback()

			if tmp_value != recent_value:

				recent_value = tmp_value
				if platform.system() == 'Darwin':
					tmp_value = board.stringForType_(AppKit.NSStringPboardType)

				try:

					# if pattern.match(tmp_value): # no time to check why it doesn't work
					if tmp_value and ("NumberLong" in tmp_value or "ObjectId" in tmp_value):
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
							scol = _handle_json(plots, scol, plots_col, pbo, ctrl_pressed)
					else:
						scol = _handle_json(j, scol, plots_col, pbo, ctrl_pressed)
					gc.collect()
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
