import re
import sys

if "win32" in sys.platform:
    from win32api import GetMonitorInfo, MonitorFromPoint
import tkinter as tk
import tkinter.ttk as ttk
from typing import Union, AnyStr, Callable
from tkinter import filedialog, messagebox

import pandas as pd
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk
)

import data
import graph
import graph as gph
import utils


def error(message: Union[AnyStr, int]):
    tk.messagebox.showerror(title="Error", message=message)


# A basic extension of Tk root class to incorporate some useful functions
class RootExpansion(tk.Tk):
    if "win" in sys.platform:  # Code to obtain taskbar height on Windows
        monitor_info = GetMonitorInfo(MonitorFromPoint((0, 0)))
        work_area = monitor_info.get("Work")
        monitor_area = monitor_info.get("Monitor")
        TASKBAR_HEIGHT = monitor_area[3] - work_area[3]
    else:
        TASKBAR_HEIGHT = 40  # Very generalized taskbar height estimate if not a Windows platform

    def __init__(self):
        super().__init__()
        self.screen_width = float(self.winfo_screenwidth())
        self.screen_height = float(self.winfo_screenheight())

        self.icon = tk.PhotoImage(master=self, file=utils.resource_path("icon.png"))
        self.wm_iconphoto(False, self.icon)

    # Code for centering widget 'root' onto the center of the screen
    def center_root(self, width: Union[int, float], height: Union[int, float]):
        self.update_idletasks()
        centered_x = (float(self.winfo_screenwidth()) - width) / 2
        centered_y = (float(self.winfo_screenheight()) - height) / 2 - self.TASKBAR_HEIGHT

        self.geometry("%dx%d+%d+%d" % (width, height, centered_x, centered_y))

    # Width/height as percentage of the current computer screen
    def percent_width(self, percent: Union[int, float]):
        return int((float(percent) / float(100)) * self.screen_width)

    def percent_height(self, percent: Union[int, float]):
        return int((float(percent) / float(100)) * self.screen_height)


# The core app
class App(RootExpansion):
    def __init__(self):
        super().__init__()
        self.app_width = self.percent_width(80)
        self.app_height = self.percent_height(80)
        self.shift_pressed = False

        # Add members
        self.file_manager = utils.FileManager(self)
        self.data_storage = data.DataStorage(self)

        self.header = Header(root=self)
        self.sidebar = Sidebar(root=self)
        self.main_pic = MainPic(root=self)
        self.menubar = Menubar(root=self)

        # Positioning
        self.grid()
        self.header.grid(row=0, column=0, columnspan=2, sticky='NSEW')
        self.sidebar.grid(row=1, column=0, sticky='NSEW')
        self.main_pic.grid(row=1, column=1, sticky='NSEW')

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=7)
        self.grid_rowconfigure(1, weight=4)
        self.config(bg="blue")

        # Customization
        self.title("SpectroView")
        self.config(menu=self.menubar)
        self.protocol("WM_DELETE_WINDOW", self.quit)
        self.center_root(width=self.app_width, height=self.app_height)
        self.bind("<KeyPress>", self.key_press)

    # Called when "Open" is clicked, starts the sequence of opening a file and turning it into pandas DataFrame
    def import_file_command(self):
        self.file_manager.add_and_gen(path=tk.filedialog.askopenfilename())

    def export_dataset(self):
        ExportDataWin(dataset=self.sidebar.get_pressed())

    def export_graph(self):
        ExportGraphWin(graph_dat=self.sidebar.get_pressed())

    # Handles keyboard shortcuts
    def key_press(self, event):
        if self.main_pic.is_graphed:
            gr = self.sidebar.get_pressed().graph
            scale = 0.5 if self.shift_pressed else 0.05
            if 'a' in event.keysym:
                diff = (gr.xmax - gr.xmin) * scale
                gr.set_scale(xmin=gr.xmin - diff, xmax=gr.xmax - diff)
            elif 's' in event.keysym:
                diff = (gr.xmax - gr.xmin) * scale
                gr.set_scale(xmin=gr.xmin + diff, xmax=gr.xmax + diff)
            elif 'q' in event.keysym:
                diff = (gr.xmax - gr.xmin) * scale
                gr.set_scale(xmin=gr.xmin - diff, xmax=gr.xmax + diff)
            elif 'e' in event.keysym:
                diff = (gr.xmax - gr.xmin) * scale
                gr.set_scale(xmin=gr.xmin + diff, xmax=gr.xmax - diff)
            elif 'w' in event.keysym:
                diff = (gr.ymax - gr.ymin) * scale
                gr.set_scale(ymax=gr.ymax - diff, ymin=-(gr.ymax - diff) * 0.1)
            elif 'z' in event.keysym:
                diff = (gr.ymax - gr.ymin) * scale
                gr.set_scale(ymax=gr.ymax + diff, ymin=-(gr.ymax + diff) * 0.1)
            elif 'k' in event.keysym:
                diff = (gr.xmax - gr.xmin) * scale * 0.1
                gr.set_scale(xmin=gr.xmin - diff, xmax=gr.xmax - diff)
            elif 'l' in event.keysym:
                diff = (gr.xmax - gr.xmin) * scale * 0.1
                gr.set_scale(xmin=gr.xmin + diff, xmax=gr.xmax + diff)
            elif '2' in event.keysym:
                diff = (gr.ymax - gr.ymin) * scale * 0.1
                gr.set_scale(ymin=gr.ymin - diff, ymax=gr.ymax - diff)
            elif '3' in event.keysym:
                diff = (gr.ymax - gr.ymin) * scale * 0.1
                gr.set_scale(ymin=gr.ymin + diff, ymax=gr.ymax + diff)
            self.main_pic.update_graph()


# The menubar at the top of the screen
class Menubar(tk.Menu):
    def __init__(self, root):
        super().__init__(root)

        # Back ref
        self.root = root

        # Add members
        self.filebar = tk.Menu(self, tearoff=0)
        self.editbar = tk.Menu(self, tearoff=0)
        self.viewbar = tk.Menu(self, tearoff=0)
        self.is_linear = tk.BooleanVar(self)

        # Initiate members
        self.init_filebar()
        self.init_editbar()
        self.init_viewbar()

    # Setting up menu bars
    def init_filebar(self):
        self.filebar.add_command(label="Open", command=self.root.import_file_command)
        self.filebar.add_separator()
        self.filebar.add_command(label="Export Dataset", command=self.root.export_dataset)
        self.filebar.add_command(label="Export Graph", command=self.root.export_graph)
        self.filebar.add_separator()
        self.filebar.add_command(label="Exit", command=self.root.destroy)

        self.filebar.entryconfig("Export Dataset", state="disabled")
        self.filebar.entryconfig("Export Graph", state="disabled")

        self.add_cascade(label="File", menu=self.filebar)

    def init_editbar(self):
        self.editbar.add_command(label="Info", command=self.root.sidebar.set_info)
        self.editbar.add_command(label="Data", command=self.root.sidebar.modify_data)

        self.add_cascade(label="Edit", menu=self.editbar)

        self.editbar.entryconfig("Info", state="disabled")
        self.editbar.entryconfig("Data", state="disabled")

    def init_viewbar(self):
        self.viewbar.add_command(label="Graph Size", command=lambda: ViewModifier(self.root.main_pic.graph_canvas))

        self.add_cascade(label='View', menu=self.viewbar)

    # List of menus that depend on a dataframe and should not be enabled until one is clicked
    def enabled_on_data_press(self, enabled: bool):
        normal_disable = "disabled"
        if enabled:
            normal_disable = "normal"
        self.editbar.entryconfig("Info", state=normal_disable)
        self.editbar.entryconfig("Data", state=normal_disable)
        self.filebar.entryconfig("Export Dataset", state=normal_disable)
        self.filebar.entryconfig("Export Graph", state=normal_disable)

    def toggle_linear(self, boolean):
        self.is_linear = boolean


