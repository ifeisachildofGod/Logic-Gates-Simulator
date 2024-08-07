import pygame
from assets.settings import *
from assets.widgets import Button
from assets.modules import is_clicked
from assets.logic_gates_components import *
from assets.widgets import Button, ScrollableSurface
from pygame_textinput import TextInputManager, TextInputVisualizer

class CircuitDisplay:
    def __init__(self, screen: pygame.Surface, max_circuit_amt: int, add_buttons_border_offset: int, add_buttons_size: tuple) -> None:
        self.screen = screen
        
        self.max_circuit_amt = max_circuit_amt
        
        self.add_buttons_size = add_buttons_size
        self.add_buttons_border_offset = add_buttons_border_offset
        
        self._theme_color = 'red'
        
        self.new_gate_tracker = None
        
        self.circuit_editors: list[Circuit] = []
        self.circuit_index = -1
        
        self.textinput_font = pygame.font.SysFont('Consolas', 55)
        self.mouse_pos = pygame.mouse.get_pos()
        self.events = pygame.event.get()
        
        textinput_manager = TextInputManager(initial = DEFAULT_CIRCUIT_NAME, validator = lambda input: len(input) < 25)
        self.textinput = TextInputVisualizer(manager=textinput_manager, font_color=(255, 255, 255), font_object=self.textinput_font)
        self.textinput.cursor_width = 4
        self.textinput.cursor_color = [(c+200)%255 for c in self.textinput.font_color]
        self.textinput.cursor_visible = False
        self.textinput_rect = self._get_textinput_rect()
        
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
        
        self.gate_display_spacing = 5
        
        max_height = max(gate_op.button.rect.height for gate_op in self.gate_options) + self.add_buttons_border_offset
        far_left = self.add_buttons_border_offset + self.add_buttons_size[0] + self.add_buttons_border_offset
        far_right = self.screen.get_width() - (self.add_buttons_border_offset * 2) - (self.add_buttons_size[0] / 2)
        gate_option_viewer_size = far_right - far_left, max_height
        gates_surf_width = sum([(gate.get_rect().width + self.gate_display_spacing) for gate in self.gate_options]) + self.gate_display_spacing
        self.gates_surf = pygame.Surface((gates_surf_width, gate_option_viewer_size[1]), pygame.SRCALPHA)
        
        x = 0
        for index, gate_op in enumerate(self.gate_options):
            self.circuit._set_gate_color(gate_op, self.circuit.theme_color)
            
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
                                                     self.screen.get_height() - gate_option_viewer_size[1] - self.add_buttons_border_offset),
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
    
    @property
    def theme_color(self):
        return self._theme_color
    
    @theme_color.setter
    def theme_color(self, v):
        self._theme_color = v
        self.circuit.theme_color = self._theme_color
        self._recompile_gate_option_viewer()
    
    def get_dict(self):
        return {
            'theme_color': self.theme_color,
            'circuit index': self.circuit_index,
            'circuits': [circuit.get_dict() for circuit in self.circuit_editors],
            'gate options': [gate_op.get_dict() for gate_op in self.gate_options[len(self.constant_gate_options):]]   
        }
    
    def set_dict(self, d: dict):
        circuits_info = d['circuits']
        circuit_index = d['circuit index']
        gate_options_info = d['gate options']
        self.circuit_editors.clear()
        self.circuit_index = -1
        
        for editor_info in circuits_info:
            circuit = Circuit('_', self.screen, 0, 0, 'red')
            circuit.set_dict(editor_info)
            self._make_new_circuit(circuit, circuit.name)
        
        self._change_circuit(circuit_index)
        
        while len(self.gate_circuits) > len(self.constant_gate_options):
            self.gate_circuits.pop()
            self._recompile_gate_option_viewer()
        
        for gate_op_info in gate_options_info:
            gate = GateBaseClass('_', self.screen, (-200, -200), 1, 1, lambda i: i[0], self.circuit.on_node_clicked)
            gate.set_dict(gate_op_info)
            gate.update()
            self.gate_options.append(gate)
            self._add_gate_to_viewer(gate)
            if isinstance(gate.logic_func_or_circuit_or_circuit_dict, dict):
                tmp_circuit = Circuit('_', self.screen, 1, 1, 'red')
                tmp_circuit.set_dict(gate.logic_func_or_circuit_or_circuit_dict)
            else:
                tmp_circuit = gate.logic_func_or_circuit_or_circuit_dict
            self.gate_circuits.append(tmp_circuit)
        
        self.theme_color = d['theme_color']
        self.textinput_focused = True
        
        self.screen.blit(self.textinput.surface, self.textinput_rect)
    
    def _remove_cicuit(self):
        self._change_circuit(self.circuit_index - 1)
        for index_info in self.edit_indices:
            if self.circuit_index + 1 == index_info[1]:
                self.edit_indices.remove(index_info)
                break
        self.circuit_editors.pop(self.circuit_index + 1)
    
    def _change_circuit(self, index):
        self.circuit_index = index
        self.circuit: Circuit = self.circuit_editors[self.circuit_index]
        self.textinput.value = self.circuit.name
        self.new_gate_tracker = self.circuit.gate
        for gate_options_index, circuit_index in self.edit_indices:
            if self.circuit_index == circuit_index:
                self.edit_index = gate_options_index
                break
        else:
            self.edit_index = None
    
    def _make_remove_gate_option_func(self, old_gate: GateBaseClass):
        def func():
            self.gate_circuits.pop(self.gate_options.index(old_gate) - len(self.constant_gate_options))
            self.gate_options.remove(old_gate)
            self._recompile_gate_option_viewer()
        
        return func
    
    def _get_textinput_rect(self):
        return self.textinput.surface.get_rect(midtop=(self.screen.get_width() / 2, 30))
    
    def _make_gate(self):
        new_gate = GateBaseClass(self.textinput.value,
                                 self.screen,
                                 (-200, -200),
                                 len(self.circuit.input_node_objects),
                                 len(self.circuit.output_nodes),
                                 self.circuit.copy())
        new_gate.update()
                
        self.circuit.gate = new_gate, self.circuit.copy()
    
    def _add_gate_to_viewer(self, gate: GateBaseClass):
        display_gate = gate.copy()
        
        gates_surf_width = sum([(gate.get_rect().width + self.gate_display_spacing) for gate in self.gate_options]) + self.gate_display_spacing
        
        new_gate_surf = pygame.Surface((gates_surf_width, self.gates_surf.get_height()), pygame.SRCALPHA)
        display_gate.configure(screen=new_gate_surf, pos=(self.gates_surf.get_width() + self.gate_display_spacing, (new_gate_surf.get_height() / 2) - (display_gate.button.rect.height / 2)))
        
        new_gate_surf.blit(self.gates_surf, (0, 0))
        
        self.circuit._set_gate_color(display_gate, self.circuit.theme_color)
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
        
        max_height = max(gate_op.button.rect.height for gate_op in self.constant_gate_options) + self.add_buttons_border_offset
        far_left = self.add_buttons_border_offset + self.add_buttons_size[0] + self.add_buttons_border_offset
        far_right = self.screen.get_width() - (self.add_buttons_border_offset * 2) - (self.add_buttons_size[0] / 2)
        gate_option_viewer_size = far_right - far_left, max_height
        gates_surf_width = sum([(gate.get_rect().width + self.gate_display_spacing) for gate in self.constant_gate_options]) + self.gate_display_spacing
        self.gates_surf = pygame.Surface((gates_surf_width, gate_option_viewer_size[1]), pygame.SRCALPHA)
        
        x = 0
        for index, gate_op in enumerate(initial_options):
            gate_op.button.configure(on_right_mouse_button_clicked=self.circuit.make_remove_gate_func(index))
            display_gate = gate_op.copy()
            display_gate.configure(screen=self.gates_surf, pos=(x, (self.gates_surf.get_height() / 2) - (display_gate.button.rect.height / 2)))
            
            x += display_gate.get_rect().width + self.gate_display_spacing
            
            dsp_but = display_gate.button.copy()
            dsp_but.configure(many_actions_one_click=False, render=False)
            
            self.display_gate_buttons_list.append(dsp_but)
            
            self.circuit._set_gate_color(display_gate, self.circuit.theme_color)
            display_gate.update()
        self.gate_option_viewer.configure(blit_surf_pos=((self.screen.get_width() / 2) - (gate_option_viewer_size[0] / 2), self.screen.get_height() - gate_option_viewer_size[1] - self.add_buttons_border_offset))
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
            circuit = Circuit(name, self.screen, self.screen.get_height() - self.add_buttons_border_offset - self.add_buttons_size[1], self.add_buttons_size[1], self.theme_color) if circuit is None else circuit
            self.circuit_editors.insert(self.circuit_index + 1, circuit)
            self._change_circuit(self.circuit_index + 1)
    
    def _update_textinput(self):
        mouse_rect = pygame.Rect(*self.mouse_pos, 1, 1)
        mouse_clicked, _, _, _ = is_clicked(mouse_rect, self.textinput_rect, on_left_clicked_func=self._force_textinput_focus)
        
        if pygame.mouse.get_pressed()[0] and not mouse_clicked:
            if not self.has_textinput_focus:
                self._free_textinput_focus()
                self.has_textinput_focus = True
        else:
            self.has_textinput_focus = False
        
        if self.textinput_focused:
            self.textinput.update(self.events)
            self.circuit.name = self.textinput.value
        
        self.textinput_rect = self._get_textinput_rect()
        self.screen.blit(self.textinput.surface, self.textinput_rect)
    
    def update(self, events):
        self.mouse_pos = pygame.mouse.get_pos()
        self.events = events
        self.keys = pygame.key.get_pressed()
        
        self.circuit.update()
        
        if self.new_gate_tracker != self.circuit.gate:
            gate, circuit = self.circuit.gate
            self.gate_options.append(gate)
            self._add_gate_to_viewer(gate)
            self.gate_circuits.append(circuit)
            self.new_gate_tracker = self.circuit.gate
        
        self.gate_option_viewer.update()
        
        self._update_textinput()
        for index, button in enumerate(self.display_gate_buttons_list):
            m_pos = (self.mouse_pos[0] - self.gate_option_viewer.blit_rect.x - self.gate_option_viewer.sub_surf_rect.x,
                         self.mouse_pos[1] - self.gate_option_viewer.blit_rect.y - self.gate_option_viewer.sub_surf_rect.y)
            
            gate = self.gate_options[index]
            gate.configure(node_on_click_func=self.circuit.on_node_clicked)
            button.configure(mouse_pos=m_pos, on_left_mouse_button_clicked=self.circuit.make_add_gate_func(gate))
            if index > len(self.constant_gate_options) - 1:
                button.configure(on_middle_mouse_button_clicked=self._make_set_circuit_editor_func(index), on_right_mouse_button_clicked=self._make_remove_gate_option_func(gate))
            button.update()



