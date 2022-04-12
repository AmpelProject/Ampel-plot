#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot-cli/ampel/cli/PlotCommand.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                15.03.2021
# Last Modified Date:  19.11.2021
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

from typing import Any
from collections.abc import Sequence
from argparse import ArgumentParser
from ampel.base.AuxUnitRegister import AuxUnitRegister
from ampel.cli.AmpelArgumentParser import AmpelArgumentParser
from ampel.cli.ArgParserBuilder import ArgParserBuilder
from ampel.cli.AbsCoreCommand import AbsCoreCommand
from ampel.cli.MaybeIntAction import MaybeIntAction
from ampel.cli.LoadJSONAction import LoadJSONAction
from ampel.cli.utils import maybe_load_idmapper
from ampel.log.AmpelLogger import AmpelLogger
from ampel.plot.SVGCollection import SVGCollection
from ampel.plot.SVGLoader import SVGLoader
from ampel.plot.SVGQuery import SVGQuery
from ampel.model.PlotBrowseOptions import PlotBrowseOptions
from ampel.plot.util.clipboard import read_from_clipboard
from ampel.plot.util.show import show_collection, show_svg_plot


h = {
	"show": "Display ampel plots retrieved via DB query(ies)",
	"save": "Not implemented yet (for now, please use 'show' and save the result(s) manually)",
	"read": "Monitors the clipboard for ampel plots which are then automatically displayed in browser",
	"config": "path to an ampel config file (yaml/json)",
	"secrets": "path to a YAML secrets store in sops format",
	"stock": "stock id(s). Comma sperated values can be used",
	"base-path": "default: body.data.plot",
	"unit": "docs will have to match the provided ampel unit name",
	"limit": "limit the number of *documents* (not plots) returned by the underlying DB query",
	# TODO: find better name
	"enforce-base-path": "within a given doc, load only plots with base-path",
	"last-body": "If body is a sequence (t2 docs), parse only the last body element",
	"latest-doc": "using the provided matching criteria, show plot(s) only from latest doc",
	"with-plot-tag": "match plots with tag",
	"without-plot-tag": "exclude plots with tag",
	"with-doc-tag": "match plots embedded in doc with tag",
	"without-doc-tag": "exclude plots embedded in doc with tag",
	"png": "convert to png (from svg). Default: 96 DPI",
	"scale": "scale png size. Default: 1.0",
	"max-size": "max-inline-size value of each HTML div",
	"html": "html output format (includes plot titles)",
	"stack": "stack <n> images into one html structure (activates html option). Default: 100",
	"out": "path to file (printed to stdout otherwise)",
	"db": "Database prefix. Multiple prefixes are supported (one query per db will be executed).\nIf set, '-mongo.prefix' value will be ignored",
	"one-db": "Whether the target ampel DB was created with flag one-db",
	"verbose": "increases verbosity",
	"debug": "debug"
}
pressed = False