# Sidebar displaying all the opened datasets
class Sidebar(tk.Frame):
    sidebar_color = "#B0B0B0"

    # The buttons that represent the different dataframes in 'datastorage'
    class DataButton(tk.Button):
        button_color = None

        def __init__(self, sidebar, dataset):
            super().__init__(master=sidebar, text=dataset.name, command=self.pressed)
            self.dataset = dataset
            self.button_color = self['bg']
            self.sidebar = sidebar
            self.rightclick_menu = tk.Menu(master=self, tearoff=0)
            self.bind("<Button-3>", self.on_rightclick)
            self.is_pressed = False

            self.gen_menu()

        def get_dataframe(self):
            return self.dataset.data_frame

        def gen_menu(self):
            self.rightclick_menu.add_command(command=self.dataset.replicate, label="Replicate")
            self.rightclick_menu.add_command(command=self.dataset.merge, label="Merge")
            self.rightclick_menu.add_command(command=self.dataset.split, label="Split")
            self.rightclick_menu.add_command(command=self.remove, label="Delete")
            self.rightclick_menu.add_command(command=self.save, label="Save")

        def remove(self):
            self.sidebar.root.data_storage.remove_data(self.dataset)
            if self.sidebar.pressed_dataset == self:
                self.sidebar.pressed_dataset = None
            self.sidebar.update_data()

        def save(self):
            SaveDatasetWindow(self.dataset)

        def on_rightclick(self, event):
            try:
                self.rightclick_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.rightclick_menu.grab_release()

        # When pressed, buttons will add their dataset to an 'active' list and remove it if pressed again
        def pressed(self):
            if not self.is_pressed:
                self["bg"] = "#676767"
                self.sidebar.pressed_dataset = self
                self.is_pressed = True
                for dataset in self.sidebar.dataset_texts:
                    if dataset != self:
                        dataset.config(bg=self.button_color)
                self.sidebar.root.menubar.enabled_on_data_press(True)
            elif self.pressed:
                self["bg"] = self.button_color
                self.sidebar.pressed_dataset = None
                self.is_pressed = False
                self.sidebar.root.menubar.enabled_on_data_press(False)

    def __init__(self, root):
        super().__init__(master=root)

        # Back references
        self.root = root

        # Customization
        self.config(bg=self.sidebar_color)

        # Members
        self.dataset_texts = []
        self.pressed_dataset = None

        self.pack_propagate(False)

    # If data is modified this should be called to update the buttons inside.
    def update_data(self):
        for button in self.dataset_texts:
            button.destroy()
        self.dataset_texts.clear()
        for dataset in self.root.data_storage.data_list:
            data_button = self.DataButton(self, dataset)
            self.dataset_texts.append(data_button)
            data_button.pack(fill=tk.X, side=tk.TOP)

    def set_info(self):
        if self.pressed_dataset is not None:
            DataSettingsUpdater(self.get_pressed())

    # Window to modify the actual data of the dataframe
    def modify_data(self):
        if self.pressed_dataset is not None:
            DataModifier(dataset=self.pressed_dataset.dataset, caller=self.root)

    def get_pressed(self):
        if self.pressed_dataset is not None:
            return self.pressed_dataset.dataset
        else:
            return None


# Includes ways to modify the dataset/graph
class Header(tk.Frame):
    header_color = "#e6e7e8"

    def __init__(self, root):
        super().__init__(master=root)

        # Back references
        self.root = root

        # Customization
        self.config(bg=self.header_color)
        self.grid_propagate(False)

        # Members
        self.graphing_message = tk.Message(master=self, text="Graphing:", width=100, bg=self.header_color)
        self.graph_button = ttk.Button(master=self, text="Graph", command=self.graph_selected)
        self.graph_type_button = ttk.Button(master=self, text="Graph Types", command=self.graph_types)
        self.zoom_button = ttk.Button(master=self, text="Zoom", command=self.zoom)
        self.threed_graph_button = ttk.Button(master=self, text="Graph 3D", command=self.threed_graph)

        self.data_manip_text = tk.Message(master=self, text="Data Manipulation", width=150, bg=self.header_color)
        self.peak_pick_button = ttk.Button(master=self, command=self.peak_pick, text="Peak Pick")
        self.ratio_sep_button = ttk.Button(master=self, command=self.ratio_sep, text="Ratio Separate")
        self.filter_known_button = ttk.Button(master=self, command=self.filter_known, text="Filter Known")

        # Positioning
        self.graphing_message.grid(row=0, column=0, sticky='w')
        self.graph_button.grid(row=1, column=0, padx=10, pady=5, sticky='w', ipady=5)
        self.graph_type_button.grid(row=1, column=1, padx=10, pady=5, sticky='w', ipady=5)
        self.zoom_button.grid(row=2, column=0, padx=10, pady=10, sticky='w', ipady=5)
        self.threed_graph_button.grid(row=2, column=1, padx=10, pady=10, sticky='w', ipady=5)
        self.data_manip_text.grid(row=0, column=2, columnspan=2, sticky='w')
        self.peak_pick_button.grid(row=1, column=2, padx=10, pady=5, sticky='w', ipady=5)
        self.ratio_sep_button.grid(row=1, column=3, padx=10, pady=10, sticky='w', ipady=5)
        self.filter_known_button.grid(row=2, column=2, padx=10, pady=10, sticky='w', ipady=5)

        self.grid_propagate(True)

    # When 'Graph' is clicked, all the datasets that are selected should be graphed.
    def graph_selected(self):
        if self.root.sidebar.get_pressed() is not None:
            self.root.main_pic.graph_selected(dataset=self.root.sidebar.get_pressed())

    def graph_types(self):
        if self.root.sidebar.get_pressed() is not None:
            GraphTypeWin(self.root.sidebar.get_pressed())

    def threed_graph(self):
        if self.root.sidebar.get_pressed() is not None:
            if len(self.root.sidebar.get_pressed().data_frame.index) > 10000:
                messagebox.showwarning("Warning", "Large datasets are very costly to manipulate in three "
                                                  "dimensions.\n Please consider running an algorithm to reduce the "
                                                  "number of datapoints before graphing.")
            ThreeDWindow(dataset=self.root.sidebar.get_pressed(), canvas=self.root.main_pic.graph_canvas)

    # When 'Zoom' is clicked, the limits of matplotlib graph are changed.
    def zoom(self):
        if self.root.sidebar.get_pressed() is not None:
            ZoomWindow(callback=self.zoom_callback)

    # Callback for ZoomWindow that provides necessary values
    def zoom_callback(self, xmin: Union[float, int] = None, xmax: Union[float, int] = None,
                      ymin: Union[float, int] = None,
                      ymax: Union[float, int] = None, auto=False):
        self.root.sidebar.get_pressed().graph.set_scale(xmin, xmax, ymin, ymax, auto)
        self.root.main_pic.update_graph()

    # Creates a new window for selecting peaks
    def peak_pick(self):
        if self.root.sidebar.get_pressed() is not None:
            PeakPickWindow(self.root.sidebar.get_pressed(), self.peak_pick_callback)

    # Information provided by PeakPickWindow
    def peak_pick_callback(self, created_window, new_name, res, min_inten, max_inten):
        created_window.destroy()
        new_data = data.peak_pick(self.root.sidebar.get_pressed(), new_name, res, min_inten, max_inten)
        self.root.data_storage.add_data(new_data)

    def ratio_sep(self):
        if self.root.sidebar.get_pressed() is not None:
            RatioWin(self.root, self.root.sidebar.get_pressed())

    def filter_known(self):
        if self.root.sidebar.get_pressed() is not None and len(self.root.sidebar.dataset_texts) > 1:
            SimilarRemoveWindow(self.root, self.root.sidebar.get_pressed())


