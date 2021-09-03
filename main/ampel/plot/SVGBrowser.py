#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-plots/ampel/plot/SVGBrowser.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 13.06.2019
# Last Modified Date: 29.06.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from typing import Optional, Any
from ampel.plot.SVGLoader import SVGLoader
from IPython.display import HTML, display
import random


class SVGBrowser:
	"""
	Alpha state, untested
	"""

	def __init__(self,
		svg_loader: SVGLoader,
		scale: Optional[float] = None,
		show_col_title: bool = True,
		show_svg_titles: bool = True,
		show_multi_stock: bool = False
	):
		self._scale = scale
		self._svg_loader = svg_loader
		self._show_col_title = show_col_title
		self._show_svg_titles = show_svg_titles
		self._show_multi_stock = show_multi_stock


	def show_multi_window(self):
		"""
		Shows all plots for one transient in one window
		"""
		pass


	def show_single_window(
		self, scale=None, append_tran_name=True,
		win_title="Ampel plots", stock_ids=None,
		png_convert=False, multiproc=0,
		global_flex_box=False
	):
		"""
		:param bool append_tran_name: appends transient name to plot titles
		"""

		win_id, dom_id = SVGBrowser._new_window(win_title)

		if global_flex_box:
			dom_id = SVGBrowser._insert_flex_box(win_id)

		if multiproc:

			from concurrent.futures import ProcessPoolExecutor
			futures = []

			with ProcessPoolExecutor(max_workers=multiproc) as executor:

				for stock_id in self._svg_loader._plots.keys():
					futures.append(
						executor.submit(
							get_html,
							stock_id,
							self._svg_loader._data_query,
							self._svg_loader._t2_query,
							scale,
							png_convert,
							not global_flex_box
						)
					)

				for future in futures:
					SVGBrowser._write_to_dom(
						dom_id, future.result(),
						'Adding %s info to %s<br>' % (stock_id, win_title)
					)
		else:

			for stock_id in self._svg_loader._plots:

				if stock_ids:
					if self._svg_loader._plots[stock_id] not in stock_ids:
						continue

				SVGBrowser._write_to_dom(
					dom_id,
					self._svg_loader._plots[stock_id]._repr_html_(
						scale=scale,
						title_prefix = self._get_title_prefix(stock_id),
						png_convert=png_convert,
						flexbox_wrap=not global_flex_box
					),
					'Adding %s info to %s<br>' % (stock_id, win_title)
				)


		display(HTML("Done"))


	def _get_title_prefix(self, stock_id: Any) -> Any:
		if isinstance(stock_id, tuple) and not self._show_multi_stock:
			return ""
		return stock_id


	def show_inline(self, scale: Optional[float] = None, png_convert: bool = False, inter_padding: int = 0):

		html = ""
		for stock_id in self._svg_loader._plots:
			if element := self._svg_loader._plots[stock_id]._repr_html_(
				scale = scale,
				title_prefix = self._get_title_prefix(stock_id),
				png_convert = png_convert,
				inter_padding = inter_padding
			):
				html += "<div>"
				html += element
				html += "</div>"

		display(HTML(html))


	@staticmethod
	def _new_window(title):
		"""
		:returns: js variable *name* pointing to body DOM element within the newly created window
		"""

		rand_str = str(random.randint(0, 100000))
		win_id = "win_" + rand_str
		body_id = "body_" + rand_str

		display(
			HTML(
				'<script type="text/Javascript"> \
					var %s=window.open("", "%s"); \
					%s.document.title="%s"; \
					var %s=%s.document.body; \
				</script>' % (win_id, title, win_id, title, body_id, win_id)
			)
		)

		return win_id, body_id


	@staticmethod
	def _write_to_dom(js_body_var_name, html_content, feedback=""):
		""" """

		display(
			HTML(
				'%s<script type="text/Javascript"> \
					%s.innerHTML += \'%s\';' \
					# %s.document.body.innerHTML += \'%s\';' \
				'</script>' % (
					feedback,
					js_body_var_name,
					html_content.replace("\n", "\\")
				)
			)
		)


	@staticmethod
	def _insert_flex_box(js_body_var_name):
		"""
		:returns: js variable *name* pointing to (flexbox)
		div DOM element within the newly created window
		"""
		flex_id = "flex_" + str(random.randint(0, 100000))

		display(
			HTML(
				'<script type="text/Javascript"> \
					%s.document.body.innerHTML += \'<div id=%s style="\
						text-align:center; \
						display: flex; \
						flex-direction: row; \
						flex-wrap: wrap; \
						justify-content: center"></div>\'; \
					var %s = %s.document.getElementById("%s");\
				</script>' % (
					js_body_var_name, flex_id,
					flex_id, js_body_var_name, flex_id
				)
			)
		)

		return flex_id


def get_html(
	stock_id, data_query, t2_query, scale=1.0,
	png_convert=False, flexbox_wrap_svg_col=True
):

	svg_loader = SVGLoader()
	svg_loader._data_query = data_query
	svg_loader._t2_query = t2_query
	svg_loader.load_plots()

	return svg_loader._plots[stock_id]._repr_html_(
		scale=scale,
		title_prefix=stock_id,
		png_convert=png_convert,
		flexbox_wrap=flexbox_wrap_svg_col
	)