class PlotCommand(AbsCoreCommand):

	def __init__(self):
		self.parsers = {}

	# Mandatory implementation
	def get_parser(self, sub_op: None | str = None) -> ArgumentParser | AmpelArgumentParser:

		if sub_op in self.parsers:
			return self.parsers[sub_op]

		sub_ops = ["show", "save", "read"]
		if sub_op is None or sub_op not in sub_ops:
			return AmpelArgumentParser.build_choice_help(
				'plot', sub_ops, h, description = 'Show or export ampel plots.'
			)

		builder = ArgParserBuilder("plot")
		builder.add_parsers(sub_ops, h)

		builder.notation_add_note_references()
		builder.notation_add_example_references()

		# Required
		builder.add_arg('show|save.required', 'config', type=str)
		builder.add_arg('save.required', 'out', type=str)

		# Optional
		builder.add_arg('show|save.optional', 'limit', type=int)
		builder.add_arg('show|save.optional', 'secrets')
		builder.add_arg('optional', 'debug', action="store_true")
		builder.add_arg('show|save.optional', 'id-mapper', type=str)
		builder.add_arg('show|save.optional', 'base-path', type=str)
		builder.add_arg('show|save.optional', 'unit', type=str)
		builder.add_arg('show|save.optional', 'enforce-base-path', action="store_true")
		builder.add_arg('show|save.optional', 'last-body', action="store_true")
		builder.add_arg('show|save.optional', 'latest-doc', action="store_true")
		builder.add_arg('optional', 'scale', nargs='?', type=float, default=1.0)
		builder.add_arg('optional', 'max-size', nargs='?', type=int)
		builder.add_arg('show|save.optional', "db", type=str, nargs="+")
		builder.add_arg('show|save.optional', "one-db", action="store_true")

		# Optional mutually exclusive args
		builder.add_x_args('optional',
			{'name': 'png', 'nargs': '?', 'type': int, 'const': 96},
			{'name': 'html', 'action': 'store_true'},
		)
		builder.add_arg('optional', 'stack', action='store', metavar='#', const=100, nargs='?', type=int, default=0)

		builder.add_group('show|save.match', 'Plot selection arguments')

		for el in (0, 1, 2, 3):
			builder.add_arg('show|save.match', f'no-t{el}', action='store_true', help=f"Ignore t{el} plots")

		for el in (0, 1, 2, 3):
			builder.add_arg('show|save.match', f't{el}', action='store_true', help=f"Match only t{el} plots")

		builder.add_arg('show|save.match', "stock", action=MaybeIntAction, nargs="+")
		builder.create_logic_args('show|save.match', "channel", "Channel")
		builder.create_logic_args('show|save.match', "with-doc-tag", "Doc tag", json=False)
		builder.create_logic_args('show|save.match', "without-doc-tag", "Doc tag", json=False)
		builder.create_logic_args('show|save.match', "with-plot-tag", "Plot tag", json=False)
		builder.create_logic_args('show|save.match', "without-plot-tag", "Plot tag", json=False)
		builder.add_arg('show|save.match', "custom-match", metavar="#", action=LoadJSONAction)

		builder.add_example('show', "-stack -300 -t2")
		builder.add_example('show', "-html -t3 -base-path body.plot -latest-doc -db HelloAmpel -one-db")
		builder.add_example('show', "-html -t2 -stock 123456 -db DB1 DB2")
		builder.add_example('show', "-stack -t2 -png 300 -limit 10")
		builder.add_example('show', "-stack -limit 10 -t2 -with-plot-tag SNCOSMO -with-doc-tag NED_NEAREST_IS_SPEC -custom-match '{\"body.data.ned.sep\": {\"$lte\": 10}}'")
		builder.add_example('show', "-stack -t2 -with-doc-tag NED_NEAREST_IS_SPEC -unit T2PS1ThumbNedSNCosmo -mongo.prefix Dipole2 -resource.mongo localhost:27050 -debug")
		builder.add_example('read', "-html")
		
		self.parsers.update(
			builder.get()
		)

		return self.parsers[sub_op]


	# Mandatory implementation
	def run(self, args: dict[str, Any], unknown_args: Sequence[str], sub_op: None | str = None) -> None:

		if sub_op == "read":
			from ampel.plot.util.keyboard import InlinePynput
			ipo = InlinePynput()
			read_from_clipboard(
				PlotBrowseOptions(**args),
				keyboard_callback = ipo.is_ctrl_pressed
			)

		stack = args.get("stack")
		limit = args.get("limit") or 0
		db_prefixes = args.get("db")
		dbs = []

		config = self.load_config(args['config'], unknown_args, freeze=False)
		vault = self.get_vault(args)

		if db_prefixes:
			for el in db_prefixes:
				config._config['mongo']['prefix'] = el
				dbs.append(
					self.get_db(
						config, vault, require_existing_db=True,
						one_db=args.get('one_db', False)
					)
				)
		else:
			dbs = [
				self.get_db(
					config, vault, require_existing_db=True,
					one_db=args.get('one_db', False)
				)
			]
			
		if (x := args.get('base_path')) and not x.startswith("body."):
			raise ValueError("Option 'base-path' must start with 'body.'")

		if 'id_mapper' in args:
			AuxUnitRegister.initialize(config)
			maybe_load_idmapper(args)

		logger = AmpelLogger.get_logger()
		ptags: dict = {}
		dtags: dict = {}

		for el in ("with_doc_tag", "with_doc_tags_and", "with_doc_tags_or"):
			if args.get(el):
				dtags['with'] = args.get(el)
				break

		for el in ("without_doc_tag", "without_doc_tags_and", "without_doc_tags_or"):
			if args.get(el):
				dtags['without'] = args.get(el)
				break

		for el in ("with_plot_tag", "with_plot_tags_and", "with_plot_tags_or"):
			if args.get(el):
				ptags['with'] = args.get(el)
				break

		for el in ("without_plot_tag", "without_plot_tags_and", "without_plot_tags_or"):
			if args.get(el):
				ptags['without'] = args.get(el)
				break

		if stack:
			scol = SVGCollection()

		for db in dbs:

			loader = SVGLoader(
				db,
				logger = logger,
				limit = limit,
				enforce_base_path= args['enforce_base_path'],
				last_body = args['last_body'],
				latest_doc = args['latest_doc']
			)

			if [k for k in ("t0", "t1", "t2", "t3") if args.get(k, False)]:
				for el in ("t0", "t1", "t2", "t3"):
					if args[el]:
						loader.add_query(
							SVGQuery(
								col = el, # type: ignore[arg-type]
								path = args.get('base_path') or 'body.data.plot',
								plot_tag = ptags,
								doc_tag = dtags,
								unit = args.get("unit"),
								stock = args.get("stock"),
								custom_match = args.get("custom_match")
							)
						)
			else:
				for el in ("t0", "t1", "t2", "t3"):
					if not args.get(f"no-{el}"):
						loader.add_query(
							SVGQuery(
								col = el, # type: ignore[arg-type]
								path = args.get('base_path') or 'body.data.plot',
								plot_tag = ptags,
								doc_tag = dtags,
								unit = args.get("unit"),
								stock = args.get("stock"),
								custom_match = args.get("custom_match")
							)
						)

			loader.run()

			i = 1
			for v in loader._plots.values():

				pbo = PlotBrowseOptions(**args)
				if stack:
					for svg in v._svgs:
						if len(dbs) > 1:
							svg._record['title'] += f"\n<span style='color: steelblue'>{db.prefix}</span>"
						scol.add_svg_plot(svg)
						if i % stack == 0:
							show_collection(scol, pbo, print_func=print)
							scol = SVGCollection()
				else:
					for svg in v._svgs:
						show_svg_plot(svg, pbo)

		if stack:
			show_collection(scol, PlotBrowseOptions(**args), print_func=print)

		if i == 1:
			AmpelLogger.get_logger().info("No plot matched")
