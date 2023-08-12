from __future__ import annotations

import numpy as np
import pandas as pd

import peaky
import utils
import gui
import graph as gph

import math
import copy
from typing import Callable, AnyStr, Union, Any


# Container class for a pandas DataFrame. Contains additional information such as the name...etc.
# Looks messy cause python doesn't allow overloaded constructors >:(
class Data:
    def __init__(self, data_frame: pd.DataFrame, owner: gui.App, name: AnyStr, freq_ax: AnyStr = None,
                 gtypes: list[AnyStr] = None, no_plot: list[AnyStr] = None):
        assert isinstance(data_frame, pd.DataFrame)
        if freq_ax is None:
            self.data_frame = data_frame
            self.owner = owner
            self.name = name
            self.ax = None
            self.freq_ax = None
            self.temp_gtypes = gtypes
            self.dup_num = 1
            self.gen_info()
        elif freq_ax is not None:
            self.data_frame = data_frame
            self.owner = owner
            self.name = name
            self.freq_ax = freq_ax
            self.ax = freq_ax
            self.temp_gtypes = gtypes
            self.dup_num = 1
            self.graph = gph.Graph(self)
            self.data_frame.sort_values(by=self.freq_ax, inplace=True)
        if no_plot is None:
            self.no_plot = []
        else:
            self.no_plot = no_plot

    def gen_info(self):
        gui.DataInfoSelector(name=self.name, data_columns=self.data_frame.columns, callback=self.fin_setup, is_gen=True)

    def update_info(self):
        gui.DataInfoSelector(name=self.name, data_columns=self.data_frame.columns, callback=self.fin_setup, is_gen=False)

    def add_column(self, name, series):
        self.data_frame[name] = series
        self.graph.column_gtypes[name] = "Line"

    def fin_setup(self, name: AnyStr, ax: AnyStr, is_gen: bool):
        self.name = name
        self.ax = ax
        if is_gen:
            self.freq_ax = ax
            self.owner.data_storage.add_data(name, self)
            self.graph = gph.Graph(self, self.temp_gtypes)
        self.data_frame.sort_values(by=self.freq_ax, inplace=True)

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
        self.owner.data_storage.add_data(self.name + " (mod)", func(df=self.data_frame, x=self.ax, col=col))

    def replicate(self):
        self.owner.data_storage.add_data("*" + self.name, self.data_frame.copy(deep=True), gtypes=self.graph.column_gtypes)

    def merge(self):
        data_list = []
        for data in self.owner.sidebar.dataset_texts:
            if data.dataset != self:
                data_list.append(data.dataset.name)
        if len(data_list) > 0:
            gui.MergeWindow(self.merge_callback, data_list)

    def merge_callback(self, to_merge: Data, combine: bool, threshold: int):
        merge_data = None
        for data in self.owner.sidebar.dataset_texts:
            if data.dataset.name == to_merge:
                merge_data = data.dataset
                break
        for column in merge_data.data_frame.columns:
            if column in self.data_frame.columns and column != merge_data.freq_ax:
                dup_num = 1
                while column + str(dup_num) in self.data_frame.columns:
                    dup_num += 1
                merge_data.data_frame.rename(columns={column: column + str(dup_num)}, inplace=True)
                merge_data.graph.column_gtypes[column + str(dup_num)] = merge_data.graph.column_gtypes[column]
                merge_data.graph.column_gtypes.pop(column)
                self.dup_num += 1
                # gui.MergeConflictWindow(right=self, left=merge_data, callback=self.merge_resolution)
                # return
        # Using 'right_on' and 'left_on' produced unexpected results
        merge_data.data_frame.rename(columns={merge_data.freq_ax: self.freq_ax}, inplace=True)
        self.data_frame = pd.merge(left=self.data_frame, right=merge_data.data_frame, on=self.freq_ax, how='outer')
        self.data_frame.sort_values(by=self.freq_ax, inplace=True)
        merge_data.graph.column_gtypes.pop(merge_data.freq_ax)
        new_gtypes = dict(self.graph.column_gtypes, **merge_data.graph.column_gtypes)
        self.graph.column_gtypes = new_gtypes
        self.owner.data_storage.remove_data(merge_data)

        if combine:
            # For this section, we assume that frequencies are close enough together that intensities between
            # them will be relatively the same.
            to_drop = []
            threshold = threshold / 1000.0  # KHz -> MHz
            self.data_frame.reset_index(drop=True, inplace=True)
            freq_array = self.data_frame[self.freq_ax].to_numpy()

            # How this works:
            # Each index (A) will check 1 in front of itself (B) if there is a value within (threshold) KHz. If it is true,
            # (A) copies the non-Nan values of (B) into itself, and assigns (B) to be deleted. Since there may be
            # more still within the threshold, it keeps (A) the same and searches one ahead again, so while (A) is the
            # same (B) is now the value of one index ahead, and it checks if it's still within (threshold), and
            # copies it if true. If true, then it checks the next up. If false, then starts with the value that was just
            # checked, as that is the next value that is not to be deleted.
            for index in range(0, freq_array.size - 2):
                if abs(freq_array[index + 1] - freq_array[index]) < threshold:
                    rel_index = index  # Saves the value where it checks
                    index += 1  # Have index simulate the value above
                    condition = True  # Why doesn't python have do-while loops??
                    while condition:
                        for column in self.data_frame.columns:
                            if column != self.freq_ax:  # Only for intensities
                                if not pd.isna(self.data_frame[column][index]):  # Make sure that NaN values don't overwrite data
                                    print(self.data_frame[column][index])
                                    self.data_frame[column][rel_index] = self.data_frame[column][index]  # Rewrite current value to previous value
                        to_drop.append(index)
                        index += 1
                        try:  # In case there is matches at the end of the data, we don't want it to check outside the index.
                            condition = (abs(freq_array[index] - freq_array[rel_index]) < threshold)
                        except IndexError:
                            condition = False
            self.data_frame.drop(index=to_drop, inplace=True)

    def merge_resolution(self, merge_data: Data):
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
        self.owner.data_storage.add_data(self.name + "(split)", new_dat, inverse_gtypes)


