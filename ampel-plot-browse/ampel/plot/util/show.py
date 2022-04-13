#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot-browse/ampel/plot/util/show.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                16.11.2021
# Last Modified Date:  13.04.2022
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

from typing import TYPE_CHECKING
import os, webbrowser, tempfile, hashlib
from collections.abc import Callable
from ampel.plot.util.transform import svg_to_png
from ampel.model.PlotBrowseOptions import PlotBrowseOptions

if TYPE_CHECKING:
	from ampel.plot.SVGCollection import SVGCollection
	from ampel.plot.SVGPlot import SVGPlot


def show_svg_plot(svg: "SVGPlot", pbo: PlotBrowseOptions) -> None:

	tmp_dir = os.path.join(tempfile.gettempdir(), "ampel")
	if not os.path.exists(tmp_dir):
		os.mkdir(tmp_dir)

	path = os.path.join(tmp_dir, svg.get_file_name())

	if pbo.png:
		path = path.removesuffix(".svg") + ".png"
		with open(path, 'wb') as fb:
			fb.write(
				svg_to_png(
					svg.get(),
					dpi = pbo.png,
					scale = pbo.scale
				)
			)

	elif pbo.html:
		path = path.removesuffix(".svg") + ".html"
		with open(path, 'w', encoding='utf-8') as fh:
			fh.write(
				svg._repr_html_(scale = pbo.scale)
			)

	else:
		with open(path, 'w', encoding='utf-8') as ft:
			ft.write(
				svg.get(scale=pbo.scale)
			)

	webbrowser.open('file://' + path)


def show_collection(scol: "SVGCollection", pbo: PlotBrowseOptions, print_func: None | Callable = None) -> None:

	if x := scol._repr_html_(scale=pbo.scale, png_convert=pbo.png):

		tmp_file = os.path.join(
			_get_ampel_tmp_dir(),
			hashlib.md5(x.encode('utf8')).hexdigest() + ".html"
		)

		with open(tmp_file, 'w', encoding='utf-8') as fh:
			fh.write(x)

		webbrowser.open('file://' + tmp_file)
	elif print_func:
		print_func("Empty collection: nothing to display") # type: ignore[operator]


def _get_ampel_tmp_dir() -> str:
	tmp_dir = os.path.join(tempfile.gettempdir(), "ampel")
	if not os.path.exists(tmp_dir):
		os.mkdir(tmp_dir)
	return tmp_dir
