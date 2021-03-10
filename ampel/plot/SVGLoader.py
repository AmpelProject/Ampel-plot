#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-plots/ampel/plot/SVGLoader.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 13.06.2019
# Last Modified Date: 10.03.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

from typing import Optional, Sequence, Union, Dict, TYPE_CHECKING
from collections import defaultdict

from ampel.type import StockId, UnitId, Tag, List
from ampel.db.AmpelDB import AmpelDB
from ampel.content.SVGRecord import SVGRecord
from ampel.plot.SVGQuery import SVGQuery
from ampel.plot.T2SVGQuery import T2SVGQuery
from ampel.plot.SVGCollection import SVGCollection

if TYPE_CHECKING:
	from ampel.plot.SVGBrowser import SVGBrowser


class SVGLoader:

	@staticmethod
	def load_t02(
		db: AmpelDB,
		stocks: Optional[Union[StockId, Sequence[StockId]]] = None,
		tags: Optional[Union[Tag, Sequence[Tag]]] = None,
		t2_unit: Optional[UnitId] = None,
		t2_config: Optional[int] = None
	) -> "SVGLoader":

		t0_query = SVGQuery(
			col = "t0",
			stocks = stocks,
			tags = tags
		)

		t2_query = T2SVGQuery(
			stocks = stocks,
			tags = tags,
			unit = t2_unit,
			config = t2_config
		)

		sl = SVGLoader(db=db, queries=[t0_query, t2_query])
		sl.run()

		return sl


	def __init__(self, db: AmpelDB, queries: Optional[List[SVGQuery]] = None) -> None:
		self._db = db
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

		for q in self._queries:
			if q.path == "plots": # root
				for el in self._db.get_collection(q.col).find(q._query):
					self._load_plots(q, el['stock'], el['plots'])
			elif q.path == "body.result.plots": # t2
				for el in self._db.get_collection(q.col).find(q._query):
					if 'result' in el['body'][-1]:
						if isinstance(el['body'][-1]['result'], dict):
							self._load_plots(
								q, el['stock'], el['body'][-1]['result']['plots']
							)
						elif isinstance(el['body'][-1]['result'], list):
							for ell in el['body'][-1]['result']:
								if isinstance(ell, dict) and "plots" in ell:
									self._load_plots(q, el['stock'], ell['plots'])

		return self


	def _load_plots(self,
		query: SVGQuery, stock: StockId, plots: Sequence[SVGRecord]
	) -> None:

		for p in plots:

			if query.tags:
				if isinstance(query.tags, (list, tuple)):
					if isinstance(p['tag'], list) and not all(x in p['tag'] for x in query.tags):
						continue
					elif isinstance(p['tag'], (int, str)) and p['tag'] not in query.tags:
						continue
				else:
					if isinstance(p['tag'], list) and query.tags not in p['tag']:
						continue
					elif isinstance(p['tag'], (int, str)) and query.tags != p['tag']:
						continue

			self._plots[stock].add_raw_db_dict(p)