# Frame for displaying the matplotlib graph
class MainPic(tk.Frame):
    def __init__(self, root):
        super().__init__(master=root)

        # Back Ref
        self.root = root

        # Members
        self.graph_canvas = gph.GraphCanvas(self)
        self.canvas = FigureCanvasTkAgg(figure=self.graph_canvas.figure, master=self)
        self.graph_canvas.set_canvas(self.canvas)
        self.toolbar = NavigationToolbar2Tk(canvas=self.canvas, window=self, pack_toolbar=False)
        self.is_graphed = False

        # Positioning
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH)
        self.pack_propagate(False)

        # Customization
        self.mainpic_width = self.root.percent_width(70)
        self.mainpic_height = self.root.percent_height(68)
        self.config(bg="white")

        self.graph_canvas.figure.canvas.mpl_connect('button_press_event', self.click_callback)

    # Graph the selected DataFrame
    def graph_selected(self, dataset: data.Data):
        self.is_graphed = True
        self.graph_canvas.set_graph(to_graph=dataset.graph)
        self.graph_canvas.graph()

    def update_graph(self):
        self.graph_canvas.graph()

    def click_callback(self, event):
        print(event.xdata, event.ydata)


# Changes how the data is viewed in the MatplotLib window
class GraphTypeWin(RootExpansion):
    def __init__(self, dataset):
        super().__init__()

        # Back Ref
        self.dataset = dataset

        # Procedurally generates gui
        self.message_list = []
        self.entry_list = []
        self.gtypes = ("None", "Line", "Scatter", "Stem")
        index = 0
        for column in dataset.data_frame.columns.values.tolist():
            message = tk.Message(master=self, text=column + ":", width=150)
            types = ttk.Combobox(master=self, state="readonly")
            types['values'] = self.gtypes
            types.current(self.gtypes.index(graph.gtype_from_val[dataset.graph.column_gtypes[column]]))

            self.message_list.append(message)
            self.entry_list.append(types)

            message.grid(row=index, column=0)
            types.grid(row=index, column=1)
            index += 1

        self.enter_button = ttk.Button(master=self, text="Enter", command=self.enter)
        self.enter_button.grid(row=index + 1, column=0, columnspan=2, pady=10)
        self.wm_title("Graph Types")

        self.update()
        self.center_root(self.winfo_width(), self.winfo_height())

    def enter(self):
        input_list = []
        for boxes in self.entry_list:
            input_list.append(boxes.get())
        for element in range(0, len(input_list)):
            input_list[element] = graph.gtype_from_string[input_list[element]]
        self.dataset.graph.modify_gtypes(input_list)
        self.destroy()


# Anything labeled "Excel" is a part of a widget to determine the starting/ending cells to look through
class CsvApp(RootExpansion):
    def __init__(self, callback: Callable, file: AnyStr):
        super().__init__()
        self.frame = ExcelFrame(self, callback, file)
        self.frame.pack()
        self.title("Excel Read Config")

        self.update()
        self.center_root(self.winfo_width(), self.winfo_height())
        self.resizable(False, False)


class ExcelFrame(tk.Frame):
    def __init__(self, root, callback: Callable, file: AnyStr):
        super().__init__(master=root)
        # Back references
        self.root = root
        self.callback = callback
        self.file = file

        # Members
        self.start_row_message = tk.Message(master=self, text="Starting Row #:", width=200)
        self.start_column_message = tk.Message(master=self, text="Starting Column #:", width=200)
        self.end_row_message = tk.Message(master=self, text="Ending Row #:", width=200)
        self.end_column_message = tk.Message(master=self, text="Ending Column #:", width=200)

        self.start_row_input = ttk.Entry(master=self, width=12)
        self.start_column_input = ttk.Entry(master=self, width=12)
        self.end_row_input = ttk.Entry(master=self, width=12)
        self.end_column_input = ttk.Entry(master=self, width=12)

        self.eof_var = tk.IntVar(self)
        self.eof_check = ttk.Checkbutton(master=self, variable=self.eof_var, text="EOF")
        self.info_text = tk.Message(master=self, width=300)
        self.info_text_var = tk.StringVar(master=self.info_text)
        self.info_text.config(textvariable=self.info_text_var)
        self.auto_button = ttk.Button(master=self, text="Auto", command=self.auto, width=5)
        self.enter_button = ttk.Button(master=self, text="Enter", command=self.enter)

        # Positioning
        self.start_row_message.grid(row=0, column=0)
        self.start_column_message.grid(row=0, column=1)
        self.end_row_message.grid(row=2, column=0)
        self.end_column_message.grid(row=2, column=1)
        self.start_row_input.grid(row=1, column=0)
        self.start_column_input.grid(row=1, column=1)
        self.end_row_input.grid(row=3, column=0)
        self.end_column_input.grid(row=3, column=1)
        self.eof_check.grid(row=1, column=2, padx=5)
        self.info_text.grid(row=4, column=0, columnspan=2)
        self.auto_button.grid(row=2, column=2, rowspan=2)
        self.enter_button.grid(row=5, column=0, pady=10, columnspan=3)

        # Customization
        self.bind('<KeyPress>', self.on_press)
        self.bind('<KeyReleased>')

        self.focus_force()

    # Allows user to type the enter key to proceed
    def on_press(self, event):
        if event.char == "\r":
            self.enter()

    # When enter is clicked, the application turns the input into a list of coordinates and sends it to the
    # fileprocessor
    def enter(self, is_full=False):
        if is_full:
            self.callback(root=self.root, is_full=True, file=self.file)
        else:
            start_row = self.start_row_input.get()
            start_column = self.start_column_input.get()
            end_row = self.end_row_input.get()
            end_column = self.end_column_input.get()
            # -1 acts as a flag for indicating it should read until EOF
            if self.eof_var.get() == 1:
                end_row = -1
            try:
                # Verify each entry is an integer, align it with a list that starts from 0
                try:
                    start_row = int(start_row) - 1
                    start_column = int(start_column) - 1
                    if not end_row == -1:
                        end_row = int(end_row) - 1
                    end_column = int(end_column) - 1
                except ValueError:
                    raise utils.NonPositiveIntegerException
                # Verify all numbers are positive
                if start_row < 0 or start_column < 0 or end_column < 0:
                    raise utils.NonPositiveIntegerException
                # Send information back to FileProcessor
                self.callback(root=self.root, info=[[start_row, start_column], [end_row, end_column]], is_full=False,
                              file=self.file)
            except utils.NonPositiveIntegerException:
                self.info_text_var.set("Please input a positive integer")
                self.update()

    def auto(self):
        self.enter(is_full=True)


