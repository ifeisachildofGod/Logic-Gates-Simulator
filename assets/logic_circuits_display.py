import pygame
from assets.settings import *
from assets.widgets import Button
from assets.modules import is_clicked
from assets.logic_gates_components import *
from assets.widgets import Button, ScrollableSurface
from pygame_textinput import TextInputManager, TextInputVisualizer

class CircuitDisplay:
    def __init__(self, screen: pygame.Surface, max_circuit_amt: int, add_buttons_border_offset: int, add_buttons_size: tuple, top_level: int) -> None:
        self.screen = screen
        
        self.max_circuit_amt = max_circuit_amt
        
        self.add_buttons_size = add_buttons_size
        self.add_buttons_border_offset = add_buttons_border_offset
        self.top_level = top_level
        
        self.input_output_node_border_offset = 50
        self.input_output_node_border_width = 8
        
        self._theme_color = 'red'
        
        self.new_gate_tracker = None
        
        self.circuit_editors: list[Circuit] = []
        self.circuit_index = -1
        
        self.pick_selected_gates: list[GateBaseClass] = []
        self.multi_selected_gates: list[GateBaseClass] = []
        
        self.textinput_font = pygame.font.SysFont('Consolas', 55)
        self.ref_mouse_pos_selected = self.ref_mouse_pos = self.mouse_pos = pygame.mouse.get_pos()
        self.events = pygame.event.get()
        
        textinput_manager = TextInputManager(initial = DEFAULT_CIRCUIT_NAME, validator = lambda input: len(input) < 25)
        self.textinput = TextInputVisualizer(manager=textinput_manager, font_color=(255, 255, 255), font_object=self.textinput_font)
        self.textinput.cursor_width = 4
        self.textinput.cursor_color = [(c+200)%255 for c in self.textinput.font_color]
        self.textinput.cursor_visible = False
        self.textinput_rect = self._get_textinput_rect()
        
        self.silent_text_input_update = False
        
        y = self.input_output_node_border_offset + self.top_level
        self.input_output_node_border_width = self.input_output_node_border_width
        height = self.screen.get_height() - (y * 2)
        
        self.selector_rect = pygame.Rect(0, 0, 0, 0)
        self.clicked_mouse_button = Button(self.screen, self.mouse_pos, (7, 7), border_radius=0, many_actions_one_click=True, on_left_mouse_button_clicked=self._on_mouse_button_clicked, on_not_left_mouse_button_clicked=self._on_mouse_button_not_clicked)
        self.selected_button = Button(self.screen, (0, 0), (0, 0), 'darkgrey', hover=False, on_left_mouse_button_clicked=self._on_selected_button_clicked, on_not_left_mouse_button_clicked=self._on_selected_button_not_clicked, many_actions_one_click=True)
        
        self.edit_index = None
        self.edit_indices = []
        
        self._make_new_circuit()
        
        self.textinput_focused = False
        self.has_textinput_focus = False
        self.gate_options_hovered = False
        
        self.constant_gate_options = [AndGate(self.screen, (0, 0), lambda node: self.circuit.on_node_clicked(node)),
                                      NotGate(self.screen, (0, 0), lambda node: self.circuit.on_node_clicked(node)),
                                      TimerGate(self.screen, (0, 0), lambda node: self.circuit.on_node_clicked(node))]
        
        self.gate_options: list[GateBaseClass] = []
        self.gate_options += self.constant_gate_options
        
        self.gate_circuits = []
        self.display_gate_buttons_list: list[Button] = []
        
        self.selected_display_ref_pos = self.ref_pos_selected = [0, 0]
        
        self.gate_display_spacing = 5
        self.gate_options_hovered_counter_false = 0
        
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
        
        height = self.gate_option_viewer.blit_rect.bottom - y
        self.left_frame_button = Button(self.screen, (self.input_output_node_border_offset, y), (self.input_output_node_border_width, height), on_left_mouse_button_clicked=self._add_input_node())
        self.right_frame_button = Button(self.screen, (self.screen.get_width() - self.input_output_node_border_width - self.input_output_node_border_offset, y), (self.input_output_node_border_width, height), on_left_mouse_button_clicked=self._add_output_node())
        self.top_frame_rect = pygame.Rect(self.left_frame_button.rect.x, self.left_frame_button.rect.y, self.right_frame_button.rect.right - self.left_frame_button.rect.left, self.input_output_node_border_width)
        self.bottom_frame_rect = pygame.Rect(self.left_frame_button.rect.x, self.left_frame_button.rect.bottom - self.input_output_node_border_width, self.right_frame_button.rect.right - self.left_frame_button.rect.left, self.input_output_node_border_width)
        
        self.selected_display_rect = pygame.Rect(0, 0, 0, 0)
        
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
        self.left_frame_button.configure(bg_color=self.circuit.input_node_objects[0][0].bg_color)
        self.right_frame_button.configure(bg_color=self.circuit.input_node_objects[0][0].bg_color)
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
            circuit = Circuit('_', self.screen, 0, 0, 'red', 1, 1, 1)
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
                tmp_circuit = Circuit('_', self.screen, 1, 1, 'red', 1, 1, 1)
                tmp_circuit.set_dict(gate.logic_func_or_circuit_or_circuit_dict)
            else:
                tmp_circuit = gate.logic_func_or_circuit_or_circuit_dict
            self.gate_circuits.append(tmp_circuit)
        
        self.theme_color = d['theme_color']
        self.textinput_focused = True
        
        self.screen.blit(self.textinput.surface, self.textinput_rect)
    
    def _add_output_node(self):
        def func():
            if not self.circuit.any_output_node_hovered:
                self.circuit.add_output(self.mouse_pos[1])
        
        return func
    
    def _add_input_node(self):
        def func():
            if not self.circuit.any_input_node_hovered:
                self.circuit.add_input(self.mouse_pos[1])
        
        return func
    
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
                                 len(self.circuit.output_node_objects),
                                 self.circuit.copy())
        new_gate.update()
                
        self.circuit.gate = new_gate, self.circuit.copy()
        
        self.textinput.value = '_'
        self.textinput_focused = True
        self.silent_text_input_update = True
        
        for wire in list(self.circuit.wires):
            wire.disconnect_all()
        self.circuit.gates.clear()
        self.circuit.wires.clear()
    
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
            circuit = Circuit(name, self.screen, self.screen.get_height() - self.add_buttons_border_offset - self.add_buttons_size[1], self.add_buttons_size[1], self.theme_color, self.input_output_node_border_offset, self.input_output_node_border_width, self.top_level) if circuit is None else circuit
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
    
    def _toogle_gate_option_hovered(self, state):
        self.gate_options_hovered = state
    
    def _on_selected_button_clicked(self):
        dx = self.ref_pos_selected[0] + (self.mouse_pos[0] - self.ref_mouse_pos_selected[0])
        dy = self.ref_pos_selected[1] + (self.mouse_pos[1] - self.ref_mouse_pos_selected[1])
        
        self.selected_display_rect.centerx = self.selected_display_ref_pos[0] + (self.mouse_pos[0] - self.ref_mouse_pos_selected[0])
        self.selected_display_rect.centery = self.selected_display_ref_pos[1] + (self.mouse_pos[1] - self.ref_mouse_pos_selected[1])
         
        self.selected_button.set_pos(center=(dx, dy))
        for index, gate in enumerate(self.multi_selected_gates):
            ref_pos = self.multi_selected_gates_ref_pos[index]
            dx = ref_pos[0] + (self.mouse_pos[0] - self.ref_mouse_pos_selected[0])
            dy = ref_pos[1] + (self.mouse_pos[1] - self.ref_mouse_pos_selected[1])
            gate.set_pos((dx, dy))
    
    def _on_selected_button_not_clicked(self):
        self.ref_mouse_pos_selected = self.mouse_pos
        self.ref_pos_selected = self.selected_button.rect.center
        self.selected_display_ref_pos = self.selected_display_rect.center
        self.multi_selected_gates_ref_pos = [gate.button.rect.center for gate in self.multi_selected_gates]
    
    def _on_mouse_button_clicked(self):
        is_anything_hovered = self.circuit.is_anything_hovered() if not self.selecting else False
        
        if not is_anything_hovered and not bool(sum(self.selected_button.size + self.selected_button.rect.topleft)):
            x = min(self.ref_mouse_pos[0], self.mouse_pos[0])
            y = min(self.ref_mouse_pos[1], self.mouse_pos[1])
            width = abs(self.mouse_pos[0] - self.ref_mouse_pos[0])
            height = abs(self.mouse_pos[1] - self.ref_mouse_pos[1])
            
            self.selector_rect.x = x
            self.selector_rect.y = y
            self.selector_rect.width = width
            self.selector_rect.height = height
            
            pygame.draw.rect(self.screen, 'red', self.selector_rect, 3)
    
    def _on_mouse_button_not_clicked(self):
        if bool(self.selector_rect.x + self.selector_rect.y + self.selector_rect.width + self.selector_rect.height):
            for index in range(len(self.circuit.gates)):
                gate = self.circuit.gates[index]
                gate_rect = gate.get_rect()
                
                x_collide = self.selector_rect.left < gate_rect.x < self.selector_rect.right - gate_rect.width
                y_collide = self.selector_rect.top < gate_rect.y < self.selector_rect.bottom - gate_rect.height
                
                if x_collide and y_collide:
                    self.multi_selected_gates.append(gate)
            
            if self.multi_selected_gates:
                offset = 5
                
                x = min([g.get_rect().left for g in self.multi_selected_gates]) - offset
                y = min([g.get_rect().top for g in self.multi_selected_gates]) - offset
                width = max([g.get_rect().right for g in self.multi_selected_gates]) - x + (offset * 2)
                height = max([g.get_rect().bottom for g in self.multi_selected_gates]) - y + (offset * 2)
                
                self.selected_button.configure(size=(30, 30))
                self.selected_button.set_pos(midleft=(x + offset + width, y + (height / 2)))
                
                self.selected_display_rect.x = x
                self.selected_display_rect.y = y
                self.selected_display_rect.width = width
                self.selected_display_rect.height = height
        
        self.selector_rect.x = 0
        self.selector_rect.y = 0
        self.selector_rect.width = 0
        self.selector_rect.height = 0
        
        self.ref_mouse_pos = self.mouse_pos
    
    def update(self, events, bg_color):
        self.mouse_pos = pygame.mouse.get_pos()
        self.events = events
        self.keys = pygame.key.get_pressed()
        self.bg_color = bg_color
        self.selecting = bool(self.selector_rect.x + self.selector_rect.y + self.selector_rect.width + self.selector_rect.height)
        
        self.clicked_mouse_button.set_pos(center=self.mouse_pos)
        self.clicked_mouse_button.configure()
        
        self.clicked_mouse_button.update()
        pygame.draw.rect(self.screen, 'green', self.selected_display_rect, 3)
        
        _, _, _, c = self.selected_button.update()
        if pygame.mouse.get_pressed()[0]:
            if not c or self.circuit.is_anything_hovered():
                self.selected_button.set_pos(topleft=(0, 0))
                self.selected_button.configure(size=(0, 0))
                
                self.selected_display_rect.x = 0
                self.selected_display_rect.y = 0
                self.selected_display_rect.width = 0
                self.selected_display_rect.height = 0
                
                self.multi_selected_gates.clear()
        
        self.circuit.update(self.gate_options_hovered, self.pick_selected_gates, self.bottom_frame_rect.bottom)
        
        pygame.draw.rect(self.screen, self.bg_color, (0, 0, self.screen.get_width(), self.top_frame_rect.top))
        pygame.draw.rect(self.screen, self.bg_color, (0, self.bottom_frame_rect.bottom, self.screen.get_width(), self.screen.get_height() - self.bottom_frame_rect.bottom))
        pygame.draw.rect(self.screen, self.bg_color, (0, 0, self.left_frame_button.rect.left, self.screen.get_height()))
        pygame.draw.rect(self.screen, self.bg_color, (self.right_frame_button.rect.right, 0, self.screen.get_width() - self.right_frame_button.rect.right, self.screen.get_height()))
        
        pygame.draw.rect(self.screen, self.left_frame_button.bg_color, self.top_frame_rect)
        pygame.draw.rect(self.screen, self.right_frame_button.bg_color, self.bottom_frame_rect)
        
        self.left_frame_button.update()
        self.right_frame_button.update()
        
        self.circuit.update_inputs()
        self.circuit.update_outputs()
        
        if self.new_gate_tracker != self.circuit.gate:
            gate, circuit = self.circuit.gate
            self.gate_options.append(gate)
            self._add_gate_to_viewer(gate)
            self.gate_circuits.append(circuit)
            self.new_gate_tracker = self.circuit.gate
        
        self.gate_option_viewer.update()
        
        if self.pick_selected_gates:
            self.pick_selected_gates[0].sub_selected = False
            if self.pick_selected_gates[0].selected == False:
                for gate in self.pick_selected_gates:
                    gate.sub_selected = False
                self.pick_selected_gates.clear()
                pass
        
        if True in list(self.circuit.wire_connected_trackers.values()):
            for gate in self.pick_selected_gates:
                gate.selected = False
                gate.sub_selected = False
        
        for index, gate in enumerate(self.pick_selected_gates[1:]):
            gate.selected = False
            gate._on_move((self.mouse_pos[0], self.mouse_pos[1] + ((gate.button.rect.height + 6) * (index + 1))))
            gate.sub_selected = True
        
        self._update_textinput()
        self.gate_options_hovered_counter_false = 0
        for index, button in enumerate(self.display_gate_buttons_list):
            m_pos = (self.mouse_pos[0] - self.gate_option_viewer.blit_rect.x - self.gate_option_viewer.sub_surf_rect.x,
                         self.mouse_pos[1] - self.gate_option_viewer.blit_rect.y - self.gate_option_viewer.sub_surf_rect.y)
            
            gate = self.gate_options[index]
            gate.configure(node_on_click_func=self.circuit.on_node_clicked)
            button.configure(mouse_pos=m_pos, on_left_mouse_button_clicked=self.circuit.make_add_gate_func(gate), on_hover=lambda: self._toogle_gate_option_hovered(True), on_not_hover=lambda: self._toogle_gate_option_hovered(False))
            if index > len(self.constant_gate_options) - 1:
                button.configure(on_middle_mouse_button_clicked=self._make_set_circuit_editor_func(index), on_right_mouse_button_clicked=self._make_remove_gate_option_func(gate))
            
            _, _, _, hovered = button.update()
            
            if not hovered:
                self.gate_options_hovered_counter_false += 1
        
        if self.gate_options_hovered_counter_false == len(self.display_gate_buttons_list):
            self.gate_options_hovered = False
        else:
            self.gate_options_hovered = True
        
        if self.silent_text_input_update:
            self.silent_text_input_update = False
            self.textinput_focused = False



