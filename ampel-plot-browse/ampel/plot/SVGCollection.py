#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot-browse/ampel/plot/SVGCollection.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                13.06.2019
# Last Modified Date:  13.04.2022
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

from multiprocessing import Pool
from ampel.plot.SVGPlot import SVGPlot
from ampel.content.SVGRecord import SVGRecord
from ampel.plot.util.compression import decompress_svg_dict
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
		png_convert: None | int = None
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
				.mainimg {height: min-content;}
				.modal {
					display: none;
					position: fixed;
					z-index: 1;
					left: 0;
					top: 0;
					width: 100%;
					height: 100%;
					overflow: auto;
					background-color: rgb(0,0,0);
					background-color: rgba(0,0,0,0.7);
				}
				.modal-content {
					margin: 0% auto;
					padding: 20px;
					cursor: pointer;
					transition: 0.3s;
					display: block;
					max-width: 90%;
					max-height: 90%;
				}
			</style>
			</head>

			<body onload="setup();">

			<div id="modal" class="modal">
				<img id="modalimg" class="modal-content"/>
			</div>

			<center>
			<div id=tagfilter style='display: block'>
				<button onclick="showAll()">↻</button>
				<input id="tags" type='text' placeholder="tags" style="width: 100px"/>
				<button onclick="toggleDivs()">Toggle</button>
				<button id="btn_h3tags" onclick="toggle('h3tags')">Tags</button>
				<button id="btn_h3title" onclick="toggle('h3title')">Titles</button>
				<input id="padding" type='text' placeholder="padding" style="width: 60px"/>
				<input id="maxwidth" type="range" min="1" max="800" value="400" style="vertical-align: middle">🔍
				<div id="datetime" style="display: inline; position: absolute; left: 0px; color: grey; padding-left: 10px;"></div>
			</div>
			</center>

			<script>

				function setup() {
					document.querySelector("#datetime").innerHTML = new Date().toISOString().replace("T", " ").substr(0, 16);
					val = document.querySelector("#maxwidth").value + "px";
					document.querySelectorAll(".mainimg").forEach(
						function(img) {
							img.style.cursor = 'pointer';
							img.style.maxInlineSize = val;
							img.onclick = imgClick;
						}
					);
				}

				function setMaxInlineSize() {
					val = document.querySelector("#maxwidth").value + "px";
					document.querySelectorAll(".mainimg").forEach(
						function(img) {
							img.style.maxInlineSize = val;
						}
					);
				}

				function handleCopy() {

					nodeList = document.querySelectorAll(".selected");
					if (nodeList.length == 0) {
						document.execCommand("copy");
						return;
					}

					arr = [];
					nodeList.forEach(
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
					tags = document.querySelector('#tags').value.split(" ");

					document.querySelectorAll(".PLOT").forEach(
						function(plot) {
							var found = false;
							cl = plot.classList;
							for (var j=0; j < tags.length; j++) {
								if (cl.contains(tags[j].toUpperCase())) {
									plot.style.display = "block";
									found = true;
								}
							}
							if (!found)
								plot.style.display = "none";
						}
					);
				}

				function showAll() {
					document.querySelector("#modal").style.display = "none";
					document.querySelectorAll(".PLOT").forEach(
						function(plot) {
							plot.classList.remove('selected');
							if (plot.style.display === "none")
								plot.style.display = "block";
						}
					);
					document.querySelectorAll("center").forEach(
						function(center) {
							if (center.style.display === "none")
								center.style.display = "";
						}
					);
				}

				function setPadding() {
					console.log("Updating padding");
					padding = document.querySelector("#padding").value + "px";
					document.querySelectorAll(".PLOT").forEach(
						function(plot) {
							plot.style.paddingBottom = padding;
						}
					);
				}

				function toggle(what) {
					var w = document.getElementsByClassName(what);
					btn = document.querySelector("#btn_"+what);
					btnval = btn.innerHTML
					sign = (w[0].style.display === "none") ? "-" : "+"
					btn.innerHTML = sign + ((/[a-zA-Z]/).test(btnval[0]) ? btnval : btnval.substr(1));
					for (var i=0; i < w.length; i ++)
						if (w[i].style.display === "none")
							w[i].style.display = "block";
						else
							w[i].style.display = "none";
				}

				function imgClick(evt) {
					var target = evt.target || evt.srcElement;
					if (evt.shiftKey)
						target.parentNode.className = target.parentNode.className + " selected"
					else if (evt.altKey) {
						var current = target;
						while (current.parentNode) {
							tagName = current.tagName.toLowerCase();
							if (tagName == 'svg' || tagName == 'img')
								break;
							current = current.parentNode;
						}
						current.parentNode.style.display = "none";
					}
					else {
						modalimg = document.querySelector("#modalimg");
						document.querySelector("#modal").style.display = "block";
						if (target.tagName.toLowerCase() == 'img')
							document.querySelector("#modalimg").src = target.src;
						else {
							var current = target;
							while (current.parentNode) {
								current = current.parentNode
								if (current.tagName.toLowerCase() == 'svg')
									break;
							}
							var template = document.createElement('template');
							template.innerHTML = current.outerHTML;
							var clone = document.importNode(template.content, true);
							clone.firstChild.style.maxInlineSize = "";
							clone.firstChild.style.height = "90%";
							clone.firstChild.style.width = "90%";
							clone.firstChild.setAttribute("class", "modal-content");
							document.querySelector("#modal").innerHTML = "";
							document.querySelector("#modal").appendChild(clone);
						}
					}
				}

				function handlePaste(e) {

					clipboardData = e.clipboardData || window.clipboardData;
					try {
						arr = JSON.parse(clipboardData.getData('Text'));
					}
					catch (error) {
						document.execCommand("paste");
						return;
					}

					e.preventDefault();
					e.stopPropagation();

					for (var i=0; i < arr.length; i++) {
						var template = document.createElement('template');
						template.innerHTML = arr[i];
						var clone = document.importNode(template.content, true);
						document.getElementById('mainwrap').appendChild(clone);
					}

					val = document.querySelector("#maxwidth").value + "px";
					document.querySelectorAll(".mainimg").forEach(
						function(img) {
							img.style.cursor = 'pointer';
							img.style.maxInlineSize = val;
							img.onclick = imgClick;
						}
					);
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
						else {
							document.querySelectorAll(".mainimg").forEach(
								function(img) {
									img.style.cursor = 'pointer';
								}
							);
						}
					}
				);

				document.body.addEventListener(
					"keydown", function(event) {
						if (event.altKey) {
							document.querySelectorAll(".mainimg").forEach(
								function(img) {
									img.style.cursor = 'not-allowed';
								}
							);
						}
					}
				);

				document.body.addEventListener('paste', handlePaste);
				document.body.addEventListener('copy', handleCopy);
				document.querySelector("#maxwidth").addEventListener(
					'input', setMaxInlineSize, false
				);

				document.querySelector("#modal").onclick = function() {
					modal.style.display = "none";
				}

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
