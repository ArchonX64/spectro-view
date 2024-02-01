from __future__ import annotations

import os.path
import typing
from typing import AnyStr
from tkinter import messagebox
import numpy as np
import pandas.errors
import pandas as pd
from xlsx2csv import Xlsx2csv
import sys
from pickle import load

import gui
import data

import math


def resource_path(rel_dir: str):
    try:
        # Does not exist until called by PyInstaller
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
        rel_dir = "resources\\" + rel_dir
    return os.path.join(base_path, rel_dir)


class InvalidTypeException(Exception):
    """File is of invalid type"""
    pass


class NonPositiveIntegerException(Exception):
    """Input must be a positive integer"""
    pass


def export_file(name: AnyStr, location: AnyStr, dataset: pd.DataFrame, file_type):
    if file_type == "CSV":
        with open(location + "/" + name + ".csv", "wb") as csvfile:
            dataset.to_csv(path_or_buf=csvfile, index=False)
        csvfile.close()


def export_graph(name: AnyStr, location: AnyStr, data: data.Data):
    graph = data.graph.create_graph()
    graph.savefig(fname=location + "/" + name + ".png", dpi='figure')


def add_file_type():
    pass


class File:
    def __init__(self, file: AnyStr):
        self.path = file
        if len(file) > 2:
            split = file.split(".")
            self.type = split[-1]
            self.name = split[-2]
        else:
            raise ValueError


class FileManager:
    def __init__(self, owner: gui.App):
        self.owner = owner

        self.allowed_type = ['txt', 'xlsx', 'csv', 'cat', 'ft', 'dat', 'fit', 'spd']
        self.custom_type = []
        self.custom_funcs = {}

        self.file_names = []
        self.files = {}

    def add_file(self, path: AnyStr):
        if path == "":
            return
        file = File(path)
        if file.type in self.allowed_type or file.type in self.custom_type:
            self.file_names.append(file.name)
            self.files[file.name] = file
        else:
            raise InvalidTypeException

    def add_and_gen(self, path: typing.AnyStr):
        if path == "":
            return
        file = File(path)
        if file.type in self.allowed_type or file.type in self.custom_type:
            self.file_names.append(file.name)
            self.files[file.name] = file
            self.gen_dataset(file.name)
        else:
            raise ValueError

    # The main command for doing files -> datasets. Will vary based on file type
    def gen_dataset(self, name: AnyStr):
        file = self.files[name]
        inten_name = file.name.split("/")[-1]
        if file.type == 'xlsx':
            messagebox.showwarning("File Type Warning", "Excel files are very slow to process compared to CSV files."
                                                        " this application will create a new CSV file that is a copy"
                                                        " of the inputted Excel file in the same location to use.")
            Xlsx2csv(xlsxfile=file.path).convert(file.path.replace("xlsx", "csv"))
            file.path = file.path.replace('xlsx', 'csv')
            file.path = 'csv'
            gui.CsvApp(callback=self.csv_callback, file=file)
            return
        elif file.type == 'csv':
            gui.CsvApp(callback=self.csv_callback, file=file)
            return
        elif file.type == "spd":
            with open(file.path, "rb") as infile:
                load_dat = load(infile)
                new_dat = data.Data(data_frame=load_dat.data_frame, owner=self.owner, name=load_dat.name,
                                    freq_ax=load_dat.freq_ax, x_ax=load_dat.freq_ax, gtypes=load_dat.gtypes,
                                    is_ratio=load_dat.is_ratio)
                self.owner.data_storage.add_data(new_dat)
            return
        elif file.type == 'cat':
            loaded = np.loadtxt(fname=file.path, usecols=[0, 2])
            dataset = pd.DataFrame(columns=["Frequency (MHz)", inten_name])
            dataset["Frequency (MHz)"] = loaded[:, 0]
            dataset[inten_name] = loaded[:, 1]
            dataset[inten_name] = dataset[inten_name].apply(func=lambda x: math.pow(10, x))
        elif file.type == 'ft':
            dataset = pd.read_csv(filepath_or_buffer=file.path, sep=" ", header=None, dtype='float')
            dataset.columns = ["Frequency (MHz)", inten_name]
        elif file.type == 'dat':
            dataset = pd.read_csv(filepath_or_buffer=file.path, sep="\t", header=None, dtype='float')
            dataset.columns = ["Frequency (MHz)", inten_name]
        elif file.type == 'fit':
            dataset = pd.read_csv(filepath_or_buffer=file.path, skiprows=25, sep=" ", header=None, usecols=[7, 7], dtype='float')
            dataset.columns = ["Frequency (MHz)"]
            dataset[inten_name] = np.zeros(dataset["Frequency (MHz)"].size)
        elif file.type in self.custom_type:
            self.owner.data_storage.add_data(self.custom_funcs[file.type](file.path))
            return
        else:
            gui.error("Unsupported File Type")
            return
        gui.DataInfoSelector(callback=self.finalize_data, df=dataset, name=file.name.split("/")[-1])

    # info is a list [[1,0],[-1,1]], where the lists are the starting/ending rows and -1 indicates that it goes to eof
    def csv_callback(self, root, file: File, is_full: bool, info=None):
        root.destroy()
        if is_full:
            dataset = pd.read_csv(filepath_or_buffer=file.path)
        else:
            # Create a list of column values that you want to read
            column_list = []
            for x in range(info.__getitem__(0).__getitem__(1), info.__getitem__(1).__getitem__(1) + 1):
                column_list.append(x)
            # -1 indicates that reader should go to EOF (no upper row bound)
            try:
                # ==== IMPORTANT ====
                # First row of Excel file MUST include column labels, NOT data points.
                # Data points will therefore be indexed from the SECOND line.
                if info.__getitem__(1).__getitem__(0) == -1:
                    dataset = pd.read_csv(filepath_or_buffer=file.path, skiprows=info.__getitem__(0).__getitem__(0),
                                          usecols=column_list)
                else:
                    dataset = pd.read_csv(filepath_or_buffer=file.path, skiprows=info.__getitem__(0).__getitem__(0),
                                          usecols=column_list,
                                          nrows=info.__getitem__(1).__getitem__(0) - info.__getitem__(0).__getitem__(0))
            except pandas.errors.ParserError:
                messagebox.showerror("Error", "Rows and columns selected are unable to be read")
                return
        # Send to DataInfoSelector to get name and freq_axis
        gui.DataInfoSelector(callback=self.finalize_data, df=dataset, name=file.name.split("/")[-1])

    # Is called by DataInfoSelector once name and freq_axis found
    def finalize_data(self, df: pd.DataFrame, name: str, freq_ax: str):
        dat = data.Data(data_frame=df, owner=self.owner, name=name, freq_ax=freq_ax)
        self.owner.data_storage.add_data(dat)

    def new_association(self, file_type, func):
        self.custom_type.append(file_type)
        self.custom_funcs[file_type] = func
