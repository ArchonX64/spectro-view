# spectro-view
A flexible application for analyzing spectroscopic data, specifically for microwave spectroscopy. Allows a number of input files and ways to modify and find patterns in data!

Supported Files: .csv, .cat, .ft, .txt, custom file types (WIP)

Required Dependencies:
pandas, matplotlib, tkinter, openpyxl, xlsx2csv, numpy, scipy

Creating An Executable:
- Install PyInstaller in any location
- From cmd, call your location of PyInstaller along with the location of "main.spec"
- Ex: "C:\Foo\PyInstaller.exe C:\Bar\main.spec"
- Executable will appear in a newly created "dist" folder in the location of main.spec
