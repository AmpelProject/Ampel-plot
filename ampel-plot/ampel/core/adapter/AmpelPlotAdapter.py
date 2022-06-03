#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot/ampel/core/adapter/AmpelPlotAdapter.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                20.04.2022
# Last Modified Date:  17.05.2022
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

from bson import ObjectId # type: ignore[import]
from ampel.util.recursion import walk_and_process_dict
from ampel.abstract.AbsUnitResultAdapter import AbsUnitResultAdapter
from ampel.struct.UnitResult import UnitResult
from ampel.view.T3Store import T3Store


class AmpelPlotAdapter(AbsUnitResultAdapter):
	"""
	Provides logic for handling plots embedded in UnitResult.
	These will be saved into dedicated collection
	"""

	def handle(self, ur: UnitResult) -> UnitResult:

		if ur.body is None or not isinstance(ur.body, (dict, list)):
			return ur

		walk_and_process_dict(
			arg = ur.body,
			callback = _insert_plots,
			match = ['plot'],
			col = self.context.db.get_collection("plots")
		)

		return ur


def _insert_plots(path, k, d, **kwargs) -> None:
	""" Used by walk_and_process_dict(...) """

	if isinstance(d[k], dict):
		if d[k].get('detached'):
			d[k]['svg'] = kwargs['col'].insert_one(d[k]).inserted_id
			del d[k]['detached']

	elif isinstance(d[k], list) and d[k]:
		insert = []
		for i in range(len(d[k])):
			d2 = d[k][i]
			if d2.get('detached'):
				del d2['detached']
				d3 = d2.copy()
				d3['_id'] = ObjectId()
				d2['svg'] = d3['_id']
				insert.append(d3)

		kwargs['col'].insert_many(insert)
