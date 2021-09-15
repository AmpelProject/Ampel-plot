#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-plots/main/ampel/plot/SVGLoader.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 13.06.2019
# Last Modified Date: 15.09.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from typing import Optional, Sequence, Union, Dict, TYPE_CHECKING
from collections import defaultdict

from ampel.types import StockId, UnitId, Tag, List, Any
from ampel.core.AmpelDB import AmpelDB
from ampel.content.SVGRecord import SVGRecord
from ampel.log.AmpelLogger import AmpelLogger
from ampel.plot.SVGQuery import SVGQuery
from ampel.plot.T2SVGQuery import T2SVGQuery
from ampel.plot.SVGCollection import SVGCollection

if TYPE_CHECKING:
	from ampel.plot.SVGBrowser import SVGBrowser


class SVGLoader:

	@staticmethod
	def load_t02(
		db: AmpelDB,
		stock: Optional[Union[StockId, Sequence[StockId]]] = None,
		tag: Optional[Union[Tag, Sequence[Tag]]] = None,
		t2_unit: Optional[UnitId] = None,
		t2_config: Optional[int] = None
	) -> "SVGLoader":

		t0_query = SVGQuery(
			col = "t0",
			stock = stock,
			tag = tag
		)

		t2_query = T2SVGQuery(
			stock = stock,
			tag = tag,
			unit = t2_unit,
			config = t2_config
		)

		sl = SVGLoader(db=db, queries=[t0_query, t2_query])
		sl.run()

		return sl


	def __init__(self,
		db: AmpelDB,
		queries: Optional[List[SVGQuery]] = None,
		logger: Optional[AmpelLogger] = None,
		limit: int = 0
	) -> None:
		self._db = db
		self.logger = logger
		self.limit = limit
		self._queries: List[SVGQuery] = []
		self._plots: Dict[StockId, SVGCollection] = defaultdict(SVGCollection)
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

			if self.logger and self.logger.verbose > 1:
				self.logger.debug(f"Running {q.col} query: {q._query}")

			if self.limit:
				res = self._db.get_collection(q.col).find(q._query).limit(self.limit)
			else:
				res = self._db.get_collection(q.col).find(q._query)

			if self.logger and self.logger.verbose > 1:
				self.logger.debug(f"{res.count()} documents matched")

			if q.path == "plot": # root
				for el in res:
					i += 1
					if self.logger and self.logger.verbose > 1:
						self.logger.debug(f"Parsing {el['_id']}")
					self._load_plots(q, el['stock'], el['plot'])
			elif q.path == "body.data.plot": # convention
				for el in res:
					i += 1
					if self.logger and self.logger.verbose > 1:
						self.logger.debug(f"Parsing {el['_id']}")
					if 'body' in el: # t1 docs do not necessarily have body
						if isinstance(el['body'], list):
							for ell in el['body']:
								self._load_body_el(q, el['stock'], ell)
						if isinstance(el['body'], dict):
							self._load_body_el(q, el['stock'], el['body'])

			if self.limit and self.limit > i:
				break

		return self


	def _load_body_el(self, q: SVGQuery, stock: StockId, arg: Any, k: str = 'data') -> None:

		if k not in arg:
			return

		if isinstance(stock, list):
			stock = tuple(stock)

		if isinstance(arg[k], dict):
			if 'plot' not in arg[k]:
				return
			self._load_plots(q, stock, arg[k]['plot'])

		elif isinstance(arg[k], list):
			for el in arg[k]:
				if isinstance(el, dict) and "plot" in el:
					self._load_plots(q, stock, el['plot'])


	def _load_plots(self,
		query: SVGQuery, stock: StockId, plots: Sequence[SVGRecord]
	) -> None:

		if self.logger and self.logger.verbose > 1:
			self.logger.debug("Loading plots")

		for p in plots:

			#if query.tag:
			#	if isinstance(query.tag, (list, tuple)):
			#		if isinstance(p['tag'], list) and not all(x in p['tag'] for x in query.tag):
			#			continue
			#		elif isinstance(p['tag'], (int, str)) and p['tag'] not in query.tag:
			#			continue
			##	else:
			#		if isinstance(p['tag'], list) and query.tag not in p['tag']:
			#			continue
			#		elif isinstance(p['tag'], (int, str)) and query.tag != p['tag']:
			#			continue

			self._plots[stock].add_raw_db_dict(p)
