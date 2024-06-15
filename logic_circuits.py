import math
import time
import pygame
from settings import *
from widgets import Button, ScrollableSurface
from logic_gates import AndGate, NotGate, GateBaseClass
from signal_tranfer import Node, Wire

class CustomGate:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        
        self.add_node_font = pygame.font.SysFont('Arial', 45)
        self.edit_button_font = pygame.font.SysFont('Sans Serif', 20)
        
        self.in_out_wire_size = 10, 20
        
        self.added_and_gate = False
        self.added_not_gate = False
        self.update_input_button_removals = False
        self.update_output_button_removals = False
        self.add_wire_breakpoint = False
        self.right_mouse_pressed = True
        self.left_mouse_pressed = True
        
        self.button_colors = 'grey'
        self.button_text_colors = 'white'
        self.button_border_offset = 20
        self.border_offset = 30
        
        self.add_input_button = Button(self.screen, (0, 0), (30, 30), self.button_colors, image=self.add_node_font.render('+', True, self.button_text_colors), on_left_mouse_button_clicked=self._add_input, border_radius=20)
        self.add_input_button.set_pos(midbottom=(self.border_offset, self.screen.get_height() - self.border_offset))
        self.add_output_button = Button(self.screen, (0, 0), (30, 30), self.button_colors, image=self.add_node_font.render('+', True, self.button_text_colors), on_left_mouse_button_clicked=self._add_output, border_radius=20)
        self.add_output_button.set_pos(midbottom=(self.screen.get_width() - self.border_offset, self.screen.get_height() - self.border_offset))
        
        self.new_gate_circuit_button = Button(self.screen, (0, 0), (100, 20), self.button_colors, image=self.edit_button_font.render('New Circuit', True, self.button_text_colors), border_radius=10, on_left_mouse_button_clicked=lambda: print('Not Implemented'))
        self.new_gate_circuit_button.set_pos(topleft=(self.button_border_offset, self.button_border_offset))
        self.add_gate_button = Button(self.screen, (0, 0), (100, 20), self.button_colors, image=self.edit_button_font.render('Make Gate', True, self.button_text_colors), border_radius=10, on_left_mouse_button_clicked=lambda: print('Not Implemented'))
        self.add_gate_button.set_pos(midtop=((self.screen.get_width() / 4) + self.button_border_offset, self.button_border_offset))
        self.rename_gate_button = Button(self.screen, (0, 0), (100, 20), self.button_colors, image=self.edit_button_font.render('Rename Gate', True, self.button_text_colors), border_radius=10, on_left_mouse_button_clicked=lambda: print('Not Implemented'))
        self.rename_gate_button.set_pos(midtop=(((self.screen.get_width() / 4) + (self.screen.get_width() / 2)) - self.button_border_offset, self.button_border_offset))
        self.update_gate_button = Button(self.screen, (0, 0), (100, 20), self.button_colors, image=self.edit_button_font.render('Update Gate', True, self.button_text_colors), border_radius=10, on_left_mouse_button_clicked=lambda: print('Not Implemented'))
        self.update_gate_button.set_pos(topright=(self.screen.get_width() - self.button_border_offset, self.button_border_offset))
        
        self.input_node_objects = []
        self.output_node_objects = []
        
        self.wire_connected_trackers = {}
        
        self.gate_options: list[GateBaseClass] = [AndGate(self.screen, (0, 0), self._on_node_clicked),
                                                  NotGate(self.screen, (0, 0), self._on_node_clicked)]
        
        self.current_circuit_name = ''
        self.circuit_editors: dict[str, dict[str, list[GateBaseClass] | list[Wire]]] = {}
        
        self.circuit_editors[self.current_circuit_name] = DEFAULT_CIRCUIT
        
        self.gate_display_spacing = 5
        
        max_height = max(gate_op.button.rect.height for gate_op in self.gate_options) + self.border_offset
        
        self.gate_option_viewer_size = (self.add_output_button.rect.left - self.border_offset) - (self.add_input_button.rect.right + self.border_offset), max_height
        
        self.display_gate_buttons_list = []
        
        gates_surf_width = len(self.gate_options) * ((self.gate_options[0].output_nodes[0].get_rect().right - self.gate_options[0].input_nodes[0].get_rect().left) + self.gate_display_spacing)
        self.gates_surf = pygame.Surface((gates_surf_width, self.gate_option_viewer_size[1]))
        
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
            dsp_but.configure(on_left_mouse_button_clicked=self._make_add_gate_func(gate_op), on_right_mouse_button_clicked=self._make_remove_gate_option_func(gate_op), many_actions_one_click=False, invisible=True)
            
            self.display_gate_buttons_list.append(dsp_but)
            
            display_gate.update()
        
        self.gate_option_viewer = ScrollableSurface(self.screen,
                                                    self.gates_surf,
                                                    (max((self.gate_option_viewer_size[0] / 2) - (self.gates_surf.get_width() / 2), 0), 0),
                                                    ((self.screen.get_width() / 2) - (self.gate_option_viewer_size[0] / 2),
                                                     self.screen.get_height() - self.gate_option_viewer_size[1] - self.border_offset),
                                                    self.gate_option_viewer_size,
                                                    orientation='x')
        
        for index, gate in enumerate(self.gate_options):
            gate.button.configure(bg_color='red', on_right_mouse_button_clicked=self._make_remove_gate_func(index))
        
        self.gate_key_index_map = {}
        
        self._add_input()
        self._add_output()
    
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
            max_nodes_amt = int((self.screen.get_height() - (self.screen.get_height() - self.add_input_button.rect.top)) / height)
            width = (but.rect.width + node.node_button.rect.width + self.in_out_wire_size[0]) + box_offset
            half_scr_offset = (self.screen.get_height() / 2) - ((min(len(self.input_node_objects), max_nodes_amt) * height) / 2) - (self.screen.get_height() - self.add_input_button.rect.bottom)
            
            x = box_offset + (math.floor(index / max_nodes_amt) * width)
            y = ((index % max_nodes_amt) * height) + half_scr_offset
            but.set_pos(topleft=(x, y))
            node.set_pos((but.rect.x + but.rect.width + self.in_out_wire_size[0], but.rect.centery - (self.in_out_wire_size[1] / 2)))
    
    def _set_output_node_positions(self, delay=False):
        if delay:
            time.sleep(0.2)
        self.output_node_objects: list[Node]
        for index, node in enumerate(self.output_node_objects):
            box_offset = 10
            height = node.node_button.rect.height + box_offset
            max_nodes_amt = int((self.screen.get_height() - (self.screen.get_height() - self.add_output_button.rect.top)) / height)
            width = node.node_button.rect.width + box_offset
            half_scr_offset = (self.screen.get_height() / 2) - ((min(len(self.output_node_objects), max_nodes_amt) * height) / 2) - (self.screen.get_height() - self.add_output_button.rect.bottom)
            
            x = self.screen.get_width() - node.node_button.rect.width - box_offset - (math.floor(index / max_nodes_amt) * width)
            y = ((index % max_nodes_amt) * height) + half_scr_offset
            node.set_pos((x, y))
    
    def _add_input(self):
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
                          on_click_func=self._on_node_clicked
                          )
        
        self.update_input_button_removals = True
        self.input_node_objects.append((ctrl_button, input_node))
        self._set_input_node_positions()
    
    def _add_output(self):
        output_node = Node(self.screen,
                          (0, 0),
                          (30, 30),
                          'yellow',
                          'darkgrey',
                          is_input=True,
                          is_click_toogleable=False,
                          static=False,
                          on_click_func=self._on_node_clicked
                          )
        
        self.update_output_button_removals = True
        self.output_node_objects.append(output_node)
        self._set_output_node_positions()
    
    def _on_node_clicked(self, input_node: Node):
        if True not in self.wire_connected_trackers.values():
            wire = Wire(self.screen, input_node.node_button.rect.center, self.mouse_pos, 5, 'pink', 'darkgrey', lambda w: self._remove_wire_func(w))
            input_node.connect(wire)
            if input_node.is_input:
                if wire.wire_move_buttons:
                    wire.wire_move_buttons.pop()
            self.circuit_editors[self.current_circuit_name][CIRCUIT_WIRE_ID].append(wire)
            self.wire_connected_trackers[wire] = True
    
    def _make_input_remove_node_func(self, index):
        def func():
            if index != 0:
                self.update_input_button_removals = True
                node = self.input_node_objects[index][1]
                connected_wires = node.connected_inputs.copy() + node.connected_inputs.copy()
                node.disconnect_all()
                for i, wire in enumerate(connected_wires):
                    self.circuit_editors[self.current_circuit_name][CIRCUIT_WIRE_ID].remove(wire)
                self.input_node_objects.pop(index)
                self._set_input_node_positions(True)
        
        return func
    
    def _make_output_remove_node_func(self, index):
        def func():
            if index != 0:
                self.update_output_button_removals = True
                
                node = self.output_node_objects[index]
                connected_wires = node.connected_inputs.copy() + node.connected_outputs.copy()
                node.disconnect_all()
                for i, wire in enumerate(connected_wires):
                    self.circuit_editors[self.current_circuit_name][CIRCUIT_WIRE_ID].remove(wire)
                self.output_node_objects.pop(index)
                self._set_output_node_positions(True)
        
        return func
    
    def _make_remove_gate_func(self, index: int):
        def func():
            for node in self.circuit_editors[self.current_circuit_name][CIRCUIT_GATE_ID][index].input_nodes + self.circuit_editors[self.current_circuit_name][CIRCUIT_GATE_ID][index].output_nodes:
                for in_wire in node.connected_inputs:
                    if in_wire in self.circuit_editors[self.current_circuit_name][CIRCUIT_WIRE_ID]:
                        self.circuit_editors[self.current_circuit_name][CIRCUIT_WIRE_ID].remove(in_wire)
                for out_wire in node.connected_outputs:
                    if out_wire in self.circuit_editors[self.current_circuit_name][CIRCUIT_WIRE_ID]:
                        self.circuit_editors[self.current_circuit_name][CIRCUIT_WIRE_ID].remove(out_wire)
            self.circuit_editors[self.current_circuit_name][CIRCUIT_GATE_ID][index].disconnect_all_nodes()
            self.circuit_editors[self.current_circuit_name][CIRCUIT_GATE_ID].pop(index)
        return func
    
    def _make_remove_gate_option_func(self, gate: GateBaseClass):
        def func():
            self._remove_gate(gate)
        
        return func
    
    def _remove_wire_func(self, wire: Wire):
        if wire.input_node is not None:
            wire.input_node.set_state(0)
        wire.disconnect_all()
        self.circuit_editors[self.current_circuit_name][CIRCUIT_WIRE_ID].remove(wire)
    
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
        dsp_but.configure(on_left_mouse_button_clicked=self._make_add_gate_func(gate), on_right_mouse_button_clicked=self._make_remove_gate_option_func(gate), many_actions_one_click=False, invisible=True)
        self.display_gate_buttons_list.append(dsp_but)
    
    def _remove_gate(self, old_gate: GateBaseClass):
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
            dsp_but.configure(on_left_mouse_button_clicked=self._make_add_gate_func(gate), invisible=True)
            self.display_gate_buttons_list.append(dsp_but)
    
    def _make_add_gate_func(self, gate: GateBaseClass):
        def func():
            gate.set_pos(pygame.mouse.get_pos())
            self.circuit_editors[self.current_circuit_name][CIRCUIT_GATE_ID].append(gate.copy())
        
        return func
    
    def make_gate(self, name):
        combinations = self._generate_combinations(len(self.input_node_objects))
        input_mapping = {}
        
        init_inp_vals = [node.get_state() for _, node in self.input_node_objects]
        
        for combs in combinations:
            for i, (_, node) in enumerate(self.input_node_objects):
                node.set_state(combs[i])
            self.made_gate = True
            self.update()
            time.sleep(.05)
            input_mapping.update({tuple(combs): [node.get_state() for node in self.output_node_objects]})
        
        new_gate = GateBaseClass(name, self.screen, (0, 0), len(self.input_node_objects), len(self.output_node_objects), lambda inputs: input_mapping[tuple(inputs)], self._on_node_clicked)
        
        for i, (_, node) in enumerate(self.input_node_objects):
            node.set_state(init_inp_vals[i])
        
        self.circuit_editors[self.current_circuit_name][GATE_ID] = new_gate
        self.gate_options.append(new_gate)
        
        self._add_gate_to_viewer(new_gate)
    
    def rename_gate(self, name):
        values = self.circuit_editors.pop(self.current_circuit_name)
        self.current_circuit_name = name
        self.circuit_editors[self.current_circuit_name] = values
        gate = self.circuit_editors[self.current_circuit_name][GATE_ID]
        if gate is not None:
            gate.configure(name=name)
    
    def new_circuit(self, name):
        self.current_circuit_name = name
        self.circuit_editors[self.current_circuit_name] = DEFAULT_CIRCUIT
        self.circuit_editors[self.current_circuit_name][CIRCUIT_WIRE_ID] = self.circuit_editors[self.current_circuit_name][CIRCUIT_WIRE_ID]
        self.circuit_editors[self.current_circuit_name][CIRCUIT_GATE_ID] = self.circuit_editors[self.current_circuit_name][CIRCUIT_GATE_ID]
    
    def update_gate(self, name):
        pass
    
    def update_addition_of_gates(self):
        for index, gate in enumerate(self.gate_options):
            new_gate = gate.copy()
            if self.gate_key_index_map.get(index) is None:
                self.gate_key_index_map[index] = False
            if self.keys[pygame.K_a + index]:
                if not self.gate_key_index_map[index]:
                    new_gate.set_pos(pygame.mouse.get_pos())
                    self.circuit_editors[self.current_circuit_name][CIRCUIT_GATE_ID].append(new_gate.copy())
                    self.gate_key_index_map[index] = True
            else:
                self.gate_key_index_map[index] = False
    
    def update_wires(self):
        for wire in self.circuit_editors[self.current_circuit_name][CIRCUIT_WIRE_ID]:
            if self.wire_connected_trackers[wire]:
                if pygame.mouse.get_pressed()[2]:
                    if not self.right_mouse_pressed:
                        if wire.input_connected:
                            wire.input_node.disconnect(wire)
                        elif wire.output_connected:
                            wire.output_node.disconnect(wire)
                        self.circuit_editors[self.current_circuit_name][CIRCUIT_WIRE_ID].remove(wire)
                        self.wire_connected_trackers[wire] = False
                    self.right_mouse_pressed = True
                else:
                    self.right_mouse_pressed = False
                
                if pygame.mouse.get_pressed()[0]:
                    if not self.left_mouse_pressed:
                        gate_nodes = []
                        for gate in self.circuit_editors[self.current_circuit_name][CIRCUIT_GATE_ID]:
                            gate_nodes += gate.get_input_nodes() + gate.get_output_nodes()
                        
                        for nodes in gate_nodes + [node for _, node in self.input_node_objects] + [node for node in self.output_node_objects]:
                            ending_point_rect = pygame.Rect(0, 0, 10, 10)
                            ending_point_rect.center = wire.ending_point
                            starting_point_rect = pygame.Rect(0, 0, 10, 10)
                            starting_point_rect.center = wire.starting_point
                            
                            if nodes.node_button.rect.collidepoint(wire.ending_point) and not ending_point_rect.colliderect(starting_point_rect):
                                nodes.connect(wire)
                                self.wire_connected_trackers[wire] = False
                                break
                        else:
                            if True not in [button.update()[-1] for _, button in wire.wire_move_buttons]:
                                wire.add_breakpoint(self.mouse_pos)
                            self.left_mouse_pressed = True
                            break
                    
                        self.left_mouse_pressed = True
                else:
                    self.left_mouse_pressed = False
                
                wire.move_breakpoint_ending_point(-1, pygame.mouse.get_pos())
            wire.update()
    
    def update_gates(self):
        for index, gate in enumerate(self.circuit_editors[self.current_circuit_name][CIRCUIT_GATE_ID]):
            gate.button.configure(on_right_mouse_button_clicked=self._make_remove_gate_func(index))
            gate.update()
    
    def update_inputs(self):
        self.add_input_button.update()
        for ctrl, out in self.input_node_objects:
            pygame.draw.line(self.screen, 'grey', ctrl.rect.center, out.node_button.rect.center)
            ctrl.update()
            out.update()
    
    def update_outputs(self):
        self.add_output_button.update()
        for out in self.output_node_objects:
            out.update()
    
    def update(self):
        self.keys = pygame.key.get_pressed()
        self.mouse_pos = pygame.mouse.get_pos()
        
        self.new_gate_circuit_button.update()
        self.add_gate_button.update()
        self.rename_gate_button.update()
        self.update_gate_button.update()
        
        self.update_gates()
        self.update_inputs()
        self.update_outputs()
        self.update_wires()
        self.gate_option_viewer.update()
        
        for button in self.display_gate_buttons_list:
            mouse = pygame.mouse.get_pos()
            mouse_pos = mouse[0] - self.gate_option_viewer.blit_rect.x - self.gate_option_viewer.sub_surf_rect.x, mouse[1] - self.gate_option_viewer.blit_rect.y - self.gate_option_viewer.sub_surf_rect.y
            button.configure(mouse_pos=mouse_pos)
            button.update()
        
        if self.update_input_button_removals:
            for i, (button, _) in enumerate(self.input_node_objects):
                button.configure(on_right_mouse_button_clicked=self._make_input_remove_node_func(i))
            self.update_input_button_removals = False
        
        if self.update_output_button_removals:
            for i, node in enumerate(self.output_node_objects):
                node.node_button.configure(on_right_mouse_button_clicked=self._make_output_remove_node_func(i))
            self.update_output_button_removals = False
        
        self.update_addition_of_gates()



