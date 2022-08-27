#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot-cli/ampel/cli/PlotCommand.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                15.03.2021
# Last Modified Date:  27.08.2022
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

import os
from typing import Any
from bson import ObjectId # type: ignore
from datetime import datetime
from collections.abc import Sequence
from argparse import ArgumentParser
from ampel.base.AuxUnitRegister import AuxUnitRegister
from ampel.cli.AmpelArgumentParser import AmpelArgumentParser
from ampel.cli.ArgParserBuilder import ArgParserBuilder
from ampel.cli.AbsCoreCommand import AbsCoreCommand
from ampel.cli.MaybeIntAction import MaybeIntAction
from ampel.cli.LoadJSONAction import LoadJSONAction
from ampel.cli.JobCommand import JobCommand
from ampel.cli.utils import maybe_load_idmapper, get_vault, get_db
from ampel.log.AmpelLogger import AmpelLogger
from ampel.log.LogFlag import LogFlag
from ampel.plot.SVGCollection import SVGCollection
from ampel.plot.SVGLoader import SVGLoader
from ampel.plot.SVGQuery import SVGQuery
from ampel.plot.SVGPlot import SVGPlot
from ampel.core.AmpelContext import AmpelContext
from ampel.model.PlotBrowseOptions import PlotBrowseOptions
from ampel.plot.util.clipboard import read_from_clipboard
from ampel.plot.util.watch import read_from_db
from ampel.plot.util.show import show_collection, show_svg_plot
from ampel.plot.util.transform import _svg_inkscape, svg_to_png
from ampel.mongo.utils import match_one_or_many
from ampel.util.pretty import out_stack


h = {
	'show': 'Display ampel plots retrieved via DB query(ies)',
	'clipboard': 'Monitor the clipboard for ampel plots and display them in browser',
	'watch': 'Monitor a given collection for new ampel plots and display them in browser',
	'export': 'Exports plots (matched by id) to EPS/PDF/SVG (EPS and PDF require inkscape)',
	'config': 'path to an ampel config file (yaml/json)',
	'secrets': 'path to a YAML secrets store in sops format',
	'stock': 'stock id(s). Comma sperated values can be used (without space)',
	'base-path': 'default: body.data.plot',
	'unit': 'docs will have to match the provided ampel unit name',
	'limit': 'limit the number of *documents* (not plots) returned by the underlying DB query',
	# TODO: find better name
	'enforce-base-path': 'within a given doc, load only plots with base-path',
	'last-body': 'If body is a sequence (t2 docs), parse only the last body element',
	'latest': 'using the provided matching criteria, show plot(s) only from latest doc',
	'with-plot-tag': 'match plots with tag',
	'without-plot-tag': 'exclude plots with tag',
	'with-doc-tag': 'match plots embedded in doc with tag',
	'without-doc-tag': 'exclude plots embedded in doc with tag',
	'png': 'convert to png (from svg). Default: 96 DPI',
	'scale': 'scale png size. Default: 1.0',
	'max-size': 'max-inline-size value of each HTML div',
	'html': 'html output format (includes plot titles)',
	'stack': 'stack <n> images into one html structure (activates html option). Default: 100',
	'out': 'path to file (printed to stdout otherwise)',
	'db': 'Database prefix. Multiple prefixes are supported (one query per db will be executed).\nIf set, "-mongo.prefix" value will be ignored',
	'col': 'Collection name',
	'run-id': 'Matches plots created during specified runs (-job arg will be ignored)',
	'job': '<path to job schema(s)>. Only plots created by the specified job will be loaded.\nOne-db and mongo.prefix will be set automatically.',
	'job-id': 'Matches plots created by specified job ids (-job arg will be ignored)',
	'job-time-from': 'Restrict event collection search using provided timestamp\n(used automatically by ampel job ... -show-plots)',
	'format': 'Export file format (svg, png, pdf, eps). Use png:150 to set custom DPI (default: 150)',
	'verbose': 'increases verbosity',
	'debug': 'debug'
}
pressed = False

