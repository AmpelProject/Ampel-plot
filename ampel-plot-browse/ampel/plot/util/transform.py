#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-plot/ampel-plot-browse/ampel/plot/util/transform.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 17.05.2019
# Last Modified Date: 19.11.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

import pyvips, base64 # type: ignore[import]


def svg_to_png(svg: str, dpi: int = 96, scale: float = 1.0) -> bytes:
	image = pyvips.Image.svgload_buffer(bytes(svg, 'utf8'), dpi=dpi, scale=scale)
	return image.write_to_buffer('.png')

def svg_to_png_b64(svg: str, dpi: int = 96, scale: float = 1.0) -> str:
	return str(
		base64.b64encode(
			svg_to_png(svg, dpi, scale)
		),
		"ascii"
	)

def svg_to_png_html(svg: str, dpi: int = 96, scale: float = 1.0) -> str:
	return '<img src="data:image/png;base64,' + svg_to_png_b64(svg, dpi, scale) + '">'

def rescale(svg: str, scale: float = 1.0) -> bytes:
	image = pyvips.Image.svgload_buffer(bytes(svg, 'utf8'), scale=scale)
	return image.write_to_buffer('.svg')

def rescale_str(svg: str, scale: float = 1.0) -> str:
	return str(rescale(svg, scale), 'ascii')