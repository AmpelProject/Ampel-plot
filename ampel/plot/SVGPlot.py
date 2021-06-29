#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-plots/ampel/plot/SVGPlot.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 13.06.2019
# Last Modified Date: 10.03.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from typing import Optional, Sequence
from ampel.types import Tag
from ampel.content.SVGRecord import SVGRecord
from ampel.plot.utils import rescale, to_png, decompress_svg_dict

class SVGPlot:

	# display_div = '<div style="display: inline-flex; justify-content: center;">'

	def __init__(
		self, content: SVGRecord, title_left_padding: int = 0, center: bool = True
	):

		if isinstance(content['svg'], bytes):
			self._record = decompress_svg_dict(content)
		else:
			self._record = content

		self._scale = 1.0
		self._tags = content['tag']
		self._title_left_padding = title_left_padding
		self._center = center


	def rescale(self, scale: float = 1.0) -> None:

		if self._scale == scale:
			return

		self._record['svg'] = rescale(self._record['svg'], scale) # type: ignore # later
		self._scale = scale


	def has_tag(self, tag: Tag) -> bool:
		if not self._tags:
			return False
		if isinstance(self._tags, (str, int)):
			return tag == self._tags
		return tag in self._tags


	def has_tags(self, tags: Sequence[Tag]) -> bool:
		if not self._tags:
			return False
		if isinstance(self._tags, (str, int)):
			return self._tags in tags
		return all(el in self._tags for el in tags)


	def _repr_html_(self,
		scale: Optional[float] = None, show_title: bool = True,
		title_prefix: Optional[str] = None, show_tags: bool = False,
		padding_bottom: int = 0, png_convert: bool = False
	) -> str:
		"""
		:param scale: if None, native scaling is used
		"""

		html = "<center>" if self._center else ""

		html += '<div style="padding-bottom: %ipx">' % padding_bottom

		if show_title:
			html += '<h3 style="padding-left:%ipx">%s %s</h3>' % (
				self._title_left_padding,
				"" if title_prefix is None else title_prefix,
				self._record['title']
			)

		if show_tags:
			html += '<h3>' + str(self._tags) + '</h3>'

		# html += SVGPlot.display_div
		html += "<div>"

		if isinstance(self._record['svg'], bytes):
			raise ValueError("SVGRecord should not be compressed")

		if scale is not None and isinstance(scale, (float, int)):
			if png_convert:
				html += to_png(
					rescale(self._record['svg'], scale),
					dpi=png_convert
				)
			else:
				html += rescale(self._record['svg'], scale)
		else:
			html += to_png(self._record['svg'], dpi=png_convert) if png_convert else self._record['svg']

		return html + '</div></div></center>' if self._center else '</div></div>'


	def show_html(self, **kwargs):
		"""
		:param **kwargs: see _repr_html_ arguments for details
		"""
		from IPython.display import HTML
		return HTML(
			self._repr_html_(**kwargs)
		)
