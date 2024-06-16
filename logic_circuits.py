import math
import threading
import time
import pygame
from settings import *
from typing import Callable
from widgets import Button, ScrollableSurface
from logic_gates import AndGate, NotGate, GateBaseClass
from signal_tranfer import Node, Wire
from pygame_textinput import TextInputManager, TextInputVisualizer

class CustomGate:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        
        self.button_colors = '#888888'
        self.button_text_colors = 'white'
        self.button_border_offset = 20
        self.border_offset = 30
        
        self.current_circuit_name = DEFAULT_CIRCUIT_NAME
        self.circuit_editors: dict[str, Circuit] = {}
        self.circuit = self.circuit_editors[self.current_circuit_name] = Circuit(self.screen, self.screen.get_height() - self.border_offset - 30)
        self.new_gate_tracker = self.circuit.gate
        
        self.add_node_font = pygame.font.SysFont('Arial', 45)
        self.edit_button_font = pygame.font.SysFont('Sans Serif', 20)
        
        self.textinput_font = pygame.font.SysFont("Consolas", 55)
        self.textinput_manager = TextInputManager(initial=self.current_circuit_name, validator = lambda input: len(input) < 25)
        self.textinput_custom = TextInputVisualizer(manager=self.textinput_manager, font_color=(255, 255, 255), font_object=self.textinput_font)
        self.textinput_custom.cursor_width = 4
        self.textinput_custom.cursor_color = [(c+200)%255 for c in self.textinput_custom.font_color]
        self.textinput_custom.cursor_visible = True
        self.textinput_rect = self.textinput_custom.surface.get_rect(midtop=(self.screen.get_width() / 2, 20))
        
        self.textinput_focused = False
        self.has_textinput_focus = False
        
        self.add_input_button = Button(self.screen, (0, 0), (30, 30), self.button_colors, image=self.add_node_font.render('+', True, self.button_text_colors), on_left_mouse_button_clicked=self.circuit.add_input, border_radius=20)
        self.add_input_button.set_pos(midbottom=(self.border_offset, self.screen.get_height() - self.border_offset))
        self.add_output_button = Button(self.screen, (0, 0), (30, 30), self.button_colors, image=self.add_node_font.render('+', True, self.button_text_colors), on_left_mouse_button_clicked=self.circuit.add_output, border_radius=20)
        self.add_output_button.set_pos(midbottom=(self.screen.get_width() - self.border_offset, self.screen.get_height() - self.border_offset))
        
        self.new_gate_circuit_button = Button(self.screen, (0, 0), (100, 20), self.button_colors, image=self.edit_button_font.render('New Circuit', True, self.button_text_colors), border_radius=10, on_left_mouse_button_clicked=lambda: self.new_circuit('_'))
        self.new_gate_circuit_button.set_pos(topleft=(self.button_border_offset, self.button_border_offset))
        self.add_gate_button = Button(self.screen, (0, 0), (100, 20), self.button_colors, image=self.edit_button_font.render('Make Gate', True, self.button_text_colors), border_radius=10, on_left_mouse_button_clicked=lambda: self.circuit.make_gate(self.textinput_custom.value))
        self.add_gate_button.set_pos(topright=(self.screen.get_width() - self.button_border_offset, self.button_border_offset))
        
        self.gate_options: list[GateBaseClass] = [AndGate(self.screen, (0, 0), self.circuit.on_node_clicked), NotGate(self.screen, (0, 0), self.circuit.on_node_clicked)]
        self.display_gate_buttons_list: list[Button] = []
        
        self.output_nodes = []
        self.input_node_objects = []
        
        self.gate_display_spacing = 5
        max_height = max(gate_op.button.rect.height for gate_op in self.gate_options) + self.border_offset
        gate_option_viewer_size = (self.add_output_button.rect.left - self.border_offset) - (self.add_input_button.rect.right + self.border_offset), max_height
        gates_surf_width = len(self.gate_options) * ((self.gate_options[0].output_nodes[0].get_rect().right - self.gate_options[0].input_nodes[0].get_rect().left) + self.gate_display_spacing)
        self.gates_surf = pygame.Surface((gates_surf_width, gate_option_viewer_size[1]))
        
        for gate_index, gate_op in enumerate(self.gate_options):
            display_gate = gate_op.copy()
            width = self.gate_options[gate_index - 1].output_nodes[0].get_rect().width + self.gate_options[gate_index - 1].node_pin_size[0]
            if gate_index:
                width += self.gate_display_spacing + (self.gate_options[gate_index - 1].output_nodes[0].get_rect().right - self.gate_options[gate_index - 1].input_nodes[0].get_rect().left + self.gate_options[gate_index - 1].node_pin_size[0])
            
            display_gate.__init__(display_gate.name,
                                  self.gates_surf,
                                  (display_gate.button.rect.x + width, (self.gates_surf.get_height() / 2) -(display_gate.button.rect.height / 2)),
                                  display_gate.input_amt,
                                  display_gate.output_amt,
                                  display_gate.logic_func,
                                  display_gate.node_on_click_func)
            dsp_but = display_gate.button.copy()
            dsp_but.configure(on_left_mouse_button_clicked=self.circuit.make_add_gate_func(gate_op), many_actions_one_click=False, invisible=True)
            
            self.display_gate_buttons_list.append(dsp_but)
            
            display_gate.update()
        
        self.gate_option_viewer = ScrollableSurface(self.screen,
                                                    self.gates_surf,
                                                    (max((gate_option_viewer_size[0] / 2) - (self.gates_surf.get_width() / 2), 0), 0),
                                                    ((self.screen.get_width() / 2) - (gate_option_viewer_size[0] / 2),
                                                     self.screen.get_height() - gate_option_viewer_size[1] - self.border_offset),
                                                    gate_option_viewer_size,
                                                    orientation='x')
        
        for index, gate in enumerate(self.gate_options):
            gate.button.configure(bg_color='red', on_right_mouse_button_clicked=self.circuit.make_remove_gate_func(index))
        
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
    
    def is_clicked(self,
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
            self.gate_options.remove(old_gate)
            self.display_gate_buttons_list.clear()
            self.gates_surf = pygame.Surface((0, self.gates_surf.get_height()))
            
            width = -self.gate_options[0].node_pin_size[0] / 2
            node_size_offset = self.gate_options[0].output_nodes[0].get_rect().width + self.gate_options[0].node_pin_size[0]
            gates_surf_width = sum((gate.output_nodes[0].get_rect().right - gate.input_nodes[0].get_rect().left) for gate in self.gate_options) + (self.gate_display_spacing * len(self.gate_options))
            
            for index, gate in enumerate(self.gate_options):
                display_gate = gate.copy()
                
                if index:
                    width += self.gate_display_spacing + (self.gate_options[index - 1].output_nodes[0].get_rect().right - self.gate_options[index - 1].input_nodes[0].get_rect().left + self.gate_options[index - 1].node_pin_size[0])
                
                new_gate_surf = pygame.Surface((gates_surf_width, self.gates_surf.get_height()))
                display_gate.__init__(display_gate.name,
                                    new_gate_surf,
                                    (width + node_size_offset, 0),
                                    display_gate.input_amt,
                                    display_gate.output_amt,
                                    display_gate.logic_func,
                                    display_gate.node_on_click_func)
                
                new_gate_surf.blit(self.gates_surf, (0, 0))
                display_gate.update()
                self.gates_surf = new_gate_surf.copy()
                
                self.gate_option_viewer.configure(sub_surf=self.gates_surf, sub_surf_pos=(max((self.gate_option_viewer.blit_surf.get_width() / 2) - (self.gate_option_viewer.sub_surf.get_width() / 2), 0), self.gate_option_viewer.sub_surf_pos[1]))
                
                dsp_but = display_gate.button.copy()
                dsp_but.configure(on_left_mouse_button_clicked=self.circuit.make_add_gate_func(gate), invisible=True)
                self.display_gate_buttons_list.append(dsp_but)
        
        return func
    
    def _add_gate_to_viewer(self, gate: GateBaseClass):
        display_gate = gate.copy()
        
        gates_surf_width = sum((gate.output_nodes[0].get_rect().right - gate.input_nodes[0].get_rect().left) for gate in self.gate_options) + (self.gate_display_spacing * len(self.gate_options))
        node_size_offset = self.gate_options[0].output_nodes[0].get_rect().width + self.gate_options[0].node_pin_size[0]
        new_gate_surf = pygame.Surface((gates_surf_width, self.gates_surf.get_height()))
        display_gate.__init__(display_gate.name,
                              new_gate_surf,
                              (self.gates_surf.get_width() + node_size_offset, (new_gate_surf.get_height() / 2) -(display_gate.button.rect.height / 2)),
                              display_gate.input_amt,
                              display_gate.output_amt,
                              display_gate.logic_func,
                              display_gate.node_on_click_func)
        new_gate_surf.blit(self.gates_surf, (0, 0))
        display_gate.update()
        self.gates_surf = new_gate_surf.copy()
        self.gate_option_viewer.configure(sub_surf=self.gates_surf, sub_surf_pos=(max((self.gate_option_viewer.blit_surf.get_width() / 2) - (self.gate_option_viewer.sub_surf.get_width() / 2), 0), self.gate_option_viewer.sub_surf_pos[1]))
        
        dsp_but = display_gate.button.copy()
        
        dsp_but.configure(on_left_mouse_button_clicked=self.circuit.make_add_gate_func(gate), on_right_mouse_button_clicked=self._make_remove_gate_option_func(gate), on_middle_mouse_button_clicked=self.make_set_circuit_editor_func(display_gate.name), many_actions_one_click=False, invisible=True)
        self.display_gate_buttons_list.append(dsp_but)
    
    def _force_textinput_focus(self):
        self.textinput_focused = True
        if self.textinput_custom.value == DEFAULT_CIRCUIT_NAME:
            self.textinput_custom.value = ''
    
    def _free_textinput_focus(self):
        self.textinput_custom.cursor_visible = True
        self.textinput_focused = False
        if self.textinput_custom.value == '':
            self.textinput_custom.value = DEFAULT_CIRCUIT_NAME
        self.textinput_custom.cursor_visible = False
    
    def make_set_circuit_editor_func(self, name):
        def func():
            self.update_gate(self.current_circuit_name)
            self.current_circuit_name = self.textinput_custom.value = name
        
        return func
    
    def rename_gate(self, name):
        circuit = self.circuit_editors.pop(self.current_circuit_name)
        self.current_circuit_name = name
        self.circuit = circuit
        
        gate = self.circuit.gate
        if gate is not None:
            gate.configure(name=name)
    
    def new_circuit(self, name):
        self.update_gate(self.current_circuit_name)
        self.current_circuit_name = self.textinput_custom.value = name
        self.circuit = self.circuit_editors[self.current_circuit_name] = Circuit(self.screen, min(self.add_output_button.rect.top, self.add_input_button.rect.top))
    
    def update_gate(self, name):
        pass
    
    def update_textinput(self):
        mouse_rect = pygame.Rect(*self.mouse_pos, 1, 1)
        self.is_clicked(mouse_rect, self.textinput_rect, on_left_clicked_func=self._force_textinput_focus)
        if self.left_mouse_clicked_outside_dict[repr(self.textinput_rect)]:
            if not self.has_textinput_focus:
                self._free_textinput_focus()
                self.has_textinput_focus = True
        else:
            self.has_textinput_focus = False
        
        if self.textinput_focused:
            self.textinput_custom.update(self.events)
        
        self.textinput_rect = self.textinput_custom.surface.get_rect(midtop=(self.screen.get_width() / 2, 20))
        self.screen.blit(self.textinput_custom.surface, self.textinput_rect)
    
    def update(self, events):
        self.events = events
        
        self.keys = pygame.key.get_pressed()
        self.mouse_pos = pygame.mouse.get_pos()
        
        self.new_gate_circuit_button.update()
        self.add_gate_button.update()
        
        self.add_input_button.update()
        self.add_output_button.update()
        
        self.circuit.update()
        
        if self.new_gate_tracker != self.circuit.gate:
            self.gate_options.append(self.circuit.gate)
            self._add_gate_to_viewer(self.circuit.gate)
            self.new_gate_tracker = self.circuit.gate
        
        self.gate_option_viewer.update()
        
        self.update_textinput()
        
        for button in self.display_gate_buttons_list:
            mouse = pygame.mouse.get_pos()
            mouse_pos = (mouse[0] - self.gate_option_viewer.blit_rect.x - self.gate_option_viewer.sub_surf_rect.x,
                         mouse[1] - self.gate_option_viewer.blit_rect.y - self.gate_option_viewer.sub_surf_rect.y)
            button.configure(mouse_pos=mouse_pos)
            button.update()
        
class Circuit:
    def __init__(self, screen: pygame.Surface, node_base_line: int) -> None:
        self.screen = screen
        
        self.in_out_wire_size = 10, 20
        
        self.wire_right_pressed = False
        self.wire_left_pressed = False
        self.gate = None
        self.gates: list[GateBaseClass] = []
        self.wires: list[Wire] = []
        self.input_node_objects = []
        self.output_nodes = []
        self.wire_connected_trackers = {}
        self.gate_key_index_map = {}
        
        self.node_base_line = node_base_line
        self.r = None
        self.add_input()
        self.add_output()
    
    def _generate_combinations(self, length):
        total_combinations = 2 ** length
        return ([int(bit) for bit in format(i, f'0{length}b')] for i in range(total_combinations))
    
    def _set_input_node_positions(self, delay=False):
        if delay:
            time.sleep(0.2)
        self.input_node_objects: list[tuple[Button, Node]]
        for index, (but, node) in enumerate(self.input_node_objects):
            box_offset = 10
            height = but.rect.height + box_offset
            max_nodes_amt = int((self.screen.get_height() - (self.screen.get_height() - self.node_base_line)) / height)
            width = (but.rect.width + node.node_button.rect.width + self.in_out_wire_size[0]) + box_offset
            half_scr_offset = (self.screen.get_height() / 2) - ((min(len(self.input_node_objects), max_nodes_amt) * height) / 2) - (self.screen.get_height() - self.node_base_line)
            
            x = box_offset + (math.floor(index / max_nodes_amt) * width)
            y = ((index % max_nodes_amt) * height) + half_scr_offset
            but.set_pos(topleft=(x, y))
            node.set_pos((but.rect.x + but.rect.width + self.in_out_wire_size[0], but.rect.centery - (self.in_out_wire_size[1] / 2)))
    
    def _set_output_node_positions(self, delay=False):
        if delay:
            time.sleep(0.2)
        self.output_nodes: list[Node]
        for index, node in enumerate(self.output_nodes):
            box_offset = 10
            height = node.node_button.rect.height + box_offset
            max_nodes_amt = int((self.screen.get_height() - (self.screen.get_height() - self.node_base_line)) / height)
            width = node.node_button.rect.width + box_offset
            half_scr_offset = (self.screen.get_height() / 2) - ((min(len(self.output_nodes), max_nodes_amt) * height) / 2) - (self.screen.get_height() - self.node_base_line)
            
            x = self.screen.get_width() - node.node_button.rect.width - box_offset - (math.floor(index / max_nodes_amt) * width)
            y = ((index % max_nodes_amt) * height) + half_scr_offset
            node.set_pos((x, y))
    
    def add_input(self):
        ctrl_button = Button(self.screen,
                             (0, 0),
                             (40, 40),
                             'grey',
                             on_left_mouse_button_clicked=lambda: input_node.set_state(not input_node.get_state())
                             )
        input_node = Node(self.screen,
                          (0, 0),
                          (20, 20),
                          'yellow',
                          'darkgrey',
                          is_input=False,
                          is_click_toogleable=False,
                          static=False,
                          on_click_func=self.on_node_clicked
                          )
        
        self.update_input_button_removal = True
        self.input_node_objects.append((ctrl_button, input_node))
        self._set_input_node_positions()
    
    def add_output(self):
        output_node = Node(self.screen,
                          (0, 0),
                          (30, 30),
                          'yellow',
                          'darkgrey',
                          is_input=True,
                          is_click_toogleable=False,
                          static=False,
                          on_click_func=self.on_node_clicked
                          )
        
        self.update_output_button_removal = True
        self.output_nodes.append(output_node)
        self._set_output_node_positions()
    
    def on_node_clicked(self, input_node: Node):
        if True not in self.wire_connected_trackers.values():
            wire = Wire(self.screen, input_node.node_button.rect.center, self.mouse_pos, 5, 'pink', 'darkgrey', lambda w: self._remove_wire_func(w))
            input_node.connect(wire)
            if input_node.is_input:
                if wire.wire_move_buttons:
                    wire.wire_move_buttons.pop()
            self.wires.append(wire)
            
            self.wire_connected_trackers[wire] = None
    
    def _make_input_remove_node_func(self, index):
        def func():
            if index != 0:
                self.update_input_button_removal = True
                _, node = self.input_node_objects[index]
                connected_wires = node.connected_inputs.copy() + node.connected_inputs.copy()
                node.disconnect_all()
                for wire in connected_wires:
                    self.wires.remove(wire)
                self.input_node_objects.pop(index)
                self._set_input_node_positions(True)
        
        return func
    
    def _make_output_remove_node_func(self, index):
        def func():
            if index != 0:
                self.update_output_button_removal = True
                
                node = self.output_nodes[index]
                connected_wires = node.connected_inputs.copy() + node.connected_outputs.copy()
                node.disconnect_all()
                for wire in connected_wires:
                    self.wires.remove(wire)
                self.output_nodes.pop(index)
                self._set_output_node_positions(True)
        
        return func
    
    def make_remove_gate_func(self, index: int):
        def func():
            for node in self.gates[index].input_nodes + self.gates[index].output_nodes:
                for in_wire in node.connected_inputs:
                    if in_wire in self.wires:
                        self.wires.remove(in_wire)
                for out_wire in node.connected_outputs:
                    if out_wire in self.wires:
                        self.wires.remove(out_wire)
            self.gates[index].disconnect_all_nodes()
            self.gates.pop(index)
        return func
    
    def _remove_wire_func(self, wire: Wire):
        if wire.input_node is not None:
            wire.input_node.set_state(0)
        wire.disconnect_all()
        self.wires.remove(wire)
    
    def make_gate(self, name):
        def func():
            combinations = self._generate_combinations(len(self.input_node_objects))
            input_mapping = {}
            
            init_inp_vals = [node.get_state() for _, node in self.input_node_objects]
            
            for combs in combinations:
                for i, (_, node) in enumerate(self.input_node_objects):
                    node.set_state(combs[i])
                self.update()
                time.sleep(0.05)
                input_mapping.update({tuple(combs): [node.get_state() for node in self.output_nodes]})
            
            new_gate = GateBaseClass(name, self.screen, (0, 0), len(self.input_node_objects), len(self.output_nodes), lambda inputs: input_mapping[tuple(inputs)], self.on_node_clicked)
            
            for i, (_, node) in enumerate(self.input_node_objects):
                node.set_state(init_inp_vals[i])
            
            self.gate = new_gate
        
        t = threading.Thread(target=func)
        t.daemon = True
        t.start()
    
    def make_add_gate_func(self, gate: GateBaseClass):
        def func():
            new_gate = gate.copy()
            new_gate.set_pos(self.mouse_pos)
            self.gates.append(new_gate)
        
        return func
    
    def _disconnect_wire(self, wire: Wire):
        if wire.input_connected:
            wire.input_node.disconnect(wire)
        elif wire.output_connected:
            wire.output_node.disconnect(wire)
        self.wires.remove(wire)
        self.wire_connected_trackers[wire] = False
    
    def update_wires_and_connections(self):
        for wire in self.wires:
            if self.wire_connected_trackers[wire]:
                if pygame.mouse.get_pressed()[2]:
                    if not self.wire_right_pressed:
                        self._disconnect_wire(wire)
                    self.wire_right_pressed = True
                else:
                    self.wire_right_pressed = False
                
                if pygame.mouse.get_pressed()[0]:
                    if not self.wire_left_pressed:
                        gate_nodes = []
                        for gate in self.gates:
                            gate_nodes += gate.get_input_nodes() + gate.get_output_nodes()
                        
                        for nodes in gate_nodes + [node for _, node in self.input_node_objects] + [node for node in self.output_nodes]:
                            is_touching_a_connection = nodes.node_button.rect.collidepoint(self.mouse_pos)
                            
                            circular_wire_connection = (((nodes.is_input and wire.input_connected)
                                                            or
                                                         (nodes.is_output and wire.output_connected))
                                                        if is_touching_a_connection else False)
                            
                            if is_touching_a_connection:
                                if not circular_wire_connection:
                                    nodes.connect(wire)
                                    self.wire_connected_trackers[wire] = False
                                break
                        else:
                            if True not in [button.update()[-1] for _, button in wire.wire_move_buttons]:
                                wire.add_breakpoint(self.mouse_pos)
                            self.wire_left_pressed = True
                            break
                    
                        self.wire_left_pressed = True
                else:
                    self.wire_left_pressed = False
                
                if wire.output_connected:
                    wire.move_breakpoint_ending_point(-1, self.mouse_pos)
                else:
                    wire.move_breakpoint_starting_point(0, self.mouse_pos)
            
            if self.wire_connected_trackers[wire] is None:
                self.wire_connected_trackers[wire] = True
            wire.update()
    
    def update_gates(self):
        for index, gate in enumerate(self.gates):
            gate.button.configure(on_right_mouse_button_clicked=self.make_remove_gate_func(index))
            gate.update()
    
    def update_inputs(self):
        for ctrl, out in self.input_node_objects:
            pygame.draw.line(self.screen, 'grey', ctrl.rect.center, out.node_button.rect.center)
            ctrl.update()
            out.update()
    
    def update_outputs(self):
        for out in self.output_nodes:
            out.update()
    
    def update(self):
        self.mouse_pos = pygame.mouse.get_pos()
        
        self.update_inputs()
        self.update_outputs()
        self.update_wires_and_connections()
        self.update_gates()
        
        if self.update_input_button_removal:
            for i, (button, _) in enumerate(self.input_node_objects):
                button.configure(on_right_mouse_button_clicked=self._make_input_remove_node_func(i))
            self.update_input_button_removal = False
        
        if self.update_output_button_removal:
            for i, node in enumerate(self.output_nodes):
                node.node_button.configure(on_right_mouse_button_clicked=self._make_output_remove_node_func(i))
            self.update_output_button_removal = False