# Window for selecting the name of a certain dataset
class DataInfoSelector(RootExpansion):
    def __init__(self, callback: Callable[[pd.DataFrame, str, str], None], df: pd.DataFrame, name: str = None):
        super().__init__()

        # Callback
        self.callback = callback
        self.df = df

        # Customization
        self.title("Info")
        self.bind('<KeyPress>', self.on_press)

        # Members
        self.name_text = tk.Message(master=self, text="Name of Dataset:", width=300)
        self.name_var = tk.StringVar(self)
        self.name_box = ttk.Entry(master=self, width=20, textvariable=self.name_var)

        self.ax_text = tk.Message(master=self, text="Axis Containing Frequency:", width=300)

        self.ax_option = tk.StringVar(self)
        self.ax_box = ttk.Combobox(master=self, textvariable=self.ax_option, state="readonly")

        self.enter_button = ttk.Button(master=self, text="Enter", command=self.enter)

        self.info_text = tk.Message(master=self, width=300)
        self.info_text_var = tk.StringVar(master=self.info_text)
        self.info_text.config(textvariable=self.info_text_var)

        # Positioning
        self.name_text.grid(row=0, column=0, padx=30, pady=5)
        self.name_box.grid(row=1, column=0, padx=30, pady=5)
        self.ax_text.grid(row=2, column=0, padx=30, pady=5)
        self.ax_box.grid(row=3, column=0, padx=30, pady=5)
        self.enter_button.grid(row=4, column=0, padx=30, pady=20)
        self.focus_force()

        # Customization
        self.ax_box['values'] = df.columns.values.tolist()
        self.ax_option.set(self.ax_box['values'][0])
        if name is not None:
            self.name_var.set(name)

        self.update()
        self.center_root(self.winfo_width(), self.winfo_height())
        self.resizable(False, False)

    # Send the name back to Data
    def enter(self):
        self.callback(self.df, self.name_var.get(), self.ax_option.get())
        self.destroy()

    # Allows pressing enter to proceed
    def on_press(self, event):
        if event.char == "\r":
            self.enter()


# Window for selecting zoom amount
class ZoomWindow(RootExpansion):
    def __init__(self, callback: Callable):
        super().__init__()
        # Back references
        self.callback = callback

        # Members
        self.xmin_message = tk.Message(master=self, text="X-Minimum:", width=200)
        self.ymin_message = tk.Message(master=self, text="Y-Minimum:", width=200)
        self.xmax_message = tk.Message(master=self, text="X-Maximum:", width=200)
        self.ymax_message = tk.Message(master=self, text="Y-Maximum:", width=200)

        self.xmin_input = ttk.Entry(master=self, width=12)
        self.ymin_input = ttk.Entry(master=self, width=12)
        self.xmax_input = ttk.Entry(master=self, width=12)
        self.ymax_input = ttk.Entry(master=self, width=12)

        self.info_text = tk.Message(master=self, width=300)
        self.info_text_var = tk.StringVar(master=self.info_text)
        self.info_text.config(textvariable=self.info_text_var)
        self.auto_button = ttk.Button(master=self, text="Auto", command=self.auto_scale, width=5)
        self.enter_button = ttk.Button(master=self, text="Enter", command=self.enter)

        # Positioning
        self.xmin_message.grid(row=0, column=0, padx=10, pady=5)
        self.ymin_message.grid(row=0, column=1, padx=10, pady=5)
        self.xmax_message.grid(row=2, column=0, padx=10, pady=5)
        self.ymax_message.grid(row=2, column=1, padx=10, pady=5)
        self.xmin_input.grid(row=1, column=0, padx=10, pady=5)
        self.ymin_input.grid(row=1, column=1, padx=10, pady=5)
        self.xmax_input.grid(row=3, column=0, padx=10, pady=5)
        self.ymax_input.grid(row=3, column=1, padx=10, pady=5)
        self.info_text.grid(row=4, column=0, columnspan=2, padx=1)
        self.auto_button.grid(row=2, column=2, padx=10)
        self.enter_button.grid(row=5, column=0, padx=10, columnspan=3, pady=10)

        # Customization
        self.bind('<KeyPress>', self.on_press)
        self.wm_title("Zoom")

        self.update()
        self.center_root(self.winfo_width(), self.winfo_height())
        self.resizable(False, False)
        self.focus_force()

    # Allows user to type the enter key to proceed
    def on_press(self, event):
        if event.char == "\r":
            self.enter()

    def enter(self):
        # I hate that this was the best way I could think of
        if self.xmin_input.get() == "":
            xmin = None
        else:
            xmin = float(self.xmin_input.get())
        if self.xmax_input.get() == "":
            xmax = None
        else:
            xmax = float(self.xmax_input.get())
        if self.ymin_input.get() == "":
            ymin = None
        else:
            ymin = float(self.ymin_input.get())
        if self.ymax_input.get() == "":
            ymax = None
        else:
            ymax = float(self.ymax_input.get())
        self.callback(xmin, xmax, ymin, ymax, auto=False)
        self.destroy()

    def auto_scale(self):
        self.callback(auto=True)
        self.destroy()


# Window for choosing options for peaky.py
class PeakPickWindow(RootExpansion):
    def __init__(self, dataset: data.Data, callback: Callable):
        super().__init__()

        self.callback = callback
        self.dataset = dataset

        # Members
        self.new_name_text = tk.Message(master=self, text="Name of Peak-Picked Set:", width=150)
        self.new_name_var = tk.StringVar(self)
        self.new_name_entry = ttk.Entry(master=self, textvariable=self.new_name_var, width=20)
        self.inten_min_text = tk.Message(master=self, text="Min Intensity:", width=150)
        self.inten_min_var = tk.StringVar(self, value="0.001")
        self.inten_min_entry = ttk.Entry(master=self, textvariable=self.inten_min_var, width=10)
        self.inten_max_text = tk.Message(master=self, text="Max Intensity:", width=150)
        self.inten_max_var = tk.StringVar(self, value="0.3")
        self.inten_max_entry = ttk.Entry(master=self, textvariable=self.inten_max_var, width=10)
        self.res_adjust_text = tk.Message(master=self, text="Adjusted Resolution (MHz):", width=150)
        self.res_adjust_var = tk.StringVar(self, value="0.002")
        self.res_adjust_entry = ttk.Entry(master=self, textvariable=self.res_adjust_var, width=10)
        self.enter_button = ttk.Button(master=self, command=self.enter, text="Enter")

        # Positioning
        self.new_name_text.grid(row=0, column=0, columnspan=2, padx=10, pady=5)
        self.new_name_entry.grid(row=1, column=0, columnspan=2, padx=10, pady=5)
        self.inten_min_text.grid(row=2, column=0, padx=10, pady=5)
        self.inten_min_entry.grid(row=3, column=0, padx=10, pady=5)
        self.inten_max_text.grid(row=2, column=1, padx=10, pady=5)
        self.inten_max_entry.grid(row=3, column=1, padx=10, pady=5)
        self.res_adjust_text.grid(row=4, column=0, columnspan=2, padx=10, pady=5)
        self.res_adjust_entry.grid(row=5, column=0, columnspan=2, padx=10, pady=5)
        self.enter_button.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

        # Customization
        self.title("Peak Pick")
        self.update()
        self.center_root(self.winfo_width(), self.winfo_height())
        self.resizable(False, False)

    def enter(self):
        if self.new_name_var.get() == "":
            name = self.dataset.name + " (peaks)"
        else:
            name = self.new_name_var.get()
        try:
            inten_min = float(self.inten_min_entry.get())
            inten_max = float(self.inten_max_entry.get())
            res = float(self.res_adjust_entry.get())
        except ValueError:
            return
        self.callback(self, name, res, inten_min, inten_max)


# Window for modifying the data in a dataframe
class DataModifier(RootExpansion):
    def __init__(self, dataset: data.Data, caller: Callable):
        super().__init__()

        # Back reference
        self.data = dataset
        self.caller = caller

        # Members
        self.tabs = ttk.Notebook(master=self)
        self.row_frame = RowFrame(self.tabs, self, dataset, caller)
        self.column_frame = ColumnFrame(self.tabs, self, dataset, caller)

        # Customization
        self.wm_title("Data")
        self.tabs.add(self.row_frame, text="Row")
        self.tabs.add(self.column_frame, text="Column")

        # Positioning
        self.grid()
        self.tabs.grid(sticky="nsew")

        self.update()
        self.center_root(self.winfo_width(), self.winfo_height())


