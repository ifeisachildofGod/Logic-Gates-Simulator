import math
import time
import pygame
import pygame.draw_py
from settings import *
from widgets import Button
from typing import Callable
from modules import set_color
from signal_tranfer import Node
from signal_tranfer import Node, Wire

class GateBaseClass:
    def __init__(self, name: str, screen: pygame.Surface, pos: tuple, input_amt, output_amt, logic_func_or_circuit_or_circuit_dict, node_on_click_func: Callable[[Node], None] = None, node_on_color = 'pink', node_off_color = 'grey') -> None:
        self.name = name
        self.screen = screen
        self.font = pygame.font.SysFont('Times New Roman', 20)
        
        self.pos = pos
        
        self.node_pin_size = 5, 2
        self.gate_border_radius = 5
        self.node_size = NODE_SIZE, NODE_SIZE
        self.text_color = 'white'
        self.gate_color = '#222222'
        self.node_pin_color = 'white'
        
        self.mouse_pos = pygame.mouse.get_pos()
        self.grid_mouse_pos = tuple(list((i - (i % GRID_SIZE)) for i in self.mouse_pos))
        
        text_surf = self.font.render(self.name, True, self.text_color)
        
        self.input_amt = input_amt
        self.output_amt = output_amt
        self.node_on_click_func = node_on_click_func
        self.logic_func_or_circuit_or_circuit_dict = logic_func_or_circuit_or_circuit_dict
        self.node_on_color = node_on_color
        self.node_off_color = node_off_color
        
        if isinstance(self.logic_func_or_circuit_or_circuit_dict, Callable):
            self.logic_func = self.logic_func_or_circuit_or_circuit_dict
        elif isinstance(self.logic_func_or_circuit_or_circuit_dict, Circuit):
            self.logic_circuit = self.logic_func_or_circuit_or_circuit_dict.copy()
            self.logic_circuit.gate_update()
            self.logic_func = self._logic_func
        
        self.prev_pos = (0, 0)
        self.prev_mouse_pos = (0, 0)
        
        self.button_size = text_surf.get_width() + (GATE_TEXT_BORDER_OFFSET_X * 2), max((GATE_TEXT_BORDER_OFFSET_Y + NODE_SIZE) * max(self.input_amt, self.output_amt), text_surf.get_height() + (GATE_TEXT_BORDER_OFFSET_Y * 2))
        
        self.disabled = False
        self.render = True
        
        self.input_nodes_state_tracker = []
        
        self.input_nodes = [Node(self.screen,
                                 (self.pos[0], self._get_node_y_pos(self.input_amt, ni)),
                                 self.node_size,
                                 color_on=self.node_on_color,
                                 color_off=self.node_off_color,
                                 static=False,
                                 is_input=True,
                                 border_radius=max(self.node_size) * 5,
                                 is_click_toogleable=False,
                                 on_click_func=self.node_on_click_func) for ni in range(self.input_amt)]

        self.button = Button(self.screen,
                             ((self.input_nodes[0].node_button.rect.right + self.node_pin_size[0]) if self.input_nodes else self.pos[0], self.pos[1]),
                             self.button_size,
                             self.gate_color,
                             hover=False,
                             many_actions_one_click=True,
                             on_left_mouse_button_clicked=lambda: self._on_move(self.grid_mouse_pos),
                             on_not_left_mouse_button_clicked=lambda: self._on_not_move(self.grid_mouse_pos),
                             image=text_surf
                             )
        
        self.output_nodes = [Node(self.screen,
                                  (self.button.rect.right + self.node_pin_size[0], self._get_node_y_pos(output_amt, no)),
                                  self.node_size,
                                  color_on=self.node_on_color,
                                  color_off=self.node_off_color,
                                  static=False,
                                  is_input=False,
                                  border_radius=max(self.node_size) * 5,
                                  is_click_toogleable=False,
                                  on_click_func=self.node_on_click_func) for no in range(self.output_amt)]
    
    def get_dict(self):
        if isinstance(self.logic_func_or_circuit_or_circuit_dict, Callable):
            l_func = f'#function{self.name}'
        else:
            l_func = self.logic_func_or_circuit_or_circuit_dict.get_dict()
        return {
            'name': self.name,
            'input_amt': self.input_amt,
            'output_amt': self.output_amt,
            'logic_func_or_circuit_or_circuit_dict': l_func,
            'node_on_color': self.node_on_color,
            'node_off_color': self.node_off_color,
            'pos': self.get_rect().topleft,
        }
    
    def set_dict(self, d: dict):
        self.configure(**d)
    
    def get_rect(self):
        if self.input_nodes:
            x = (self.input_nodes[0].node_button.rect.left) if self.input_nodes else self.button.rect.left
            y = min(self.input_nodes[0].node_button.rect.top, self.button.rect.top) if self.input_nodes else self.button.rect.top
            width = self.output_nodes[0].node_button.rect.right - x
            height = max(self.button.rect.height, self.button.rect.bottom - y, max(self.input_nodes[-1].node_button.rect.bottom, self.output_nodes[-1].node_button.rect.bottom) - y)
        else:
            x = self.button.rect.left
            y = self.button.rect.top
            width = self.output_nodes[0].node_button.rect.right - x
            height = max(self.button.rect.height, self.button.rect.bottom - y, self.output_nodes[-1].node_button.rect.bottom - y)
        
        return pygame.Rect(x, y, width, height)
    
    def _get_node_y_pos(self, amt, index):
        if amt == 1:
            return self.pos[1] + ((self.button_size[1] / 2) - (self.node_size[1] / 2))
        return (self.pos[1] + (index / (amt - (1 + 0.000000001))) * self.button_size[1]) - self.node_size[1] * (index / (amt - (1 + 0.000000001)))
    
    def configure(self, **kwargs):
        screen = kwargs.get('screen')
        if screen is not None:
            self.screen = screen
            for node in self.input_nodes + self.output_nodes:
                node.configure(screen=self.screen)
            
            self.button.configure(screen=self.screen)
        
        pos = kwargs.get('pos')
        if pos is not None:
            self.pos = pos
            rect = self.get_rect()
            self._on_move((self.pos[0] + (rect.width / 2), self.pos[1] + (rect.height / 2)))
        
        name = kwargs.get('name')
        if name is not None:
            self.name = name
            text_surf = self.font.render(self.name, True, self.text_color)
            size = (text_surf.get_width() + (GATE_TEXT_BORDER_OFFSET_X * 2), max((GATE_TEXT_BORDER_OFFSET_Y + NODE_SIZE) * max(self.input_amt, self.output_amt), text_surf.get_height() + (GATE_TEXT_BORDER_OFFSET_Y * 2)))
            self.button.configure(size=size, image=text_surf)
        
        input_amt = kwargs.get('input_amt')
        if input_amt is not None:
            self.input_amt = input_amt
            self.button_size = text_surf.get_width() + (GATE_TEXT_BORDER_OFFSET_X * 2), max((GATE_TEXT_BORDER_OFFSET_Y + NODE_SIZE) * max(self.input_amt, self.output_amt), text_surf.get_height() + (GATE_TEXT_BORDER_OFFSET_Y * 2))
            self.button.configure(size=self.button_size)
            new_node = Node(self.screen,
                            (0, 0),
                            self.node_size,
                            color_on=self.node_on_color,
                            color_off=self.node_off_color,
                            static=False,
                            is_input=True,
                            border_radius=max(self.node_size) * 5,
                            is_click_toogleable=False,
                            on_click_func=self.node_on_click_func)
            self.input_nodes.append(new_node)
            for index, node in enumerate(self.input_nodes):
                node.configure(pos=self._get_node_y_pos(self.input_amt, index))
        
        output_amt = kwargs.get('output_amt')
        if output_amt is not None:
            self.output_amt = output_amt
            self.button_size = text_surf.get_width() + (GATE_TEXT_BORDER_OFFSET_X * 2), max((GATE_TEXT_BORDER_OFFSET_Y + NODE_SIZE) * max(self.input_amt, self.output_amt), text_surf.get_height() + (GATE_TEXT_BORDER_OFFSET_Y * 2))
            self.button.configure(size=self.button_size)
            new_node = Node(self.screen,
                            (0, 0),
                            self.node_size,
                            color_on=self.node_on_color,
                            color_off=self.node_off_color,
                            static=False,
                            is_input=True,
                            border_radius=max(self.node_size) * 5,
                            is_click_toogleable=False,
                            on_click_func=self.node_on_click_func)
            self.input_nodes.append(new_node)
            for index, node in enumerate(self.input_nodes):
                node.configure(pos=(self.button.rect.right + self.node_pin_size[0], self._get_node_y_pos(output_amt, index)))
        
        logic_func_or_circuit_or_circuit_dict = kwargs.get('logic_func_or_circuit_or_circuit_dict')
        if logic_func_or_circuit_or_circuit_dict is not None:
            self.logic_func_or_circuit_or_circuit_dict = logic_func_or_circuit_or_circuit_dict
            if isinstance(self.logic_func_or_circuit_or_circuit_dict, str):
                if '#function' in self.logic_func_or_circuit_or_circuit_dict:
                    match self.logic_func_or_circuit_or_circuit_dict.replace('#function', ''):
                        case 'And':
                            self.logic_func_or_circuit_or_circuit_dict = AndGate(self.screen, self.get_rect().topleft, self.node_on_click_func).logic_func
                        case 'Not':
                            self.logic_func_or_circuit_or_circuit_dict = NotGate(self.screen, self.get_rect().topleft, self.node_on_click_func).logic_func
                        case 'Timer':
                            self.logic_func_or_circuit_or_circuit_dict = TimerGate(self.screen, self.get_rect().topleft, self.node_on_click_func).logic_func
            
            if isinstance(self.logic_func_or_circuit_or_circuit_dict, Callable):
                self.logic_func = self.logic_func_or_circuit_or_circuit_dict
            elif isinstance(self.logic_func_or_circuit_or_circuit_dict, dict):
                self.logic_circuit = Circuit(self.name, self.screen, 1, 1, 'red')
                self.logic_circuit.set_dict(self.logic_func_or_circuit_or_circuit_dict)
                self.logic_circuit.gate_update()
            elif isinstance(self.logic_func_or_circuit_or_circuit_dict, GateBaseClass):
                self.logic_circuit = self.logic_func_or_circuit_or_circuit_dict.copy()
                self.logic_circuit.gate_update()
                self.logic_func = self._logic_func
        
        render = kwargs.get('render')
        if render is not None:
            self.render = render
        
        disabled = kwargs.get('disabled')
        if disabled is not None:
            self.disabled = disabled
        
        mouse_pos = kwargs.get('mouse_pos')
        if mouse_pos is not None:
            self.mouse_pos = mouse_pos
        
        node_pin_color = kwargs.get('node_pin_color')
        if node_pin_color is not None:
            self.node_pin_color = node_pin_color
        
        node_on_color = kwargs.get('node_on_color')
        if node_on_color is not None:
            self.node_on_color = node_on_color
            for node in self.input_nodes:
                node.configure(color_on=self.node_on_color)
            for node in self.output_nodes:
                node.configure(color_on=self.node_on_color)
        
        node_off_color = kwargs.get('node_off_color')
        if node_off_color is not None:
            self.node_off_color = node_off_color
            for node in self.input_nodes:
                node.configure(color_off=self.node_off_color)
            for node in self.output_nodes:
                node.configure(color_off=self.node_off_color)
        
        gate_color = kwargs.get('gate_color')
        if gate_color is not None:
            self.gate_color = gate_color
            self.button.configure(bg_color=self.gate_color)
        
        text_color = kwargs.get('text_color')
        if text_color is not None:
            self.text_color = text_color
            text_surf = self.font.render(self.name, True, self.text_color)
            self.button.configure(image=text_surf)
        
        node_on_click_func = kwargs.get('node_on_click_func')
        if node_on_click_func is not None:
            self.node_on_click_func = node_on_click_func
    
    def _on_move(self, dest):
        dest_x, dest_y = dest
        x = self.prev_pos[0] + (dest_x - self.prev_mouse_pos[0])
        y = self.prev_pos[1] + (dest_y - self.prev_mouse_pos[1])
        self.set_pos((x, y))
    
    def _on_not_move(self, dest):
        self.prev_pos = self.button.rect.centerx, self.button.rect.centery
        self.prev_mouse_pos = dest
    
    def copy(self):
        gate = GateBaseClass(name=self.name,
                             screen=self.screen,
                             pos= self.button.rect.topleft,
                             input_amt=self.input_amt,
                             output_amt=self.output_amt,
                             logic_func_or_circuit_or_circuit_dict=self.logic_func_or_circuit_or_circuit_dict,
                             node_on_click_func=self.node_on_click_func)
        gate.configure(gate_color=self.gate_color, text_color=self.text_color, node_on_color=self.node_on_color, node_off_color=self.node_off_color)
        
        return gate
    
    def disconnect_all_nodes(self):
        for node in self.input_nodes:
            node.disconnect_all()
        for node in self.output_nodes:
            node.disconnect_all()
    
    def set_pos(self, pos):
        prev_x, prev_y = self.button.rect.x, self.button.rect.y
        self.button.set_pos(center=pos)
        for node in self.input_nodes + self.output_nodes:
            node.configure(pos=(node.get_rect().x + (self.button.rect.x - prev_x), node.get_rect().y + (self.button.rect.y - prev_y)))
    
    def get_input_nodes(self):
        return self.input_nodes
    
    def get_output_nodes(self):
        return self.output_nodes
    
    def get_output(self):
        return [node.get_state() for node in self.output_nodes]
    
    def draw(self):
        for node_in in self.input_nodes:
            if self.render:
                pygame.draw.rect(self.screen, self.node_pin_color, (self.button.rect.left - self.node_pin_size[0], node_in.get_rect().centery - self.node_pin_size[1] / 2, *self.node_pin_size))
            node_in.update()
            node_in.configure(render=self.render)
            node_in.node_button.configure(disabled=self.disabled)
        
        for node_out in self.output_nodes:
            if self.render:
                pygame.draw.rect(self.screen, self.node_pin_color, (self.button.rect.right, node_out.get_rect().centery - self.node_pin_size[1] / 2, *self.node_pin_size))
            node_out.update()
            node_out.configure(render=self.render)
            node_out.node_button.configure(disabled=self.disabled)
    
    def _logic_func(self, inputs):
        self.logic_circuit.set_inputnodes(inputs)
        self.logic_circuit.gate_update()
        
        return [node.get_state() for node in self.logic_circuit.output_nodes]
    
    def logic(self, input_states):
        outputs = self.logic_func(input_states)
        for index, state in enumerate(outputs):
            self.output_nodes[index].set_state(state)
    
    def update(self):
        input_states = [node.get_state() for node in self.input_nodes]
        self.logic(input_states)
        self.draw()
        self.button.update()
        self.button.configure(disabled=self.disabled, render=self.render)
        self.mouse_pos = pygame.mouse.get_pos()
        self.grid_mouse_pos = tuple(list((i - (i % GRID_SIZE)) for i in self.mouse_pos))

