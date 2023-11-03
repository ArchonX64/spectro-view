from __future__ import annotations

import numpy as np
import pandas as pd

import peaky
import gui
import graph as gph

import math
import copy
from typing import Callable, AnyStr, Union, Any


# Container class for a pandas DataFrame, with additional information relative to this app's functions
class Data:
    def __init__(self, data_frame: pd.DataFrame, owner: gui.App, name: str, freq_ax: str, x_ax: str = None,
                 gtypes: dict = None, is_ratio: bool = False):
        self.data_frame = data_frame
        self.owner = owner
        self.name = name
        self.freq_ax = freq_ax
        self.gtypes = gtypes
        if x_ax is None:
            self.ax = freq_ax
        else:
            self.ax = x_ax
        self.graph = gph.Graph(self, gtypes)
        self.is_ratio = is_ratio

    def add_column(self, name, series) -> None:
        self.data_frame[name] = series
        self.graph.column_gtypes[name] = "Line"

    def copy(self) -> Data:
        return Data(name=self.name + "*", data_frame=self.data_frame.copy(True), freq_ax=self.freq_ax, gtypes=self.graph.column_gtypes.copy(),
                    owner=self.owner, x_ax=self.ax)

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
        self.owner.data_storage.add_data(name=self.name + " (mod)", data=func(df=self.data_frame, x=self.ax, col=col))

    def replicate(self):
        self.owner.data_storage.add_data(self.copy())

    def merge(self):
        data_list = []
        for data in self.owner.sidebar.dataset_texts:
            if data.dataset != self:
                data_list.append(data.dataset.name)
        if len(data_list) > 0:
            gui.MergeWindow(self.merge_callback, self.owner, self)

    def merge_callback(self, to_merge: str, combine: bool, threshold: int):
        for data in self.owner.sidebar.dataset_texts:
            if data.dataset.name == to_merge:
                to_merge_dat = data.dataset
                break

        new_m = to_merge_dat.data_frame.copy(deep=True)
        new_m.rename(columns={to_merge_dat.freq_ax: self.freq_ax}, inplace=True)
        for column_s in self.data_frame.columns:
            for column_m in to_merge_dat.data_frame.columns:
                if column_s == column_m and column_s != self.freq_ax and column_m != to_merge_dat.freq_ax:
                    new_m.rename(columns={column_m: column_m + " (" + to_merge_dat.name + ")"},
                                 inplace=True)
                    to_merge_dat.rename(columns={column_m: column_m + " (" + to_merge_dat.name + ")"},
                                        inplace=True)
        merged = pd.merge(on=self.freq_ax, left=self.data_frame, right=new_m, how="outer")

        already_found = []
        to_rename = {}
        for column in merged:
            if column in already_found:
                to_rename[column] = column + "*"
            else:
                already_found.append(column)
        merged.rename(mapper=to_rename)

        new_gtypes = {}
        for column in merged.columns:
            new_gtypes[column] = gph.LINE

        merged_data = Data(data_frame=merged, owner=self.owner, name=self.name + " + " + to_merge_dat.name,
                           freq_ax=self.freq_ax, gtypes=new_gtypes, x_ax=self.ax)
        self.owner.data_storage.add_data(data=merged_data)

        if combine:
            # For this section, we assume that frequencies are close enough together that intensities between
            # them will be relatively the same.
            to_drop = []
            threshold = threshold / 1000.0  # KHz -> MHz
            merged_data.data_frame.reset_index(drop=True, inplace=True)
            freq_array = merged_data.data_frame[merged_data.freq_ax].to_numpy()

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
                        for column in merged_data.data_frame.columns:
                            if column != merged_data.freq_ax:  # Only for intensities
                                if not pd.isna(merged_data.data_frame[column][index]):  # Make sure that NaN values don't overwrite data
                                    merged_data.data_frame[column][rel_index] = merged_data.data_frame[column][index]  # Rewrite current value to previous value
                        to_drop.append(index)
                        index += 1
                        try:  # In case there is matches at the end of the data, we don't want it to check outside the index.
                            condition = (abs(freq_array[index] - freq_array[rel_index]) < threshold)
                        except IndexError:
                            condition = False
            merged_data.data_frame.drop(index=to_drop, inplace=True)

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
        self.owner.data_storage.add_data(name=self.name + "(split)", data=new_dat, gtypes=inverse_gtypes)


# Where all the opened datasets are held
class DataStorage:
    def __init__(self, root: gui.App):
        self.root = root
        self.data_list = []
        self.temp_storage = None  # Temporary storage so that the dataset isn't garbage collected accidentally

    def add_data(self, data: Data):
        self.data_list.append(data)
        self.root.sidebar.update_data()

    def remove_data(self, data):
        self.data_list.remove(data)
        self.root.sidebar.update_data()


def peak_pick(data: Data, name: AnyStr, res: float, inten_min: float, inten_max: float) -> Data:
    data_frame = data.data_frame
    new_data = pd.DataFrame()  # Create new dataframe
    is_new = True

    # Current dataframe is divided into frequency/amplitude pairs in order to be run through peaky
    for column in data_frame.columns:  # Copy each column into the new dataframe
        if column == data.freq_ax:  # Don't create dataframe with double frequency axes
            continue
        if data.graph.column_gtypes[column] == gph.NONE:  # Allows control over peak pick on certain axes
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


def calc_ratios(dataset: Data, against):  # against is the column that the other columns will be divided by
    df = dataset.data_frame
    columns = df.columns.values.tolist()

    columns.remove(against)  # Prevent creating a ratio of against with against
    columns.remove(dataset.freq_ax)  # Prevent creating ratios with the frequency axis

    column_dict = {}
    for column in columns:
        name = column + "/" + against
        dataset.add_column(name=name, series=df[column] / df[against])
        dataset.graph.column_gtypes[name] = gph.NONE
        column_dict[column] = name
    return column_dict  # Returns a dictionary with each column and corresponding ratio column


def remove_from(on: Data, values_from: Data, threshold: Union[int, float], return_removed: bool, add_back: bool):
    on.data_frame.reset_index(drop=True, inplace=True)
    threshold = threshold / 1000.0
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
        on_index += 1
    removed = on.copy()
    removed.data_frame = on.data_frame.on.data_frame.loc[to_drop[0:index]]
    removed.name = on.name + " (removed)"

    new_on = on.copy()
    new_on.data_frame = on.data_frame.drop(axis=0, labels=to_drop[0:index])
    new_on.name = on.name + " - " + values_from.name

    on.owner.data_storage.add_data(new_on)
    if add_back:
        def renamer(name):
            if name != removed.freq_ax:
                return name + " (" + values_from.name + ")"
            else:
                return name
        to_back = removed.data_frame.rename(mapper=renamer, axis=1)
        on.data_frame = pd.merge(left=on.data_frame, right=to_back, left_on=on.freq_ax, right_on=removed.freq_ax, how="outer")
        for column in to_back.columns:
            on.graph.column_gtypes[column] = "Line"
    if return_removed:
        on.owner.data_storage.add_data(removed)

