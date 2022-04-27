#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot/ampel/plot/create.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                17.05.2019
# Last Modified Date:  27.04.2022
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

import io, os
import matplotlib as plt
from matplotlib.figure import Figure
from typing import Any

from ampel.types import Tag, OneOrMany
from ampel.content.NewSVGRecord import NewSVGRecord
from ampel.protocol.LoggerProtocol import LoggerProtocol
from ampel.model.PlotProperties import PlotProperties
from ampel.util.compression import TCompression, compress as compress_func
from ampel.util.tag import merge_tags


def create_plot_record(
	mpl_fig: Figure,
	props: PlotProperties,
	extra: None | dict[str, Any] = None,
	tag_complement: None | OneOrMany[Tag] = None,
	close: bool = True, logger: None | LoggerProtocol = None
) -> NewSVGRecord:
	"""
	:param extra: required if file_name, title or fig_text in PlotProperties use a format string ("such_%s_this")
	"""

	svg_doc = fig_to_plot_record(
		mpl_fig,
		file_name = props.get_file_name(extra=extra),
		title = props.get_title(extra=extra),
		fig_include_title = props.fig_include_title,
		width = props.width,
		height = props.height,
		tags = props.tags if not tag_complement else merge_tags(props.tags, tag_complement),
		compression_behavior = props.get_compression_behavior(),
		compression_alg = props.compression_alg,
		compression_level = props.compression_level,
		detached = props.detached,
		logger = logger,
		close = close
	)

	if props.disk_save:
		fname = os.path.join(props.disk_save, props.get_file_name(extra=extra))
		if logger and getattr(logger, "verbose", 0) > 1:
			logger.debug(f"Saving {fname}")
		with open(fname, "w") as f:
			f.write(
				svg_doc.pop("svg_str") # type: ignore
				if props.get_compression_behavior() == 2
				else svg_doc['svg']
			)

	return svg_doc


def fig_to_plot_record(
	mpl_fig: Figure,
	file_name: str,
	title: None | str = None,
	tags: None | OneOrMany[Tag] = None,
	compression_behavior: int = 1,
	compression_alg: TCompression = "ZIP_DEFLATED",
	compression_level: int = 9,
	width: None | int = None,
	height: None | int = None,
	close: bool = True,
	fig_include_title: None | bool = False,
	detached: bool = True,
	logger: None | LoggerProtocol = None
) -> NewSVGRecord:
	"""
	:param mpl_fig: matplotlib figure
	:param tags: one or many plot tags
	:param compression_behavior:
		0: no compression, 'svg' value will be a string
		1: compression_behavior svg, 'svg' value will be compressed bytes (usage: store plots into db)
		2: compression_behavior svg and include uncompressed string into key 'sgv_str'
		(useful for saving plots into db and additionaly to disk for offline analysis)
	:param width: figure width, for example 10 inches
	:param height: figure height, for example 10 inches
	:returns: svg dict instance
	"""

	if logger:
		logger.info("Saving plot %s" % file_name)

	imgdata = io.StringIO()

	if width is not None and height is not None:
		mpl_fig.set_size_inches(width, height)

	if title and fig_include_title:
		mpl_fig.suptitle(title)

	mpl_fig.savefig(imgdata, format='svg', bbox_inches='tight')
	if close:
		plt.pyplot.close(mpl_fig)

	ret: NewSVGRecord = {'name': file_name}

	if tags:
		ret['tag'] = tags

	if title:
		ret['title'] = title

	ret['detached'] = detached

	if compression_behavior == 0:
		ret['svg'] = imgdata.getvalue()
		return ret

	ret['svg'] = compress_func(
		imgdata.getvalue().encode('utf8'),
		file_name,
		alg = compression_alg,
		compression_level = compression_level
	)

	if compression_behavior == 2:
		ret['svg_str'] = imgdata.getvalue()

	return ret


def get_tags_as_str(
	plot_tag: None | OneOrMany[Tag] = None,
	extra_tags: None | OneOrMany[Tag] = None
) -> str:

	if plot_tag:
		t = merge_tags(plot_tag, extra_tags) if extra_tags else plot_tag # type: ignore
	elif extra_tags:
		t = extra_tags
	else:
		return ""

	if isinstance(t, (int, str)):
		return "[%s]" % t

	return "[%s]" % ", ".join([
		str(el) if isinstance(el, int) else el
		for el in t
	])
