#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot/ampel/content/SVGRecord.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                13.02.2021
# Last Modified Date:  20.04.2022
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

from typing import TypedDict
from typing_extensions import NotRequired
from collections.abc import Sequence
from ampel.types import Tag


class SVGRecord(TypedDict, total=False):

	name: str
	title: str
	tag: Tag | Sequence[Tag]
	svg: bytes | str # bytes means compressed svg
	svg_str: NotRequired[str]
