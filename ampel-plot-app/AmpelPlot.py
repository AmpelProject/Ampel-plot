#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot-app/AmpelPlot.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                16.11.2021
# Last Modified Date:  19.11.2021
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

import os, warnings, sys, psutil, PySimpleGUI as sg # type: ignore[import]
from tkinter import Menu, BooleanVar
from multiprocessing import Process, Value, freeze_support

from datetime import datetime
from ampel.plot.util.keyboard import MultiProcessingPynput
#from ampel.plot.util.keyboard import InlinePynput
from ampel.plot.util.clipboard import set_print, read_from_clipboard
from ampel.model.PlotBrowseOptions import PlotBrowseOptions

window = None
p = None
toggle_bool = False


def goodbye():
	warnings.filterwarnings("ignore", category=UserWarning)
	with warnings.catch_warnings():
		warnings.filterwarnings(action="ignore", category=UserWarning, module=r"multiprocessing")
		if p:
			p.terminate()
		if window:
			window.close()
		sys.exit(0)


def main(keyboard_callback) -> None:

	global window, p

	try:
		sg.set_options(icon=resource_path("ampel_plot.png"))
		sg.theme('SystemDefault1')
		layout = [
			[
				sg.Multiline(
					size=(85, 20), font=('Helvetica', 12), justification='left', key='text',
					autoscroll=True, auto_refresh=True
				)
			],
			[
				*_ltxt('stack', 20, tooltip=' Max # of plots to display per tab/window '),
				*_ltxt('scale', 1.0, tooltip=' Image scale factor '),
				_chkbox('debug', tooltip=' Increase verbosity '),
				_chkbox('html', default=True, tooltip=' HTML output format (includes plot titles) '),
				_chkbox('Tight layout', key='tight', tooltip=' Suppress botton margins '),
				_chkbox('png', enable_events=True, tooltip=' Convert SVG to PNG '),
				sg.Column(
					[[_itxt('dpi', 96, tooltip=' SVG quality '), _txt('dpi')]],
					key='coldpi', pad=(0, 0), visible = False
				)
			],
			[sg.Button('Apply', pad=10), sg.Push(), sg.Button('Exit', pad=10)]
		]

		window = sg.Window(
			'AmpelPlot', layout,
			finalize=True
		)
		set_print(_print)

		on_top = BooleanVar()
		menubar = Menu(window.TKroot)
		vm = Menu(menubar, tearoff=0)
		vm.add_checkbutton(
			label="Always on top",
			onvalue=1, offvalue=0, variable=on_top,
			command=lambda: window.keep_on_top_set() if on_top.get() else window.keep_on_top_clear() # type: ignore
		)
		menubar.add_cascade(label="View ", menu=vm) # space in on purpose

		window.TKroot.config(menu=menubar)
		window.TKroot.protocol("WM_DELETE_WINDOW", goodbye)
		window.TKroot.tk.createcommand('::tk::mac::Quit', goodbye)
		window.TKroot.master.attributes("-fullscreen", True)

		while True:
			read_from_clipboard(
				PlotBrowseOptions(
					debug = window['debug'].get(),
					html = window['html'].get(),
					png = int(window['dpi'].get()) if window['png'].get() else None,
					max_size = float(window['max_size'].get()),
					scale = float(window['scale'].get()),
					stack = int(window['stack'].get())
				),
				keyboard_callback = keyboard_callback,
				gui_callback = window_callback,
				exit_on_interrupt = False
			)
	except Exception as e:
		import traceback
		with open('AmpelPlot_error.log', 'w') as f:
			f.write(f"{e}\n")
			traceback.print_exc(file=f)


def _txt(txt, **kwargs):
	return sg.Text(txt, expand_y = True, size=(None, 1), **kwargs)

def _itxt(k, v, **kwargs):
	return sg.InputText(v, size=(4, 1), pad=(0, 0), key=k, **kwargs)

def _ltxt(k, v, **kwargs):
	return _txt(k), _itxt(k, v, **kwargs)

def _chkbox(k, **kwargs):
	return sg.Checkbox(k, expand_y = True, size=(None, 1), key=kwargs.pop('key', k), **kwargs)


def _print(*args):
	el = window['text']
	#el.update(disabled=False)
	el.print(
		datetime.now().strftime('[%d/%m/%Y %H:%M:%S] '),
		text_color="#808080",
		end = ""
	)
	if len(args) > 1:
		el.print(args[0] + " ", end="")
		el.print(" ".join(args[1:]), text_color="#4682B4")
	else:
		el.print(" ".join(args))
	#window.read(timeout=10)
	#el.update(disabled=True)


def window_callback():
	global toggle_bool
	event, values = window.read(timeout=10)
	if event == 'Apply':
		_print("Applying new config")
		raise KeyboardInterrupt
	elif event == 'png':
		toggle_bool = not toggle_bool
		window['coldpi'].update(visible=toggle_bool)
	elif event == sg.WIN_CLOSED or event == 'Exit':
		import warnings
		warnings.filterwarnings("ignore", category=UserWarning)
		with warnings.catch_warnings():
			warnings.filterwarnings(action="ignore", category=UserWarning, module=r"multiprocessing")
			goodbye()


def resource_path(relative_path):
	return os.path.join(
		getattr(sys, '_MEIPASS'),
		#"..",
		#"Resources",
		relative_path
	)


if __name__ == "__main__":

	freeze_support()

	if len([proc for proc in psutil.process_iter() if proc.name() == "AmpelPlot"]) > 1:
		print("Exit...(AmpelPlot is already running)")
		os._exit(1)

	# Not running Pynput in a dedicated process result in a programm crash (Illegal instruction: 4)
	v = Value('i', 0)
	mpp = MultiProcessingPynput(v)
	p = Process(target=mpp.run)
	p.start()

	#main(InlinePynput().is_ctrl_pressed)
	main(mpp.is_ctrl_pressed)
