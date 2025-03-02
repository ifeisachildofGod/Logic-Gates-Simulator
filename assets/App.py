import os
import sys
import json
import pickle
import pygame
import threading
import subprocess
from pathlib import Path
from assets.save import Save
from assets.modules import set_color
from assets.widgets import MenuBar, ListView, Button
from assets.logic_circuits_display import CircuitDisplay
from assets.settings import SCR_WIDTH, SCR_HEIGHT, FPS, APP_NAME

class App:
    def __init__(self, file_path: str | None, new_file: bool) -> None:
        pygame.init()
        
        self.screen = pygame.display.set_mode((SCR_WIDTH, SCR_HEIGHT))
        logo = pygame.image.load('assets/logos/logo.png')
        pygame.display.set_icon(logo)
        pygame.display.set_caption(APP_NAME + ' - *Unsaved' if file_path is None else '')
        self.clock = pygame.time.Clock()
        
        self._file_path = file_path
        
        self.mainpy_file_path = [path.as_posix() for path in list(Path(os.getcwd()).glob('*.py'))][0]
        
        self.font = pygame.font.SysFont('Consolas', 20)
        
        with open('assets/themes.json') as file:
            self.bg_colors = json.loads(file.read())
        
        self._bg_color = None
        self.BG_COLOR_tracker = self.bg_colors["0"]
        
        self.save = Save(self.file_path, {}, self._open_new, ['IFEs Logical File', '*.logic'], self._save_func)
        
        self.reset_it = False
        
        self.button_colors = '#777777'
        self.button_text_colors = 'white'
        self.border_radius = 10
        self.border_offset = 30
        self.add_buttons_size = 30, 39
        self.add_buttons_border_offset = 30
        
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
        app_control_options = {
            "New Circuit": self.circuit_displayer._make_new_circuit,
            "   Create  ": self.circuit_displayer._make_gate,
            " Edit Gate ": self.circuit_displayer._edit_circuit,
        }
        
        self.menubar = MenuBar(self.screen, 0, 40, 20, 100, 25, 'grey15', 'grey15', 'lightblue', 'white', 'grey15', 2, 2, 2, menu_bar_options, dropdown_font_family='System')
        
        self.detailed_font = pygame.font.SysFont('Arial', 500)
        self.add_node_font = pygame.font.SysFont('Arial', 45)
        self.edit_button_font = pygame.font.SysFont('Sans Serif', 20)
        
        self.delete_circuit_button = Button(self.screen, (0, 0), (10, 10), 'red', image=self.detailed_font.render('x', True, 'white'), on_left_mouse_button_clicked=self.circuit_displayer._remove_cicuit, border_radius=0, scale_img=True)
        
        self.prev_circuit_button = Button(self.screen, (0, 0), (20, 20), self.button_colors, image=self.edit_button_font.render('<', True, self.button_text_colors), on_left_mouse_button_clicked=lambda: self.circuit_displayer._change_circuit(self.circuit_displayer.circuit_index - 1))
        self.next_circuit_button = Button(self.screen, (0, 0), (20, 20), self.button_colors, image=self.edit_button_font.render('>', True, self.button_text_colors), on_left_mouse_button_clicked=lambda: self.circuit_displayer._change_circuit(self.circuit_displayer.circuit_index + 1))
        
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
                                    'grey30',
                                    'grey6',
                                    None,
                                    'white',
                                    app_control_widget_spacing,
                                    app_control_widget_x_border_offset,
                                    app_control_widget_y_border_offset,
                                    app_control_options,
                                    'horizontal',
                                    font=pygame.font.SysFont('Cambria', int(app_control_widget_height / 2)))
        
        self.delete_circuit_button.set_pos(bottomright=self.app_control.bg_rect.topright)
        self.prev_circuit_button.set_pos(midright=(self.app_control.bg_rect.left, self.app_control.bg_rect.centery))
        self.next_circuit_button.set_pos(midleft=(self.app_control.bg_rect.right, self.app_control.bg_rect.centery))
        
        self.gate_circuit_index_tracker = None
    
    @property
    def file_path(self):
        return self._file_path
    
    @file_path.setter
    def file_path(self, v):
        self._file_path = v
        pygame.display.set_caption(f'{APP_NAME} - {self._file_path}')
    
    @property
    def BG_COLOR(self):
        return self._bg_color
    
    @BG_COLOR.setter
    def BG_COLOR(self, v):
        self._bg_color = v
        self.circuit_displayer.theme_color = self._bg_color
        self._recolor_widgets(self._bg_color)
    
    def _init_circuit_displayer(self, new_file: str):
        self.circuit_displayer = CircuitDisplay(self.screen, len(self.bg_colors), self.add_buttons_border_offset, self.add_buttons_size, 40)
        if self.file_path is not None and not new_file:
            with open(self.file_path, 'rb') as file_path:
                value = pickle.load(file_path)
                self.file_path = self.save.file_path
                self.circuit_displayer.set_dict(value)
    
    def _save_func(self, info, file_path):
        pickle.dump(info, open(file_path, 'wb'))
        self.file_path = self.save.file_path
    
    def _open_new(self, file_path, new_file):
        subprocess_thread = threading.Thread(target=lambda: subprocess.run(['py', self.mainpy_file_path, file_path, str(int(new_file))]))
        subprocess_thread.daemon = True
        subprocess_thread.start()
    
    def _recolor_widgets(self, color):
        buttons_ui_colors = set_color(color, 170)
        menu_bar_ui_color = set_color(color, 120)
        app_control_ui_color = set_color(color, 30)
        app_control_buttons_ui_color = set_color(color, 210)
        
        self.prev_circuit_button.configure(bg_color=buttons_ui_colors)
        self.next_circuit_button.configure(bg_color=buttons_ui_colors)
        
        self.menubar.configure(bg_color=menu_bar_ui_color)
        self.app_control.configure(bg_color=app_control_ui_color)
        for button in self.app_control.buttons:
            button.configure(bg_color=app_control_buttons_ui_color)
    
    def _on_save(self):
        self.save.update_info(self.circuit_displayer.get_dict())
        self.reset_it = False
    
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
        
        self.circuit_displayer.update(self.events, self.BG_COLOR)
        self.app_control.buttons[-1].configure(disabled=self.circuit_displayer.edit_index is None)
        
        if self.circuit_displayer.circuit_index > 0:
            self.delete_circuit_button.update()
            self.prev_circuit_button.update()
            self.prev_circuit_button.configure(border_radius=-1, border_top_left_radius=self.border_radius, border_bottom_left_radius=self.border_radius, border_top_right_radius=-1, border_bottom_right_radius=-1)
        
        if self.circuit_displayer.circuit_index < len(self.circuit_displayer.circuit_editors) - 1:
            self.next_circuit_button.update()
            self.next_circuit_button.configure(border_radius=-1, border_top_left_radius=-1, border_bottom_left_radius=-1, border_top_right_radius=self.border_radius, border_bottom_right_radius=self.border_radius)
        
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

            self.BG_COLOR_tracker = self.bg_colors[str(self.circuit_displayer.circuit_index)]
            
            if self.BG_COLOR != self.BG_COLOR_tracker:
                self.BG_COLOR = self.BG_COLOR_tracker
            
            if self.save.file_path is not None:
                if self.circuit_displayer.get_dict() != self.save.save_info:
                    if not self.reset_it:
                        pygame.display.set_caption(f'{APP_NAME} - {self._file_path} - *Unsaved')
                        self.reset_it = True
            
            self.screen.fill(self.BG_COLOR)
            
            self.events = pygame.event.get()
            for event in self.events:
                self._event_loop(event)
            
            self._app_loop()

            pygame.display.update()
    
