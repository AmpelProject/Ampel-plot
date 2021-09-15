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
from ampel.mongo.schema import apply_schema, apply_excl_schema
from ampel.model.operator.AnyOf import AnyOf
from ampel.model.operator.AllOf import AllOf
from ampel.model.operator.OneOf import OneOf


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
		doc_tag: Optional[
			Dict[
				Literal['with', 'without'],
				Union[Tag, Dict, AllOf[Tag], AnyOf[Tag], OneOf[Tag]]
			]
		] = None,
		plot_tag: Optional[
			Dict[
				Literal['with', 'without'],
				Union[Tag, Dict, AllOf[Tag], AnyOf[Tag], OneOf[Tag]]
			]
		] = None,
		custom_match: Optional[dict] = None
	):
		self._query = {path: {'$exists': True}}
		self.path = path
		self.col = col

		if stock:
			self.set_stock(stock)

		if plot_tag:
			self.set_plot_tag(plot_tag)

		if doc_tag:
			self.set_doc_tag(doc_tag)

		if unit:
			self._query['unit'] = unit

		if config:
			self._query['config'] = unit

		if custom_match:
			self._query.update(custom_match)


	def get_query(self) -> Dict[str, Any]:
		return self._query


	def set_stock(self, stock: Union[StockId, Sequence[StockId]]) -> None:

		if isinstance(stock, (list, tuple)):
			self._query['stock'] = {'$in': stock}
		else:
			self._query['stock'] = stock


	def set_doc_tag(self,
		tag: Dict[
			Literal['with', 'without'],
			Union[Tag, Dict, AllOf[Tag], AnyOf[Tag], OneOf[Tag]]
		]
	) -> None:

		if 'with' in tag:
			apply_schema(self._query, 'tag', tag['with'])

		# Order matters, parse_dict(...) must be called *after* parse_excl_dict(...)
		if 'without' in tag:
			apply_excl_schema(self._query, 'tag', tag['without'])


	def set_plot_tag(self,
		tag: Dict[
			Literal['with', 'without'],
			Union[Tag, Dict, AllOf[Tag], AnyOf[Tag], OneOf[Tag]]
		]
	) -> None:

		if 'with' in tag:
			apply_schema(self._query, self.path + ".tag", tag['with'])

		# Order matters, parse_dict(...) must be called *after* parse_excl_dict(...)
		if 'without' in tag:
			apply_excl_schema(self._query, self.path + ".tag", tag['without'])


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