# Part of DataModifier
class ColumnFrame(tk.Frame):
    def __init__(self, tabs, root, dataset: data.Data, caller):
        super().__init__(master=tabs)

        # Back Ref
        self.root = root
        self.dataset = dataset
        self.caller = caller

        # Members
        self.remove_text = tk.Message(master=self, text="Remove:", width=150)
        self.remove_var = tk.StringVar(self)
        self.remove_box = ttk.Combobox(master=self, textvariable=self.remove_var, state="readonly")
        self.remove_button = ttk.Button(master=self, text="Remove", command=self.remove)
        self.info_var = tk.StringVar(self, value="")
        self.info_text = tk.Message(master=self, textvariable=self.info_var, width=10)

        # Positioning
        self.remove_text.grid(row=0, column=0)
        self.remove_box.grid(row=1, column=0, padx=20)
        self.remove_button.grid(row=1, column=1)
        self.info_text.grid(row=2, column=1, columnspan=2)

        # Customization
        self.remove_box['values'] = self.dataset.data_frame.columns.values.tolist()
        self.pack_propagate(False)

    def remove(self):
        if not self.remove_var.get() == '':
            if not self.remove_var.get() == self.dataset.ax:
                self.dataset.drop_column(self.remove_var.get())
                self.caller.sidebar.update_data()
                self.caller.main_pic.update_graph()
                self.root.destroy()
            else:
                self.info_var.set("Removed column cannot be current x-axis.")


class RowFrame(tk.Frame):
    def __init__(self, tabs, root, dataset: data.Data, caller):
        super().__init__(master=tabs)

        # Back Ref
        self.root = root
        self.data = dataset
        self.caller = caller

        # Members
        self.dropdown = ["Index"] + self.data.data_frame.columns.values.tolist()

        self.remove_rowval_text = tk.Message(master=self, text="Remove Row By Value:", width=150)
        self.remove_rowval_var = tk.StringVar(self)
        self.remove_rowval_drop = ttk.Combobox(master=self, textvariable=self.remove_rowval_var, state="readonly")
        self.remove_rowval_entry_var = tk.StringVar(self)
        self.remove_rowval_entry = ttk.Entry(master=self, textvariable=self.remove_rowval_entry_var)
        self.remove_rowval_button = ttk.Button(master=self, text="Remove", command=self.remove_rowval_command)

        self.remove_val_text = tk.Message(master=self, text="Remove By Value:", width=150)
        self.remove_val_var = tk.StringVar(self)
        self.remove_val_drop = ttk.Combobox(master=self, textvariable=self.remove_val_var)
        self.remove_val_entry_var = tk.StringVar(self)
        self.remove_val_entry = ttk.Entry(master=self, textvariable=self.remove_val_entry_var)
        self.remove_val_button = ttk.Button(master=self, text="Remove", command=self.remove_val_command)

        self.modify_val_message = tk.Message(master=self, text="Modify With Expression:", width=150)
        self.modify_val_combo_val = tk.StringVar(self)
        self.modify_val_col = ttk.Combobox(master=self, textvariable=self.modify_val_combo_val)
        self.modify_val_entry = ttk.Entry(master=self)
        self.modify_val_button = ttk.Button(master=self, text="Modify", command=self.modify_val_command)

        self.info_var = tk.StringVar(self)
        self.info = tk.Message(master=self, textvariable=self.info_var, width=150)

        # Positioning
        self.remove_rowval_text.grid(row=0, column=0)
        self.remove_rowval_drop.grid(row=1, column=0, padx=10)
        self.remove_rowval_entry.grid(row=2, column=0, pady=5)
        self.remove_rowval_button.grid(row=2, column=1, padx=10)
        self.remove_val_text.grid(row=3, column=0)
        self.remove_val_drop.grid(row=4, column=0, padx=10)
        self.remove_val_entry.grid(row=5, column=0, pady=5)
        self.remove_val_button.grid(row=5, column=1, padx=10)
        self.modify_val_message.grid(row=6, column=0)
        self.modify_val_col.grid(row=7, column=0, padx=10)
        self.modify_val_entry.grid(row=8, column=0, pady=5)
        self.modify_val_button.grid(row=8, column=1, padx=10)
        self.info.grid(row=9, column=0, columnspan=2)

        # Customization
        self.remove_rowval_drop['values'] = self.dropdown
        self.remove_val_drop['values'] = self.dropdown
        self.modify_val_col['values'] = self.data.data_frame.columns.values.tolist()
        self.pack_propagate(False)

    def remove_rowval_command(self):
        if self.remove_rowval_var.get() != "":
            self.remove_val_command(whole_row=True)

    def remove_val_command(self, whole_row=False):
        if not whole_row and self.remove_val_entry_var.get() == "":
            return

        command = self.remove_rowval_entry_var.get() if whole_row else self.remove_val_entry_var.get()
        axis = self.remove_rowval_var.get() if whole_row else self.remove_val_var.get()
        command_list = None

        # RegEx to find all values in between brackets
        keywords = re.findall("(?<={)(.*?)(?=})", command)
        if len(keywords) != 0:
            # Replace anything that is in brackets with a temporary asterisk
            for value in keywords:
                command = command.replace("{" + value + "}", " * ")
            # Split string based on spaces
            command_list = command.split()
            # Replace asterisks with the labels for a complete command list
            index_keywords = 0
            index_command = 0
            for value in command_list:
                if value == "*":
                    # Include dollar sign to indicate to data that this is a label
                    command_list[index_command] = "$" + keywords[index_keywords]
                    index_keywords += 1
                index_command += 1
        else:
            command_list = command.split()
        if len(command_list) == 2 or len(command_list) == 3:
            self.data.remove_data(command_list, axis, whole_row=whole_row)
            self.root.caller.main_pic.update_graph()

    def modify_val_command(self):
        mod = self.modify_val_entry.get()
        if mod != "":
            split = mod.split()
            try:
                if len(split) == 2:
                    self.data.modify_data(column=self.modify_val_col.get(), operator=split[0], values=[float(split[1])])
                self.info_var.set("Modification successful")
            except ValueError:
                self.info_var.set("Please check your syntax")


# Window for providing info on how to export data
class ExportDataWin(RootExpansion):
    def __init__(self, dataset: data.Data):
        super().__init__()

        # Back Ref
        self.data = dataset

        # Members
        self.name_text = tk.Message(master=self, text="Name of New File:", width=150)
        self.name_entry = ttk.Entry(master=self, width=30)
        self.location_text = tk.Message(master=self, text="File Location:", width=150)
        self.location_var = tk.StringVar(self)
        self.location_entry = ttk.Entry(master=self, textvariable=self.location_var, width=30)
        self.location_button = ttk.Button(master=self, text="Browse", command=self.browse_location)
        self.type_message = tk.Message(master=self, text="File Output Type:", width=150)
        self.type_var = tk.StringVar(self)
        self.type_entry = ttk.Combobox(master=self, textvariable=self.type_var, state="readonly")
        self.enter_button = ttk.Button(master=self, text="Enter", command=self.enter)

        # Positioning
        self.name_text.grid(row=0, column=0, columnspan=2, padx=10, pady=5)
        self.name_entry.grid(row=1, column=0, columnspan=2, padx=10, pady=5)
        self.location_text.grid(row=2, column=0, padx=10, pady=5)
        self.location_entry.grid(row=3, column=0, padx=10, pady=5)
        self.location_button.grid(row=3, column=1, padx=10, pady=5)
        self.type_message.grid(row=4, column=0, columnspan=2, padx=10, pady=5)
        self.type_entry.grid(row=5, column=0, columnspan=2, padx=10, pady=5)
        self.enter_button.grid(row=6, column=0, columnspan=2, padx=10, pady=20)

        # Customization
        self.wm_title("Export")
        self.type_entry['values'] = ['CSV', 'Text File']

        self.update()
        self.center_root(self.winfo_width(), self.winfo_height())

    def browse_location(self):
        dir_path = tk.filedialog.askdirectory()
        self.location_var.set(dir_path)
        self.focus_force()

    def enter(self):
        name = self.name_entry.get()
        location = self.location_var.get()
        file_type = self.type_var.get()
        if "" not in [name, location, file_type]:
            utils.export_file(name, location, self.data.data_frame, file_type)
            self.destroy()


