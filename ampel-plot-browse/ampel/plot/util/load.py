#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-plot/ampel-plot-browse/ampel/plot/util/load.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 17.05.2019
# Last Modified Date: 19.11.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from ampel.content.SVGRecord import SVGRecord
from ampel.util.compression import decompress_str


def decompress_svg_dict(svg_dict: SVGRecord) -> SVGRecord:
	"""
	Modifies input dict by potentionaly decompressing compressed 'svg' value
	"""

	if not isinstance(svg_dict, dict):
		raise ValueError("Parameter svg_dict must be an instance of dict")

	if isinstance(svg_dict['svg'], bytes):
		svg_dict['svg'] = decompress_str(svg_dict['svg'])

	return svg_dict
