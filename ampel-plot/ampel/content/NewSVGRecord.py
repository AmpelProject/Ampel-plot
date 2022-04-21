#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot/ampel/content/NewSVGRecord.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                20.04.2022
# Last Modified Date:  20.04.2022
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

from typing_extensions import NotRequired
from ampel.content.SVGRecord import SVGRecord


class NewSVGRecord(SVGRecord):
	"""
	Dict crafted by :class:`~ampel.plot.utils.fig_to_plot_record`
	"""
	detached: NotRequired[bool]