class MergeWindow(RootExpansion):
    def __init__(self, callback: Callable, owner: App, who: data.Data):
        super().__init__()

        # Back Refs
        self.callback = callback
        self.owner = owner

        # Members
        self.to_merge_message = tk.Message(master=self, text="Merge With:", width=300)
        self.to_merge_var = tk.StringVar(self)
        self.to_merge_box = ttk.Combobox(master=self, state="readonly")
        self.combine_var = tk.IntVar(master=self, value=0)
        self.combine_val_box = ttk.Checkbutton(master=self, variable=self.combine_var, text="Combine")
        self.threshold_message = tk.Message(master=self, text="Threshold (kHz):", width=150)
        self.threshold_var = tk.StringVar(master=self, value="10")
        self.threshold_box = ttk.Entry(master=self, textvariable=self.threshold_var)
        self.enter_button = tk.Button(master=self, command=self.enter, text="Enter")

        # Positioning
        self.to_merge_message.grid(row=0, column=0, columnspan=2, padx=20, pady=5)
        self.to_merge_box.grid(row=1, column=0, columnspan=2, padx=20, pady=5)
        self.combine_val_box.grid(row=2, column=0, rowspan=2, padx=10)
        self.threshold_message.grid(row=2, column=1, padx=10, pady=5)
        self.threshold_box.grid(row=3, column=1, padx=10, pady=5)
        self.enter_button.grid(row=4, column=0, columnspan=2, padx=20, pady=5)

        # Customization
        data_names = []
        for dataset in owner.data_storage.data_list:
            if dataset.name != who.name:
                data_names.append(dataset.name)

        self.to_merge_box['values'] = data_names

        self.update()
        self.center_root(self.winfo_width(), self.winfo_height())
        self.resizable(False, False)

    def enter(self):
        if self.to_merge_box.get() != "":
            try:
                to_merge = None
                thresh = int(self.threshold_var.get())
                for dat in self.owner.data_storage.data_list:
                    if self.to_merge_box.get() == dat.name:
                        to_merge = dat.name
                self.callback(to_merge, bool(self.combine_var.get()), thresh)
                self.destroy()
            except ValueError:
                return


class MergeConflictWindow(RootExpansion):
    def __init__(self, left: data.Data, right: data.Data, callback: Callable):
        super().__init__()

        # Back Ref
        self.left = left
        self.right = right
        self.callback = callback

        # Members
        self.warning_message = tk.Message(master=self, text="Two or more axes have the same names. Please"
                                                            " create a unique name for each axis.", width=150)
        self.vars = []
        self.entries = []
        index = 0
        for column in right.data_frame.columns.values.tolist() + left.data_frame.columns.values.tolist():
            if column != right.freq_ax:
                var = tk.StringVar(self, value=column)
                entry = ttk.Entry(master=self, textvariable=var)

                self.vars.append(var)
                self.entries.append(entry)

                entry.grid(row=index, column=0)
                index += 1
        self.info_var = tk.StringVar(self)
        self.info = tk.Message(master=self, textvariable=self.info_var)
        self.enter_button = tk.Button(master=self, text="Enter", command=self.enter)

        self.info.grid(row=index + 1, column=0)
        self.enter_button.grid(row=index + 2, column=0)

        self.update()
        self.center_root(self.winfo_width(), self.winfo_height())
        self.focus_force()

    def enter(self):
        name_map = {}

        index = 0
        while index < len(self.right.data_frame.columns.values.tolist()):
            name_map[index] = self.vars[index].get()
            index += 1
        self.right.data_frame.rename(index=name_map)
        name_map.clear()

        index2 = 0
        while index < len(self.left.data_frame.columns.values.tolist()):
            name_map[index] = self.vars[index + index2].get()
            index2 += 1
        self.left.data_frame.rename(index=name_map)
        self.callback(self.left)
        self.destroy()


class SplitWindow(RootExpansion):
    def __init__(self, columns, callback: Callable):
        super().__init__()

        # Back Ref
        self.columns = columns
        self.callback = callback

        # Members
        self.split_on_message = tk.Message(master=self, text="Columns to Split Off:", width=300)
        self.split_on_var = tk.StringVar(self)
        self.split_on_entry = ttk.Entry(master=self, textvariable=self.split_on_var, width=50)
        self.from_message = tk.Message(master=self, text="Options:", width=300)
        self.from_box = ttk.Combobox(master=self, state="readonly")
        self.add_button = tk.Button(master=self, command=self.add, text="Add")
        self.enter_button = tk.Button(master=self, command=self.enter, text="Enter")
        self.info_var = tk.StringVar(self)
        self.info_message = tk.Message(master=self, textvariable=self.info_var, width=300)

        # Positioning
        self.split_on_message.grid(row=0, column=0, columnspan=2)
        self.split_on_entry.grid(row=1, column=0, columnspan=2)
        self.from_message.grid(row=2, column=0, columnspan=2)
        self.from_box.grid(row=3, column=0)
        self.add_button.grid(row=3, column=1)
        self.info_message.grid(row=4, column=0, columnspan=2)
        self.enter_button.grid(row=5, column=0, columnspan=2)

        # Customization
        self.from_box['values'] = columns

        self.update()
        self.center_root(self.winfo_width(), self.winfo_height())

    def add(self):
        if self.from_box.get() != "":
            self.split_on_var.set(
                self.from_box.get() if self.split_on_var.get() == "" else self.split_on_var.get() + "; "
                                                                          + self.from_box.get())
        self.from_box.set("")

    def enter(self):
        vals = self.split_on_var.get().split("; ")
        for val in vals:
            if val not in self.columns:
                self.info_var.set("Unidentified value in input")
                return
        self.callback(vals)
        self.destroy()


class ExportGraphWin(RootExpansion):
    def __init__(self, graph_dat: data.Data):
        super().__init__()

        # Back Ref
        self.graph = graph_dat

        # Members
        self.name_text = tk.Message(master=self, text="Name of New File:", width=150)
        self.name_entry = ttk.Entry(master=self, width=30)
        self.location_text = tk.Message(master=self, text="File Location:", width=150)
        self.location_var = tk.StringVar(self)
        self.location_entry = ttk.Entry(master=self, textvariable=self.location_var, width=30)
        self.location_button = ttk.Button(master=self, text="Browse", command=self.browse_location)
        self.type_message = tk.Message(master=self, text="Graph Type:", width=150)
        self.type_var = tk.StringVar(self)
        self.type_entry = ttk.Combobox(master=self, textvariable=self.type_var, state="readonly")
        self.enter_button = ttk.Button(master=self, text="Enter", command=self.enter)

        # Positioning
        self.name_text.grid(row=0, column=0, columnspan=2, padx=10, pady=5)
        self.name_entry.grid(row=1, column=0, columnspan=2, padx=10, pady=5)
        self.location_text.grid(row=2, column=0, padx=10, pady=5)
        self.location_entry.grid(row=3, column=0, padx=10, pady=5)
        self.location_button.grid(row=3, column=1, padx=10, pady=5)
        self.type_message.grid(row=4, column=0, columnspan=2, padx=10, pady=5)
        self.type_entry.grid(row=5, column=0, columnspan=2, padx=10, pady=5)
        self.enter_button.grid(row=6, column=0, columnspan=2, padx=10, pady=20)

        # Customization
        self.wm_title("Export")
        self.type_entry['values'] = ['Line', 'Scatter']

        self.update()
        self.center_root(self.winfo_width(), self.winfo_height())

    def browse_location(self):
        dir_path = tk.filedialog.askdirectory()
        self.location_var.set(dir_path)
        self.focus_force()

    def enter(self):
        name = self.name_entry.get()
        location = self.location_var.get()
        if "" not in [name, location]:
            utils.export_graph(name, location, self.graph)
            self.destroy()


