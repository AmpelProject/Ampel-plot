#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot/ampel/content/SVGRecord.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                13.02.2021
# Last Modified Date:  22.02.2021
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

from typing import TypedDict
from collections.abc import Sequence
from ampel.types import Tag


class SVGRecord(TypedDict, total=False):
	"""
	Dict crafted by :class:`~ampel.plot.utils.mplfig_to_svg_dict`
	"""
	name: str
	tag: Tag | Sequence[Tag]
	title: str
	svg: bytes | str # bytes means compressed svg
	svg_str: str
