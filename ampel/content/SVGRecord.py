#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-plots/ampel/content/SVGRecord.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 13.02.2021
# Last Modified Date: 22.02.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from typing import Union, TypedDict, Sequence
from ampel.types import Tag


class SVGRecord(TypedDict, total=False):
	"""
	Dict crafted by :class:`~ampel.plot.utils.mplfig_to_svg_dict`
	"""
	name: str
	tag: Union[Tag, Sequence[Tag]]
	title: str
	svg: Union[bytes, str] # bytes means compressed svg
	svg_str: str
