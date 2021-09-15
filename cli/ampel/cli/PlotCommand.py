#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-plots/cli/ampel/cli/PlotCommand.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 15.03.2021
# Last Modified Date: 15.09.2021
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
from ampel.cli.utils import maybe_convert_stock
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
	"with-tag": "match plots with tag",
	"without-tag": "exclude plots with tag",
	"png": "convert to png (from svg)",
	"html": "html output format (includes plot titles)",
	"stack": "stack <n> images into one html structure (html option required). No arguments means all images are stacked together.",
	"out": "path to file (printed to stdout otherwise)",
	"verbose": "increases verbosity"
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
		builder.create_logic_args('match', "with-tag", "Tag")
		builder.add_arg('match', "custom-match", metavar="#", action=LoadJSONAction)

		self.parsers.update(
			builder.get()
		)

		return self.parsers[sub_op]

		"""
		for el in (0, 1, 2, 3):
			optional.add_argument(f'--t{el}', dest=f't{el}', action='store_true', help=f"match t{el} plots")
			optional.set_defaults(**{f"t{el}": False})
		for el in (0, 1, 2, 3):
			optional.add_argument(f'--no-t{el}', dest=f't{el}', action='store_false', help=f"do not match t{el} plots (default)")

		optional.add_argument("--png", dest='png', action='store_true', help=h['png'])
		optional.set_defaults(png=False)
		optional.add_argument("--secrets", default=None, help=h['secrets'])
		optional.add_argument("--with-tag", type=str, default=True, help=h['with-tag'])
		optional.add_argument("--without-tag", type=str, default=True, help=h['without-tag'])
		optional.add_argument("-v", "--verbose", action="count", default=0, help=h['verbose'])
		optional.add_argument("-d", "--debug", action="count", default=0, help=h['verbose'])


		parser.epilog = (
			"examples:\n" +
 			"-> ampel plot --config ampel_conf.yaml --stock 85628462 --with-tag SNCOSMO -out images"
		)
		"""

	# Mandatory implementation
	def run(self, args: Dict[str, Any], unknown_args: Sequence[str], sub_op: Optional[str] = None) -> None:

		html = args.get("html")
		stack = args.get("stack")
		limit = args.get("limit") or 0
		png_dpi = args.get("png")

		if stack and not html:
			raise ValueError("Option 'stack' requires option 'html'")

		ctx = self.get_context(args, unknown_args) # type: ignore[var-annotated]
		maybe_convert_stock(args)

		logger = AmpelLogger.from_profile(
			ctx, 'console_debug' if args['debug'] else 'console_info',
			base_flag = LogFlag.MANUAL_RUN
		)

		l = SVGLoader(ctx.db, logger=logger, limit=limit)

		if [k for k in ("t0", "t1", "t2", "t3") if args.get(k, False)]:
			for el in ("t0", "t1", "t2", "t3"):
				if args[el]:
					l.add_query(
						SVGQuery(
							col = el, # type: ignore[arg-type]
							path = 'body.data.plot',
							tag = args.get("with-tag")
						)
					)
		else:
			for el in ("t0", "t1", "t2", "t3"):
				if not args.get(f"no-{el}"):
					l.add_query(
						SVGQuery(
							col = el, # type: ignore[arg-type]
							path = 'body.data.plot',
							tag = args.get("with-tag")
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
