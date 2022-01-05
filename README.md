# Ampel-plot

provides:
- a standardized document structure called `SVGRecord` for saving plots into the ampel DB
- a model for configuring plot properties in unit config: `PlotProperties`
- methods for converting matplotlib figures into SVG dictionaries

Dependencies: *ampel-interface*, *matplotlib*

# Ampel-plot-browse

provides:
- tools for visualizing plots
- methods for manipulating SVG structures (rescaling, conversions)

Dependencies: *ampel-plot*, *pyvips*, *clipboard*, *pynput*

# Ampel-plot-cli

makes the ampel CLI command `ampel plot` available which allows to fetch and render plots from DB

Dependencies: *ampel-plot*, *ampel-core*

# Ampel-plot-app

A standalone GUI app providing similar functionality to `ampel plot read`
