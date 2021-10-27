#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-plots/cli/ampel/cli/PlotCommand.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 15.03.2021
# Last Modified Date: 13.10.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

import os, webbrowser, tempfile, hashlib
from cairosvg import svg2png
from typing import Sequence, Dict, Any, Optional, Union
from argparse import ArgumentParser
from ampel.cli.AmpelArgumentParser import AmpelArgumentParser
from ampel.cli.ArgParserBuilder import ArgParserBuilder
from ampel.cli.AbsCoreCommand import AbsCoreCommand
from ampel.cli.MaybeIntAction import MaybeIntAction
from ampel.cli.LoadJSONAction import LoadJSONAction
from ampel.cli.utils import maybe_load_idmapper
from ampel.log.LogFlag import LogFlag
from ampel.log.AmpelLogger import AmpelLogger
from ampel.plot.SVGCollection import SVGCollection
from ampel.plot.SVGLoader import SVGLoader
from ampel.plot.SVGQuery import SVGQuery

# Let's have these in one place
h = {
	"config": "path to an ampel config file (yaml/json)",
	"secrets": "path to a YAML secrets store in sops format",
	"stock": "stock id(s). Comma sperated values can be used",
	"base-path": "default: body.data.plot",
	"unit": "docs will have to match the provided ampel unit name",
	"limit": "limit for underlying DB query",
	# TODO: find better name
	"enforce-base-path": "within a given doc, load only plots with base-path",
	"last-body": "If body is a sequence (t2 docs), parse only the last body element",
	"latest-doc": "using the provided matching criteria, show plot(s) only from latest doc",
	"with-plot-tag": "match plots with tag",
	"without-plot-tag": "exclude plots with tag",
	"with-doc-tag": "match plots embedded in doc with tag",
	"without-doc-tag": "exclude plots embedded in doc with tag",
	"png": "convert to png (from svg)",
	"html": "html output format (includes plot titles)",
	"stack": "stack <n> images into one html structure (html option required). No arguments means all images are stacked together.",
	"out": "path to file (printed to stdout otherwise)",
	"verbose": "increases verbosity",
	"debug": "debug"
}

