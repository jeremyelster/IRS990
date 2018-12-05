from bokeh.io import show
from bokeh.models import LogColorMapper, ColorBar, FixedTicker
from bokeh.palettes import Viridis6 as palette
from bokeh.plotting import figure
from bokeh.sampledata.us_states import data as states
from bokeh.models import ColumnDataSource
from bokeh.palettes import Spectral6, Spectral10
from bokeh.transform import factor_cmap
from bokeh.models import HoverTool
import numpy as np
from bokeh.models import Span, Label, NumeralTickFormatter, CategoricalTickFormatter


def choropleth(df):
    palette.reverse()

    if "HI" in states:
        del states["HI"]
        del states["AK"]

    state_xs = [states[code]["lons"] for code in states]
    state_ys = [states[code]["lats"] for code in states]
    state_names = [name for name in states]
    state_rates = [df[state] if state in df else 0 for state in states]

    color_mapper = LogColorMapper(
        palette="Viridis256", low=0, high=max(state_rates))

    data = dict(
        x=state_xs,
        y=state_ys,
        name=state_names,
        rate=state_rates,
    )

    TOOLS = "pan,wheel_zoom,reset,hover,save"

    p = figure(
        width=850, height=500,
        title="Location of Charities in Forward Investivation", tools=TOOLS,
        x_axis_location=None, y_axis_location=None,
        tooltips=[
            ("State", "@name"), ("Number of Charities", "@rate")
        ])
    p.grid.grid_line_color = None
    p.hover.point_policy = "follow_mouse"

    p.patches('x', 'y', source=data,
              fill_color={'field': 'rate', 'transform': color_mapper},
              fill_alpha=0.7, line_color="black", line_width=0.5)

    color_bar = ColorBar(
        color_mapper=color_mapper,
        ticker=FixedTicker(
            ticks=[1, 10, 20, 50, 100, 500]),
        label_standoff=8, border_line_color=None, location=(0, 0))

    p.add_layout(color_bar, 'right')
    show(p)


def taxYearHist(df):

    years = [str(y) for y in df.index]
    counts = list(df.values)

    source = ColumnDataSource(data=dict(year=years, counts=counts))

    p = figure(
        x_range=years, plot_height=350,
        toolbar_location=None, title="990 Filings by Year",
        tooltips=[
            ("Year", "@year"), ("Number of Filings", "@counts")
        ])
    p.grid.grid_line_color = None
    p.hover.point_policy = "follow_mouse"
    p.vbar(
        x='year', top='counts', width=0.9, source=source,
        legend="year", line_color='white',
        fill_color=factor_cmap("year", palette=Spectral6, factors=years))

    p.xgrid.grid_line_color = None
    p.y_range.start = 0
    p.y_range.end = 2000
    p.legend.orientation = "vertical"
    p.legend.location = "center_left"

    show(p)


def scatterplot(df, y_col, x_col, log=True):

    if log:
        y_col_val = y_col + "Log"
        x_col_val = x_col + "Log"
    else:
        y_col_val = y_col
        x_col_val = x_col

    plot = figure(
        title=f"{y_col_val} v {x_col_val}",
        width=850, height=500,
    )

    df_tmp = df.copy()
    top_7_ntee = df_tmp["NTEECommonCode"].value_counts()[0:7].index
    df_tmp.loc[
        ~df_tmp["NTEECommonCode"].isin(top_7_ntee), "NTEECommonCode"] = "Other"
    df_tmp["NTEECommonCode"] = df_tmp["NTEECommonCode"]\
        .apply(lambda x: str(x)[0:40])
    df_tmp["OrganizationName"] = df_tmp["OrganizationName"]\
        .apply(lambda x: str(x)[0:40])
    org_types = [str(org) for org in set(df_tmp["NTEECommonCode"])]

    source = ColumnDataSource(data=df_tmp)

    plot.circle(
        x=x_col_val, y=y_col_val, source=source,
        size=5, legend="NTEECommonCode",
        color=factor_cmap(
            "NTEECommonCode", palette=Spectral10, factors=org_types))

    # Hover tool with vline mode
    tooltips = [
        ('Year', '@TaxYr'),
        ('OrganizationName', '@OrganizationName'),
        (y_col_val, '@' + y_col_val),
        (x_col_val, '@' + x_col_val)]

    if log:
        tooltips = tooltips + [(y_col, '@' + y_col), (x_col, '@' + x_col)]

    # Configure a renderer to be used upon hover
    hover_glyph = plot.circle(
        x=x_col_val, y=y_col_val, source=source,
        size=10, alpha=0,
        hover_fill_color='black', hover_alpha=0.1)

    max_val = max(max(df_tmp[x_col_val]), max(df_tmp[y_col_val])) * 1.1
    plot.line([0, max_val], [0, max_val])
    # Add the HoverTool to the figure
    plot.add_tools(HoverTool(tooltips=tooltips, renderers=[hover_glyph]))
    plot.xaxis.axis_label = x_col_val
    plot.yaxis.axis_label = y_col_val
    plot.legend.orientation = "vertical"
    plot.legend.location = "top_left"
    plot.title.align = "center"
    show(plot)


