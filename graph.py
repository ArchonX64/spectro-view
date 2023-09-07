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


class GraphCanvas:
    def __init__(self, owner):
        # Back ref
        self.canvas = None
        self.owner = owner

        # Members
        self.figure = plt.Figure(figsize=(12, 5.5), layout='constrained')
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
                self.column_gtypes[column] = "Line"
        else:
            self.column_gtypes = gtypes
        self.xmin, self.xmax, self.ymin, self.ymax = None, None, None, None

    def plot(self, plot: plt.Subplot, is_first: bool = False):
        index = 0
        for column in self.dataset.data_frame.columns:
            if column != self.dataset.freq_ax and column != self.dataset.ax:
                if self.column_gtypes[column] == "None":
                    continue
                if self.column_gtypes[column] == "Line":
                    plot.plot(self.dataset.data_frame[self.dataset.ax],
                              self.dataset.data_frame[column], label=column, color="C" + str(index))
                elif self.column_gtypes[column] == "Scatter":
                    plot.scatter(self.dataset.data_frame[self.dataset.ax],
                                 self.dataset.data_frame[column], label=column, c="C" + str(index))
                elif self.column_gtypes[column] == "Stem":
                    plot.stem(self.dataset.data_frame[self.dataset.ax],
                              self.dataset.data_frame[column], label=column, linefmt="C" + str(index),
                              markerfmt="None")
            index += 1
        plot.set_xlabel(self.dataset.ax)
        if self.dataset.ax == self.dataset.freq_ax:
            plot.set_ylabel("Intensity (V)")
        if not is_first:
            plot.set_xlim(left=self.xmin, right=self.xmax)
            plot.set_ylim(bottom=self.ymin, top=self.ymax)
            plot.legend()
            self.scale(plot)
        if self.is_auto:
            plot.autoscale(True)
            self.is_auto = False
        self.xmin, self.xmax = plot.get_xlim()
        self.ymin, self.ymax = plot.get_ylim()
        return plot

    def plot_3d(self, plot: plt.Subplot, x, y, z, graph_type: AnyStr):
        if graph_type == "Line":
            plot.plot(self.dataset.data_frame[x], self.dataset.data_frame[y], self.dataset.data_frame[z])
        if graph_type == "Scatter":
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

    def scale(self, plot: plt.Subplot):
        plot.set_xlim(left=self.xmin, right=self.xmax)
        plot.set_ylim(bottom=self.ymin, top=self.ymax)

    def set_scale(self, xmin: Number = None, xmax: Number = None, ymin: Number = None, ymax: Number = None, auto: bool = False):
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