class Circuit:
    def __init__(self, name: str, screen: pygame.Surface, node_base_line: int, add_nodes_buttons_height: int, theme_color) -> None:
        self.screen = screen
        self.name = name
        
        self.in_out_wire_size = 10, 20
        
        self.wire_right_pressed = False
        self.wire_left_pressed = False
        self.gate = None
        
        self._theme_color = theme_color
        
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
    
    @property
    def theme_color(self):
        return self._theme_color
    
    @theme_color.setter
    def theme_color(self, v):
        self._theme_color = v
        self._recolor(self._theme_color)
    
    def _get_wire_connected_indexes(self):
        nodes = self._get_all_nodes()
        wire_index_connections = []
        for wire in self.wires:
            wire_nodes = []
            for node in nodes:
                if wire.is_connected_to(node):
                    wire_nodes.append(nodes.index(node))
            wire_index_connections.append(wire_nodes)
        
        return wire_index_connections
    
    def copy(self):
        circuit = Circuit(self.name, self.screen, self.node_base_line, self.add_nodes_buttons_height, self.theme_color)
        
        def make_input_button_func(new_node): return lambda: new_node.set_state(not new_node.get_state())
        
        circuit.input_node_objects.clear()
        circuit.output_nodes.clear()
        circuit.gates.clear()
        circuit.wires.clear()
        
        circuit.update_output_button_removal = True
        circuit.update_input_button_removal = True
        circuit.wire_connected_trackers = {wire: False for wire in circuit.wires}
        
        for but, node in self.input_node_objects:
            new_node = node.copy()
            new_but = but.copy()
            new_but.configure(on_left_mouse_button_clicked=make_input_button_func(new_node))
            circuit.input_node_objects.append([new_but, new_node])
        
        for node in self.output_nodes:
            circuit.output_nodes.append(node.copy())
        
        for gate in self.gates:
            circuit.gates.append(gate.copy())
        
        for wire in self.wires:
            new_wire = wire.copy()
            new_wire.configure(delete_func=lambda w: circuit._remove_wire(w))
            circuit.wires.append(new_wire)
        
        circuit_nodes = circuit._get_all_nodes()
        for node in circuit_nodes:
            node.configure(on_click_func=circuit.on_node_clicked)
        
        for index, node_connection in enumerate(self._get_wire_connected_indexes()):
            for node_index in node_connection:
                circuit_nodes[node_index].connect(circuit.wires[index])
        
        return circuit
    
    def get_dict(self):
        return {
            'name': self.name,
            'node_base_line': self.node_base_line,
            'add_nodes_buttons_height': self.add_nodes_buttons_height,
            'theme_color': self.theme_color,
            
            'input_node_objects': [[but.get_dict(), node.get_dict()] for but, node in self.input_node_objects],
            'output_nodes': [node.get_dict() for node in self.output_nodes],
            'gates': [gate.get_dict() for gate in self.gates],
            'wires': [wire.get_dict() for wire in self.wires],
            'wire_connected_indexes': self._get_wire_connected_indexes()
        }
    
    def set_dict(self, d: dict):
        input_node_objects = d.pop('input_node_objects')
        output_nodes = d.pop('output_nodes')
        gates = d.pop('gates')
        wires = d.pop('wires')
        wire_connected_indexes = d.pop('wire_connected_indexes')
        
        self.input_node_objects.clear()
        self.output_nodes.clear()
        self.gates.clear()
        self.wires.clear()
        
        self.update_input_button_removal = True
        self.update_output_button_removal = True
        
        self.__dict__.update(d)
        
        def make_input_button_func(new_node): return lambda: new_node.set_state(not new_node.get_state())
        
        for but_info, node_info in input_node_objects:
            new_but = Button(self.screen, (0, 0), (0, 0), 'red')
            new_but.set_dict(but_info)
            new_node = Node(self.screen, (0, 0), (0, 0), 'red', 'red', True)
            new_node.set_dict(node_info)
            new_but.configure(on_left_mouse_button_clicked=make_input_button_func(new_node))
            self.input_node_objects.append([new_but, new_node])
        
        for node_info in output_nodes:
            new_node = Node(self.screen, (0, 0), (0, 0), 'red', 'red', True)
            new_node.set_dict(node_info)
            self.output_nodes.append(new_node)
        
        for gate_info in gates:
            new_gate = GateBaseClass('_', self.screen, (0, 0), 1, 1, lambda l: l, self.on_node_clicked)
            new_gate.set_dict(gate_info)
            self.gates.append(new_gate)
        
        for wire_info in wires:
            new_wire = Wire(self.screen, [0, 0], [1, 1], 2, 'red', 'red', None)
            new_wire.set_dict(wire_info)
            new_wire.configure(delete_func=lambda w: self._remove_wire(w))
            self.wires.append(new_wire)
        
        self.wire_connected_trackers = {wire: False for wire in self.wires}
        
        nodes = self._get_all_nodes()
        for index, node_connection in enumerate(wire_connected_indexes):
            for node_index in node_connection:
                nodes[node_index].connect(self.wires[index])
        
        self.theme_color = d.pop('theme_color')
    
    def _get_node_on_color(self, color):
        on_color = []
        for i, v in enumerate(set_color(color, 255)):
            v = (v * i) % 255
            on_color.append(v)
        
        return on_color
    
    def _get_node_off_color(self, color):
        return set_color(color, 125)
        # on_color = []
        # for i, v in enumerate(set_color(color, 255)):
        #     v = (v * i) % 255
        #     on_color.append(v)
        
        # return on_color
    
    def _set_gate_color(self, gate: GateBaseClass, color):
        gate_body_color = set_color(color, 200)
        gate_text_color = set_color(color, 10)
        gate.configure(gate_color=gate_body_color, text_color=gate_text_color, node_on_color=self._get_node_on_color(color), node_off_color=self._get_node_off_color(color))
    
    def _get_all_nodes(self):
        nodes_in_gate = []
        for gate in sorted(self.gates, key= lambda v: v.get_rect().x):
            for node in gate.input_nodes + gate.output_nodes:
                nodes_in_gate.append(node)
        
        return [node for _, node in self.input_node_objects] + nodes_in_gate + self.output_nodes
    
    def _recolor(self, color):
        on_color = self._get_node_on_color(color)
        off_color = self._get_node_off_color(color)
        control_button_colors = set_color(color, 90)
        
        for button, node in self.input_node_objects:
            button.configure(bg_color=control_button_colors)
            node.configure(color_on=on_color, color_off=off_color)
        
        for node in self.output_nodes:
            node.configure(color_on=on_color, color_off=off_color)
        
        for wire in self.wires:
            wire.configure(color_on=on_color, color_off=off_color)
        
        for gate in self.gates:
            self._set_gate_color(gate, color)
    
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
            max_nodes_amt = (self.screen.get_height() - (self.screen.get_height() - self.node_base_line)) / height + 0.000000001
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
            max_nodes_amt = (self.screen.get_height() - (self.screen.get_height() - self.node_base_line)) / height + 0.000000001
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
        self._recolor(self.theme_color)
    
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
        self._recolor(self.theme_color)
    
    def on_node_clicked(self, input_node: Node):
        if True not in self.wire_connected_trackers.values():
            wire = Wire(self.screen, input_node.node_button.rect.center, self.grid_mouse_pos, 5, 'pink', 'darkgrey', lambda w: self._remove_wire(w))
            input_node.connect(wire)
            if input_node.is_input:
                if wire.wire_move_buttons:
                    wire.wire_move_buttons.pop()
            self.wires.append(wire)
            self._recolor(self.theme_color)
            self.wire_connected_trackers[wire] = True
        else:
            for key in self.wire_connected_trackers.keys():
                self.wire_connected_trackers[key] = False
            
            for wire in self.wires:
                if pygame.mouse.get_pressed()[0]:
                    for nodes in self._get_all_nodes():
                        is_touching_a_connection = nodes.node_button.rect.collidepoint(self.grid_mouse_pos)
                                
                        circular_wire_connection = (((nodes.is_input and wire.input_connected)
                                                        or
                                                        (nodes.is_output and wire.output_connected))
                                                    if is_touching_a_connection else False)
                        self.wire = wire
                        if is_touching_a_connection:
                            if not circular_wire_connection:
                                nodes.connect(self.wire)
                                # self.wire_connected_trackers[wire] = False
                            break
            
            # is_touching_a_connection = input_node.node_button.rect.collidepoint(self.mouse_pos)
            
            # if self.wire is not None:
            #     circular_wire_connection = (((input_node.is_input and self.wire.input_connected)
            #                                     or
            #                                  (input_node.is_output and self.wire.output_connected))
            #                             if is_touching_a_connection else False)
            #     if not circular_wire_connection:
            #         input_node.connect(self.wire)
    
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
            # def sub_func():
                # time.sleep(5)
                new_gate = gate.copy()
                new_gate.set_pos(self.grid_mouse_pos)
                self.gates.append(new_gate)
                self._recolor(self.theme_color)
                time.sleep(0.1)
            # t = threading.Thread(target=sub_func)
            # t.daemon = True
            # t.start()
        
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
                                    # nodes.connect(wire)
                                    pass
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

class AndGate(GateBaseClass):
    def __init__(self, screen, pos, node_on_click_func) -> None:
        super().__init__('And', screen, pos, 2, 1, lambda inputs: [inputs[0] and inputs[1]], node_on_click_func)

class NotGate(GateBaseClass):
    def __init__(self, screen, pos, node_on_click_func) -> None:
        super().__init__('Not', screen, pos, 1, 1, lambda inputs: [not inputs[0]], node_on_click_func)

class TimerGate(GateBaseClass):
    def __init__(self, screen, pos, node_on_click_func) -> None:
        super().__init__('Timer', screen, pos, 0, 1, self._logic_func, node_on_click_func)
    
    def _logic_func(self, inputs):
        t = [int(time.time()) % 2]
        return t

