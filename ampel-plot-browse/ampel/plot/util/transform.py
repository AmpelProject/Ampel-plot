#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot-browse/ampel/plot/util/transform.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                17.05.2019
# Last Modified Date:  19.08.2022
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

from typing import Literal
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
	return '<img class=mainimg src="data:image/png;base64,%s">' % svg_to_png_b64(svg, dpi, scale)

def svg_to_eps(svg: str, outpath: str, fname: str, feedback: bool = True) -> None:
	_svg_inkscape(svg, outpath, fname, 'eps', feedback)

def svg_to_pdf(svg: str, outpath: str, fname: str, feedback: bool = True) -> None:
	_svg_inkscape(svg, outpath, fname, 'pdf', feedback)

def _svg_inkscape(
	svg: str,
	outpath: str,
	fname: str,
	ext: Literal['pdf', 'eps'],
	feedback: bool = True
) -> None:
	import tempfile, os, subprocess
	fp = tempfile.NamedTemporaryFile(delete=False)
	tmp_name = fp.name
	fp.write(bytes(svg, 'utf8'))
	fp.close()
	outname = os.path.join(outpath, fname) + '.' + ext
	x = subprocess.Popen(
		['inkscape', tmp_name, f'--export-filename={outname}']
	)
	out, err = x.communicate()
	if err:
		raise ValueError(err)
	else:
		if feedback:
			print(outname)
	os.unlink(tmp_name)


def rescale(svg: str, scale: float = 1.0) -> bytes:
	image = pyvips.Image.svgload_buffer(bytes(svg, 'utf8'), scale=scale)
	return image.write_to_buffer('.svg')

def rescale_str(svg: str, scale: float = 1.0) -> str:
	return str(rescale(svg, scale), 'ascii')