class PlotCommand(AbsCoreCommand):

	@staticmethod
	def get_sub_ops() -> list[str]:
		return ['show', 'export', 'clipboard', 'watch']

	# Implement
	def get_parser(self, sub_op: None | str = None) -> ArgumentParser | AmpelArgumentParser:

		if sub_op in self.parsers:
			return self.parsers[sub_op]

		sub_ops = self.get_sub_ops()
		if sub_op is None or sub_op not in sub_ops:
			return AmpelArgumentParser.build_choice_help(
				'plot', sub_ops, h, description = 'Display or export ampel plots.'
			)

		builder = ArgParserBuilder('plot')
		builder.add_parsers(sub_ops, h)

		builder.notation_add_note_references()
		builder.notation_add_example_references()

		builder.req('config')
		builder.req('out', 'export')
		builder.opt('format', 'export', default='svg')
		builder.req('oid', 'export', nargs='+')

		builder.opt('limit', 'show', type=int)
		builder.opt('secrets')
		builder.opt('debug', action='store_true')
		builder.opt('id-mapper', 'show', type=str)
		builder.opt('base-path', 'show', type=str)
		builder.opt('unit', 'show', type=str)
		builder.opt('run-id', 'show', action=MaybeIntAction, nargs='+')
		builder.opt('enforce-base-path', 'show', action='store_true')
		builder.opt('last-body', 'show', action='store_true')
		builder.opt('latest', 'show', action='store_true')
		builder.opt('scale', nargs='?', type=float, default=1.0)
		builder.opt('max-size', nargs='?', type=int)
		builder.opt('db', 'show|export|clipboard', type=str, nargs='+')
		builder.opt('job', 'show|watch|clipboard', type=str, nargs='+')
		builder.opt('job-id', 'show|watch|clipboard', action=MaybeIntAction, nargs='+')
		builder.opt('job-time-from', 'show', action=MaybeIntAction, nargs='?')
		builder.req('db', 'watch', type=str, nargs='+')
		builder.req('col', 'watch', type=str, nargs='?')

		# Optional mutually exclusive args
		builder.xargs(
			group='optional', sub_ops='show|watch|clipboard', xargs=[
				{'name': 'png', 'nargs': '?', 'type': int, 'const': 96},
				{'name': 'html', 'action': 'store_true'}
			]
		)
		builder.opt(
			'stack', 'show|watch|clipboard',
			action='store', metavar='#', const=100, nargs='?', type=int, default=0
		)

		builder.add_group('match', 'Plot selection arguments', sub_ops='show|watch')
		for el in (0, 1, 2, 3):
			builder.arg(
				f'no-t{el}', group='match', sub_ops='show|watch',
				action='store_true', help=f'Ignore t{el} plots'
			)
			builder.arg(
				f't{el}', group='match', sub_ops='show|watch',
				action='store_true', help=f'Match only t{el} plots'
			)

		builder.arg(
			'plots-col', group='match', sub_ops='show|watch', action='store_true',
			help='Match only plots from plots collections'
		)
		builder.arg('stock', group='match', sub_ops='show|watch', action=MaybeIntAction, nargs='+')
		builder.logic_args('channel', descr='Channel', group='match', sub_ops='show|watch')
		builder.logic_args('with-doc-tag', descr='Doc tag', group='match', sub_ops='show|watch', json=False)
		builder.logic_args('without-doc-tag', descr='Doc tag', group='match', sub_ops='show|watch', json=False)
		builder.logic_args('with-plot-tag', descr='Plot tag', group='match', sub_ops='show|watch', json=False)
		builder.logic_args('without-plot-tag', descr='Plot tag', group='match', sub_ops='show|watch', json=False)
		builder.arg('custom-match', group='match', sub_ops='show|watch', metavar='#', action=LoadJSONAction)

		builder.example('show', '-stack -300 -t2')
		builder.example('show', '-html -t3 -base-path body.plot -latest -db HelloAmpel')
		builder.example('show', '-html -t2 -stock 123456 -db DB1 DB2')
		builder.example('show', '-stack -t2 -png 300 -limit 10')
		builder.example('show',
			'-stack -limit 10 -t2 -with-plot-tag SNCOSMO -with-doc-tag NED_NEAREST_IS_SPEC ' +
			'-custom-match \'{\"body.data.ned.sep\": {\"$lte\": 10}}\''
		)
		builder.example('show',
			'-stack -t2 -with-doc-tag NED_NEAREST_IS_SPEC -unit T2PS1ThumbNedSNCosmo ' +
			'-mongo.prefix Dipole2 -resource.mongo localhost:27050 -debug'
		)
		builder.example('show',
			'-html -stack 1000 -t3 -base-path body.plot ' +
			'-unit T3CosmoDipole -latest -job DIPOLE.zhel.ztf225.yaml'
		)
		builder.example('clipboard', '-html')
		builder.example('watch', '-db MyDB -col t3 -stack -png 200')
		builder.example('export', '-db SIM -out /Users/you/Documents/ -oid 62fde88cf4880a864494b291')
		builder.example('export', '-db SIM -format pdf -out /Users/you/Documents/ -oid 62fde88cf4880a864494b291 62fde88cf4880a864494b292')
		builder.example('export', '-db SIM -format png:200 -out /Users/you/Documents/ -oid 62fde88cf4880a864494b295')
		
		self.parsers.update(
			builder.get()
		)

		return self.parsers[sub_op]


	# Mandatory implementation
	def run(self, args: dict[str, Any], unknown_args: Sequence[str], sub_op: None | str = None) -> None:

		stack = args.get('stack')
		limit = args.get('limit') or 0
		db_prefixes = args.get('db')
		dbs = []

		config = self.load_config(args['config'], unknown_args, freeze=False)
		vault = get_vault(args)

		logger = AmpelLogger.from_profile(
			self.get_context(args, unknown_args, ContextClass=AmpelContext),
			'console_debug' if args['debug'] else 'console_info',
			base_flag=LogFlag.MANUAL_RUN
		)

		if args.get('job_id'):
			job_sig = args['job_id']
		elif args.get('job'):
			job, job_sig = JobCommand.get_job_schema(args['job'], logger)
			if job.mongo and job.mongo.prefix:
				db_prefixes = [job.mongo.prefix]
			args['one_db'] = True
		else:
			job_sig = None

		if db_prefixes:
			for el in db_prefixes:
				config._config['mongo']['prefix'] = el
				dbs.append(
					get_db(config, vault, require_existing_db=True, one_db = 'auto')
				)
		else:
			dbs = [
				get_db(config, vault, require_existing_db=True, one_db='auto')
			]

		run_ids = None

		if args.get('run_id'):
			run_ids = args['run_id']

		elif args.get('job'):

			mcrit: dict[str, Any] = {'jobid': job_sig}
			if args['job_time_from']:
				mcrit['_id'] = {
					'$gt': ObjectId.from_datetime(
						datetime.fromtimestamp(args['job_time_from'])
					)
				}

				run_id = next(dbs[0].get_collection('event').find(mcrit), None)

			else:

				run_id = next(
					dbs[0].get_collection('event') \
						.find(mcrit) \
						.sort('_id', -1) \
						.limit(1),
					None
				)

			if run_id is None:
				logger.info('No run found for specified job')
				return

			run_ids = run_id['run']


		if sub_op == 'export':

			docs = dbs[0] \
				.get_collection('plot') \
				.find({'_id': match_one_or_many([ObjectId(el) for el in args['oid']])})

			dpi = 0
			fmode = 'w'
			get_plot_name = lambda doc: doc['name']
			if args['format'].startswith('png'):
				dpi = 150
				fmode = 'wb'
				get_plot_name = lambda doc: doc['name'].replace('.svg', f'_{dpi}dpi.png')
				if ':' in args['format']:
					dpi = int(args['format'].split(':')[1])
			elif args['format'] not in ('eps', 'pdf', 'svg'):
				with out_stack():
					raise ValueError("Option format must be one of: eps, pdf, svg, png")

			i = 0
			inkscape = args['format'] in ('pdf', 'eps')
			func = lambda x: svg_to_png(x, dpi=dpi) if dpi else lambda x: x
			for doc in docs:
				i += 1
				if i == 1:
					print("Exporting:")
				if inkscape:
					_svg_inkscape(
						SVGPlot(doc).get(), args['out'],
						doc['name'].replace('.svg', ''),
						ext = args['format']
					)
				else:
					outname = os.path.join(args['out'], get_plot_name(doc))
					with open(outname, fmode) as f:
						f.write(func(SVGPlot(doc).get()))
						print(outname)

			if i == 0:
				print("Plot(s) not found")

			return

		if sub_op == 'clipboard':
			from ampel.plot.util.keyboard import InlinePynput
			ipo = InlinePynput()
			read_from_clipboard(
				PlotBrowseOptions(**args),
				plots_col = dbs[0].get_collection('plot'),
				keyboard_callback = ipo.is_ctrl_pressed
			)
		
		if (x := args.get('base_path')) and not x.startswith('body.'):
			raise ValueError('Option "base-path" must start with "body."')

		if sub_op == 'watch':
			read_from_db(
				dbs[0].get_collection(args['col']),
				PlotBrowseOptions(**args)
			)

		if 'id_mapper' in args:
			AuxUnitRegister.initialize(config)
			maybe_load_idmapper(args)

		ptags: dict = {}
		dtags: dict = {}

		for el in ('with_doc_tag', 'with_doc_tags_and', 'with_doc_tags_or'):
			if args.get(el):
				dtags['with'] = args.get(el)
				break

		for el in ('without_doc_tag', 'without_doc_tags_and', 'without_doc_tags_or'):
			if args.get(el):
				dtags['without'] = args.get(el)
				break

		for el in ('with_plot_tag', 'with_plot_tags_and', 'with_plot_tags_or'):
			if args.get(el):
				ptags['with'] = args.get(el)
				break

		for el in ('without_plot_tag', 'without_plot_tags_and', 'without_plot_tags_or'):
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
				latest_doc = args['latest']
			)

			if args['plots_col']:
				loader.add_query(
					SVGQuery(
						col = 'plots',
						path = '',
						plot_tag = ptags,
						doc_tag = dtags,
						unit = args.get('unit'),
						stock = args.get('stock'),
						job_sig = job_sig,
						run_id = run_ids,
						custom_match = args.get('custom_match')
					)
				)
			else:
				if [k for k in ('t0', 't1', 't2', 't3') if args.get(k, False)]:
					for el in ('t0', 't1', 't2', 't3'):
						if args[el]:
							loader.add_query(
								SVGQuery(
									col = el, # type: ignore[arg-type]
									path = args.get('base_path') or 'body.data.plot',
									plot_tag = ptags,
									doc_tag = dtags,
									unit = args.get('unit'),
									stock = args.get('stock'),
									job_sig = job_sig,
									run_id = run_ids,
									custom_match = args.get('custom_match')
								)
							)
				else:
					for el in ('t0', 't1', 't2', 't3'):
						if not args.get(f'no-{el}'):
							loader.add_query(
								SVGQuery(
									col = el, # type: ignore[arg-type]
									path = args.get('base_path') or 'body.data.plot',
									plot_tag = ptags,
									doc_tag = dtags,
									unit = args.get('unit'),
									stock = args.get('stock'),
									job_sig = job_sig,
									run_id = run_ids,
									custom_match = args.get('custom_match')
								)
							)

			loader.run()

			i = 1
			for v in loader._plots.values():

				pbo = PlotBrowseOptions(**args)
				if stack:
					for svg in v._svgs:
						i += 1
						if len(dbs) > 1:
							svg._record['title'] += f'\n<span style="color: steelblue">{db.prefix}</span>'
						scol.add_svg_plot(svg)
						if i % stack == 0:
							show_collection(scol, pbo, print_func=print)
							scol = SVGCollection()
				else:
					for svg in v._svgs:
						i += 1
						show_svg_plot(svg, pbo)

		if stack:
			show_collection(scol, PlotBrowseOptions(**args), print_func=print)

		if i == 1:
			AmpelLogger.get_logger().info('No plot matched')
