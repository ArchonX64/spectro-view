from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib import use as plt_use
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import data

from typing import Union, AnyStr

plt_use("TkAgg")

Number = Union[float, int]

LINE = 0
SCATTER = 1
STEM = 2
NONE = 3

gtype_from_val = {LINE: "Line", SCATTER: "Scatter", STEM: "Stem", NONE: "None"}
gtype_from_string = {"Line": LINE, "Stem": STEM, "Scatter": SCATTER, "None": NONE}


class GraphCanvas:
    def __init__(self, owner):
        # Back ref
        self.canvas = None
        self.owner = owner

        # Members
        self.figure = plt.Figure(figsize=(12, 8), layout='compressed')
        self.curr_graph = None

        # Customization
        self.figure.get_layout_engine().set(w_pad=0.25, h_pad=0.25)


    def set_canvas(self, canvas):
        self.canvas = canvas

    def graph(self):
        if self.curr_graph is not None:
            self.figure.clear()
            self.curr_graph.plot(plot=self.figure.add_subplot())
            self.canvas.draw()

    def threed_graph(self, x, y, z, gtype: AnyStr):
        if self.curr_graph is not None:
            self.figure.clear()
            self.curr_graph.plot_3d(plot=self.figure.add_subplot(projection="3d"), x=x, y=y, z=z, graph_type=gtype)
            self.canvas.draw()

    def set_graph(self, to_graph: Graph):
        self.curr_graph = to_graph


class Graph:
    def __init__(self, dataset: data.Data, gtypes=None):
        self.dataset = dataset
        self.is_auto = True
        if gtypes is None:
            self.column_gtypes = {}
            for column in dataset.data_frame.columns:
                self.column_gtypes[column] = LINE
        else:
            self.column_gtypes = gtypes

        # Initialize a maximum and minimum for the x components
        self.xmin = self.dataset.data_frame[self.dataset.ax].min()
        self.xmax = self.dataset.data_frame[self.dataset.ax].max()
        self.ymin, self.ymax = None, None

    def plot(self, plot: plt.Subplot):
        color_index = 0  # Allows each plot to be a different color

        if self.is_auto:
            self.reset_x()
            self.ymax, self.ymin = None, None

        # Include only the portions of the spectrum needed to be seen
        cut_set = self.dataset.data_frame[self.dataset.data_frame[self.dataset.ax].between(self.xmin, self.xmax)]

        # Plot each column present in the dataset
        for column in self.dataset.data_frame.columns:
            if column != self.dataset.freq_ax and column != self.dataset.ax and self.column_gtypes[column] != NONE:  # Do not plot frequency axis or x-axis
                if self.column_gtypes[column] == LINE:
                    plot.plot(cut_set[self.dataset.ax], cut_set[column],
                              label=column, color="C" + str(color_index))
                elif self.column_gtypes[column] == SCATTER:
                    plot.scatter(cut_set[self.dataset.ax], cut_set[column],
                                 label=column, c="C" + str(color_index))
                elif self.column_gtypes[column] == STEM:
                    plot.stem(cut_set[self.dataset.ax], cut_set[column],
                              label=column, linefmt="C" + str(color_index), markerfmt="None")
            color_index += 1
        plot.set_xlabel(self.dataset.ax)

        # If None is passed for ymin/max above, the graph will autoscale, and we can obtain the values that matplolib gives
        plot.set_ylim(self.ymin, self.ymax)
        self.ymin, self.ymax = plot.get_ylim()

        # Cutting the spectrum creates inconsistent zooming, so points are placed at the limits
        plot.scatter((self.xmax, self.xmin), (self.ymax, self.ymin))

        # Hide the additional points
        thresh = (self.xmax - self.xmin) * 0.01
        plot.set_xlim(self.xmin + thresh, self.xmax - thresh)

        return plot

    def plot_3d(self, plot: plt.Subplot, x, y, z, graph_type: AnyStr):
        if graph_type == LINE:
            plot.plot(self.dataset.data_frame[x], self.dataset.data_frame[y], self.dataset.data_frame[z])
        if graph_type == SCATTER:
            plot.scatter(self.dataset.data_frame[x], self.dataset.data_frame[y], self.dataset.data_frame[z])
        plot.set_xlabel(x)
        plot.set_ylabel(y)
        plot.set_zlabel(z)
        return plot

    def create_graph(self):
        fig = plt.Figure(figsize=(12, 6))
        self.plot(plot=fig.add_subplot())
        return fig

    def modify_gtypes(self, new_types: list):
        index = 0
        if len(new_types) != len(self.column_gtypes.values()):
            raise ValueError
        for column in self.dataset.data_frame.columns:
            self.column_gtypes[column] = new_types[index]
            index += 1

    def reset_x(self):
        self.xmin = self.dataset.data_frame[self.dataset.ax].min()
        self.xmax = self.dataset.data_frame[self.dataset.ax].max()

    def set_scale(self, xmin: Number = None, xmax: Number = None, ymin: Number = None, ymax: Number = None,
                  auto: bool = False):
        if auto:
            self.is_auto = True
            return
        self.is_auto = False
        if xmin is not None:
            self.xmin = xmin
        if xmax is not None:
            self.xmax = xmax
        if ymin is not None:
            self.ymin = ymin
        if ymax is not None:
            self.ymax = ymax
