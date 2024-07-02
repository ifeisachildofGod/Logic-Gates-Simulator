import json
import subprocess
import sys
import threading
import pygame
from settings import SCR_WIDTH, SCR_HEIGHT, FPS
from logic_circuits_display import GateDisplay
from widgets import MenuBar, ListView
from misc import Save
import pickle


class App:
    def __init__(self, file_path: str | None, main_file_path: str, new_file: bool) -> None:
        pygame.init()
        
        self.screen = pygame.display.set_mode((SCR_WIDTH, SCR_HEIGHT))
        logo = pygame.image.load('logos/logo.png')
        pygame.display.set_icon(logo)
        pygame.display.set_caption('IFEs Logic Gate Simulator')
        self.clock = pygame.time.Clock()
        
        self._file_path = file_path
        
        self.main_file_path = main_file_path
        
        self.font = pygame.font.SysFont('Consolas', 20)
        
        with open('themes.json') as file:
            self.bg_colors = json.loads(file.read())
        
        self.BG_COLOR = self.bg_colors["0"]
        
        self.save = Save(self.file_path, {}, self._open_new, ['IFEs Logical File', '*.logic'], self._save_func)
        
        self._init_circuit_displayer(new_file)
        
        menu_bar_options = {
            "File": {
                'New': self.save.new,
                'Open': self.save.open,
                'Save': self._save,
                'Save As': self._save_as,
                'Close': self._quit,
            },
            "Edit": {
                'Undo': print,
                'Redo': print,
                'Cut': print,
                'Copy': print,
                'Paste': print,
            }
        }
        self.menubar = MenuBar(self.screen, 0, 50, 25, 'blue', 'white', 'black', 2, 2, 2, menu_bar_options)
        
        app_control_options = {
            "     I+     ": lambda: self.circuit_displayer.circuit.add_input(),
            "New Circuit": self.circuit_displayer._make_new_circuit,
            " Make Gate ": self.circuit_displayer._make_gate,
            "     O+     ": lambda: self.circuit_displayer.circuit.add_output(),
        }
        app_control_widget_width = 90
        app_control_widget_height = 25
        app_control_widget_spacing = 10
        app_control_widget_x_border_offset = 5
        app_control_widget_y_border_offset = 3
        app_control_width = (app_control_widget_spacing + app_control_widget_width + (app_control_widget_x_border_offset * 2)) * len(app_control_options)
        self.app_control = ListView(self.screen,
                                    ((self.screen.get_width() / 2) - (app_control_width / 2),
                                     self.screen.get_height() - app_control_widget_height - (app_control_widget_y_border_offset * 2)),
                                    app_control_widget_width,
                                    app_control_widget_height,
                                    'blue',
                                    'white',
                                    app_control_widget_spacing,
                                    app_control_widget_x_border_offset,
                                    app_control_widget_y_border_offset,
                                    app_control_options,
                                    'horizontal')
        
        self.gate_circuit_index_tracker = None
    
    @property
    def file_path(self):
        return self._file_path
    
    @file_path.setter
    def file_path(self, v):
        self._file_path = v
        pygame.display.set_caption(f'IFEs Logic Gate Simulator - {self._file_path}')
    
    def _init_circuit_displayer(self, new_file: str):
        self.circuit_displayer = GateDisplay(self.screen, 100)
        if self.file_path is not None and not new_file:
            with open(self.file_path, 'rb') as file_path:
                value = pickle.load(file_path)
                self.file_path = self.save.file_path
                self.circuit_displayer.set_dict(value)
    
    def _save_func(self, info, file_path):
        pickle.dump(info, open(file_path, 'wb'))
        self.file_path = self.save.file_path
    
    def _open_new(self, file_path, new_file):
        subprocess_thread = threading.Thread(target=lambda: subprocess.run(['py', self.main_file_path, file_path, str(int(new_file))]))
        subprocess_thread.daemon = True
        subprocess_thread.start()
    
    def _on_save(self):
        self.save.update_info(self.circuit_displayer.get_dict())
    
    def _save(self):
        self._on_save()
        self.save.save()
    
    def _save_as(self):
        self._on_save()
        self.save.save_as()
    
    def _quit(self):
        pygame.quit()
        sys.exit()
    
    def _app_loop(self):
        self.fps_surf = self.font.render(f'FPS: {round(self.clock.get_fps())}', False, 'white')
        self.fps_rect = self.fps_surf.get_rect(bottomright=(SCR_WIDTH - 20, SCR_HEIGHT))
        self.screen.blit(self.fps_surf, self.fps_rect)
        
        self.circuit_displayer.update(self.events)
        self.menubar.update()
        self.app_control.update()
    
    def _event_loop(self, event):
        self.keys = pygame.key.get_pressed()
        
        if event.type == pygame.QUIT:
            self._quit()
    
    def run(self):
        while True:
            self.keys = pygame.key.get_pressed()
            self.mouse_pos = pygame.mouse.get_pos()
            self.delta_time = self.clock.tick(FPS)
            
            self.BG_COLOR = self.bg_colors[str(self.circuit_displayer.circuit_index)]
            
            if self.gate_circuit_index_tracker != self.circuit_displayer.circuit_index:
                self.circuit_displayer.theme_color = self.BG_COLOR
            
            self.screen.fill(self.BG_COLOR)

            self.events = pygame.event.get()
            for event in self.events:
                self._event_loop(event)
            
            self._app_loop()

            pygame.display.update()
    