def officerPayPercentHist(df, col, n_bins=100):
    values = df[df[col] > 0][col]

    vals = sorted(values)
    bins = np.linspace(0, 1, n_bins + 1)
    hist, edges = np.histogram(vals, density=True, bins=bins)
    hist = hist / n_bins

    cdf = np.cumsum(hist)
    ecdf = vals
    y = np.arange(1, len(ecdf) + 1) / len(ecdf)

    p = figure(
        title="Officer Pay as Percentage of Total Expenses", tools='',
        width=850, height=500)
    p.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:],
           fill_color="navy", line_color="white", alpha=0.5)


    mean_span = Span(
        location=np.mean(vals),
        dimension='height', line_color='red',
        line_dash='dashed', line_width=3)
    p.add_layout(mean_span)
    mean_label = Label(
        x=400, y=.09, x_units='screen',
        text='-- Mean Officer Pay Percentage: ' + str(round(100.0 * np.mean(vals), 2)) + '%', render_mode='css',
      background_fill_color='white', background_fill_alpha=1.0,
      text_color="red")
    p.add_layout(mean_label)
    median_span = Span(
        location=np.median(vals),
        dimension='height', line_color='blue',
        line_dash='dashed', line_width=3)
    p.add_layout(median_span)
    median_label = Label(
        x=400, y=.1, x_units='screen',
        text='-- Median Officer Pay Percentage: ' + str(round(100.0 * np.median(vals), 2)) + '%', render_mode='css',
      background_fill_color='white', background_fill_alpha=1.0,
      text_color="blue")
    p.add_layout(median_label)
    #legend = Legend(
    #    items=[
    #        LegendItem(label="Mean Officer Pay Percentage"),
    #        LegendItem(label="Median Officer Pay Percentage")])
    #p.add_layout(legend)



    #p.line(x, pdf, line_color="#ff8888", line_width=4, alpha=0.7, legend="PDF")
    #p.circle(ecdf, y, color="#ff8888", size=5, alpha=0.7, legend="ECDF")
    #p.line(edges[1:], cdf, line_color="orange", line_width=2, alpha=0.7, legend="CDF")

    # Axes
    p.xaxis[0].formatter = NumeralTickFormatter(format="0.0%")


    show(p)


def salaryBinHist(df):

    salary = [str(y) for y in df.index]
    counts = list(df.values)
    labels = [
        "Less than $30,000", "$30,001 to $60,000", "$60,001 to $100,000",
        "$100,001 to $150,000", "$150,001 to $250,000", "$250,001 to $500,000",
        "More than $500,000"]
    source = ColumnDataSource(data=dict(salary=salary, counts=counts, labels=labels))

    p = figure(
        x_range=salary, width=850, height=500,
        toolbar_location=None, title="Salary by Range",
        tooltips=[
            ("Salary", "@salary"), ("Number of Filings", "@counts")
        ])
    p.grid.grid_line_color = None
    p.hover.point_policy = "follow_mouse"
    p.vbar(
        x='salary', top='counts', width=0.9, source=source,
        legend="labels", line_color='white',
        fill_color=factor_cmap("salary", palette=Spectral10, factors=salary))
    #p.xaxis.ticker = CategoricalTickFormatter(t=labels)
    p.xgrid.grid_line_color = None
    p.y_range.start = 0
    p.y_range.end = max(counts) * 1.1
    p.legend.orientation = "vertical"
    p.legend.location = "top_right"

    show(p)
