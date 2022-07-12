#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot-browse/ampel/plot/SVGLoader.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                13.06.2019
# Last Modified Date:  14.05.2022
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

from bson import ObjectId # type: ignore[import]
from typing import TYPE_CHECKING
from collections.abc import Sequence
from collections import defaultdict
from string import digits

from ampel.types import StockId, UnitId, Tag, OneOrMany
from ampel.core.AmpelDB import AmpelDB
from ampel.content.SVGRecord import SVGRecord
from ampel.log.AmpelLogger import AmpelLogger
from ampel.plot.SVGQuery import SVGQuery
from ampel.plot.T2SVGQuery import T2SVGQuery
from ampel.plot.SVGCollection import SVGCollection
from ampel.util.recursion import walk_and_process_dict
from ampel.model.operator.AnyOf import AnyOf
from ampel.model.operator.AllOf import AllOf
from ampel.model.operator.OneOf import OneOf

if TYPE_CHECKING:
	from ampel.plot.SVGBrowser import SVGBrowser

remove_digits = str.maketrans('', '', digits)


class SVGLoader:

	@staticmethod
	def load_t02(
		db: AmpelDB,
		stock: None | StockId | Sequence[StockId] = None,
		tag: None | OneOrMany[Tag] = None,
		t2_unit: None | UnitId = None,
		t2_config: None | int = None
	) -> "SVGLoader":

		t0_query = SVGQuery(
			col = "t0",
			stock = stock,
			plot_tag = tag
		)

		t2_query = T2SVGQuery(
			stock = stock,
			plot_tag = tag,
			unit = t2_unit,
			config = t2_config
		)

		sl = SVGLoader(db=db, queries=[t0_query, t2_query])
		sl.run()

		return sl


	def __init__(self,
		db: AmpelDB,
		queries: None | list[SVGQuery] = None,
		logger: None | AmpelLogger = None,
		last_body: bool = False,
		enforce_base_path: bool = False,
		limit: int = 0,
		latest_doc: bool = False
	) -> None:
		self._db = db
		self.logger: AmpelLogger = logger or AmpelLogger.get_logger()
		self.limit = limit
		self.last_body = last_body
		self.latest_doc = latest_doc
		self.enforce_base_path = enforce_base_path
		self._queries: list[SVGQuery] = []
		self._plots: dict[StockId, SVGCollection] = defaultdict(SVGCollection)
		self._debug = self.logger and self.logger.verbose > 1
		self._plot_col = self._db.get_collection('plots')
		
		if queries:
			for q in queries:
				self.add_query(q)


	def add_query(self, query: SVGQuery) -> "SVGLoader":
		self._queries.append(query)
		return self


	def spawn_browser(self) -> "SVGBrowser":
		from ampel.plot.SVGBrowser import SVGBrowser
		return SVGBrowser(self)


	def run(self) -> "SVGLoader":

		i = 0

		for q in self._queries:

			if self._debug:
				dbname = self._db.get_collection(q.col).database._Database__name
				self.logger.debug(
					f"Running query (db '{dbname}' - collection '{q.col}'): {q._query}"
				)

			if self.latest_doc:
				res = self._db.get_collection(q.col).find(q._query).sort("_id", -1).limit(1)
				if self._debug:
					count = self._db.get_collection(q.col).count_documents(q._query)
					if count:
						self.logger.debug(f"{count} documents matched [loading only the latest]")
					else:
						self.logger.debug("No document matched")
			elif self.limit:
				res = self._db.get_collection(q.col).find(q._query).limit(self.limit)
				if self._debug:
					self.logger.debug(f"{res.count()} document(s) matched [{res.count(True)} with limit]")
			else:
				res = self._db.get_collection(q.col).find(q._query)

			for el in res:

				i += 1
				if self._debug:
					self.logger.debug(f"Parsing {el['_id']}")

				if q.col == "plots":
					self._plots[None].add_raw_db_dict(el)
					continue

				if not el.get('body'):
					if self._debug:
						self.logger.debug(" Skipping doc: empty body")
					continue

				stock = el.get('stock', 0)

				if isinstance(el['body'], list):
					if self.last_body:
						walk_and_process_dict(
							arg = el['body'][-1],
							callback = self._gather_plots_callback,
							match = ['plot'],
							q = q,
							stock = stock
						)
					else:
						for ell in el['body']:
							walk_and_process_dict(
								arg = ell,
								callback = self._gather_plots_callback,
								match = ['plot'],
								q = q,
								stock = stock
							)
				elif isinstance(el['body'], dict):
					walk_and_process_dict(
						arg = el['body'],
						callback = self._gather_plots_callback,
						match = ['plot'],
						q = q,
						stock = stock
					)
				else:
					if self._debug:
						self.logger.debug(f" Skipping doc: unrecognized body type ({type(el['body'])}")

			#	self._load_plots(q, stock, get_by_path(el['body'], rel_path) if nested else el['body'][rel_path])

			if self.limit and self.limit > i:
				break

		return self


	def _gather_plots_callback(self, path, k, d, **kwargs) -> None:

		if self.enforce_base_path and kwargs['q'].path:
			# quick n dirty (to be improved)
			# will yield troubles if path keys contain numbers
			# will yield troubles with double digit sequence ('body.data.0.21.tra')
			# but those can't be used for matching anyway
			sequenceless_path = "body." + path.translate(remove_digits).replace("..", "")
			if sequenceless_path not in kwargs['q'].path:
				if self._debug:
					self.logger.debug(
						f" Ignoring plot(s) with path body.{path}.plot "
						f" (Path {sequenceless_path[:-1]} is outside base path {kwargs['q'].path})"
					)
				return
				
		if self._debug:
			if path:
				self.logger.debug(f" Loading plot(s) with path body.{path}.plot")
			else:
				self.logger.debug(" Loading plot(s) with path body.plot")

		self._load_plots(kwargs['q'], kwargs['stock'], [d[k]] if isinstance(d[k], dict) else d[k])


	def _load_plots(self, query: SVGQuery, stock: StockId, plots: Sequence[SVGRecord]) -> None:

		if not plots:
			return

		for i, p in enumerate(plots):

			if self._debug:
				self.logger.debug(f"Loading plot with index {i}")

			if query.plot_tag:
				if 'with' in query.plot_tag:
					wqt = query.plot_tag['with']
					if (
						(isinstance(wqt, AllOf) and not all(x in p['tag'] for x in wqt.all_of)) or
						(isinstance(wqt, AnyOf) and not [x in p['tag'] for x in wqt.any_of]) or
						(isinstance(wqt, OneOf) and not wqt.any_of == [p['tag']]) or
						(isinstance(wqt, (int, str)) and wqt not in p['tag'])
					):
						if self.logger and self.logger.verbose > 1:
							self.logger.debug("Excluding plot (tag matching failed)")
						continue

			if isinstance(p['svg'], ObjectId):
				if self._debug:
					self.logger.debug(f"Side-loading {p['name']}")
				p['svg'] = next(self._plot_col.find({'_id': p['svg']}))['svg']

			self._plots[stock].add_raw_db_dict(p)
