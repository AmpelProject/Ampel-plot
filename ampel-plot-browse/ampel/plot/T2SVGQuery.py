#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot-browse/ampel/plot/T2SVGQuery.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                15.06.2019
# Last Modified Date:  19.11.2021
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

from collections.abc import Sequence
from ampel.types import UnitId, StockId, Tag
from ampel.plot.SVGQuery import SVGQuery


class T2SVGQuery(SVGQuery):

	def __init__(self,
		stocks: None | StockId | Sequence[StockId] = None,
		tags: None | Tag | Sequence[Tag] = None,
		unit: None | UnitId = None,
		config: None | int = None,
		query_path: str = 'body.data.plots' # convention
	):

		super().__init__(path = query_path, col = "t2", stocks = stocks, tags = tags)

		if unit:
			self.set_t2_unit(unit)

		if config:
			self.set_t2_config(config)

		self._query[self.path] = {'$exists': True}


	def set_t2_unit(self, unit: UnitId) -> None:
		self._query['unit'] = unit


	def set_t2_config(self, config: int) -> None:
		self._query['config'] = config
