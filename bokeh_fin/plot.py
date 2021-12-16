import pandas as pd
import yfinance as yf
from bokeh.layouts import column
from bokeh.models import (
    BooleanFilter,
    ColumnDataSource,
    CDSView,
    HoverTool,
    CrosshairTool,
    NumeralTickFormatter
)
from bokeh.plotting import figure, show


w = 0.5


class plot:
    def __init__(self, stock, data, volume=True):
        self._stock = stock
        self._volume = volume
        self._tools = "pan,xwheel_zoom,box_zoom,zoom_in,zoom_out,reset,save"
        self._linked_crosshair = CrosshairTool(dimensions="both")
        self._grid_line_alpha = 0.3
        NBSP = "\N{NBSP}" * 4
        self._tool_tips = dict(
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
            ],
            formatters={"@Date": "datetime"},
            mode="vline",
        )
        self._p = []
        self._plot(data)

    def _plot(self, data):
        data["index1"] = data.index
        source = ColumnDataSource(data)
        inc = source.data["Close"] > source.data["Open"]
        dec = source.data["Open"] > source.data["Close"]
        view_inc = CDSView(source=source, filters=[BooleanFilter(inc)])
        view_dec = CDSView(source=source, filters=[BooleanFilter(dec)])

        options = dict(x_axis_type="datetime", plot_width=1000)
        major_label_overrides = {
            i: date.strftime("%b %d")
            for i, date in enumerate(pd.to_datetime(source.data["Date"]))
        }
        segment = dict(x0="index1", x1="index1", y0="Low", y1="High", color="black")

        p1 = figure(plot_height=400, title=self._stock, tools=self._tools, **options)
        p1.xaxis.major_label_overrides = major_label_overrides
        p1.grid.grid_line_alpha = self._grid_line_alpha

        p1.segment(
            **segment, source=source
        )

        vbar_options = dict(
            x="index1",
            width=w,
            top="Open",
            bottom="Close",
            line_color="black",
            source=source,
        )

        t1 = p1.vbar(fill_color="green", view=view_inc, **vbar_options)
        t2 = p1.vbar(fill_color="red", view=view_dec, **vbar_options)

        p1.add_tools(
            HoverTool(
                renderers=[t1, t2],
                **self._tool_tips,
            ),
            self._linked_crosshair,
        )
        p1.add_tools(self._linked_crosshair)
        self._p.append(p1)

        if self._volume:
            p2 = figure(x_range=p1.x_range, plot_height=100, **options)
            p2.xaxis.major_label_overrides = major_label_overrides
            p2.grid.grid_line_alpha = self._grid_line_alpha

            p2.segment(
                **segment, source=source
            )

            vbar_options = dict(
                x="index1",
                width=w,
                top="Volume",
                bottom=0,
                line_color="black",
                source=source,
            )

            t1 = p2.vbar(fill_color="green", view=view_inc, **vbar_options)
            t2 = p2.vbar(fill_color="red", view=view_dec, **vbar_options)

            p2.add_tools(
                HoverTool(
                    renderers=[t1, t2],
                    **self._tool_tips,
                ),
                self._linked_crosshair,
            )
            p2.yaxis.formatter = NumeralTickFormatter(format='0.0a')
            self._p.append(p2)
        


    def show(self):
        show(column(self._p))