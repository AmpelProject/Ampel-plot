#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot-browse/ampel/plot/SVGCollection.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                13.06.2019
# Last Modified Date:  20.04.2022
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

import pkg_resources # type: ignore[import]
from multiprocessing import Pool
from ampel.plot.SVGPlot import SVGPlot
from ampel.content.SVGRecord import SVGRecord
from ampel.plot.util.compression import decompress_svg_dict
from ampel.plot.util.transform import svg_to_png_html

distrib = pkg_resources.get_distribution("ampel-plot-browse")
base_html = distrib.get_resource_string(__name__, "data/collection.html").decode('utf-8')


class SVGCollection:

	def __init__(self, title: str = None) -> None:
		""" :param title: title of this collection """
		self._svgs: list[SVGPlot] = []
		self._col_title = title


	def add_svg_plot(self, svgp: SVGPlot) -> None:

		if not isinstance(svgp, SVGPlot):
			raise ValueError("Instance of ampel.plot.SVGPlot expected")

		self._svgs.append(svgp)


	def add_svg_dict(self, svgd: SVGRecord, title_left_padding: int = 0) -> None:
		self._svgs.append(
			SVGPlot(
				content = svgd,
				title_left_padding = title_left_padding
			)
		)


	def add_raw_db_dict(self, svgd: SVGRecord) -> None:
		""" :param svgd: raw svg dict loaded from DB """
		self.add_svg_dict(
			decompress_svg_dict(svgd)
		)


	def get_svgs(self, tag: None | str = None, tags: None | list[str] = None) -> list[SVGPlot]:

		if tag:
			return [svg for svg in self._svgs if svg.has_tag(tag)]
		if tags:
			return [svg for svg in self._svgs if svg.has_tags(tags)]

		return self._svgs


	def _repr_html_(self,
		scale: float = 1.0,
		show_col_title: bool = True,
		title_prefix: None | str = None,
		hide_if_empty: bool = True,
		flexbox_wrap: bool = True,
		full_html: bool = True,
		png_convert: None | int = None
	) -> None | str:
		"""
		:param scale: if None, native scaling is used
		"""

		if hide_if_empty and not self._svgs:
			return None

		if full_html:
			html = base_html
		else:
			html = ""

		# html += '<hr style="width:100%; border: 2px solid;"/>'

		if show_col_title and self._col_title:
			html += '<h1 style="color: darkred">' + self._col_title.replace("\n", "<br/>") + '</h1>'

		if flexbox_wrap:
			html += '<div id=mainwrap style="\
				text-align:center; \
				display: flex; \
				flex-direction: row; \
				flex-wrap: wrap; \
				justify-content: center">'

		if png_convert and len(self._svgs) > 1:

			with Pool() as pool:
				futures = [
					pool.apply_async(svg_to_png_html, (svg._record['svg'], png_convert, scale))
					for svg in self._svgs
				]
				for f, svg in zip(futures, self._svgs):
					if svg._pngd is None:
						svg._pngd = {}
					svg._pngd[(scale, png_convert)] = f.get() # type: ignore

		for svg in self._svgs:
			html += svg._repr_html_(
				scale = scale,
				title_prefix = title_prefix,
				png_convert = png_convert
			)

		if flexbox_wrap:
			html += "</div>"

		if full_html:
			html += "</body><html>"

		return html


	def show_html(self, **kwargs):
		"""
		:param **kwargs: see _repr_html_ arguments for details
		"""
		from IPython.display import HTML
		return HTML(
			self._repr_html_(**kwargs)
		)
