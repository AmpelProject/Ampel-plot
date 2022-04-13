#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot-browse/ampel/model/PlotBrowseOptions.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                19.11.2021
# Last Modified Date:  12.04.2022
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

from ampel.base.AmpelFlexModel import AmpelFlexModel

class PlotBrowseOptions(AmpelFlexModel):

	debug: bool = False
	html: bool = True
	stack: int = 20
	scale: float = 1.0
	png: None | int = None
