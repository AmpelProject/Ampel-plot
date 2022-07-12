#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot-browse/ampel/plot/SVGQuery.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                15.06.2019
# Last Modified Date:  12.07.2022
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

from typing import Literal, Any
from ampel.types import OneOrMany, StockId, Tag, UnitId
from ampel.mongo.schema import apply_schema, apply_excl_schema
from ampel.model.operator.AnyOf import AnyOf
from ampel.model.operator.AllOf import AllOf
from ampel.model.operator.OneOf import OneOf


class SVGQuery:

	_query: dict[str, Any]
	col: Literal["t0", "t1", "t2", "t3", "plots"]
	path: str
	tags: None | OneOrMany[Tag]

	def __init__(self,
		col: Literal["t0", "t1", "t2", "t3", "plots"],
		path: str = 'body.data.plot',
		unit: None | UnitId = None,
		config: None | int = None,
		job_sig: None | int = None,
		stock: OneOrMany[StockId] = None,
		doc_tag: None | dict[
			Literal['with', 'without'],
			Tag | AllOf[Tag] | AnyOf[Tag] | OneOf[Tag]
		] = None,
		plot_tag: None | dict[
			Literal['with', 'without'],
			Tag | AllOf[Tag] | AnyOf[Tag] | OneOf[Tag]
		] = None,
		custom_match: None | dict = None
	):
		self._query = {path: {'$exists': True}} if path else {}
		self.path = path
		self.col = col
		self.plot_tag: None | dict[
			Literal['with', 'without'],
			Tag | AllOf[Tag] | AnyOf[Tag] | OneOf[Tag]
		] = None

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

		if job_sig:
			self._query['meta.jobid'] = job_sig

		if custom_match:
			self._query.update(custom_match)


	def get_query(self) -> dict[str, Any]:
		return self._query


	def set_stock(self, stock: OneOrMany[StockId]) -> None:

		if isinstance(stock, str) and "," in stock:
			self._query['stock'] = {'$in': [int(el.strip()) for el in stock.split(",")]}
		elif isinstance(stock, (list, tuple)):
			self._query['stock'] = {'$in': stock}
		else:
			self._query['stock'] = stock


	def set_doc_tag(self,
		tag: dict[
			Literal['with', 'without'],
			Tag | AllOf[Tag] | AnyOf[Tag] | OneOf[Tag]
		]
	) -> None:

		if 'with' in tag:
			apply_schema(self._query, 'tag', tag['with'])

		# Order matters, parse_dict(...) must be called *after* parse_excl_dict(...)
		if 'without' in tag:
			apply_excl_schema(self._query, 'tag', tag['without'])


	def set_plot_tag(self,
		tag: dict[
			Literal['with', 'without'],
			Tag | AllOf[Tag] | AnyOf[Tag] | OneOf[Tag]
		]
	) -> None:

		self.plot_tag = tag

		if 'with' in tag:
			apply_schema(self._query, ".".join([self.path, "tag"]), tag['with'])

		# Order matters, parse_dict(...) must be called *after* parse_excl_dict(...)
		if 'without' in tag:
			apply_excl_schema(self._query, ".".join([self.path, "tag"]), tag['without'])


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
