"""
An ASCII Visual Python File Class/Function Explorer - Pure Python with no dependencies.

Tested with Python 3.12 on Windows 7, 10 and 11.

Source,
https://github.com/Hagtronics/Python-File-Visual-Class-and-Function-Explorer

Totally freeware - See the "Unlicense",
https://github.com/Hagtronics/Python-File-Visual-Class-and-Function-Explorer/blob/main/LICENSE

Written: Aug 6, 2026
"""
from __future__ import annotations

import ast
import ctypes
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


#$ ===== ASCII Tree Generator Core =====
class TreeGen:
    """
    Generate an ASCII tree of all top-level functions, classes,
    methods, and their decorators.
    """
    def __init__(self) -> None:
        self.output_tree = ''

    def generate_tree(self, module_path: str | Path) -> None:
        self.path = Path(module_path)
        try:
            self.tree = ast.parse(
                self.path.read_text(encoding='utf-8'),
                filename=str(self.path),
            )
        except SyntaxError:
            self.output_tree = 'Invalid Syntax Exception.\nNot a valid Python file?'
            return

        self.lines = [self.path.name]

        items = [
            node
            for node in self.tree.body
            if isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
            )
        ]

        for i, node in enumerate(items):
            last = i == len(items) - 1

            if isinstance(node, ast.ClassDef):
                branch = '└── ' if last else '├── '
                decorators = self._format_decorators(node.decorator_list)
                self.lines.append(f'{branch}{node.name}{decorators}')

                methods = [
                    n
                    for n in node.body
                    if isinstance(
                        n,
                        (ast.FunctionDef, ast.AsyncFunctionDef),
                    )
                ]

                prefix = '    ' if last else '│   '

                for j, method in enumerate(methods):
                    self._add_function(
                        method,
                        prefix,
                        j == len(methods) - 1,
                    )

            else:
                self._add_function(node, '', last)

        self.output_tree = '\n'.join(self.lines)

    def _decorator_name(self, dec: ast.AST) -> str:
        """Return a readable decorator string."""
        try:
            return ast.unparse(dec)  # Python 3.9+
        except AttributeError:
            if isinstance(dec, ast.Name):
                return dec.id
            elif isinstance(dec, ast.Attribute):
                return f'{self._decorator_name(dec.value)}.{dec.attr}'
            else:
                return '<decorator>'

    def _format_decorators(self, decorator_list: list[ast.expr]) -> str:
        if not decorator_list:
            return ''
        return ' ' + ' '.join(
            f'@{self._decorator_name(dec)}'
            for dec in decorator_list
        )

    def _add_function(
        self,
        func: ast.FunctionDef | ast.AsyncFunctionDef,
        prefix: str,
        is_last: bool,
    ) -> None:
        branch = '└── ' if is_last else '├── '
        suffix = ' async' if isinstance(func, ast.AsyncFunctionDef) else ''
        decorators = self._format_decorators(func.decorator_list)

        self.lines.append(
            f'{prefix}{branch}{func.name}(){suffix}{decorators}'
        )

    def get_tree(self) -> str:
        return self.output_tree


#$ ===== Helper Functions =====
def set_dpi_awareness()->None:
    """
    Set the apps DPI awareness (if possible) - This works for Windows only
    Must be run before any windows are spawned.
    """
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2) # '2' scales across all windows.
        # print('Info: DPI Awareness set for Win 8.1, 10 or 11.')

        # Returns: 100, 125, 150, etc. Can be used later to help resize windows, etc.
        # win_sf = ctypes.windll.shcore.GetScaleFactorForDevice(0)
        # print(f'Info: Current Text Scale Factor = {win_sf}.')
    except:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
            # print('info: DPI set for Win 7, 8')
        except:
            print('Info: DPI Awareness could not be set!')


def center_window(window):
    """ Center Tk Window on screen """
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f'{width}x{height}+{x}+{y}')


def trim_path_middle(path: str, max_len: int) -> str:
    """
    Trim a directory path to a maximum length by inserting ellipsis in the middle.
    Priority:
      - Preserve the final directory/file name as fully as possible.
      - Preserve the separator before the final component if it fits.
      - Only keep front characters if there is remaining space.
    """
    if len(path) <= max_len:
        return path

    ellipsis = '...'
    ellipsis_len = len(ellipsis)

    # Determine separator
    sep = '\\' if '\\' in path else '/'

    parts = path.split(sep)

    # If no meaningful split, fallback to simple end-preserving trim
    if len(parts) == 1:
        end_len = max_len - ellipsis_len
        return ellipsis + path[-end_len:]

    last_part = parts[-1]
    last_with_sep = sep + last_part  # what we want to preserve if possible

    # Space available for the end portion
    end_space = max_len - ellipsis_len

    # If the last component (with separator) is too long, trim its left side
    if len(last_with_sep) > end_space:
        return ellipsis + last_with_sep[-end_space:]

    # Otherwise, we can keep the whole last component + separator
    end_len = len(last_with_sep)
    front_space = max_len - ellipsis_len - end_len

    # Keep as much of the front as possible
    front = path[:front_space]

    return front + ellipsis + last_with_sep


