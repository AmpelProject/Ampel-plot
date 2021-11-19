#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File              : Ampel-plots/main/ampel/plot/util/create.py
# License           : BSD-3-Clause
# Author            : vb <vbrinnel@physik.hu-berlin.de>
# Date              : 17.05.2019
# Last Modified Date: 16.11.2021
# Last Modified By  : vb <vbrinnel@physik.hu-berlin.de>

import io
import matplotlib as plt
from matplotlib.figure import Figure
from typing import Optional, List, Dict, Any, Union

from ampel.types import Tag
from ampel.content.SVGRecord import SVGRecord
from ampel.protocol.LoggerProtocol import LoggerProtocol
from ampel.model.PlotProperties import PlotProperties
from ampel.util.compression import compress as fcompress


def mplfig_to_svg_dict(
	mpl_fig, file_name: str, title: Optional[str] = None, tags: Optional[Union[Tag, List[Tag]]] = None,
	compress: int = 1, width: Optional[int] = None, height: Optional[int] = None,
	close: bool = True, fig_include_title: Optional[bool] = False, logger: Optional[LoggerProtocol] = None
) -> SVGRecord:
	"""
	:param mpl_fig: matplotlib figure
	:param tags: list of plot tags
	:param compress:
		0: no compression, 'svg' value will be a string
		1: compress svg, 'svg' value will be compressed bytes (usage: store plots into db)
		2: compress svg and include uncompressed string into key 'sgv_str'
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

	ret: SVGRecord = {'name': file_name}

	if tags:
		ret['tag'] = tags

	if title:
		ret['title'] = title

	if compress == 0:
		ret['svg'] = imgdata.getvalue()
		return ret

	ret['svg'] = fcompress(imgdata.getvalue().encode('utf8'), file_name)

	if compress == 2:
		ret['svg_str'] = imgdata.getvalue()

	return ret


def mplfig_to_svg_dict1(
	mpl_fig: Figure,
	props: PlotProperties,
	extra: Optional[Dict[str, Any]] = None,
	tag_complement: Optional[Union[Tag, List[Tag]]] = None,
	close: bool = True, logger: Optional[LoggerProtocol] = None
) -> SVGRecord:
	"""
	:param extra: required if file_name, title or fig_text in PlotProperties use a format string ("such_%s_this")
	"""

	svg_doc = mplfig_to_svg_dict(
		mpl_fig,
		file_name = props.get_file_name(extra=extra),
		title = props.get_title(extra=extra),
		fig_include_title = props.fig_include_title,
		width = props.width,
		height = props.height,
		tags = props.tags if not tag_complement else _merge_tags(props.tags, tag_complement),
		compress = props.get_compress(),
		logger = logger,
		close = close
	)

	if props.disk_save:
		file_name = props.get_file_name(extra=extra)
		if logger and getattr(logger, "verbose", 0) > 1:
			logger.debug("Saving %s/%s" % (props.disk_save, file_name))
		with open("%s/%s" % (props.disk_save, file_name), "w") as f:
			f.write(
				svg_doc.pop("svg_str") # type: ignore
				if props.get_compress() == 2
				else svg_doc['svg']
			)

	return svg_doc


def get_tags_as_str(
	plot_tag: Optional[Union[Tag, List[Tag]]] = None,
	extra_tags: Optional[Union[Tag, List[Tag]]] = None
) -> str:

	if plot_tag:
		t = _merge_tags(plot_tag, extra_tags) if extra_tags else plot_tag # type: ignore
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


def _merge_tags(arg1: Optional[Union[Tag, List[Tag]]], arg2: Union[Tag, List[Tag]]) -> Union[Tag, List[Tag]]:
	"""
	Note: not using ampel.util.collections.merge_to_list to avoid Ampel-core dependency
	"""

	if not arg1:
		return arg2

	if isinstance(arg1, (str, int)):
		if isinstance(arg2, (str, int)):
			if arg2 != arg1:
				return [arg1, arg2]
			return arg1
		else:
			if arg1 in arg2:
				return arg2 if isinstance(arg2, list) else list(arg2)
			l = list(arg2)
			l.append(arg1)
			return l

	# arg1 is a list
	else:
		if isinstance(arg2, (int, str)):
			if arg2 in arg1:
				return arg1 if isinstance(arg1, list) else list(arg1)
			l = list(arg1)
			l.append(arg2)
			return l

		# arg1 and arg2 are list
		else:
			return list(
				(arg1 if isinstance(arg1, set) else set(arg1)) |
				(arg2 if isinstance(arg2, set) else set(arg2))
			)
