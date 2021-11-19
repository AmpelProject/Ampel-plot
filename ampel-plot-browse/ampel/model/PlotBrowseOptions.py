#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-plot/ampel-plot-browse/ampel/model/PlotBrowseOptions.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 19.11.2021
# Last Modified Date: 19.11.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from typing import Optional
from ampel.base.AmpelFlexModel import AmpelFlexModel

class PlotBrowseOptions(AmpelFlexModel):

	debug: bool = False
	html: bool = True
	tight: bool = False
	stack: int = 20
	scale: float = 1.0
	png: Optional[int] = None