# Changes the size of the MatplotLib canvas in case that it does not fit correctly
class ViewModifier(RootExpansion):
    def __init__(self, canvas: gph.GraphCanvas):
        super().__init__()

        # Back Ref
        self.canvas = canvas

        # Members
        self.width_message = tk.Message(master=self, text="Width:", width=150)
        self.width_var = tk.StringVar(master=self, value=canvas.figure.get_size_inches()[0])
        self.width_entry = ttk.Entry(master=self, textvariable=self.width_var, width=10)
        self.height_message = tk.Message(master=self, text="Height:", width=150)
        self.height_var = tk.StringVar(master=self, value=canvas.figure.get_size_inches()[1])
        self.height_entry = ttk.Entry(master=self, textvariable=self.height_var, width=10)
        self.enter_button = ttk.Button(master=self, command=self.enter, text="Enter")

        # Positioning
        self.width_message.grid(row=0, column=0, pady=5, padx=10)
        self.width_entry.grid(row=1, column=0, pady=5, padx=10)
        self.height_message.grid(row=0, column=1, pady=5, padx=10)
        self.height_entry.grid(row=1, column=1, pady=5, padx=10)
        self.enter_button.grid(row=1, column=2, pady=5, padx=10)

        # Customization
        self.title("Graph Size")

        self.update()
        self.center_root(self.winfo_width(), self.winfo_height())

    def enter(self):
        if self.width_var.get() != "" and self.height_var.get() != "":
            try:
                width = float(self.width_var.get())
                height = float(self.height_var.get())
                self.canvas.figure.set_size_inches(width, height)
                self.destroy()
            except ValueError:
                pass


class ThreeDWindow(RootExpansion):
    def __init__(self, dataset: data.Data, canvas: gph.GraphCanvas):
        super().__init__()

        # Back Ref
        self.dataset = dataset
        self.canvas = canvas

        # Members
        self.x_message = tk.Message(master=self, text="X-Axis:", width=300)
        self.x_var = tk.StringVar(self)
        self.x_entry = ttk.Combobox(master=self, textvariable=self.x_var, state="readonly")
        self.y_message = tk.Message(master=self, text="Y-Axis:", width=300)
        self.y_var = tk.StringVar(self)
        self.y_entry = ttk.Combobox(master=self, textvariable=self.y_var, state="readonly")
        self.z_message = tk.Message(master=self, text="Z-Axis:", width=300)
        self.z_var = tk.StringVar(self)
        self.z_entry = ttk.Combobox(master=self, textvariable=self.z_var, state="readonly")
        self.graph_type_message = tk.Message(master=self, text="Graph Type:", width=300)
        self.graph_type_var = tk.StringVar(self)
        self.graph_type_entry = ttk.Combobox(master=self, textvariable=self.graph_type_var, state="readonly")
        self.info_var = tk.StringVar(self)
        self.info_text = tk.Message(master=self, textvariable=self.info_var, width=300)
        self.enter_button = tk.Button(master=self, text="Enter", command=self.enter)

        # Positioning
        self.x_message.grid(row=0, column=0)
        self.x_entry.grid(row=0, column=1)
        self.y_message.grid(row=1, column=0)
        self.y_entry.grid(row=1, column=1)
        self.z_message.grid(row=2, column=0)
        self.z_entry.grid(row=2, column=1)
        self.graph_type_message.grid(row=3, column=0)
        self.graph_type_entry.grid(row=3, column=1)
        self.info_text.grid(row=4, column=0, columnspan=2)
        self.enter_button.grid(row=5, column=0, columnspan=2)

        # Customization
        vals = dataset.data_frame.columns.values.tolist()
        self.x_entry['values'] = self.y_entry['values'] = self.z_entry['values'] = vals
        self.graph_type_entry['values'] = ['Line', 'Scatter']

        self.update()
        self.center_root(self.winfo_width(), self.winfo_height())

    def enter(self):
        x = self.x_var.get()
        y = self.y_var.get()
        z = self.z_var.get()
        gtype = self.graph_type_var.get()
        if x != "" and y != "" and z != "" and gtype != "":
            self.canvas.set_graph(self.dataset.graph)
            self.canvas.threed_graph(x, y, z, gtype)
        else:
            self.info_var.set("Please select a value for every box")


class RatioWin(RootExpansion):
    def __init__(self, owner: App, dataset: data.Data):
        super().__init__()

        # Back Ref
        self.dataset = dataset
        self.owner = owner

        # Members
        self.is_single_flag = False

        self.step_1_box = ttk.LabelFrame(master=self, text="Step 1:")
        self.axis_message = tk.Message(master=self.step_1_box, text="Against:", width=150)
        self.axis_var = tk.StringVar(self.step_1_box)
        self.axis_box = ttk.Combobox(master=self.step_1_box, textvariable=self.axis_var, state="readonly")
        self.enter_axis_button = ttk.Button(master=self.step_1_box, text="Enter", command=self.enter_axis)

        self.step_2_box = ttk.LabelFrame(master=self, text="Step 2:")
        self.axis_from_text = tk.Message(master=self.step_2_box, text="Axis to Remove From:", width=150)
        self.axis_from_var = tk.StringVar(self)
        self.axis_from_entry = ttk.Combobox(master=self.step_2_box, )
        self.ratio_message = tk.Message(master=self.step_2_box, text="Target Ratio:", width=150)
        self.ratio_entry = ttk.Entry(master=self.step_2_box)
        self.margin_message = tk.Message(master=self.step_2_box, text="Margin:", width=150)
        self.margin_entry = ttk.Entry(master=self.step_2_box)
        self.ratio_exe = ttk.Button(master=self.step_2_box, text="Execute", command=self.ratio_margin_command)

        self.include_var = tk.StringVar(self.step_2_box, value="i")
        self.include_button = ttk.Radiobutton(master=self.step_2_box, text="Include", variable=self.include_var,
                                              value="i")
        self.exclude_button = ttk.Radiobutton(master=self.step_2_box, text="Exclude", variable=self.include_var,
                                              value="e")

        self.info_var = tk.StringVar(self)
        self.info = tk.Message(master=self, textvariable=self.info_var, width=150)

        # Positioning
        self.step_1_box.pack(fill="x", anchor="n", side="top", expand=True, padx=10, pady=10)
        self.step_2_box.pack(fill="x", anchor="n", side="top", expand=True, padx=10, pady=10)

        self.axis_message.grid(row=0, column=0, sticky='w', padx=10)
        self.axis_box.grid(row=1, column=0, padx=10, pady=5)
        self.enter_axis_button.grid(row=1, column=1)

        self.ratio_message.grid(row=0, column=0)
        self.ratio_entry.grid(row=1, column=0, padx=10)
        self.margin_message.grid(row=0, column=1)
        self.margin_entry.grid(row=1, column=1, padx=10)
        self.ratio_exe.grid(row=1, column=2)
        self.include_button.grid(row=2, column=0, pady=5)
        self.exclude_button.grid(row=2, column=1, pady=5)

        # Customization
        axis_list = dataset.data_frame.columns.values.tolist()
        axis_list.remove(dataset.freq_ax)
        self.axis_box['values'] = axis_list

        if self.dataset.is_ratio:
            self.axis_box["state"] = "disabled"
            self.enter_axis_button["state"] = "disabled"

        self.update()
        self.center_root(self.winfo_width(), self.winfo_height())

    def enter_axis(self):
        if self.axis_var.get() != "":
            data.calc_ratios(self.dataset, self.axis_var.get())
            self.dataset.is_ratio = True
            self.destroy()

    def ratio_margin(self):
        if self.axis_var.get() != "" and self.ratio_entry.get() != "" and self.margin_entry.get() != "":
            axis = self.axis_var.get()
            df = self.dataset.data_frame

            try:  # Convert values to floats
                margin = float(self.margin_entry.get())
                ratio = float(self.ratio_entry.get())
            except ValueError:
                self.info_var.set("Please input a number")
                return

            # Generate ratios
            ratio_columns = data.calc_ratios(self.dataset, axis)
            self.dataset.is_ratio = True

            if self.include_var == "e":  # 'e' stands for exclude, the else is if its 'i' for include
                for column in ratio_columns:  # Only use for columns that have a ratio calculated
                    self.dataset.data_frame = df[(df[ratio_columns[column]] > ratio + margin)
                                                 | (df[ratio_columns[column]] < ratio - margin)]
            else:
                for column in ratio_columns:
                    self.dataset.data_frame = df[(df[ratio_columns[column]] > ratio - margin)
                                                 & (df[ratio_columns[column]] < ratio + margin)]
                return ratio_columns

    def ratio_margin_command(self):
        self.ratio_margin()
        self.owner.main_pic.update_graph()
        self.destroy()


