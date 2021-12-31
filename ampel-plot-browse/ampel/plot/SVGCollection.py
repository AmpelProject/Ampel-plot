#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot-browse/ampel/plot/SVGCollection.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                13.06.2019
# Last Modified Date:  30.11.2021
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

from typing import Optional
from ampel.plot.util.load import decompress_svg_dict
from ampel.plot.SVGPlot import SVGPlot
from ampel.content.SVGRecord import SVGRecord


class SVGCollection:

	def __init__(self,
		title: str = None,
		inter_padding: int = 100,
		center: bool = True
	) -> None:
		"""
		:param title: title of this collection
		:param scale: scale factor for all SVGs (default: 1.0)
		:param inter_padding: sets padding in px between plots of this collection
		"""
		self._svgs: list[SVGPlot] = []
		self._col_title = title
		self._inter_padding = inter_padding
		self._center = center


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


	def get_svgs(self, tag: Optional[str] = None, tags: Optional[list[str]] = None) -> list[SVGPlot]:

		if tag:
			return [svg for svg in self._svgs if svg.has_tag(tag)]
		if tags:
			return [svg for svg in self._svgs if svg.has_tags(tags)]

		return self._svgs


	def _repr_html_(self,
		scale: float = 1.0, show_col_title: bool = True,
		title_prefix: Optional[str] = None, show_svg_titles: bool = True,
		hide_if_empty: bool = True,
		png_convert: Optional[int] = None,
		inter_padding: Optional[int] = None,
		flexbox_wrap: bool = True,
		full_html: bool = True
	) -> Optional[str]:
		"""
		:param scale: if None, native scaling is used
		"""

		if hide_if_empty and not self._svgs:
			return None

		if full_html:
			# TODO: put this in a file, update package data and access it via pkg_resources
			html = """
			<html>
			<body>

			<div id=tagfilter style='display: block'>
				<input id=tags type='text' placeholder="tags" style="width: 100px"/>
				<button onclick="show_only()">Show</button>
				<button onclick="toggle_div()">Toggle</button>
				<button onclick="show_all()">Clear</button>
				<button id=tightbtn onclick="tight()">Tight</button>
				<button id=tightbtn onclick="toggle_titles()">Titles</button>
			<div>

			<script>

				function toggle_div() {
					tags = document.getElementById('tags').value.split(" ");
					for (var y = 0; y < tags.length; y++) {
						var plots = document.getElementsByClassName(tags[y]);
						for (var i = 0; i < plots.length; i++) {
							if (plots[i].style.display === "none")
								plots[i].style.display = "block";
							else
								plots[i].style.display = "none";
						}
					}
				}

				function show_only() {
					var plots = document.getElementsByClassName("PLOT");
					tags = document.getElementById('tags').value.split(" ");
					for (var i = 0; i < plots.length; i++) {
						var found = false;
						for (var j=0; j < tags.length; j++) {
							if (plots[i].classList.contains(tags[j].toUpperCase())) {
								plots[i].style.display = "block";
								found = true;
							}
						}
						if (!found)
							plots[i].style.display = "none";
					}
				}

				function show_all() {
					var plots = document.getElementsByClassName("PLOT");
					for (var i=0; i < plots.length; i ++) {
						if (plots[i].style.display === "none")
							plots[i].style.display = "block";
					}
				}

				function tight() {
					var plots = document.getElementsByClassName("PLOT");
					for (var i=0; i < plots.length; i ++)
						plots[i].style.paddingBottom = "0px";
					document.getElementById("tightbtn").style.display = "none";
				}

				function toggle_titles() {
					var h3s = document.getElementsByTagName("h3");
					for (var i=0; i < h3s.length; i ++)
						if (h3s[i].style.display === "none")
							h3s[i].style.display = "block";
						else
							h3s[i].style.display = "none";
				}

				document.getElementById("tags")
					.addEventListener("keyup", function(event) {
						event.preventDefault();
						if (event.keyCode === 13)
							show_only();
					}
				);
			</script>
			"""
		else:
			html = ""

		html += "<center>" if self._center else ""
		# html += '<hr style="width:100%; border: 2px solid;"/>'

		if show_col_title and self._col_title:
			html += '<h1 style="color: darkred">' + self._col_title.replace("\n", "<br/>") + '</h1>'

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
			html += "</div></center>" if self._center else "</div>"
		elif self._center:
			html += "</center>"

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
