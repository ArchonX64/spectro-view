from __future__ import annotations

import numpy as np
import pandas as pd
import re

import peaky
import utils
import gui
import graph as gph

import math
import copy
import typing
from typing import Callable, AnyStr, Union, Any


# Container class for a pandas DataFrame. Contains additional information such as the name...etc.
# Looks messy cause python doesn't allow overloaded constructors >:(
class Data:
    def __init__(self, data_frame: pd.DataFrame, owner: gui.App, name: AnyStr = None, freq_ax: AnyStr = None,
                 gtypes: list[AnyStr] = None, no_plot: list[AnyStr] = None):
        assert isinstance(data_frame, pd.DataFrame)
        if name is None and freq_ax is None:
            self.data_frame = data_frame
            self.owner = owner
            self.name = None
            self.ax = None
            self.freq_ax = None
            self.temp_gtypes = gtypes
            self.gen_info()
        elif name is not None and freq_ax is not None:
            self.data_frame = data_frame
            self.owner = owner
            self.name = name
            self.freq_ax = freq_ax
            self.ax = freq_ax
            self.temp_gtypes = gtypes
            self.graph = gph.Graph(self)
        if no_plot is None:
            self.no_plot = []
        else:
            self.no_plot = no_plot

    def gen_info(self):
        gui.DataInfoSelector(data_columns=self.data_frame.columns, callback=self.fin_setup, is_gen=True)

    def update_info(self):
        gui.DataInfoSelector(data_columns=self.data_frame.columns, callback=self.fin_setup, is_gen=False)

    def add_column(self, name, series):
        self.data_frame[name] = series
        self.graph.column_gtypes[name] = "Line"

    def fin_setup(self, name: AnyStr, ax: AnyStr, is_gen: bool):
        self.name = name
        self.ax = ax
        if is_gen:
            self.freq_ax = ax
            self.owner.data_storage.add_data(self)
            self.graph = gph.Graph(self, self.temp_gtypes)

    def remove_data(self, value: list[Any], axis, whole_row: bool):
        length = len(value)
        if length == 2:
            left = self.data_frame[axis]
            if value[1][0] == "$":
                right = self.data_frame[value[1].replace("$", "")]
            else:
                if self.data_frame[axis].dtype == "int64":
                    right = int(value[1])
                elif self.data_frame[axis].dtype == "float64":
                    right = float(value[1])
                else:
                    raise ValueError
        else:
            if value[0][0] == "$":
                left = self.data_frame[value[0].replace("$", "")]
            else:
                if self.data_frame[axis].dtypes == "int64":
                    left = int(value[0])
                elif self.data_frame[axis].dtypes == "float64":
                    left = float(value[0])
                else:
                    raise ValueError
            if value[2][0] == "$":
                right = self.data_frame[value[0].replace("$", "")]
            else:
                if self.data_frame[axis].dtypes == "int64":
                    right = int(value[2])
                elif self.data_frame[axis].dtypes == "float64":
                    right = float(value[2])
                else:
                    raise ValueError

        index = 0 if length == 2 else 1
        if not whole_row:
            if value[index] == "<":
                self.data_frame[axis] = self.data_frame[axis][left > right]
            elif value[index] == ">":
                self.data_frame[axis] = self.data_frame[axis][left < right]
            else:
                raise ValueError
        else:
            if value[index] == "<":
                self.data_frame = self.data_frame[left > right]
            elif value[index] == ">":
                self.data_frame = self.data_frame[left < right]
            else:
                raise ValueError

    def modify_data(self, column, operator: AnyStr, values: list):
        if len(values) == 1:
            if operator == "*":
                self.data_frame[column] = self.data_frame[column].apply(func=lambda x: x * values[0])
            elif operator == "/":
                self.data_frame[column] = self.data_frame[column].apply(func=lambda x: x / values[0])
            elif operator == "^":
                self.data_frame[column] = self.data_frame[column].apply(func=lambda x: math.pow(x, values[0]))
            elif operator == "log":
                self.data_frame[column] = self.data_frame[column].apply(func=lambda x: math.log(x, values[0]))
        else:
            raise ValueError

    def drop_column(self, column):
        self.data_frame.drop(columns=column, inplace=True)
        self.graph.column_gtypes.pop(column)

    # === IMPORTANT ===
    # The external function being called NEEDS TO
    # - Output a new DataFrame
    # - Have arguments for the target DataFrame, the x-axis, and target column
    def extern_modify(self, func: Callable, col):
        self.owner.data_storage.add_data(func(df=self.data_frame, x=self.ax, col=col))

    def replicate(self):
        self.owner.data_storage.add_data(self.data_frame.copy(deep=True), gtypes=self.graph.column_gtypes)

    def merge(self):
        data_list = []
        for data in self.owner.sidebar.dataset_texts:
            if data.dataset != self:
                data_list.append(data.dataset.name)
        if len(data_list) > 0:
            gui.MergeWindow(self.merge_callback, data_list)

    def merge_callback(self, to_merge: Data):
        merge_data = None
        for data in self.owner.sidebar.dataset_texts:
            if data.dataset.name == to_merge:
                merge_data = data.dataset
                break
        for column in merge_data.data_frame.columns:
            if column in self.data_frame.columns and column != merge_data.freq_ax:
                gui.MergeConflictWindow(self, merge_data, self.merge_callback)
                return
        # Using 'right_on' and 'left_on' produced unexpected results
        merge_data.data_frame.rename(columns={merge_data.freq_ax: self.freq_ax}, inplace=True)
        self.data_frame = pd.merge(left=self.data_frame, right=merge_data.data_frame, on=self.freq_ax, how='outer')
        merge_data.graph.column_gtypes.pop(merge_data.freq_ax)
        new_gtypes = dict(self.graph.column_gtypes, **merge_data.graph.column_gtypes)
        self.graph.column_gtypes = new_gtypes
        self.owner.data_storage.remove_data(merge_data)

    def split(self):
        cols = self.data_frame.columns.values.tolist()
        cols.remove(self.freq_ax)
        gui.SplitWindow(columns=cols, callback=self.split_callback)

    def split_callback(self, column_list: list):
        self.ax = self.freq_ax
        new_dat = self.data_frame.copy(deep=True)
        self.data_frame.drop(columns=column_list, inplace=True)
        inverse_remove = []
        for value in self.data_frame.columns:
            if value not in column_list and value != self.freq_ax:
                inverse_remove.append(value)
        new_dat.drop(columns=inverse_remove, inplace=True)
        inverse_gtypes = copy.deepcopy(self.graph.column_gtypes)
        for value in column_list:
            self.graph.column_gtypes.pop(value)
        for value in inverse_remove:
            inverse_gtypes.pop(value)
        self.owner.data_storage.add_data(new_dat, inverse_gtypes)


