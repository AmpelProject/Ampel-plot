#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-plots/ampel/plot/SVGCollection.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 13.06.2019
# Last Modified Date: 09.02.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from typing import Optional, List
from ampel.plot.utils import decompress_svg_dict
from ampel.plot.SVGPlot import SVGPlot
from ampel.content.SVGRecord import SVGRecord


class SVGCollection:

	def __init__(self,
		title: str = None, scale: float = 1.0,
		inter_padding: int = 100, center: bool = True
	) -> None:
		"""
		:param title: title of this collection
		:param scale: scale factor for all SVGs (default: 1.0)
		:param inter_padding: sets padding in px between plots of this collection
		"""
		self._svgs: List[SVGPlot] = []
		self._col_title = title
		self._scale = scale
		self._inter_padding = inter_padding
		self._center = center


	def rescale(self, scale: float = 1.0) -> None:
		"""
		:param float scale: scale factor for all SVGs (default: 1.0)
		"""
		if self._scale == scale:
			return
		for el in self._svgs:
			el.rescale(scale)
		self._scale = scale


	def set_inter_padding(self, inter_padding: int) -> None:
		"""
		Sets padding in px between plots of this collection
		"""
		self._inter_padding = inter_padding


	def add_svg_plot(self, svgp: SVGPlot) -> None:

		if not isinstance(svgp, SVGPlot):
			raise ValueError("Instance of ampel.plot.SVGPlot expected")

		self._svgs.append(svgp)


	def add_svg_dict(self, svg_dict: SVGRecord, title_left_padding: int = 0) -> None:
		"""
		:param Dict svg_dict:
		:param int title_left_padding:
		"""
		self._svgs.append(
			SVGPlot(
				content = svg_dict,
				title_left_padding = title_left_padding
			)
		)


	def add_raw_db_dict(self, svg_dict: SVGRecord) -> None:
		"""
		:param Dict svg_dict: raw svg dict loaded from DB
		"""
		self.add_svg_dict(
			decompress_svg_dict(svg_dict)
		)


	def get_svgs(self, tag: Optional[str] = None, tags: Optional[List[str]] = None) -> List[SVGPlot]:

		if tag:
			return [svg for svg in self._svgs if svg.has_tag(tag)]
		if tags:
			return [svg for svg in self._svgs if svg.has_tags(tags)]

		return self._svgs


	def _repr_html_(
		self, scale: Optional[float] = None, show_col_title: bool = True,
		title_prefix: Optional[str] = None, show_svg_titles: bool = True,
		hide_if_empty: bool = True,
		png_convert: bool = False,
		inter_padding: Optional[int] = None,
		flexbox_wrap: bool = True
	) -> Optional[str]:
		"""
		:param scale: if None, native scaling is used
		"""

		if hide_if_empty and not self._svgs:
			return None

		html = "<center>" if self._center else ""
		# html += '<hr style="width:100%; border: 2px solid;"/>'

		if show_col_title and self._col_title:
			html += '<h1 style="color: darkred">' + self._col_title + '</h1>'

		if flexbox_wrap:
			html += '<div style="\
				text-align:center; \
				display: flex; \
				flex-direction: row; \
				flex-wrap: wrap; \
				justify-content: center">'

		for svg in self._svgs:
			html += svg._repr_html_(
				scale = scale,
				show_title = show_svg_titles,
				title_prefix = title_prefix,
				padding_bottom = self._inter_padding if inter_padding is None else inter_padding,
				png_convert = png_convert
			)

		if flexbox_wrap:
			return html + "</div></center>" if self._center else html + "</div>"
		else:
			return html + "</center>" if self._center else html


	def show_html(self, **kwargs):
		"""
		:param **kwargs: see _repr_html_ arguments for details
		"""
		from IPython.display import HTML
		return HTML(
			self._repr_html_(**kwargs)
		)
