#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot-browse/ampel/plot/SVGPlot.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                13.06.2019
# Last Modified Date:  19.11.2021
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

import os
from typing import Optional, Union
from collections.abc import Sequence
from ampel.types import Tag
from ampel.content.SVGRecord import SVGRecord
from ampel.plot.util.load import decompress_svg_dict
from ampel.plot.util.transform import svg_to_png_html, rescale_str


class SVGPlot:

	def __init__(self,
		content: SVGRecord,
		title_left_padding: int = 0,
		center: bool = True,
		doc_tags: Union[None, Tag, list[Tag]] = None
	):

		if isinstance(content['svg'], bytes):
			self._record = decompress_svg_dict(content)
		else:
			self._record = content

		self._tags = content['tag']
		self._title_left_padding = title_left_padding
		self._center = center
		self._doc_tags = doc_tags


	def has_tag(self, tag: Tag) -> bool:
		if not self._tags:
			return False
		if isinstance(self._tags, (str, int)):
			return tag == self._tags
		return tag in self._tags


	def get_file_name(self) -> str:
		return self._record['name'] # type: ignore


	def has_tags(self, tags: Sequence[Tag]) -> bool:
		if not self._tags:
			return False
		if isinstance(self._tags, (str, int)):
			return self._tags in tags
		return all(el in self._tags for el in tags)


	def to_html_file(self, path: str) -> None:
		with open(os.path.join(path, self._record['name']) + '.html', 'w') as f:
			f.write("<html><head></head><body>")
			f.write(self._repr_html_())
			f.write("</body></html>")
		

	def _get_title(self, title_prefix: Optional[str] = None) -> str:
		return '<h3 style="padding-left:%ipx;line-height:20pt">%s %s</h3>' % (
			self._title_left_padding,
			"" if title_prefix is None else title_prefix,
			self._record['title'].replace("\n", "<br/>")
		)


	def _get_tags(self, include_doc_tags: bool = False) -> str:
		ret = '<h3>' + str(self._tags) + '</h3>'
		if include_doc_tags and self._doc_tags:
			ret += str(self._doc_tags) if isinstance(self._doc_tags, (int, str)) \
				else " ".join(self._doc_tags) # type: ignore[arg-type]
		else:
			ret += str(self._tags)
		return ret + '</h3>'


	def get(self, scale: float = 1.0) -> str:
		if scale == 1.0:
			return self._record['svg'] # type: ignore[return-value]
		return rescale_str(self._record['svg'], scale) # type: ignore


	def _repr_html_(self,
		scale: float = 1.0, show_title: bool = True,
		title_prefix: Optional[str] = None, title_on_top: bool = False,
		show_tags: bool = False, tags_on_top: bool = False,
		include_doc_tags: bool = False, padding_bottom: int = 0,
		png_convert: Optional[int] = None
	) -> str:
		"""
		:param scale: if None, native scaling is used
		:param png_convert: DPI value of the produced image
		"""

		html = "<center>" if self._center else ""
		html += '<div style="padding-bottom: %ipx" class="%s">' % (
			padding_bottom,
			"PLOT" if not self._tags else " ".join(
				str(el) if isinstance(el, int) else el
				for el in ([self._tags] if isinstance(self._tags, (int, str)) else self._tags)
			) + " PLOT"
		)

		if show_title and title_on_top:
			html += self._get_title(title_prefix)

		if show_tags and tags_on_top:
			html += self._get_tags(include_doc_tags)

		# html += SVGPlot.display_div
		html += "<div>"

		if isinstance(self._record['svg'], bytes):
			raise ValueError("SVGRecord should not be compressed")

		if png_convert:
			html += svg_to_png_html(self._record['svg'], scale=scale, dpi=png_convert)
		else:
			if scale == 1.0:
				html += self._record['svg']
			else:
				html += rescale_str(self._record['svg'], scale=scale)

		html += '</div>'

		if show_title and not title_on_top:
			html += self._get_title(title_prefix)

		if show_tags and not tags_on_top:
			html += self._get_tags(include_doc_tags)

		return html + '</div></center>' if self._center else '</div></div>'


	def show_html(self, **kwargs):
		"""
		:param **kwargs: see _repr_html_ arguments for details
		"""
		from IPython.display import HTML
		return HTML(
			self._repr_html_(**kwargs)
		)
