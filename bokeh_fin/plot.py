import pandas as pd
import yfinance as yf
from bokeh.layouts import column
from bokeh.models import (
    BooleanFilter,
    ColumnDataSource,
    CDSView,
    HoverTool,
    CrosshairTool,
    NumeralTickFormatter,
)
from bokeh.plotting import figure, show


w = 0.5


class plot:
    def __init__(self, stock, data, kind="candlestick", volume=True, addplot=None):
        self._stock = stock
        self._kind = kind
        self._volume = volume
        self._addplot = addplot
        self._tools = "pan,xwheel_zoom,box_zoom,zoom_in,zoom_out,reset,save"
        self._linked_crosshair = CrosshairTool(dimensions="both")
        self._grid_line_alpha = 0.3
        self._p = []
        self._process_data(data)
        self._plot()
    
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
        inc = self._source.data["Close"] > self._source.data["Open"]
        dec = self._source.data["Open"] > self._source.data["Close"]
        self._view_inc = CDSView(source=self._source, filters=[BooleanFilter(inc)])
        self._view_dec = CDSView(source=self._source, filters=[BooleanFilter(dec)])
        self._view = CDSView(source=self._source)
        self._options = dict(x_axis_type="datetime", plot_width=1000)
        self._major_label_overrides = {
            i: date.strftime("%b %d")
            for i, date in enumerate(pd.to_datetime(self._source.data["Date"]))
        }
        self._segment = dict(
            x0="index1", x1="index1", y0="Low", y1="High", color="black"
        )

    def _volume_plot(self):
        if self._volume:
            p = figure(x_range=self._p[0].x_range, plot_height=100, **self._options)
            p.xaxis.major_label_overrides = self._major_label_overrides
            p.grid.grid_line_alpha = self._grid_line_alpha

            p.segment(**self._segment, source=self._source)

            vbar_options = dict(
                x="index1",
                width=w,
                top="Volume",
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
    
    def _add_mainplot(self, p):
        if not self._addplot:
            return []
        ind_tooltip = []
        for ind in self._addplot:
            if ind['kind'] == 'line':
                p.line(x="index1", y=ind['column'], source=self._source)
                ind_tooltip.append((ind['column'], f"@{ind['column']}"))
        return ind_tooltip


    def _candlestick_plot(self):
        p = figure(
            plot_height=400, title=self._stock, tools=self._tools, **self._options
        )
        p.xaxis.major_label_overrides = self._major_label_overrides
        p.grid.grid_line_alpha = self._grid_line_alpha

        p.segment(**self._segment, source=self._source)

        vbar_options = dict(
            x="index1",
            width=w,
            top="Open",
            bottom="Close",
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
        self._p.append(p)

    def _line_plot(self):
        p = figure(
            plot_height=400, title=self._stock, tools=self._tools, **self._options
        )
        p.xaxis.major_label_overrides = self._major_label_overrides
        p.grid.grid_line_alpha = self._grid_line_alpha

        l = p.line(x="index1", y="Close", source=self._source)

        ind_tooltip = self._add_mainplot(p)

        p.add_tools(
            HoverTool(
                renderers=[l],
                **self._format_tooltips(ind_tooltip),
            ),
            self._linked_crosshair,
        )
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