# Where all the opened datasets are held
class DataStorage:
    def __init__(self, root: gui.App):
        self.root = root

        self.data_list = []
        self.temp_storage = None  # Temporary storage so that the dataset isn't garbage collected accidentally

    def add_data(self, name: AnyStr, data: Union[Data, pd.DataFrame], gtypes: list[AnyStr] = None):
        if isinstance(data,
                      pd.DataFrame):  # If a DataFrame is added, it is passed to a Data constructor to be properly wrapped
            self.temp_storage = Data(name=name, data_frame=data, owner=self.root, gtypes=gtypes)
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
        if data.graph.column_gtypes[column] == "None":
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


def regen_spec(dataset: Data, mod_list: list, line_width: Union[float, int]):
    df = dataset.data_frame
    # Copied from Rebecca Peeble's New Spectrum Generator
    step = line_width / 2.8
    nfreq = pd.DataFrame(math.ceil((df[dataset.freq_ax].cummax() - df[dataset.freq_ax].cummin()) / step),
                         columns=[dataset.freq_ax])
    # Expand resolution
    df = pd.merge(left=df, right=nfreq, how="outer", on=dataset.freq_ax)
    index = 0
    for column in mod_list:
        transint = df[column][index]
        transfreq = df[dataset.freq_ax][index]


def remove_from(on: Data, values_from: Data, threshold: Union[int, float]):
    on.data_frame.reset_index(drop=True, inplace=True)
    # Check to make sure that dataset is a true frequency spectrum
    if len(values_from.data_frame.columns) > 2:
        raise IndexError
    # Find intensity axis of values_from
    value_list = values_from.data_frame.columns.values.tolist()
    value_list.remove(values_from.freq_ax)
    # Eliminate all values that go past frequency range
    vf = values_from.data_frame[(values_from.data_frame[values_from.freq_ax] < on.data_frame[on.freq_ax].max())
                                & (values_from.data_frame[values_from.freq_ax] > on.data_frame[on.freq_ax].min())]
    on_nump = on.data_frame[on.freq_ax].to_numpy()
    from_nump = vf[values_from.freq_ax].to_numpy()
    to_drop = np.zeros(on.data_frame[on.freq_ax].size)
    index = 0
    on_index = 0
    for value in on_nump:
        for value1 in from_nump:
            if value + threshold > value1 > value - threshold:
                to_drop[index] = on_index
                index += 1
                break
                # if value1 > value + threshold:
                #     break
        on_index += 1
    on.owner.data_storage.add_data(name=on.name + " (fitted)", data=on.data_frame.loc[0:(index - 1)])
    on.data_frame.drop(axis=0, labels=to_drop[0:(index - 1)], inplace=True)

