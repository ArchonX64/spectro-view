# spectro-view
A flexible application for analyzing spectroscopic data, specifically for microwave spectroscopy. Allows a number of input files and ways to modify and find patterns in data!

Documentation: [SpectroView User GUide](https://docs.google.com/document/d/1115FLJRKV3av07rBjWV4WWhspwziUJL0CXjLDepaTSg/edit?usp=sharing)

Supported Files: .csv, .cat, .ft, .txt, custom file types (WIP)

Required Dependencies:
pandas, matplotlib, tkinter, openpyxl, xlsx2csv, numpy, scipy

Using PyInstaller to Create An Executable:
- SpectroView supports using pyinstaller to create easy to open executables on your device.
- Once PyInstaller is downloaded, run PyInstaller in your command line along with the location of the "main.spec" file.
- An executable will be created in a new "dist" folder in your project folder.

This project is still in a very early stage, and the primary focus is making sure that this application is usable and useful.
Refinements will be the next big step!

Special thanks to Rebecca Peebles to providing peaky.py, a program that provides peak fitting functions.