#$ ===== TkInter Main Window GUI =====
class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title('Python Visual File Explorer')
        self.geometry('640x700')
        self.minsize(640, 700)
        center_window(self)

        self._build_ui()
        self._connect_slots()
        self._configure_resizing()

        self.selected_diectory = ''


    #$ ===== Build UI =====
    def _build_ui(self):

        # Main window grid behavior
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)
        self.grid_rowconfigure(0, minsize=0)
        self.grid_rowconfigure(2, minsize=0)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        # Row 0: Folder selection + File display
        self.btnSelectFile = ttk.Button(self, text='Select File', width=30)
        self.btnSelectFile.grid(row=0, column=0, padx=10, pady=10, sticky='ew')

        self.txtFile = ttk.Entry(self)
        self.txtFile.insert(0, 'Please Select A Python File...')
        self.txtFile.state(['readonly'])
        self.txtFile.grid(row=0, column=1, columnspan=3, padx=10, pady=10, sticky='ew')

        # Row 1: Text Box with Scrollbars
        self.txtFrame = ttk.Frame(self)
        self.txtFrame.grid(row=1, column=0, columnspan=4, padx=10, pady=(0,0), sticky='nsew')

        # Text frame grid behavior
        self.txtFrame.rowconfigure(0, weight=1)   # text expands
        self.txtFrame.rowconfigure(1, weight=0)   # horizontal scrollbar stays fixed
        self.txtFrame.columnconfigure(0, weight=1)

        self.txtTreeView = tk.Text(self.txtFrame, wrap='none')
        self.txtTreeView.grid(row=0, column=0, sticky='nsew')

        self.txtTreeView.insert('1.0', 'No Tree View Generated Yet...')

        self.scrollY = ttk.Scrollbar(self.txtFrame, orient='vertical',
                                    command=self.txtTreeView.yview)
        self.scrollY.grid(row=0, column=1, sticky='ns')

        self.scrollX = ttk.Scrollbar(self.txtFrame, orient='horizontal',
                                    command=self.txtTreeView.xview)
        self.scrollX.grid(row=1, column=0, sticky='ew')

        self.txtTreeView.configure(yscrollcommand=self.scrollY.set,
                                xscrollcommand=self.scrollX.set)

        # Row 2: Copy + Exit
        self.btnCopy = ttk.Button(self, text='Copy Tree To Clipboard', width=30)
        self.btnCopy.grid(row=2, column=0, padx=10, pady=(10,10), sticky='w')

        self.btnExit = ttk.Button(self, text='Exit')
        self.btnExit.grid(row=2, column=3, padx=10, pady=(10,10), sticky='e')


    #$ ===== Connect Slots =====
    def _connect_slots(self)->None:
        self.btnSelectFile.configure(command=self.slot_select_dir)
        self.btnCopy.configure(command=self.slot_copy)
        self.btnExit.configure(command=self.slot_exit)


    #$ ===== Construct App Window as Resizable =====
    def _configure_resizing(self)->None:
        # Make columns expand
        self.columnconfigure(0, weight=0)   # buttons
        self.columnconfigure(1, weight=1)   # entry
        self.columnconfigure(2, weight=1)   # buttons
        self.columnconfigure(3, weight=1)   # buttons


    #$ ===== Slots (Callbacks) =====
    def slot_select_dir(self)->None:
        file = filedialog.askopenfilename(
            title='Select A Python File',
            filetypes=[
                ('Python Files', '*.py'),
                ('All Files', '*.*'),
                ],
        )

        if file:
            p = Path(file)
            if (not file) or (not p.exists()) or (not p.is_file()):
                messagebox.showwarning('Warning', 'Please select a valid file first.')
                return

            # Figure out the line edit current character width - changes with DPI and Text Size.
            sample_string = 'Lorem ipsum dolor'  # Will work with non-monospaced fonts also.
            font = tkfont.Font(font=self.txtFile.cget('font'))
            char_width = font.measure(sample_string) / len(sample_string)
            entry_width = self.txtFile.winfo_width()
            chars_visible = int(entry_width / char_width)
            # print(f'{chars_visible = }')

            self.txtFile.state(['!readonly'])
            self.txtFile.delete(0, 'end')
            self.txtFile.insert(0, trim_path_middle(file, max_len=chars_visible))
            self.txtFile.state(['readonly'])
            tg = TreeGen()
            self.txtTreeView.delete('1.0', tk.END)
            self.txtTreeView.insert('1.0', 'Working...')
            self.txtTreeView.update()
            try:
                tg.generate_tree(str(file))
            except:
                self.txtTreeView.delete('1.0', tk.END)
                self.txtTreeView.insert('1.0', 'Parsing error.\nIs the file you picked a valid Python file?')

            tree = tg.get_tree()
            if len(tree) == 0:
                self.txtTreeView.delete('1.0', tk.END)
                self.txtTreeView.insert('1.0', 'No Tree Was Generated.\nIs the file you picked a valid Python file?')
            else:
                self.txtTreeView.delete('1.0', tk.END)
                self.txtTreeView.insert('1.0', tree)

    def slot_copy(self):
        text = self.txtTreeView.get('1.0', tk.END).strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)

    def slot_exit(self):
        self.destroy()


#$ ===== Tk Main Loop =====
if __name__ == '__main__':
    set_dpi_awareness()
    app = MainWindow()
    app.mainloop()

# Fini
