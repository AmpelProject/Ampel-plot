# Ampel-plot

provides:
- a standardized document structure called `SVGRecord` for saving plots into the ampel DB
- a model for configuring plot properties in unit config: `PlotProperties`
- methods for converting matplotlib figures into SVG dictionaries

Dependencies: *ampel-interface*, *matplotlib*

# Ampel-plot-browse

provides:
- tools for browsing and visualizing plots directly from the DB
- methods for manipulating SVG structures (rescaling, conversions)

Dependencies: *ampel-plot*, *pyvips*, *clipboard*, *pynput*

# Ampel-plot-cli

makes the ampel CLI command `ampel plot` available

Dependencies: *ampel-plot*, *ampel-core*

# Ampel-plot-app

provides a standalone GUI app providing similar functionality to `ampel plot read` 
