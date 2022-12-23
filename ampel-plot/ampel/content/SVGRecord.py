#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot/ampel/content/SVGRecord.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                13.02.2021
# Last Modified Date:  07.12.2022
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

from typing import TypedDict, Any
from typing_extensions import NotRequired
from collections.abc import Sequence
from ampel.types import Tag


class SVGRecord(TypedDict, total=False):

	name: str
	title: str
	tag: Tag | Sequence[Tag]
	svg: bytes | str # bytes means compressed svg
	svg_str: NotRequired[str]
	oid: NotRequired[str]
	run: NotRequired[int]
	# data used to create figure (compressed numpy array bytes for example)
	data: NotRequired[Any]
