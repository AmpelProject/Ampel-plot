#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot-browse/ampel/plot/SVGCollection.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                13.06.2019
# Last Modified Date:  12.04.2022
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

from multiprocessing import Pool
from ampel.plot.SVGPlot import SVGPlot
from ampel.content.SVGRecord import SVGRecord
from ampel.plot.util.load import decompress_svg_dict
from ampel.plot.util.transform import svg_to_png_html


class SVGCollection:

	def __init__(self, title: str = None) -> None:
		"""
		:param title: title of this collection
		:param scale: scale factor for all SVGs (default: 1.0)
		"""
		self._svgs: list[SVGPlot] = []
		self._col_title = title


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
		png_convert: None | int = None,
		max_size: None | int = None
	) -> None | str:
		"""
		:param scale: if None, native scaling is used
		"""

		if hide_if_empty and not self._svgs:
			return None

		if full_html:
			# TODO: put this in a file, update package data and access it via pkg_resources
			html = """
			<html>
			<head>
			<style>
				.hovernow {margin: 10px; transition: box-shadow 0.3s ease-in-out;}
				.hovernow:hover {box-shadow: 0 5px 15px rgba(0, 0, 0, 0.8);}
				.selected {box-shadow: 0 5px 15px rgba(255, 1, 1, 0.8);}
			</style>
			</head>

			<body onload="showTime();">

			<center>
			<div id=tagfilter style='display: block'>
				<input id="tags" type='text' placeholder="tags" style="width: 100px"/>
				<button id="btn_tags" onclick="showOnly()">Filter</button>
				<button onclick="showAll()">Reset</button>
				<button onclick="toggleDivs()">Toggle</button>
				<button id=tightbtn onclick="toggle('h3tags')">Tags</button>
				<button id=tightbtn onclick="toggle('h3title')">Titles</button>
				<input id="padding" type='text' placeholder="padding" style="width: 60px"/>
				<button id="btn_padding" onclick="setPadding()">Set</button>
				<button id="btn_copy" onclick="doCopy()">Copy</button>
				<div id="datetime" style="display: inline; color: grey; padding-left: 10px; font-style: italic;"></div>
			</div>
			</center>

			<script>

				function showTime() {
					document.getElementById("datetime").innerHTML = new Date().toISOString().replace("T", " ").substr(0, 16);
				}

				function doCopy() {
					arr = [];
					Array.from(
						document.getElementsByClassName("selected")
					).forEach(
						function(item) {
							item.classList.remove('selected');
							arr.push(item.outerHTML);
						}
					);

					jstr = JSON.stringify(arr);
					function listener(e) {
						e.clipboardData.setData("text/html", jstr);
						e.clipboardData.setData("text/plain", jstr);
						e.preventDefault();
					}
					document.addEventListener("copy", listener);
					document.execCommand("copy");
					document.removeEventListener("copy", listener);
				}

				function toggleDivs() {
					console.log("Toggling divs");
					var plots = document.getElementsByClassName("PLOT");
					for (var i = 0; i < plots.length; i++) {
						if (plots[i].style.display === "none")
							plots[i].style.display = "block";
						else
							plots[i].style.display = "none";
					}
				}

				function showOnly() {
					console.log("Filtering divs");
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

				function showAll() {
					var plots = document.getElementsByClassName("PLOT");
					var centers = document.getElementsByTagName("center");
					for (var i=0; i < plots.length; i ++) {
						plots[i].classList.remove('selected');
						if (plots[i].style.display === "none")
							plots[i].style.display = "block";
					}
					for (var i=0; i < centers.length; i ++) {
						if (centers[i].style.display === "none")
							centers[i].style.display = "";
					}
				}

				function setPadding() {
					console.log("Updating padding");
					var plots = document.getElementsByClassName("PLOT");
					for (var i=0; i < plots.length; i ++)
						plots[i].style.paddingBottom = document.getElementById("padding").value + "px";
				}

				function toggle(what) {
					var h3s = document.getElementsByClassName(what);
					for (var i=0; i < h3s.length; i ++)
						if (h3s[i].style.display === "none")
							h3s[i].style.display = "block";
						else
							h3s[i].style.display = "none";
				}

				function hide_parent(evt) {
					var target = evt.target || evt.srcElement;
					if (evt.shiftKey)
						target.parentNode.className = target.parentNode.className + " selected"
					else
						target.parentNode.style.display = "none";
				}

				function handlePaste(e) {
					e.stopPropagation();
					e.preventDefault();

					clipboardData = e.clipboardData || window.clipboardData;
					arr = JSON.parse(clipboardData.getData('Text'));

					for (var i=0; i < arr.length; i++) {
						var template = document.createElement('template');
						template.innerHTML = arr[i];
						var clone = document.importNode(template.content, true);
						document.getElementById('mainwrap').appendChild(clone);
					}
				}

				document.getElementById("tags").addEventListener(
					"keyup", function(event) {
						if (event.keyCode === 13) {
							event.preventDefault();
							showOnly();
						}
					}
				);

				document.getElementById("padding").addEventListener(
					"keyup", function(event) {
						if (event.keyCode === 13) {
							event.preventDefault();
							setPadding();
						}
					}
				);

				document.body.addEventListener(
					"keyup", function(event) {
						if (event.keyCode === 27)
							showAll();
					}
				);

				document.body.addEventListener('paste', handlePaste);

			</script>
			"""
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
					pool.apply_async(svg_to_png_html, (svg._record['svg'], png_convert, scale, max_size))
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
				png_convert = png_convert,
				max_size = max_size
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
