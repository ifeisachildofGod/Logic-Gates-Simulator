import json
import sys
import pygame
# import random
from settings import *
from logic_gates import *
from typing import Callable
from logic_circuits import Circuit
from widgets import Button, ScrollableSurface
from pygame_textinput import TextInputManager, TextInputVisualizer


class App:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCR_WIDTH, SCR_HEIGHT))
        logo = pygame.image.load('logos/logo.png')
        pygame.display.set_icon(logo)
        pygame.display.set_caption('IFEs Logic Gate Simulator')
        self.clock = pygame.time.Clock()
        self.BG_COLOR = 'black'
        
        with open('themes.json') as file:
            self.bg_colors = json.loads(file.read())
        
        self.max_circuit_amt = len(self.bg_colors)
        
        # self.bg_colors = [(255 * random.uniform(0, 1), 255 * random.uniform(0, 1), 255 * random.uniform(0, 1)) for _ in range(self.max_circuit_amt)]
        # with open('themes.json', "w") as file:
        #     file.write(json.dumps({index: color for index, color in enumerate(self.bg_colors)}, indent=2))
        
        self.BG_COLOR = self.bg_colors['0']
        
        self.events = pygame.event.get()
        
        self.button_colors = '#777777'
        self.button_text_colors = 'white'
        self.button_border_offset = 20
        self.border_offset = 30
        self.border_radius = 10
        self.add_buttons_size = 30, 39
        
        self.new_gate_tracker = None
        
        self.circuit_editors: list[Circuit] = []
        self.circuit_names = []
        self.circuit_index = -1
                
        self.detailed_font = pygame.font.SysFont('Arial', 500)
        self.add_node_font = pygame.font.SysFont('Arial', 45)
        self.edit_button_font = pygame.font.SysFont('Sans Serif', 20)
        self.textinput_font = pygame.font.SysFont('Consolas', 55)
        
        self.delete_circuit_button = Button(self.screen, (0, 0), (15, 25), 'red', image=self.detailed_font.render('x', True, 'white'), on_left_mouse_button_clicked=self._remove_cicuit, border_radius=0, scale_img=True)
        self.delete_circuit_button.set_pos(topright=(self.screen.get_width(), 0))
        
        self.edit_gate_option_button = Button(self.screen, (0, 0), (100, 20), self.button_colors, image=self.edit_button_font.render('Edit', True, self.button_text_colors), border_radius=self.border_radius, on_left_mouse_button_clicked=self._edit_circuit)
        self.edit_gate_option_button.set_pos(midtop=(self.screen.get_width() / 2, 0))
        
        self.textinput_manager = TextInputManager(validator = lambda input: len(input) < 25)
        self.textinput = TextInputVisualizer(manager=self.textinput_manager, font_color=(255, 255, 255), font_object=self.textinput_font)
        self.textinput.cursor_width = 4
        self.textinput.cursor_color = [(c+200)%255 for c in self.textinput.font_color]
        self.textinput.cursor_visible = True
        self.textinput_rect = self.textinput.surface.get_rect(midtop=(self.screen.get_width() / 2, self.delete_circuit_button.rect.bottom))
        
        self.new_gate_circuit_button = Button(self.screen, (0, 0), (100, 20), self.button_colors, image=self.edit_button_font.render('New Circuit', True, self.button_text_colors), border_radius=self.border_radius, on_left_mouse_button_clicked=self._make_new_circuit)
        self.new_gate_circuit_button.set_pos(topleft=(self.button_border_offset, self.delete_circuit_button.rect.bottom))
        self.add_gate_button = Button(self.screen, (0, 0), (100, 20), self.button_colors, image=self.edit_button_font.render('Make Gate', True, self.button_text_colors), border_radius=self.border_radius, on_left_mouse_button_clicked=self._make_gate)
        self.add_gate_button.set_pos(topright=(self.screen.get_width() - self.button_border_offset, self.delete_circuit_button.rect.bottom))
        
        self.prev_circuit_button = Button(self.screen, (0, 0), (20, 20), self.button_colors, image=self.edit_button_font.render('<', True, self.button_text_colors), on_left_mouse_button_clicked=lambda: self._change_circuit(self.circuit_index - 1), border_radius=self.border_radius)
        self.prev_circuit_button.set_pos(topleft=(0, self.add_gate_button.rect.bottom))
        self.next_circuit_button = Button(self.screen, (0, 0), (20, 20), self.button_colors, image=self.edit_button_font.render('>', True, self.button_text_colors), on_left_mouse_button_clicked=lambda: self._change_circuit(self.circuit_index + 1), border_radius=self.border_radius)
        self.next_circuit_button.set_pos(topright=(self.screen.get_width(), self.add_gate_button.rect.bottom))
        
        self.add_input_button = Button(self.screen, (0, 0), self.add_buttons_size, self.button_colors, image=self.add_node_font.render('+', True, self.button_text_colors), on_left_mouse_button_clicked=lambda: self.circuit.add_input(), border_radius=self.border_radius)
        self.add_input_button.set_pos(midbottom=(self.border_offset, self.screen.get_height() - self.border_offset))
        self.add_output_button = Button(self.screen, (0, 0), self.add_buttons_size, self.button_colors, image=self.add_node_font.render('+', True, self.button_text_colors), on_left_mouse_button_clicked=lambda: self.circuit.add_output(), border_radius=self.border_radius)
        self.add_output_button.set_pos(midbottom=(self.screen.get_width() - self.border_offset, self.screen.get_height() - self.border_offset))

        self.edit_index = None
        self.edit_indices = []
        self._make_new_circuit()
        
        self.textinput_focused = False
        self.has_textinput_focus = False
        
        self.constant_gate_options = [AndGate(self.screen, (0, 0), lambda node: self.circuit.on_node_clicked(node)),
                                      NotGate(self.screen, (0, 0), lambda node: self.circuit.on_node_clicked(node)),
                                      TimerGate(self.screen, (0, 0), lambda node: self.circuit.on_node_clicked(node))]
        
        self.gate_options: list[GateBaseClass] = []
        self.gate_options += self.constant_gate_options
        
        self.gate_circuits = []
        self.display_gate_buttons_list: list[Button] = []
        
        self.output_nodes = []
        self.input_node_objects = []
        
        self.gate_display_spacing = 5
        
        max_height = max(gate_op.button.rect.height for gate_op in self.gate_options) + self.border_offset
        gate_option_viewer_size = (self.add_output_button.rect.left - self.border_offset) - (self.add_input_button.rect.right + self.border_offset), max_height
        gates_surf_width = sum([(gate.get_rect().width + self.gate_display_spacing) for gate in self.gate_options]) + self.gate_display_spacing
        self.gates_surf = pygame.Surface((gates_surf_width, gate_option_viewer_size[1]), pygame.SRCALPHA)
        
        x = 0
        for index, gate_op in enumerate(self.gate_options):
            gate_op.button.configure(on_right_mouse_button_clicked=self.circuit.make_remove_gate_func(index))
            display_gate = gate_op.copy()
            display_gate.configure(screen=self.gates_surf, pos=(x, (self.gates_surf.get_height() / 2) - (display_gate.button.rect.height / 2)))
            
            x += display_gate.get_rect().width + self.gate_display_spacing
            
            dsp_but = display_gate.button.copy()
            dsp_but.configure(many_actions_one_click=False, render=False)
            
            self.display_gate_buttons_list.append(dsp_but)
            
            display_gate.update()
        
        self.gate_option_viewer = ScrollableSurface(self.screen,
                                                    self.gates_surf,
                                                    (max((gate_option_viewer_size[0] / 2) - (self.gates_surf.get_width() / 2), 0), 0),
                                                    ((self.screen.get_width() / 2) - (gate_option_viewer_size[0] / 2),
                                                     self.screen.get_height() - gate_option_viewer_size[1] - self.border_offset),
                                                    gate_option_viewer_size,
                                                    orientation='x')
        
        self.left_mouse_clicked_dict = {}
        self.left_mouse_clicked_outside_dict = {}
        self.middle_mouse_clicked_dict = {}
        self.middle_mouse_clicked_outside_dict = {}
        self.right_mouse_clicked_dict = {}
        self.right_mouse_clicked_outside_dict = {}
        
        self.left_mouse_tracker_clicked_dict = {}
        self.left_mouse_tracker_not_clicked_dict = {}
        self.middle_mouse_tracker_clicked_dict = {}
        self.middle_mouse_tracker_not_clicked_dict = {}
        self.right_mouse_tracker_clicked_dict = {}
        self.right_mouse_tracker_not_clicked_dict = {}
        
        self.hover_tracker_dict = {}
        self.not_hover_tracker_dict = {}
        
        self.gate_options_tracker = self.gate_options
    
    def _recolor_widgets(self, color):
        self.new_gate_circuit_button.configure(bg_color=color)
        self.add_gate_button.configure(bg_color=color)
        self.prev_circuit_button.configure(bg_color=color)
        self.next_circuit_button.configure(bg_color=color)
        self.add_input_button.configure(bg_color=color)
        self.add_output_button.configure(bg_color=color)
    
    def _remove_cicuit(self):
        self._change_circuit(self.circuit_index - 1)
        for index_info in self.edit_indices:
            if self.circuit_index + 1 == index_info[1]:
                self.edit_indices.remove(index_info)
                break
        self.circuit_editors.pop(self.circuit_index + 1)
    
    def _set_color(self, color, opacity: int):
        if isinstance(color, str):
            if '#' in color:
                color_tuple = [(abs(255 - (col * 255)) / 255) for col in pygame.Color(color).cmy]
            else:
                color_tuple = [i/255 for i in pygame.colordict.THECOLORS[color]]
        elif isinstance(color, tuple | list | pygame.color.Color):
            color_tuple = [i/255 for i in color]
        elif isinstance(color, int):
            color_tuple = [i/255 for i in pygame.Color(color)]
        else:
            raise Exception('Invalid color argument')

        for i in color_tuple[:3]:
            black = i == 0
            if not black:
                break
        
        color = [255 - opacity for _ in color_tuple] if black else [i * opacity for i in color_tuple]
        
        if len(color) >= 4:
            color = color[:3]
        
        return color
    
    def _change_circuit(self, index):
        self.circuit_index = index
        self.circuit = self.circuit_editors[self.circuit_index]
        self.textinput.value = self.circuit.name
        self.new_gate_tracker = self.circuit.gate
        for gate_options_index, circuit_index in self.edit_indices:
            if self.circuit_index == circuit_index:
                self.edit_index = gate_options_index
                break
        else:
            self.edit_index = None
        self.BG_COLOR = self.bg_colors[str(self.circuit_index)]
        self._recolor_widgets(self._set_color(self.BG_COLOR, 200))
    
    def _is_clicked(self,
                   mouse_rect: pygame.Rect,
                   target_rect: pygame.Rect,
                   hover_func: Callable = None,
                   not_hover_func: Callable = None,
                   on_left_clicked_func: Callable = None,
                   on_middle_clicked_func: Callable = None,
                   on_right_clicked_func: Callable = None,
                   on_not_left_clicked_func: Callable = None,
                   on_not_middle_clicked_func: Callable = None,
                   on_not_right_clicked_func: Callable = None,
                   left_many_actions_one_click: bool = False,
                   left_many_actions_one_not_click: bool = False,
                   middle_many_actions_one_click: bool = False,
                   middle_many_actions_one_not_click: bool = False,
                   right_many_actions_one_click: bool = False,
                   right_many_actions_one_not_click: bool = False,
                   hover_many_actions_one_click: bool = False,
                   not_hover_many_actions_one_click: bool = False):
        
        left_mouse_clicked, middle_mouse_clicked, right_mouse_clicked = pygame.mouse.get_pressed()
        mouse_collission = mouse_rect.colliderect(target_rect)
        
        target_rect_key = repr(target_rect)
        
        if target_rect_key not in self.left_mouse_clicked_dict:
            self.left_mouse_clicked_dict[target_rect_key] = False
        if target_rect_key not in self.left_mouse_clicked_outside_dict:
            self.left_mouse_clicked_outside_dict[target_rect_key] = False
        if target_rect_key not in self.middle_mouse_clicked_dict:
            self.middle_mouse_clicked_dict[target_rect_key] = False
        if target_rect_key not in self.middle_mouse_clicked_outside_dict:
            self.middle_mouse_clicked_outside_dict[target_rect_key] = False
        if target_rect_key not in self.right_mouse_clicked_dict:
            self.right_mouse_clicked_dict[target_rect_key] = False
        if target_rect_key not in self.right_mouse_clicked_outside_dict:
            self.right_mouse_clicked_outside_dict[target_rect_key] = False
        
        if target_rect_key not in self.left_mouse_tracker_clicked_dict:
            self.left_mouse_tracker_clicked_dict[target_rect_key] = False
        if target_rect_key not in self.left_mouse_tracker_not_clicked_dict:
            self.left_mouse_tracker_not_clicked_dict[target_rect_key] = False
        if target_rect_key not in self.middle_mouse_tracker_clicked_dict:
            self.middle_mouse_tracker_clicked_dict[target_rect_key] = False
        if target_rect_key not in self.middle_mouse_tracker_not_clicked_dict:
            self.middle_mouse_tracker_not_clicked_dict[target_rect_key] = False
        if target_rect_key not in self.right_mouse_tracker_clicked_dict:
            self.right_mouse_tracker_clicked_dict[target_rect_key] = False
        if target_rect_key not in self.right_mouse_tracker_not_clicked_dict:
            self.right_mouse_tracker_not_clicked_dict[target_rect_key] = False
        
        if target_rect_key not in self.hover_tracker_dict:
            self.hover_tracker_dict[target_rect_key] = False
        if target_rect_key not in self.not_hover_tracker_dict:
            self.not_hover_tracker_dict[target_rect_key] = False
        
        if mouse_collission:
            self.not_hover_tracker_dict[target_rect_key] = False
            if not self.hover_tracker_dict[target_rect_key] or hover_many_actions_one_click:
                if hover_func is not None:
                    hover_func()
                self.hover_tracker_dict[target_rect_key] = True
        else:
            self.hover_tracker_dict[target_rect_key] = False
            if not self.not_hover_tracker_dict[target_rect_key] or not_hover_many_actions_one_click:
                if not_hover_func is not None:
                    not_hover_func()
                self.not_hover_tracker_dict[target_rect_key] = True
        
        if left_mouse_clicked and mouse_collission:
            self.left_mouse_clicked_dict[target_rect_key] = True
        if not left_mouse_clicked:
            self.left_mouse_clicked_dict[target_rect_key] = False
        if not self.left_mouse_clicked_dict[target_rect_key] and not mouse_collission:
            self.left_mouse_clicked_outside_dict[target_rect_key] = False
        if not left_mouse_clicked:
            self.left_mouse_clicked_outside_dict[target_rect_key] = True
        
        if middle_mouse_clicked and mouse_collission:
            self.middle_mouse_clicked_dict[target_rect_key] = True
        if not middle_mouse_clicked:
            self.middle_mouse_clicked_dict[target_rect_key] = False
        if not self.middle_mouse_clicked_dict[target_rect_key] and not mouse_collission:
            self.middle_mouse_clicked_outside_dict[target_rect_key] = False
        if not middle_mouse_clicked:
            self.middle_mouse_clicked_outside_dict[target_rect_key] = True
        
        if right_mouse_clicked and mouse_collission:
            self.right_mouse_clicked_dict[target_rect_key] = True
        if not right_mouse_clicked:
            self.right_mouse_clicked_dict[target_rect_key] = False
        if not self.right_mouse_clicked_dict[target_rect_key] and not mouse_collission:
            self.right_mouse_clicked_outside_dict[target_rect_key] = False
        if not right_mouse_clicked:
            self.right_mouse_clicked_outside_dict[target_rect_key] = True
        
        left_mouse_clicked = self.left_mouse_clicked_dict[target_rect_key] and self.left_mouse_clicked_outside_dict[target_rect_key]
        middle_mouse_clicked = self.middle_mouse_clicked_dict[target_rect_key] and self.middle_mouse_clicked_outside_dict[target_rect_key]
        right_mouse_clicked = self.right_mouse_clicked_dict[target_rect_key] and self.right_mouse_clicked_outside_dict[target_rect_key]
        
        if left_mouse_clicked:
            self.left_mouse_tracker_not_clicked_dict[target_rect_key] = False
            if not self.left_mouse_tracker_clicked_dict[target_rect_key] or left_many_actions_one_click:
                if on_left_clicked_func is not None:
                    on_left_clicked_func()
                self.left_mouse_tracker_clicked_dict[target_rect_key] = True
        else:
            self.left_mouse_tracker_clicked_dict[target_rect_key] = False
            if not self.left_mouse_tracker_not_clicked_dict[target_rect_key] or left_many_actions_one_not_click:
                if on_not_left_clicked_func is not None:
                    on_not_left_clicked_func()
                self.left_mouse_tracker_not_clicked_dict[target_rect_key] = True
        
        if middle_mouse_clicked:
            self.middle_mouse_tracker_not_clicked_dict[target_rect_key] = False
            if not self.middle_mouse_tracker_clicked_dict[target_rect_key] or middle_many_actions_one_click:
                if on_middle_clicked_func is not None:
                    on_middle_clicked_func()
                self.middle_mouse_tracker_clicked_dict[target_rect_key] = True
        else:
            self.middle_mouse_tracker_clicked_dict[target_rect_key] = False
            if not self.middle_mouse_tracker_not_clicked_dict[target_rect_key] or middle_many_actions_one_not_click:
                if on_not_middle_clicked_func is not None:
                    on_not_middle_clicked_func()
                self.middle_mouse_tracker_not_clicked_dict[target_rect_key] = True
        
        if right_mouse_clicked:
            self.right_mouse_tracker_not_clicked_dict[target_rect_key] = False
            if not self.right_mouse_tracker_clicked_dict[target_rect_key] or right_many_actions_one_click:
                if on_right_clicked_func is not None:
                    on_right_clicked_func()
                self.right_mouse_tracker_clicked_dict[target_rect_key] = True
        else:
            self.right_mouse_tracker_clicked_dict[target_rect_key] = False
            if not self.right_mouse_tracker_not_clicked_dict[target_rect_key] or right_many_actions_one_not_click:
                if on_not_right_clicked_func is not None:
                    on_not_right_clicked_func()
                self.right_mouse_tracker_not_clicked_dict[target_rect_key] = True
        
        return left_mouse_clicked, middle_mouse_clicked, right_mouse_clicked, mouse_collission
    
    def _make_remove_gate_option_func(self, old_gate: GateBaseClass):
        def func():
            self.gate_circuits.pop(self.gate_options.index(old_gate) - len(self.constant_gate_options))
            self.gate_options.remove(old_gate)
            self._recompile_gate_option_viewer()
        
        return func
    
    def _make_gate(self):
        logic_gate = self.circuit.copy()
        logic_gate.gate_update()
        def logic_func(inputs):
            logic_gate.set_inputnodes(inputs)
            logic_gate.gate_update()
            
            return [node.get_state() for node in logic_gate.output_nodes]
        
        new_gate = GateBaseClass(self.textinput.value, self.screen, (0, 0), len(logic_gate.input_node_objects), len(logic_gate.output_nodes), logic_func, ())
        
        self.circuit.gate = new_gate, self.circuit.copy()
    
    def _add_gate_to_viewer(self, gate: GateBaseClass):
        display_gate = gate.copy()
        
        gates_surf_width = sum([(gate.get_rect().width + self.gate_display_spacing) for gate in self.gate_options]) + self.gate_display_spacing
        
        new_gate_surf = pygame.Surface((gates_surf_width, self.gates_surf.get_height()), pygame.SRCALPHA)
        display_gate.configure(screen=new_gate_surf, pos=(self.gates_surf.get_width() + self.gate_display_spacing, (new_gate_surf.get_height() / 2) - (display_gate.button.rect.height / 2)))
        
        new_gate_surf.blit(self.gates_surf, (0, 0))
        
        display_gate.update()
        self.gates_surf = new_gate_surf.copy()
        
        surf_pos_x = max((self.gate_option_viewer.blit_surf.get_width() / 2) - (self.gate_option_viewer.sub_surf.get_width() / 2), 0)
        self.gate_option_viewer.configure(sub_surf=self.gates_surf, sub_surf_pos=(surf_pos_x, self.gate_option_viewer.sub_surf_pos[1]))
        
        dsp_but = display_gate.button.copy()
        dsp_but.configure(many_actions_one_click=False, render=False)
        
        self.display_gate_buttons_list.append(dsp_but)
    
    def _edit_circuit(self):
        circuits_edit_index = self.edit_index - len(self.constant_gate_options)
        self.gate_options.pop(self.edit_index)
        self.gate_circuits.pop(circuits_edit_index)
        self._make_gate()
        gate, circuit = self.circuit.gate
        self.gate_options.insert(self.edit_index, gate.copy())
        self.new_gate_tracker = self.circuit.gate
        self.gate_circuits.insert(circuits_edit_index, circuit)
        self._recompile_gate_option_viewer()
    
    def _recompile_gate_option_viewer(self):
        self.display_gate_buttons_list.clear()
        
        initial_options = self.gate_options[:len(self.constant_gate_options)]
        custom_options = self.gate_options[len(self.constant_gate_options):].copy()
        
        max_height = max(gate_op.button.rect.height for gate_op in self.constant_gate_options) + self.border_offset
        gate_option_viewer_size = (self.add_output_button.rect.left - self.border_offset) - (self.add_input_button.rect.right + self.border_offset), max_height
        gates_surf_width = sum([(gate.get_rect().width + self.gate_display_spacing) for gate in self.constant_gate_options]) + self.gate_display_spacing
        self.gates_surf = pygame.Surface((gates_surf_width, gate_option_viewer_size[1]), pygame.SRCALPHA)

        width = 0
        for index, gate_op in enumerate(initial_options):
            gate_op.button.configure(on_right_mouse_button_clicked=self.circuit.make_remove_gate_func(index))
            display_gate = gate_op.copy()
            display_gate.configure(screen=self.gates_surf, pos=(width, (self.gates_surf.get_height() / 2) - (display_gate.button.rect.height / 2)))
            
            width += self.gate_display_spacing + display_gate.get_rect().width
            
            dsp_but = display_gate.button.copy()
            dsp_but.configure(many_actions_one_click=False, render=False)
            
            self.display_gate_buttons_list.append(dsp_but)
            
            display_gate.update()
        
        self.gate_option_viewer.configure(blit_surf_size=gate_option_viewer_size, sub_surf=self.gates_surf)
        for gate in custom_options:
            self.gate_options.remove(gate)
        for gate in custom_options:
            self.gate_options.append(gate)
            self._add_gate_to_viewer(gate)
    
    def _force_textinput_focus(self):
        self.textinput_focused = True
    
    def _free_textinput_focus(self):
        self.textinput.cursor_visible = True
        self.textinput_focused = False
        if self.textinput.value == '':
            self.textinput.value = DEFAULT_CIRCUIT_NAME
        self.textinput.cursor_visible = False
    
    def _make_set_circuit_editor_func(self, index):
        def func():
            self.edit_index = index
            
            for edit_index, circuit_index in self.edit_indices:
                if index == edit_index:
                    self._change_circuit(circuit_index)
                    break
            else:
                circuit = self.gate_circuits[self.edit_index - len(self.constant_gate_options)]
                self._make_new_circuit(circuit, circuit.name)
                self.edit_indices.append((self.edit_index, self.circuit_index))
        
        return func
    
    def _make_new_circuit(self, circuit = None, name: str = None):
        if len(self.circuit_editors) < self.max_circuit_amt:
            name = DEFAULT_CIRCUIT_NAME if name is None else name
            circuit = Circuit(name, self.screen, self.screen.get_height() - self.border_offset - self.add_buttons_size[1], self.add_buttons_size[1]) if circuit is None else circuit
            self.circuit_editors.insert(self.circuit_index + 1, circuit)
            self._change_circuit(self.circuit_index + 1)
    
    def _update_textinput(self):
        mouse_rect = pygame.Rect(*self.mouse_pos, 1, 1)
        self._is_clicked(mouse_rect, self.textinput_rect, on_left_clicked_func=self._force_textinput_focus)
        if self.left_mouse_clicked_outside_dict[repr(self.textinput_rect)]:
            if not self.has_textinput_focus:
                self._free_textinput_focus()
                self.has_textinput_focus = True
        else:
            self.has_textinput_focus = False
        
        if self.textinput_focused:
            self.textinput.update(self.events)
            self.circuit.name = self.textinput.value
        
        self.textinput_rect = self.textinput.surface.get_rect(midtop=(self.screen.get_width() / 2, 20))
        self.screen.blit(self.textinput.surface, self.textinput_rect)
    
    def _app_loop(self):
        # self.fps_surf = self.add_node_font.render(f'FPS: {round(self.clock.get_fps())}', False, 'white')
        # self.fps_rect = self.fps_surf.get_rect(bottomright=(SCR_WIDTH - 20, SCR_HEIGHT))
        # self.screen.blit(self.fps_surf, self.fps_rect)
        
        self.keys = pygame.key.get_pressed()
        
        self.new_gate_circuit_button.update()
        self.add_gate_button.update()
        self.add_input_button.update()
        self.add_output_button.update()
        
        if self.edit_index is not None:
            self.edit_gate_option_button.update()
        
        if self.circuit_index > 0:
            self.delete_circuit_button.update()
            self.prev_circuit_button.update()
            self.prev_circuit_button.configure(border_radius=-1, border_top_left_radius=self.border_radius, border_bottom_left_radius=self.border_radius, border_top_right_radius=-1, border_bottom_right_radius=-1)
        
        if self.circuit_index < len(self.circuit_editors) - 1:
            self.next_circuit_button.update()
            self.next_circuit_button.configure(border_radius=-1, border_top_left_radius=-1, border_bottom_left_radius=-1, border_top_right_radius=self.border_radius, border_bottom_right_radius=self.border_radius)
        
        self.circuit.update()
        
        if self.new_gate_tracker != self.circuit.gate:
            gate, circuit = self.circuit.gate
            self.gate_options.append(gate)
            self._add_gate_to_viewer(gate)
            self.gate_circuits.append(circuit)
            self.new_gate_tracker = self.circuit.gate
        
        for gate in self.gate_options:
            gate.configure(node_on_click_func=self.circuit.on_node_clicked)
        
        self.gate_option_viewer.update()
        
        self._update_textinput()
        
        for index, button in enumerate(self.display_gate_buttons_list):
            m_pos = (self.mouse_pos[0] - self.gate_option_viewer.blit_rect.x - self.gate_option_viewer.sub_surf_rect.x,
                         self.mouse_pos[1] - self.gate_option_viewer.blit_rect.y - self.gate_option_viewer.sub_surf_rect.y)
            
            gate = self.gate_options[index]
            button.configure(mouse_pos=m_pos, on_left_mouse_button_clicked=self.circuit.make_add_gate_func(gate))
            if index > len(self.constant_gate_options) - 1:
                button.configure(on_middle_mouse_button_clicked=self._make_set_circuit_editor_func(index), on_right_mouse_button_clicked=self._make_remove_gate_option_func(gate))
            button.update()
    
    def _event_loop(self, event):
        self.keys = pygame.key.get_pressed()
        
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    
    def run(self):
        while True:
            self.mouse_pos = pygame.mouse.get_pos()
            self.delta_time = self.clock.tick(FPS)
            
            self.screen.fill(self.BG_COLOR)

            self.events = pygame.event.get()
            for event in self.events:
                self._event_loop(event)
            
            self._app_loop()

            pygame.display.update()
    

def main():
    game = App()
    game.run()

if __name__ == '__main__':
    main()



