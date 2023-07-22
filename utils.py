import os.path
import typing
from typing import AnyStr
from tkinter import messagebox
import numpy as np
import pandas.errors
import pandas as pd
from xlsx2csv import Xlsx2csv
import sys

import gui
import graph as gp

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
            dataset.to_csv(path_or_buf=csvfile)
        csvfile.close()


def export_graph(name: AnyStr, location: AnyStr, graph: gp.Graph):
    graph = graph.create_graph()
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
    def __init__(self, owner):
        self.owner = owner

        self.allowed_type = ['txt', 'xlsx', 'csv', 'cat', 'ft']
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
        if file.type == 'xlsx':
            messagebox.showwarning("File Type Warning", "Excel files are very slow to process compared to CSV files."
                                                        " this application will create a new CSV file that is a copy"
                                                        " of the inputted Excel file in the same location to use.")
            Xlsx2csv(xlsxfile=file.path).convert(file.path.replace("xlsx", "csv"))
            file.path = file.path.replace('xlsx', 'csv')
            file.path = 'csv'
            gui.CsvApp(callback=self.csv_callback, file=file)
        elif file.type == 'csv':
            gui.CsvApp(callback=self.csv_callback, file=file)
        elif file.type == 'cat':
            loaded = np.loadtxt(fname=file.path, usecols=[0, 2], )
            dataset = pd.DataFrame(columns=["Frequency (MHz)", "Intensity (V)"])
            dataset["Frequency (MHz)"] = loaded[:, 0]
            dataset["Intensity (V)"] = loaded[:, 1]
            dataset["Intensity (V)"] = dataset["Intensity (V)"].apply(func=lambda x: math.pow(10, x))
            self.owner.data_storage.add_data(dataset)
        elif file.type == 'ft':
            dataset = pd.read_csv(filepath_or_buffer=file.path, sep=" ", header=None, dtype='float')
            dataset.columns = ["Frequency (MHz)", "Intensity (V)"]
            self.owner.data_storage.add_data(dataset)
        elif file.type in self.custom_type:
            self.owner.data_storage.add_data(self.custom_funcs[file.type](file.path))

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
        # Add created dataset to the DataStorage of the main app
        self.owner.data_storage.add_data(data=dataset)

    def new_association(self, file_type, func):
        self.custom_type.append(file_type)
        self.custom_funcs[file_type] = func