class PlotCommand(AbsCoreCommand):

	def __init__(self):
		self.parsers = {}

	# Mandatory implementation
	def get_parser(self, sub_op: Optional[str] = None) -> Union[ArgumentParser, AmpelArgumentParser]:

		if sub_op in self.parsers:
			return self.parsers[sub_op]

		sub_ops = ["show", "save"]
		if sub_op is None or sub_op not in sub_ops:
			return AmpelArgumentParser.build_choice_help(
				'plot', sub_ops, h, description = 'Show or export ampel plots.'
			)

		builder = ArgParserBuilder("plot")
		builder.add_parsers(sub_ops, h)

		builder.notation_add_note_references()
		builder.notation_add_example_references()

		# Required
		builder.add_arg('required', 'config', type=str)
		builder.add_arg('save.required', 'out', type=str)

		# Optional
		builder.add_arg('optional', 'limit', type=int)
		builder.add_arg('optional', 'secrets')
		builder.add_arg('optional', 'debug', action="store_true")
		builder.add_arg('optional', 'id-mapper', type=str)
		builder.add_arg('optional', 'base-path', type=str)
		builder.add_arg('optional', 'unit', type=str)
		builder.add_arg('optional', 'enforce-base-path', action="store_true")
		builder.add_arg('optional', 'last-body', action="store_true")
		builder.add_arg('optional', 'latest-doc', action="store_true")

		# Optional mutually exclusive args
		builder.add_x_args('optional',
			{'name': 'png', 'nargs': '?', 'type': int, 'const': 96},
			{'name': 'html', 'action': 'store_true'},
		)
		builder.add_arg('optional', 'stack', action='store', metavar='#', const=1, nargs='?', type=int, default=0)
		

		builder.add_group('match', 'Plot selection arguments')

		for el in (0, 1, 2, 3):
			builder.add_arg('match', f'no-t{el}', action='store_true', help=f"Ignore t{el} plots")

		for el in (0, 1, 2, 3):
			builder.add_arg('match', f't{el}', action='store_true', help=f"Match only t{el} plots")

		builder.add_arg('match', "stock", action=MaybeIntAction, nargs="+")
		builder.create_logic_args('match', "channel", "Channel")
		builder.create_logic_args('match', "with-doc-tag", "Doc tag", json=False)
		builder.create_logic_args('match', "without-doc-tag", "Doc tag", json=False)
		builder.create_logic_args('match', "with-plot-tag", "Plot tag", json=False)
		builder.create_logic_args('match', "without-plot-tag", "Plot tag", json=False)
		builder.add_arg('match', "custom-match", metavar="#", action=LoadJSONAction)

		builder.add_example('show', "-stack 100 -html -t2")
		builder.add_example('show', "-html -t3 -base-path body.plot -latest-doc")
		builder.add_example('show', "-stack -html -limit 10 -t2 -with-plot-tag SNCOSMO -with-doc-tag NED_NEAREST_IS_SPEC -custom-match '{\"body.data.ned.sep\": {\"$lte\": 10}}'")
		builder.add_example('show', "-stack 100 -html -t2 -with-doc-tag NED_NEAREST_IS_SPEC -unit T2PS1ThumbNedSNCosmo -mongo.prefix Dipole2 -resource.mongo localhost:27050 -debug")
		
		self.parsers.update(
			builder.get()
		)

		return self.parsers[sub_op]


	# Mandatory implementation
	def run(self, args: Dict[str, Any], unknown_args: Sequence[str], sub_op: Optional[str] = None) -> None:

		html = args.get("html")
		stack = args.get("stack")
		limit = args.get("limit") or 0
		png_dpi = args.get("png")

		if stack and not html:
			raise ValueError("Option 'stack' requires option 'html'")

		if (x := args.get('base_path')) and not x.startswith("body."):
			raise ValueError("Option 'base-path' must start with 'body.'")

		ctx = self.get_context(args, unknown_args) # type: ignore[var-annotated]
		maybe_load_idmapper(args)

		logger = AmpelLogger.from_profile(
			ctx, 'console_debug' if args['debug'] else 'console_info',
			base_flag = LogFlag.MANUAL_RUN
		)

		l = SVGLoader(
			ctx.db,
			logger = logger,
			limit = limit,
			enforce_base_path= args['enforce_base_path'],
			last_body = args['last_body'],
			latest_doc = args['latest_doc']
		)

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

		if [k for k in ("t0", "t1", "t2", "t3") if args.get(k, False)]:
			for el in ("t0", "t1", "t2", "t3"):
				if args[el]:
					l.add_query(
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
					l.add_query(
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

		l.run()

		if stack:
			scol = SVGCollection()

		i = 1
		for v in l._plots.values():

			for svg in v._svgs:

				tmp_dir = os.path.join(tempfile.gettempdir(), "ampel")
				if not os.path.exists(tmp_dir):
					os.mkdir(tmp_dir)
				path = os.path.join(tmp_dir, svg.get_file_name())
				if png_dpi:
					path = path.removesuffix(".svg") + ".png"
					with open(path, 'wb') as fb:
						fb.write(svg2png(bytestring=svg._record['svg'], dpi=png_dpi))
				elif html:
					if stack:
						scol.add_svg_plot(svg)
					else:
						path = path.removesuffix(".svg") + ".html"
						with open(path, 'w') as fh:
							fh.write(svg._repr_html_())
				else:
					with open(path, 'w') as ft:
						ft.write(svg._record['svg']) # type: ignore[arg-type]

				if not stack:
					webbrowser.open('file://' + path)

				i += 1

				if stack > 1 and i % stack == 0:
					self.show_collection(scol)
					scol = SVGCollection()

		if stack:
			self.show_collection(scol)

		if i == 1:
			AmpelLogger.get_logger().info("No plot matched")


	def show_collection(self, scol: SVGCollection) -> None:

		if x := scol._repr_html_():

			tmp_file = os.path.join(
				self._get_ampel_tmp_dir(),
				hashlib.md5(x.encode('utf8')).hexdigest() + ".html"
			)

			with open(tmp_file, 'w') as fh:
				fh.write(x)

			webbrowser.open('file://' + tmp_file)
		else:
			AmpelLogger.get_logger().info("Empty collection: nothing to display")


	def _get_ampel_tmp_dir(self) -> str:
		tmp_dir = os.path.join(tempfile.gettempdir(), "ampel")
		if not os.path.exists(tmp_dir):
			os.mkdir(tmp_dir)
		return tmp_dir
