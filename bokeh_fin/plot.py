import pandas as pd
import yfinance as yf
from bokeh.layouts import column
from bokeh.models import (
    BooleanFilter,
    CustomJS,
    ColumnDataSource,
    CDSView,
    HoverTool,
    CrosshairTool,
    NumeralTickFormatter,
)
from bokeh.plotting import figure, show
import os

w = 0.5

with open(os.path.join(os.path.dirname(__file__), 'autoscale_cb.js'),
          encoding='utf-8') as _f:
    _AUTOSCALE_JS_CALLBACK = _f.read()

class plot:
    def __init__(self, 
                stock, 
                data, 
                date='Date',
                open='Open', 
                high="High", 
                low="Low", 
                close="Close", 
                volume="Volume", 
                kind="candlestick", 
                show_volume=True, 
                addplot=None,
                main_plot_height=400,
                volume_plot_height=100):
        self._stock = stock
        self._date = date
        self._open = open
        self._high = high
        self._low = low
        self._close = close
        self._volume = volume
        self._kind = kind
        self._show_volume = show_volume
        self._addplot = addplot
        self._main_plot_height = main_plot_height
        self._volume_plot_height = volume_plot_height
        self._tools = "pan,xwheel_zoom,box_zoom,zoom_in,zoom_out,reset,save"
        self._linked_crosshair = CrosshairTool(dimensions="both")
        self._grid_line_alpha = 0.3
        self._p = []
        self._process_data(data)
        self._plot()
    
    def add_subplot(self, subplot):
        p = figure(x_range=self._p[0].x_range, plot_height=200, **self._options)
        p.xaxis.major_label_overrides = self._major_label_overrides
        p.grid.grid_line_alpha = self._grid_line_alpha

        ind_line = []
        ind_tooltip = []
        for ind in subplot:
            if ind['kind'] == 'line':
                l = p.line(x="index1",
                        y=ind['column'],source=self._source, **self._format_style('line', **ind))
                ind_line.append(l)
                ind_tooltip.append((ind['column'], f"@{ind['column']}"))
            elif ind['kind'] == 'scatter':
                s = p.scatter(x="index1", y=ind['column'], source=self._source, **self._format_style('scatter', **ind))
                ind_line.append(s)
                ind_tooltip.append((ind['column'], f"@{ind['column']}"))
            else:
                raise ValueError("Other kinds are not supported.")
        p.add_tools(
            HoverTool(
                renderers=ind_line,
                point_policy="follow_mouse",
                tooltips=ind_tooltip,
                mode="vline")
            )
        p.add_tools(self._linked_crosshair)
        self._p.append(p)
    
    def _format_tooltips(self, custom):
        NBSP = "\N{NBSP}" * 4
        tool_tips = dict(
            point_policy="follow_mouse",
            tooltips=[
                ("Date", "@Date{%F}"),
                (
                    "OHLC",
                    NBSP.join(
                        (
                            "@Open{0,0.00}",
                            "@High{0,0.00}",
                            "@Low{0,0.00}",
                            "@Close{0,0.00}",
                        )
                    ),
                ),
                ("Volume", "@Volume{0,0.0[0000]}"),
            ] + custom,
            formatters={"@Date": "datetime"},
            mode="vline",
        )
        return tool_tips

    def _process_data(self, data):
        data["index1"] = data.index
        self._source = ColumnDataSource(data)
        inc = self._source.data[self._close] > self._source.data[self._open]
        dec = self._source.data[self._open] > self._source.data[self._close]
        self._view_inc = CDSView(source=self._source, filters=[BooleanFilter(inc)])
        self._view_dec = CDSView(source=self._source, filters=[BooleanFilter(dec)])
        self._view = CDSView(source=self._source)
        self._options = dict(x_axis_type="datetime", plot_width=1000)
        self._major_label_overrides = {
            i: date.strftime("%b %d")
            for i, date in enumerate(pd.to_datetime(self._source.data[self._date]))
        }
        self._segment = dict(
            x0="index1", x1="index1", y0=self._low, y1=self._high, color="black"
        )

    def _volume_plot(self):
        if self._show_volume:
            p = figure(x_range=self._p[0].x_range, plot_height=self._volume_plot_height, **self._options)
            p.xaxis.major_label_overrides = self._major_label_overrides
            p.grid.grid_line_alpha = self._grid_line_alpha

            vbar_options = dict(
                x="index1",
                width=w,
                top=self._volume,
                bottom=0,
                line_color="black",
                source=self._source,
            )

            t1 = p.vbar(fill_color="green", view=self._view_inc, **vbar_options)
            t2 = p.vbar(fill_color="red", view=self._view_dec, **vbar_options)

            p.add_tools(
                HoverTool(
                    renderers=[t1, t2],
                    **self._format_tooltips([]),
                )
            )
            p.add_tools(self._linked_crosshair)

            p.yaxis.formatter = NumeralTickFormatter(format="0.0a")
            self._p.append(p)

    def _format_style(self, plot, **kwargs):
        styles = {}
        if plot == 'line':
            styles['color'] = kwargs['color'] if 'color' in kwargs else 'black'
            styles['line_width'] = kwargs['line_width'] if 'line_width' in kwargs else 1
            styles['alpha'] = kwargs['alpha'] if 'alpha' in kwargs else 1
        elif plot == 'scatter':
            styles['color'] = kwargs['color'] if 'color' in kwargs else 'black'
            styles['size'] = kwargs['size'] if 'size' in kwargs else 3
            styles['alpha'] = kwargs['alpha'] if 'alpha' in kwargs else 1
            styles['marker'] = kwargs['marker'] if 'marker' in kwargs else 'dot'
        
        return styles

    
    def _add_mainplot(self, p):
        if not self._addplot:
            return []
        ind_tooltip = []
        for ind in self._addplot:
            if ind['kind'] == 'line':
                p.line(x="index1",
                        y=ind['column'],source=self._source, **self._format_style('line', **ind))
            elif ind['kind'] == 'scatter':
                p.scatter(x="index1", y=ind['column'], source=self._source, **self._format_style('scatter', **ind))
            else:
                raise ValueError("Other kinds are not supported.")
            ind_tooltip.append((ind['column'], f"@{ind['column']}"))
            
        return ind_tooltip
    
    def _auto_scale(self, p):
        custom_js_args = dict(ohlc_range=p.y_range,
                          source=self._source)
        p.x_range.js_on_change('end', CustomJS(args=custom_js_args,
                                                  code=_AUTOSCALE_JS_CALLBACK))
        return p
    
    def _candlestick_plot(self):
        p = figure(
            plot_height=self._main_plot_height, title=self._stock, tools=self._tools, **self._options
        )
        p.xaxis.major_label_overrides = self._major_label_overrides
        p.grid.grid_line_alpha = self._grid_line_alpha

        p.segment(**self._segment, source=self._source)

        vbar_options = dict(
            x="index1",
            width=w,
            top=self._open,
            bottom=self._close,
            line_color="black",
            source=self._source,
        )

        t1 = p.vbar(fill_color="green", view=self._view_inc, **vbar_options)
        t2 = p.vbar(fill_color="red", view=self._view_dec, **vbar_options)

        ind_tooltip = self._add_mainplot(p)

        p.add_tools(
            HoverTool(
                renderers=[t1,t2],
                **self._format_tooltips(ind_tooltip),
            ),
            self._linked_crosshair,
        )
        self._auto_scale(p)
        self._p.append(p)

    def _line_plot(self):
        p = figure(
            plot_height=self._main_plot_height, title=self._stock, tools=self._tools, **self._options
        )
        p.xaxis.major_label_overrides = self._major_label_overrides
        p.grid.grid_line_alpha = self._grid_line_alpha

        l = p.line(x="index1", y=self._close, source=self._source)

        ind_tooltip = self._add_mainplot(p)

        p.add_tools(
            HoverTool(
                renderers=[l],
                **self._format_tooltips(ind_tooltip),
            ),
            self._linked_crosshair,
        )
        self._auto_scale(p)
        self._p.append(p)

    def _plot(self):
        if self._kind == "candlestick":
            self._candlestick_plot()
        elif self._kind == "line":
            self._line_plot()
        else:
            raise ValueError("Please choose from the following: candlestock, line")

        self._volume_plot()

    def show(self):
        show(column(self._p))
