<img align="left" src="https://user-images.githubusercontent.com/17532220/213290006-0ee9291e-9018-4bc9-aae9-5bcae3835d90.png" width="150" height="150"/>
<br>

# AMPEL-plot
<br><br>



## Ampel-plot

provides:
- a standardized document structure called `SVGRecord` for saving plots into the ampel DB
- a model for configuring plot properties in unit config: `PlotProperties`
- methods for converting matplotlib figures into SVG dictionaries

Dependencies: *ampel-interface*, *matplotlib*

## Ampel-plot-browse

provides:
- tools for loading plots from DB (either using queries or by monitoring changes to given databases)
- a way to automatically load plots from clipboard (handy in combination with Robot3T for example)
- options for visualizing plots, in particular, plots can be stacked into a HTML structure displayable by web browsers
- methods for manipulating SVG structures (rescaling, format conversions)

Dependencies: *ampel-plot*, *pyvips*, *clipboard*, *pynput*, , *pygments*

## Ampel-plot-cli

makes the ampel CLI command `ampel plot` available which allows to fetch and render plots from DB

Dependencies: *ampel-plot*, *ampel-core*

## Ampel-plot-app

A standalone GUI app providing similar functionality to `ampel plot clipboard`. It needs an update.