class SimilarRemoveWindow(RootExpansion):
    def __init__(self, owner: App, dataset: data.Data):
        super().__init__()

        # Back Ref
        self.owner = owner
        self.dataset = dataset

        # Members
        self.dataset_message = tk.Message(master=self, text="Dataset to Remove From:", width=150)
        self.dataset_var = tk.StringVar(self)
        self.dataset_entry = ttk.Combobox(master=self, textvariable=self.dataset_var, state="readonly")
        self.threshold_message = tk.Message(master=self, text="Threshold (kHz):", width=150)
        self.threshold_entry = ttk.Entry(master=self)
        self.include_var = tk.IntVar(self)
        self.include_check = ttk.Checkbutton(master=self, text="Include List of Removed", variable=self.include_var)
        self.replace_var = tk.IntVar(self)
        self.replace_check = ttk.Checkbutton(master=self, text="Replace Known", variable=self.replace_var)
        self.include_var = tk.IntVar(self)
        self.include_check = ttk.Checkbutton(master=self, text="Include", variable=self.include_var,
                                             command=self.include_command)
        self.enter_button = ttk.Button(master=self, command=self.enter, text="Enter")

        # Positioning
        self.dataset_message.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.dataset_entry.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.threshold_message.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.threshold_entry.grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.include_check.grid(row=4, column=0, sticky="w", padx=10)
        self.replace_check.grid(row=5, column=0, sticky="w", padx=10)
        self.enter_button.grid(row=6, column=0, padx=10, pady=15)

        # Customization
        self.data_map = {}
        for value in self.owner.data_storage.data_list:
            if value != self.dataset:
                self.data_map[value.name] = value
        self.dataset_entry['values'] = list(self.data_map.keys())

        self.update()
        self.center_root(self.winfo_width(), self.winfo_height())

    def enter(self):
        if self.dataset_var.get != "" and self.threshold_entry.get() != "":
            try:
                threshold = float(self.threshold_entry.get())
                data.remove_from(on=self.dataset, values_from=self.data_map[self.dataset_var.get()],
                                 threshold=threshold, return_removed=bool(self.include_var.get()),
                                 add_back=bool(self.replace_var.get()))
                self.destroy()
            except ValueError:
                pass  # If value is not a number, then ignore the input

    def include_command(self):
        if self.replace_check["state"] == "disabled":
            self.replace_check["state"] = "normal"
        else:
            self.replace_var.set(0)
            self.replace_check["state"] = "disabled"


class DataSettingsUpdater(RootExpansion):
    def __init__(self, dataset: data.Data):
        super().__init__()

        # Back ref
        self.dataset = dataset

        # Members
        self.name_message = tk.Message(master=self, text="Name:", width=150)
        self.name_var = tk.StringVar(self, value=self.dataset.name)
        self.name_entry = ttk.Entry(master=self, textvariable=self.name_var)

        self.freqax_message = tk.Message(master=self, text="Frequency Axis:", width=150)
        self.freqax_var = tk.StringVar(self, value=self.dataset.freq_ax)
        self.freqax_entry = ttk.Combobox(master=self, values=self.dataset.data_frame.columns.values.tolist(),
                                         state="readonly", textvariable=self.freqax_var)

        self.ax_message = tk.Message(master=self, text="X-Axis:", width=150)
        self.ax_var = tk.StringVar(self, value=self.dataset.ax)
        self.ax_entry = ttk.Combobox(master=self, values=self.dataset.data_frame.columns.values.tolist(),
                                     state="readonly", textvariable=self.ax_var)

        self.enter_button = ttk.Button(master=self, command=self.enter, text="Enter")

        # Positioning
        self.name_message.grid(row=0, column=0, padx=10, pady=5)
        self.name_entry.grid(row=1, column=0, padx=10, pady=5)
        self.freqax_message.grid(row=2, column=0, padx=10, pady=5)
        self.freqax_entry.grid(row=3, column=0, padx=10, pady=5)
        self.ax_message.grid(row=4, column=0, padx=10, pady=5)
        self.ax_entry.grid(row=5, column=0, padx=10, pady=5)
        self.enter_button.grid(row=6, column=0, padx=10, pady=20)

        # Customization
        self.update()
        self.center_root(self.winfo_width(), self.winfo_height())

    def enter(self):
        if self.name_var.get() != "" and self.freqax_var.get() != "" and self.ax_var.get() != "":
            self.dataset.name = self.name_var.get()
            self.dataset.freq_ax = self.freqax_var.get()
            self.dataset.ax = self.ax_var.get()
            self.dataset.owner.sidebar.update_data()
            self.destroy()


class SaveDatasetWindow(RootExpansion):
    def __init__(self, dataset):
        super().__init__()

        # Back Ref
        self.dataset = dataset

        # Members
        self.name_message = tk.Message(master=self, text="Name:", width=150)
        self.location_message = tk.Message(master=self, text="Location:", width=200)
        self.location_var = tk.StringVar(self)
        self.location_entry = ttk.Entry(master=self, textvariable=self.location_var, width=30)
        self.location_button = ttk.Button(master=self, text="Browse", command=self.browse)
        self.enter_button = ttk.Button(master=self, text="Enter", command=self.enter)

        # Positioning
        self.location_message.grid(row=0, column=0, columnspan=2, padx=10, pady=5)
        self.location_entry.grid(row=1, column=0, padx=10, pady=5)
        self.location_button.grid(row=1, column=2, padx=10, pady=5)
        self.enter_button.grid(row=2, column=0, columnspan=2, padx=10, pady=5)

        # Customization
        self.update()
        self.center_root(self.winfo_width(), self.winfo_height())

    def enter(self):
        try:
            self.dataset.save(self.location_entry.get())
        except ValueError:
            error("This is not a valid path")
        self.destroy()

    def browse(self):
        path = tk.filedialog.askdirectory()
        self.location_var.set(path)
        self.focus_force()
