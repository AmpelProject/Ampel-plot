#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot-browse/ampel/plot/util/keyboard.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                16.11.2021
# Last Modified Date:  19.11.2021
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

import time
from pynput import keyboard # type: ignore[import]

class MultiProcessingPynput:

	def __init__(self, v):
		self.v = v

	def run(self) -> None:

		def on_press(key):
			if key == keyboard.Key.ctrl:
				self.v.value = 1

		def on_release(key):
			if key == keyboard.Key.ctrl:
				time.sleep(0.2)
				self.v.value = 0

		# Collect events until released
		with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
			listener.join()

	def is_ctrl_pressed(self) -> bool:
		return bool(self.v.value)


class InlinePynput:
	
	def __init__(self):
		self.pressed = False

		def on_press(key):
			if key == keyboard.Key.ctrl:
				self.pressed = True

		def on_release(key):
			if key == keyboard.Key.ctrl:
				time.sleep(0.2)
				self.pressed = False

		# Collect events until released
		listener = keyboard.Listener(on_press=on_press, on_release=on_release)
		listener.start()

	def is_ctrl_pressed(self) -> bool:
		return self.pressed
