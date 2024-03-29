#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot-browse/ampel/plot/SVGPlot.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                13.06.2019
# Last Modified Date:  26.09.2022
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

import os, html
from collections.abc import Sequence
from ampel.types import Tag
from ampel.content.SVGRecord import SVGRecord
from ampel.plot.util.compression import decompress_svg_dict
from ampel.plot.util.transform import svg_to_png_html, rescale_str


class SVGPlot:

	def __init__(self,
		content: SVGRecord,
		title_left_padding: int = 0,
		doc_tags: None | Tag | list[Tag] = None
	):

		if isinstance(content['svg'], bytes):
			self._record = decompress_svg_dict(content)
		else:
			self._record = content

		self._tags = content['tag']
		self._title_left_padding = title_left_padding
		self._doc_tags = sorted(doc_tags) if doc_tags else doc_tags
		self._pngd: None | dict[tuple[float, int], str] = None


	def has_tag(self, tag: Tag) -> bool:
		if not self._tags:
			return False
		if isinstance(self._tags, (str, int)):
			return tag == self._tags
		return tag in self._tags


	def get_file_name(self) -> str:
		return self._record['name']


	def get_oid(self) -> None | str:
		return self._record.get('oid')


	def has_tags(self, tags: Sequence[Tag]) -> bool:
		if not self._tags:
			return False
		if isinstance(self._tags, (str, int)):
			return self._tags in tags
		return all(el in self._tags for el in tags)


	def to_html_file(self, path: str, **kwargs) -> None:
		with open(os.path.join(path, self._record['name']) + '.html', 'w') as f:
			f.write("<html><head></head><body>")
			f.write(self._repr_html_(**kwargs))
			f.write("</body></html>")
		

	def _get_title(self, title_prefix: None | str = None, html_escape: bool = False) -> str:
		return '<h3 class="h3title" style="padding-left:%ipx;line-height:20pt;text-align:center">%s %s</h3>' % (
			self._title_left_padding,
			"" if title_prefix is None else title_prefix,
			(
				html.escape(self._record['title']) if html_escape
				else self._record['title']
			).replace("\n", "<br/>")
		)


	def _get_tags(self,
		include_doc_tags: bool = False,
		display: bool = False,
		html_escape: bool = False
	) -> str:

		if display:
			first = '<h3 class="h3tags">'
		else:
			first = '<h3 class="h3tags" style="display:none">'

		if include_doc_tags and self._doc_tags:
			tags = str(self._doc_tags) if isinstance(self._doc_tags, (int, str)) \
				else " ".join(self._doc_tags) # type: ignore[arg-type]
		else:
			tags = str(self._tags)

		if html_escape:
			return first + html.escape(tags) + '</h3>'

		return first + tags + '</h3>'


	def _get_extra(self, display: bool = False) -> str:

		if display:
			out = '<h3 class="h3extra">'
		else:
			out = '<h3 class="h3extra" style="display:none">'

		if (oid := self.get_oid()):
			out += f'<span class="oid" data-oid="{oid}">oid</span>'

		out += f'<a href="#" download="{self.get_file_name()}">download</a></h3>'
		return out


	def get(self, scale: float = 1.0) -> str:
		if scale == 1.0:
			return self._record['svg'] # type: ignore[return-value]
		return rescale_str(self._record['svg'], scale) # type: ignore


	def _build_png(self, png_convert: int, scale: float = 1.0) -> str:
		if self._pngd is None:
			self._pngd = {}
		if (scale, png_convert) not in self._pngd:
			self._pngd[(scale, png_convert)] = svg_to_png_html(
				self._record['svg'], # type: ignore[arg-type]
				scale = scale,
				dpi = png_convert
			)
		return self._pngd[(scale, png_convert)]


	def _repr_html_(self,
		scale: float = 1.0,
		title_prefix: None | str = None,
		title_on_top: bool = False,
		tags_on_top: bool = True,
		include_doc_tags: bool = False,
		padding_bottom: int = 0,
		png_convert: None | int = None
	) -> str:
		"""
		:param scale: if None, native scaling is used
		:param png_convert: DPI value of the produced image
		"""

		html = '<div style="padding-bottom: %ipx;text-align: center" class="%s">' % (
			padding_bottom,
			" ".join(
				str(el) if isinstance(el, int) else el
				for el in ([self._tags] if isinstance(self._tags, (int, str)) else self._tags)
			) + " PLOT hovernow"
		)

		if title_on_top:
			html += self._get_title(title_prefix, html_escape=True)

		if tags_on_top:
			html += self._get_tags(include_doc_tags, html_escape=True)

		html += self._get_extra()

		# html += SVGPlot.display_div

		if isinstance(self._record['svg'], bytes):
			raise ValueError("SVGRecord should not be compressed")

		if png_convert:
			print(f"Converting {self.get_file_name()} to PNG")
			if self._pngd and (scale, png_convert) in self._pngd:
				html += self._pngd[(scale, png_convert)]
			else:
				html += svg_to_png_html(
					self._record['svg'],
					scale = scale,
					dpi = png_convert
				)
		else:
			if scale == 1.0:
				html += self._record['svg'].replace('xlink"', 'xlink" class=mainimg')
			else:
				html += rescale_str(self._record['svg'], scale=scale).replace('xlink"', 'xlink" class=mainimg')

		if not title_on_top:
			html += self._get_title(title_prefix, html_escape=True)

		if not tags_on_top:
			html += self._get_tags(include_doc_tags, html_escape=True)

		return html + '</div>'


	def show_html(self, **kwargs):
		"""
		:param **kwargs: see _repr_html_ arguments for details
		"""
		from IPython.display import HTML
		return HTML(
			self._repr_html_(**kwargs)
		)
