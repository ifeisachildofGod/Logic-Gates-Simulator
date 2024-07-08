import os
import json
from pathlib import Path
from tkinter import filedialog
from typing import Any, Callable

class Save:
    def __init__(self, file_path: str, init_save_info: Any, new_screen_initializer_func: Callable[[str, bool], None], filetype: tuple[str, str], save_func: Callable[[Any, str], None] = None):
        self.filetype = filetype
        self.save_info = init_save_info
        self.save_func = save_func if save_func is not None else self._default_save
        self.new_screen_initializer_func = new_screen_initializer_func
        self.file_path = Path(file_path).absolute().as_posix() if file_path is not None else None
    
    def _default_save(self, info, file_path):
        with open(file_path, 'w') as save_file:
            save_file.write(json.dumps(info, indent=2))
    
    def _get_new_or_saveas_filedialog(self, title: str):
        path = filedialog.asksaveasfilename(initialdir=os.getcwd(), filetypes=[self.filetype, ], title=title)
        
        if path:
            file_extention = '.' + self.filetype[1].split('.')[-1]
            if path.endswith(file_extention):
                return path
            return path + file_extention
    
    def _get_open_filedialog(self):
        path = filedialog.askopenfilename(initialdir=os.getcwd(), filetypes=[self.filetype, ], title='Open File')
        if path:
            return path
    
    def _get_save_filedialog(self):
        if self.file_path:
            return self.file_path
        return self._get_new_or_saveas_filedialog('Save File')
    
    def _save_or_saveas(self, file_path):
        if file_path:
            self.file_path = file_path
            self.save_func(self.save_info, self.file_path)
    
    def new(self):
        file_path = self._get_new_or_saveas_filedialog('New File')
        if file_path:
            self.new_screen_initializer_func(file_path, True)
    
    def open(self):
        file_path = self._get_open_filedialog()
        if file_path:
            self.new_screen_initializer_func(file_path, False)
    
    def save(self):
        file_path = self._get_save_filedialog()
        self._save_or_saveas(file_path)
    
    def save_as(self):
        file_path = self._get_new_or_saveas_filedialog('Save As File')
        self._save_or_saveas(file_path)
    
    def update_info(self, save_info: Any):
        self.save_info = save_info

