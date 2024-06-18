import math
import time
import pygame
from widgets import Button
from settings import GRID_SIZE
from logic_gates import GateBaseClass
from signal_tranfer import Node, Wire


class Circuit:
    def __init__(self, name: str, screen: pygame.Surface, node_base_line: int, add_nodes_buttons_height: int) -> None:
        self.screen = screen
        self.name = name
        
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
        
        self.mouse_pos = pygame.mouse.get_pos()
        self.grid_mouse_pos = tuple(list((i - (i % GRID_SIZE)) for i in self.mouse_pos))
        
        self.node_base_line = node_base_line
        self.add_nodes_buttons_height = add_nodes_buttons_height
        
        self.wire = None
        
        self.is_updating_with_displays = True
        
        self.render = True
        self.has_circuit_set_state = False
        
        self.add_input()
        self.add_output()
    
    def _get_all_nodes(self):
        nodes_in_gate = []
        for gate in self.gates:
            for node in gate.input_nodes + gate.output_nodes:
                nodes_in_gate.append(node)
        
        return [node for _, node in self.input_node_objects] + self.output_nodes + nodes_in_gate
    
    def copy(self):
        nodes = self._get_all_nodes()
        wire_index_connections = []
        for wire in self.wires:
            wire_nodes = []
            for node in nodes:
                if wire.is_connected_to(node):
                    wire_nodes.append(nodes.index(node))
            wire_index_connections.append(wire_nodes)
        
        circuit = Circuit(self.name, self.screen, self.node_base_line, self.add_nodes_buttons_height)
        
        def make_input_button_func(new_node):
            def func():
                new_node.set_state(not new_node.get_state())
            
            return func
        
        input_node_objects = []
        for but, node in self.input_node_objects:
            new_node = node.copy()
            new_but = but.copy()
            new_but.configure(on_left_mouse_button_clicked=make_input_button_func(new_node))
            input_node_objects.append([new_but, new_node])
        circuit.input_node_objects = input_node_objects
        circuit.update_input_button_removal = True
        
        circuit.output_nodes = [node.copy() for node in self.output_nodes]
        circuit.update_output_button_removal = True
        circuit.gates = [gate.copy() for gate in self.gates]
        
        wires = []
        for wire in self.wires:
            new_wire = wire.copy()
            new_wire.configure(delete_func=lambda w: circuit._remove_wire(w))
            wires.append(new_wire)
        circuit.wires = wires
        
        circuit.wire_connected_trackers = {wire: False for wire in circuit.wires}
        
        circuit_nodes = circuit._get_all_nodes()
        for node in circuit_nodes:
            node.configure(on_click_func=circuit.on_node_clicked)
        
        for index, node_connection in enumerate(wire_index_connections):
            for node_index in node_connection:
                circuit_nodes[node_index].connect(circuit.wires[index])
        
        return circuit
    
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
            half_scr_offset = (self.screen.get_height() / 2) - ((min(len(self.input_node_objects), max_nodes_amt) * height) / 2) - (self.screen.get_height() - (self.node_base_line + self.add_nodes_buttons_height))
            
            x = box_offset + (math.floor(index / max_nodes_amt) * width)
            y = ((index % max_nodes_amt) * height) + half_scr_offset
            but.set_pos(topleft=(x, y))
            
            node_center_x = (but.rect.x + but.rect.width + self.in_out_wire_size[0]) + (node.node_button.rect.width / 2)
            node_center_y = (but.rect.centery - (self.in_out_wire_size[1] / 2)) + (node.node_button.rect.height / 2)
            node.node_button.set_pos(center=(node_center_x - (node_center_x % GRID_SIZE), node_center_y - (node_center_y % GRID_SIZE)))
    
    def _set_output_node_positions(self, delay=False):
        if delay:
            time.sleep(0.2)
        self.output_nodes: list[Node]
        for index, node in enumerate(self.output_nodes):
            box_offset = 10
            height = node.node_button.rect.height + box_offset
            max_nodes_amt = int((self.screen.get_height() - (self.screen.get_height() - self.node_base_line)) / height)
            width = node.node_button.rect.width + box_offset
            half_scr_offset = (self.screen.get_height() / 2) - ((min(len(self.output_nodes), max_nodes_amt) * height) / 2) - (self.screen.get_height() - (self.node_base_line + self.add_nodes_buttons_height))
            
            centerx = (self.screen.get_width() - node.node_button.rect.width - box_offset - (math.floor(index / max_nodes_amt) * width)) + (node.node_button.rect.width / 2)
            centery = (((index % max_nodes_amt) * height) + half_scr_offset) + (node.node_button.rect.height / 2)
            node.node_button.set_pos(center=(centerx - (centerx % GRID_SIZE), centery - (centery % GRID_SIZE)))
    
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
            wire = Wire(self.screen, input_node.node_button.rect.center, self.grid_mouse_pos, 5, 'pink', 'darkgrey', lambda w: self._remove_wire(w))
            input_node.connect(wire)
            if input_node.is_input:
                if wire.wire_move_buttons:
                    wire.wire_move_buttons.pop()
            self.wires.append(wire)
            
            self.wire_connected_trackers[wire] = True
        else:
            for key in self.wire_connected_trackers.keys():
                self.wire_connected_trackers[key] = False
            
            is_touching_a_connection = input_node.node_button.rect.collidepoint(self.mouse_pos)
            
            circular_wire_connection = (((input_node.is_input and self.wire.input_connected)
                                            or
                                            (input_node.is_output and self.wire.output_connected))
                                        if is_touching_a_connection else False)
            if self.wire is not None:
                if not circular_wire_connection:
                    input_node.connect(self.wire)
    
    def _make_input_remove_node_func(self, index):
        def func():
            if index != 0:
                self.update_input_button_removal = True
                
                _, node = self.input_node_objects[index]
                connected_wires = node.connected_inputs.copy() + node.connected_outputs.copy()
                
                for wire in connected_wires:
                    self._remove_wire(wire)
                self.input_node_objects.pop(index)
                self._set_input_node_positions(True)
        
        return func
    
    def _make_output_remove_node_func(self, index):
        def func():
            if index != 0:
                self.update_output_button_removal = True
                
                node = self.output_nodes[index]
                connected_wires = node.connected_inputs.copy() + node.connected_outputs.copy()
                for wire in connected_wires:
                    self._remove_wire(wire)
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
    
    def make_add_gate_func(self, gate: GateBaseClass):
        def func():
            new_gate = gate.copy()
            new_gate.set_pos(self.grid_mouse_pos)
            self.gates.append(new_gate)
        
        return func
    
    def set_inputnodes(self, state_list: list[int]):
        for index, (_, node) in enumerate(self.input_node_objects):
            node.set_state(state_list[index])
    
    def _remove_wire(self, wire: Wire):
        for button in wire.get_move_buttons():
            if button.rect.collidepoint(self.grid_mouse_pos):
                break
        else:
            if wire in self.wires:
                if wire.input_connected:
                    wire.input_node.disconnect(wire)
                elif wire.output_connected:
                    wire.output_node.disconnect(wire)
                self.wires.remove(wire)
                self.wire_connected_trackers.pop(wire)
    
    def _set_all_buttons_disable_state(self, state: bool):
        for node in self.output_nodes:
            node.node_button.configure(disabled=state)
        
        for button, node in self.input_node_objects:
            node.node_button.configure(disabled=state)
            button.configure(disabled=state)
        
        for gate in self.gates:
            for node in gate.input_nodes + gate.output_nodes:
                node.configure(disabled=state)
        
        for wire in self.wires:
            for _, button in wire.wire_move_buttons:
                button.configure(disabled=state)
    
    def _update_wires_and_connections(self):
        for wire in self.wires:
            if self.wire_connected_trackers[wire]:
                if pygame.mouse.get_pressed()[2]:
                    if not self.wire_right_pressed:
                        self._remove_wire(wire)
                    self.wire_right_pressed = True
                else:
                    self.wire_right_pressed = False
                
                if pygame.mouse.get_pressed()[0]:
                    if not self.wire_left_pressed:
                        for nodes in self._get_all_nodes():
                            is_touching_a_connection = nodes.node_button.rect.collidepoint(self.grid_mouse_pos)
                            
                            circular_wire_connection = (((nodes.is_input and wire.input_connected)
                                                            or
                                                         (nodes.is_output and wire.output_connected))
                                                        if is_touching_a_connection else False)
                            self.wire = wire
                            if is_touching_a_connection:
                                if not circular_wire_connection:
                                    pass
                                    # nodes.connect(wire)
                                    # self.wire_connected_trackers[wire] = False
                                break
                        else:
                            if True not in [button.update()[-1] for _, button in wire.wire_move_buttons]:
                                wire.add_breakpoint(self.grid_mouse_pos)
                            self.wire_left_pressed = True
                            break
                    
                        self.wire_left_pressed = True
                else:
                    self.wire_left_pressed = False
                
                if wire.output_connected:
                    wire.move_breakpoint_ending_point(-1, self.grid_mouse_pos)
                else:
                    wire.move_breakpoint_starting_point(0, self.grid_mouse_pos)
            
            # if self.wire_connected_trackers[wire] is None:
            #     self.wire_connected_trackers[wire] = True
            
            wire.update()
            wire.configure(render=self.render, mouse_pos=self.mouse_pos)
    
    def _update_gates(self):
        for index, gate in enumerate(self.gates):
            gate.button.configure(on_right_mouse_button_clicked=self.make_remove_gate_func(index), render=self.render, mouse_pos=self.mouse_pos)
            gate.update()
    
    def _update_inputs(self):
        for ctrl, out in self.input_node_objects:
            if self.render:
                pygame.draw.line(self.screen, 'grey', ctrl.rect.center, out.node_button.rect.center)
            ctrl.update()
            ctrl.configure(render=self.render, mouse_pos=self.mouse_pos)
            out.update()
            out.configure(render=self.render, mouse_pos=self.mouse_pos)
    
    def _update_outputs(self):
        for out in self.output_nodes:
            out.update()
            out.configure(render=self.render, mouse_pos=self.mouse_pos)
    
    def _update_logic(self):
        self._update_wires_and_connections()
        self._update_gates()
        self._update_inputs()
        self._update_outputs()
    
    def _gate_update_logic(self):
        self._update_inputs()
        self._update_wires_and_connections()
        self._update_gates()
        self._update_outputs()
    
    def gate_update(self):
        for gate in self.gates:
            gate.button.set_pos(bottomright=(-200, -200))
        for node in self._get_all_nodes():
            node.node_button.set_pos(bottomright=(-200, -200))
        for button, _ in self.input_node_objects:
            button.set_pos(bottomright=(-200, -200))
        self.render = False
        self._set_all_buttons_disable_state(True)
        self._gate_update_logic()
    
    def update(self):
        self.render = True
        self.mouse_pos = pygame.mouse.get_pos()
        self.grid_mouse_pos = tuple(list((i - (i % GRID_SIZE)) for i in self.mouse_pos))
        
        if not self.has_circuit_set_state:
            self._set_all_buttons_disable_state(False)
            self.has_circuit_set_state = True
        
        self._update_logic()
        
        if self.update_input_button_removal:
            for i, (button, _) in enumerate(self.input_node_objects):
                button.configure(on_right_mouse_button_clicked=self._make_input_remove_node_func(i))
            self.update_input_button_removal = False
        
        if self.update_output_button_removal:
            for i, node in enumerate(self.output_nodes):
                node.node_button.configure(on_right_mouse_button_clicked=self._make_output_remove_node_func(i))
            self.update_output_button_removal = False