# Where all the opened datasets are held
class DataStorage:
    def __init__(self, root: gui.App):
        self.root = root

        self.data_list = []
        self.temp_storage = None  # Temporary storage so that the dataset isn't garbage collected accidentally

    def add_data(self, data: Union[Data, pd.DataFrame], gtypes: list[AnyStr] = None):
        if isinstance(data,
                      pd.DataFrame):  # If a DataFrame is added, it is passed to a Data constructor to be properly wrapped
            self.temp_storage = Data(data_frame=data, owner=self.root, gtypes=gtypes)
            return
        elif isinstance(data, Data):
            self.data_list.append(data)
            self.root.sidebar.update_data()
        else:
            raise utils.InvalidTypeException

    def remove_data(self, data):
        self.data_list.remove(data)
        self.root.sidebar.update_data()


def peak_pick(data: Data, name: AnyStr, res: float, inten_min: float, inten_max: float):
    data_frame = data.data_frame
    new_data = pd.DataFrame()  # Create new dataframe
    is_new = True

    # Current dataframe is divided into frequency/amplitude pairs in order to be run through peaky
    for column in data_frame.columns:  # Copy each column into the new dataframe
        if column == data.freq_ax:  # Don't create dataframe with double frequency axes
            continue
        partial_frame = data_frame.copy(deep=True)  # Copy dataframe into new frame
        to_drop = []
        for temp_column in data_frame.columns:  # Find all columns that need to be dropped
            if temp_column != data.freq_ax and temp_column != column:
                to_drop.append(temp_column)
        partial_frame.drop(columns=to_drop, inplace=True)  # Drop specified columns

        # Convert partial frame into numpy array, run through peaky
        nump = partial_frame.to_numpy(copy=True)
        res_spect = peaky.cubic_spline(nump, res)
        (peaks, freq_low, freq_high) = peaky.peakpicker(res_spect, inten_min, inten_max)

        # Convert new peaked data back into a dataframe
        temp_frame = pd.DataFrame(peaks, columns=[data.freq_ax, column])
        if is_new:
            new_data = pd.concat(objs=[new_data, temp_frame], axis=1)
            new_data.columns = [data.freq_ax, column]
            is_new = False
        else:
            new_data = new_data.merge(right=temp_frame, on=data.freq_ax, how="outer")
    return Data(data_frame=new_data, owner=data.owner, name=name, freq_ax=data.freq_ax)


def calc_ratios(dataset: Data, against):
    df = dataset.data_frame
    columns = df.columns.values.tolist()
    columns.remove(against)
    columns.remove(dataset.freq_ax)
    column_dict = {}
    for column in columns:
        name = column + "/" + against
        dataset.add_column(name=name, series=df[column] / df[against])
        dataset.graph.column_gtypes[name] = "None"
        column_dict[column] = name
    return column_dict
