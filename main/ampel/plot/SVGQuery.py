#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-plots/main/ampel/plot/SVGQuery.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 15.06.2019
# Last Modified Date: 15.09.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from typing import Literal, Optional, Sequence, Dict, Any, Union
from ampel.types import StockId, Tag, UnitId

class SVGQuery:

	_query: Dict[str, Any]
	col: Literal["t0", "t1", "t2", "t3"]
	path: str
	tags: Optional[Union[Tag, Sequence[Tag]]]

	def __init__(self,
		col: Literal["t0", "t1", "t2", "t3"],
		path: str = 'body.data.plot',
		unit: Optional[UnitId] = None,
		config: Optional[int] = None,
		stock: Union[None, StockId, Sequence[StockId]] = None,
		tag: Union[None, Tag, Sequence[Tag]] = None,
	):
		self._query = {path: {'$exists': True}}
		self.tag: Union[None, Tag, Sequence[Tag]] = None
		self.path = path
		self.col = col

		if stock:
			self.set_stock(stock)

		if tag:
			self.set_tag(tag)

		if unit:
			self._query['unit'] = unit

		if config:
			self._query['config'] = unit


	def get_query(self) -> Dict[str, Any]:
		return self._query


	def set_stock(self, stock: Union[StockId, Sequence[StockId]]) -> None:

		if isinstance(stock, (list, tuple)):
			self._query['stock'] = {'$in': stock}
		else:
			self._query['stock'] = stock


	def set_tag(self, tag: Union[Tag, Sequence[Tag]]) -> None:
		self.tag = tag
		self._query[self.path + ".tag"] = {'$all': tag} if isinstance(tag, (list, tuple)) else tag


	def set_query_parameter(self, name: str, value: Any, overwrite: bool = False) -> None:
		"""
		For example:
		set_query_parameter(
			"$or", [
				{'unit': 'myFirstT2', 'config': 'default'},
				{'unit': 'myT2'}
			]
		)
		"""
		if name in self._query and not overwrite:
			raise ValueError(
				"Parameter %s already defined (use overwrite=True if you know what you're doing)" % name
			)

		self._query[name] = value
