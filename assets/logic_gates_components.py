import time
import pygame
from collections import deque
from typing import Callable
from assets.settings import *
from assets.widgets import Button
from assets.modules import set_color
from assets.signal_tranfer import Node, Wire

class GateBaseClass:
    def __init__(self, name: str, screen: pygame.Surface, pos: tuple, input_amt, output_amt, logic_func_or_circuit_or_circuit_dict, node_on_click_func: Callable[[Node], None] = None, node_on_color = 'pink', node_off_color = 'grey') -> None:
        self.name = name
        self.screen = screen
        self.font = pygame.font.SysFont('Times New Roman', 20)
        
        self.pos = pos
        
        self.selected = False
        self.new_mouse_pos = False
        
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
        
        self.prev_pos = (0, 0)
        self.prev_mouse_pos = (0, 0)
        
        self.button_size = text_surf.get_width() + (GATE_TEXT_BORDER_OFFSET_X * 2), max((GATE_TEXT_BORDER_OFFSET_Y + NODE_SIZE) * max(self.input_amt, self.output_amt), text_surf.get_height() + (GATE_TEXT_BORDER_OFFSET_Y * 2))
        
        self.disabled = False
        self.render = True
        self.sub_selected = False
        
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
                             (self.input_nodes[0].node_button.rect.centerx if self.input_nodes else self.pos[0], self.pos[1]),
                             self.button_size,
                             self.gate_color,
                             hover=False,
                             on_left_mouse_button_clicked=self._toogle_selected,
                             image=text_surf
                             )
        
        self.output_nodes = [Node(self.screen,
                                  (self.button.rect.right - (self.node_size[0] / 2), self._get_node_y_pos(self.output_amt, no)),
                                  self.node_size,
                                  color_on=self.node_on_color,
                                  color_off=self.node_off_color,
                                  static=False,
                                  is_input=False,
                                  border_radius=max(self.node_size) * 5,
                                  is_click_toogleable=False,
                                  on_click_func=self.node_on_click_func) for no in range(self.output_amt)]
        
        self.configure(logic_func_or_circuit_or_circuit_dict=logic_func_or_circuit_or_circuit_dict)
    
    def _toogle_selected(self):
        any_node_is_touched = bool(sum([node.node_button.rect.collidepoint(self.mouse_pos) for node in self.input_nodes + self.output_nodes]))
        if self.selected:
            if self.index == 0:
                if not any_node_is_touched:
                    self.selected = self.gate_options_hovered
            else:
                self.set_pos((self.button.rect.centerx, self.button.rect.centery + self.button.rect.height))
        else:
            if not any_node_is_touched:
                self.selected = True
    
    def get_dict(self):
        if isinstance(self.logic_func_or_circuit_or_circuit_dict, str | dict):
            l_func = self.logic_func_or_circuit_or_circuit_dict
        elif isinstance(self.logic_func_or_circuit_or_circuit_dict, Callable):
            l_func = f'#function{self.name}'
        elif isinstance(self.logic_func_or_circuit_or_circuit_dict, Circuit):
            l_func = self.logic_func_or_circuit_or_circuit_dict.get_dict()
        
        return {
            'name': self.name,
            'input_amt': self.input_amt,
            'output_amt': self.output_amt,
            'logic_func_or_circuit_or_circuit_dict': l_func,
            'node_on_color': self.node_on_color,
            'node_off_color': self.node_off_color,
            'pos': self.pos,
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
        
        name = kwargs.get('name')
        if name is not None:
            self.name = name
            text_surf = self.font.render(self.name, True, self.text_color)
            size = (text_surf.get_width() + (GATE_TEXT_BORDER_OFFSET_X * 2), max((GATE_TEXT_BORDER_OFFSET_Y + NODE_SIZE) * max(self.input_amt, self.output_amt), text_surf.get_height() + (GATE_TEXT_BORDER_OFFSET_Y * 2)))
            self.button.configure(size=size, image=text_surf)
        
        pos = kwargs.get('pos')
        if pos is not None:
            self.pos = pos
            rect = self.get_rect()
            self._on_move((self.pos[0] + (rect.width / 2), self.pos[1] + (rect.height / 2)))
        
        logic_func_or_circuit_or_circuit_dict = kwargs.get('logic_func_or_circuit_or_circuit_dict')
        if logic_func_or_circuit_or_circuit_dict is not None:
            self.logic_func_or_circuit_or_circuit_dict = logic_func_or_circuit_or_circuit_dict
            if isinstance(self.logic_func_or_circuit_or_circuit_dict, dict):
                self.logic_circuit = Circuit(self.name, self.screen, 1, 1, 'red', 1, 1, 1)
                self.logic_circuit.set_dict(self.logic_func_or_circuit_or_circuit_dict)
                self.logic_circuit.gate_update()
                self.logic_func = self._logic_func
            elif isinstance(self.logic_func_or_circuit_or_circuit_dict, str):
                if '#function' in self.logic_func_or_circuit_or_circuit_dict:
                    rect = self.get_rect()
                    match self.logic_func_or_circuit_or_circuit_dict.replace('#function', ''):
                        case 'And':
                            self.logic_func = AndGate(self.screen, rect.topleft, self.node_on_click_func).logic_func
                        case 'Not':
                            self.logic_func = NotGate(self.screen, rect.topleft, self.node_on_click_func).logic_func
                        case 'Timer':
                            self.logic_func = TimerGate(self.screen, rect.topleft, self.node_on_click_func).logic_func
            elif isinstance(self.logic_func_or_circuit_or_circuit_dict, Callable):
                self.logic_func = self.logic_func_or_circuit_or_circuit_dict
            elif isinstance(self.logic_func_or_circuit_or_circuit_dict, Circuit):
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
            for node in self.input_nodes + self.output_nodes:
                node.configure(on_click_func=self.node_on_click_func)
        
        input_amt = kwargs.get('input_amt')
        if input_amt is not None:
            self.input_amt = input_amt
            add = (-(self.button.rect.height / 2) + (self.node_size[1] / 2))
            self.input_nodes = [Node(self.screen,
                                    (self.pos[0], self._get_node_y_pos(self.input_amt, ni) + add),
                                    self.node_size,
                                    color_on=self.node_on_color,
                                    color_off=self.node_off_color,
                                    static=False,
                                    is_input=True,
                                    border_radius=max(self.node_size) * 5,
                                    is_click_toogleable=False,
                                    on_click_func=self.node_on_click_func) for ni in range(self.input_amt)]
        
        output_amt = kwargs.get('output_amt')
        if output_amt is not None:
            self.output_amt = output_amt
            add = (-(self.button.rect.height / 2) + (self.node_size[1] / 2))
            self.output_nodes = [Node(self.screen,
                                    (self.button.rect.right - (self.node_size[0] / 2), self._get_node_y_pos(self.output_amt, no) + add),
                                    self.node_size,
                                    color_on=self.node_on_color,
                                    color_off=self.node_off_color,
                                    static=False,
                                    is_input=False,
                                    border_radius=max(self.node_size) * 5,
                                    is_click_toogleable=False,
                                    on_click_func=self.node_on_click_func) for no in range(self.output_amt)]
    
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
        if self.input_nodes:
            self.pos = self.input_nodes[0].node_button.rect.topleft
        else:
            self.pos = self.button.rect.topleft
    
    def get_input_nodes(self):
        return self.input_nodes
    
    def get_output_node_objects(self):
        return self.output_nodes
    
    def get_output(self):
        return [node.get_state() for node in self.output_nodes]
    
    def update_nodes(self):
        for node_in in self.input_nodes:
            node_in.node_button.new_mouse_pos = True
            node_in.node_button.mouse_pos = self.mouse_pos
            node_in.update()
            node_in.configure(render=self.render)
            node_in.node_button.configure(disabled=self.disabled)
        
        for node_out in self.output_nodes:
            node_out.node_button.new_mouse_pos = True
            node_out.node_button.mouse_pos = self.mouse_pos
            node_out.update()
            node_out.configure(render=self.render)
            node_out.node_button.configure(disabled=self.disabled)
    
    def _logic_func(self, inputs):
        self.logic_circuit.set_inputnodes(inputs)
        self.logic_circuit.gate_update_logic()
        
        return [self.logic_circuit.output_node_objects[index][0].get_state() for index in range(len(self.logic_circuit.output_node_objects))]
    
    def logic(self, input_states):
        outputs = self.logic_func(input_states)
        for index, state in enumerate(outputs):
            self.output_nodes[index].set_state(state)
    
    def update(self, index=0, gate_options_hovered=False, is_wire_on = False):
        self.index = index
        self.gate_options_hovered = gate_options_hovered
        self.is_wire_on = is_wire_on
        
        input_states = [node.get_state() for node in self.input_nodes]
        self.logic(input_states)
        self.button.update()
        self.button.configure(disabled=self.disabled, render=self.render)
        
        self.update_nodes()
        
        if not self.new_mouse_pos:
            self.mouse_pos = pygame.mouse.get_pos()
        
        self.button.new_mouse_pos = True
        self.button.mouse_pos = self.mouse_pos
        
        self.grid_mouse_pos = tuple(list((i - (i % GRID_SIZE)) for i in self.mouse_pos))
        
        self.selected = self.selected and not self.is_wire_on
        if self.selected:
            self._on_move(self.grid_mouse_pos)
        else:
            if not self.sub_selected:
                self._on_not_move(self.grid_mouse_pos)





class Circuit:
    def __init__(self, name: str, screen: pygame.Surface, node_base_line: int, add_nodes_buttons_height: int, theme_color, border_offset, border_width, top_level) -> None:
        self.screen = screen
        self.name = name
        
        self.ctrl_button_dim = 20
        self.node_button_dim = 10
        self.in_out_wire_size = 40, 3
        
        self.border_width = border_width
        self.nodes_box_offset = border_offset
        self.top_level = top_level
        
        self.selected_output_node_button_index = -1
        self.selected_input_node_button_index = -1
        
        self.wire_right_pressed = False
        self.wire_left_pressed = False
        self.gate = None
        self.any_input_node_hovered = False
        self.any_output_node_hovered = False
        
        self._theme_color = theme_color
        
        self.gates: deque[GateBaseClass] = deque([])
        self.wires: deque[Wire] = deque([])
        self.input_node_objects: deque[tuple[Button, Button, Node]] = deque([])
        self.output_node_objects: deque[tuple[Node, Button, Button]] = deque([])
        self.wire_connected_trackers = {}
        self.gate_key_index_map = {}
        
        self.mouse_pos = pygame.mouse.get_pos()
        self.grid_mouse_pos = tuple(list((i - (i % GRID_SIZE)) for i in self.mouse_pos))
        
        self.node_base_line = node_base_line
        self.add_nodes_buttons_height = add_nodes_buttons_height
        
        self.is_updating_with_displays = True
        
        self.removed_gate = False
        self.removed_wire = False
        self.removed_output = False
        self.removed_input = False
        
        self.render = True
        self.has_circuit_set_state = False
        
        self.add_input(self.screen.get_height() / 2)
        self.add_output(self.screen.get_height() / 2)
    
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
        for wire in list(self.wires):
            wire_nodes = []
            for node in nodes:
                if wire.is_connected_to(node):
                    wire_nodes.append(nodes.index(node))
            wire_index_connections.append(wire_nodes)
        
        return wire_index_connections
    
    def copy(self):
        circuit = Circuit(self.name, self.screen, self.node_base_line, self.add_nodes_buttons_height, self.theme_color, self.nodes_box_offset, self.border_width, self.top_level)
        
        def make_input_button_func(new_node): return lambda: new_node.set_state(not new_node.get_state())
        
        circuit.input_node_objects.clear()
        circuit.output_node_objects.clear()
        circuit.gates.clear()
        circuit.wires.clear()
        
        circuit.update_output_button_removal = True
        circuit.update_input_button_removal = True
        
        for but, move_but, node in self.input_node_objects:
            new_node = node.copy()
            new_move_but = move_but.copy()
            new_but = but.copy()
            new_but.configure(on_left_mouse_button_clicked=make_input_button_func(new_node))
            circuit.input_node_objects.append([new_but, new_move_but, new_node])
        
        for node, move_button, button in self.output_node_objects:
            circuit.output_node_objects.append([node.copy(), move_button.copy(), button.copy()])
        
        for gate in self.gates:
            circuit.gates.append(gate.copy())
        
        for wire in self.wires:
            new_wire = wire.copy()
            new_wire.configure(delete_func=lambda w: circuit._remove_wire(w))
            circuit.wires.append(new_wire)
        
        circuit.wire_connected_trackers = {wire: False for wire in circuit.wires}
        
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
            'border_offset': self.nodes_box_offset,
            'border_width': self.border_width,
            'top_level': self.top_level,
            
            'theme_color': self.theme_color,
            'input_node_objects': [move_but.rect.centery for _, move_but, _ in self.input_node_objects],
            'output_node_objects': [move_but.rect.centery for _, move_but, _ in self.output_node_objects],
            'gates': [gate.get_dict() for gate in self.gates],
            'wires': [wire.get_dict() for wire in self.wires],
            'wire_connected_indexes': self._get_wire_connected_indexes()
        }
    
    def set_dict(self, d: dict):
        input_node_objects = d['input_node_objects']
        output_node_objects = d['output_node_objects']
        gates = d['gates']
        wires = d['wires']
        wire_connected_indexes = d['wire_connected_indexes']
        
        self.input_node_objects.clear()
        self.output_node_objects.clear()
        self.gates.clear()
        
        self.update_input_button_removal = True
        self.update_output_button_removal = True
        
        self.name = d['name']
        self.node_base_line = d['node_base_line']
        self.add_nodes_buttons_height = d['add_nodes_buttons_height']
        self.border_offset = d['border_offset']
        self.border_width = d['border_width']
        self.top_level = d['top_level']
        
        for centery in input_node_objects:
            self.add_input(centery)
        
        for centery in output_node_objects:
            self.add_output(centery)
        
        for gate_info in gates:
            new_gate = GateBaseClass('_', self.screen, (20, 20), 1, 1, lambda l: l, self.on_node_clicked)
            new_gate.set_dict(gate_info)
            self.gates.append(new_gate)
        
        for wire in list(self.wires):
            wire.disconnect_all()
        
        self.wires.clear()
        
        for wire_info in wires:
            new_wire = Wire(self.screen, [0, 0], [1, 1], 2, 'red', 'red', delete_func=lambda w: self._remove_wire(w))
            new_wire.set_dict(wire_info)
            new_wire.disconnect_all()
            self.wires.append(new_wire)
        
        self.wire_connected_trackers = {wire: False for wire in self.wires}
        
        nodes = self._get_all_nodes()
        for index, node_connection in enumerate(wire_connected_indexes):
            for node_index in node_connection:
                nodes[node_index].connect(self.wires[index])

        self.theme_color = d['theme_color']
    
    def _get_node_on_color(self, color):
        on_color = []
        for i, v in enumerate(set_color(color, 255)):
            v = (v * i) % 255
            on_color.append(v)
        
        return on_color
    
    def _get_node_off_color(self, color):
        return set_color(color, 125)
    
    def _set_gate_color(self, gate: GateBaseClass, color):
        gate_body_color = set_color(color, 200)
        gate_text_color = set_color(color, 10)
        gate.configure(gate_color=gate_body_color, text_color=gate_text_color, node_on_color=self._get_node_on_color(color), node_off_color=self._get_node_off_color(color))
    
    def _get_all_nodes(self):
        nodes_in_gate = []
        for gate in self.gates:
            for node in gate.input_nodes + gate.output_nodes:
                nodes_in_gate.append(node)
        
        return [node for _, _, node in list(self.input_node_objects)] + nodes_in_gate + [node for node, _, _ in list(self.output_node_objects)]
    
    def _recolor(self, color):
        on_color = self._get_node_on_color(color)
        off_color = self._get_node_off_color(color)
        control_button_colors = set_color(color, 90)
        
        for button, _, node in list(self.input_node_objects):
            button.configure(bg_color=control_button_colors)
            node.configure(color_on=on_color, color_off=off_color)
        
        for node, _, button in list(self.output_node_objects):
            button.configure(bg_color=control_button_colors)
            node.configure(color_on=on_color, color_off=off_color)
        
        for wire in list(self.wires):
            wire.configure(color_on=on_color, color_off=off_color)
        
        for gate in list(self.gates):
            self._set_gate_color(gate, color)
    
    def _generate_combinations(self, length):
        total_combinations = 2 ** length
        return ([int(bit) for bit in format(i, f'0{length}b')] for i in range(total_combinations))
    
    def _make_move_input_node_object_func(self, index):
        def func():
            if self.selected_input_node_button_index == -1:
                self.selected_input_node_button_index = index
            else:
                self.selected_input_node_button_index = -1
        
        return func
    
    def _make_move_output_node_object_func(self, index):
        def func():
            if self.selected_output_node_button_index == -1:
                self.selected_output_node_button_index = index
            else:
                self.selected_output_node_button_index = -1
    
        return func
    
    def add_input(self, centery):
        move_button = Button(self.screen,
                             (self.nodes_box_offset, centery - (self.node_button_dim / 2)),
                             (self.border_width, self.node_button_dim),
                             'transparent',
                             on_left_mouse_button_clicked=self._make_move_input_node_object_func(len(self.input_node_objects)),
                             border_radius=0
                             )
        ctrl_button = Button(self.screen,
                             (move_button.rect.centerx - (self.ctrl_button_dim / 2) - (self.in_out_wire_size[0] / 2), centery - (self.ctrl_button_dim / 2)),
                             (self.ctrl_button_dim, self.ctrl_button_dim),
                             'grey',
                             on_left_mouse_button_clicked=lambda: input_node.set_state(not input_node.get_state()),
                             border_radius=10
                             )
        input_node = Node(self.screen,
                          (ctrl_button.rect.centerx + self.in_out_wire_size[0] - (self.node_button_dim / 2), centery - (self.node_button_dim / 2)),
                          (self.node_button_dim, self.node_button_dim),
                          'yellow',
                          'darkgrey',
                          is_input=False,
                          is_click_toogleable=False,
                          static=False,
                          on_click_func=self.on_node_clicked,
                          border_radius=10
                          )
        
        self.update_input_button_removal = True
        self.input_node_objects.append([ctrl_button, move_button, input_node])
        self._recolor(self.theme_color)
        self.selected_input_node_button_index = -1
    
    def add_output(self, centery):
        move_button = Button(self.screen,
                             (self.screen.get_width() - self.nodes_box_offset - self.border_width, centery - (self.node_button_dim / 2)),
                             (self.border_width, self.node_button_dim),
                             'transparent',
                             on_left_mouse_button_clicked=self._make_move_output_node_object_func(len(self.output_node_objects)),
                             border_radius=0
                             )
        output_node = Node(self.screen,
                          (move_button.rect.centerx - (self.in_out_wire_size[0] / 2) - (self.node_button_dim / 2), centery - (self.node_button_dim / 2)),
                          (self.node_button_dim, self.node_button_dim),
                          'yellow',
                          'darkgrey',
                          is_input=True,
                          is_click_toogleable=False,
                          static=False,
                          on_click_func=self.on_node_clicked,
                          border_radius=10
                          )
        ctrl_button = Button(self.screen,
                             (output_node.node_button.rect.centerx + self.in_out_wire_size[0] - (self.ctrl_button_dim / 2), centery - (self.ctrl_button_dim / 2)),
                             (self.ctrl_button_dim, self.ctrl_button_dim),
                             'grey',
                             on_left_mouse_button_clicked=lambda: output_node.set_state(False) if not output_node.connected_inputs + output_node.connected_outputs else 0,
                             border_radius=10
                             )
        
        self.update_output_button_removal = True
        self.output_node_objects.append([output_node, move_button, ctrl_button])
        self._recolor(self.theme_color)
        self.selected_output_node_button_index = -1
    
    def on_node_clicked(self, node: Node):
        if True not in self.wire_connected_trackers.values():
            wire = Wire(self.screen, node.node_button.rect.center, self.grid_mouse_pos, 5, 'pink', 'darkgrey', lambda w: self._remove_wire(w))
            node.connect(wire)
            if node.is_input:
                if wire.wire_move_buttons:
                    wire.wire_move_buttons.pop()
            self.wires.append(wire)
            self._recolor(self.theme_color)
            self.wire_connected_trackers[wire] = True
        else:
            curr_wire = None
            for wire, looking in self.wire_connected_trackers.items():
                if looking:
                    curr_wire = wire
                self.wire_connected_trackers[wire] = False
            
            circular_wire_connection = (node.is_input and curr_wire.input_connected) or (node.is_output and curr_wire.output_connected)
            if not circular_wire_connection:
                node.connect(wire)
            else:
                wire.disconnect_all()
                self.wires.remove(curr_wire)
    
    def is_anything_hovered(self):
        mouse_rect = pygame.Rect(0, 0, 4, 4)
        mouse_rect.center = self.mouse_pos
        
        nodes_collided = [node.node_button.rect.collidepoint(self.mouse_pos) for node in self._get_all_nodes()]
        gate_buttons_collided = [self.gates[index].button.rect.collidepoint(self.mouse_pos) for index in range(len(self.gates))]
        wires_collided = []
        for index in range(len(self.wires)):
            for line in self.wires[index].breakpoints:
                wires_collided.append(mouse_rect.clipline(line[0], line[1]))
        
        collisions = wires_collided + gate_buttons_collided + nodes_collided
        return True in collisions
    
    def _make_remove_input_func(self, index):
        def func():
            if index < len(self.input_node_objects):
                self.update_input_button_removal = True
                
                _, _, node = self.input_node_objects[index]
                connected_wires = node.connected_inputs.copy() + node.connected_outputs.copy()
                
                for wire in connected_wires:
                    self._remove_wire(wire)
                self.input_node_objects.remove(self.input_node_objects[index])
                self.removed_input = True
        
        return func
    
    def _make_remove_output_func(self, index):
        def func():
            if index < len(self.output_node_objects):
                self.update_output_button_removal = True
                
                node, _, _ = self.output_node_objects[index]
                connected_wires = node.connected_inputs.copy() + node.connected_outputs.copy()
                for wire in connected_wires:
                    self._remove_wire(wire)
                self.output_node_objects.remove(self.output_node_objects[index])
        
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
            self.gates.remove(self.gates[index])
            self.removed_gate = True
            for gate in self.selected_gates:
                gate.selected = False
                gate.sub_selected = False
        
        return func
    
    def make_add_gate_func(self, gate: GateBaseClass):
        def func():
            new_gate = gate.copy()
            new_gate.set_pos(self.grid_mouse_pos)
            self.gates.append(new_gate)
            self._recolor(self.theme_color)
            self.selected_gates.append(new_gate)
        
        return func
    
    def set_inputnodes(self, state_list: list[int]):
        for index, (_, _, node) in enumerate(self.input_node_objects):
            node.set_state(state_list[index])
    
    def _remove_wire(self, wire: Wire):
        for button in wire.get_move_buttons():
            if button.rect.collidepoint(self.mouse_pos):
                break
        else:
            if wire in self.wires:
                if wire.input_connected:
                    wire.input_node.disconnect(wire)
                elif wire.output_connected:
                    wire.output_node.disconnect(wire)
                self.wires.remove(wire)
                self.removed_wire = True
                self.wire_connected_trackers.pop(wire)
    
    def _set_all_buttons_disable_state(self, state: bool):
        for node, move_but, but in self.output_node_objects:
            node.node_button.configure(disabled=state)
            move_but.configure(disabled=state)
            but.configure(disabled=state)
        
        for button, move_but, node in self.input_node_objects:
            node.node_button.configure(disabled=state)
            move_but.configure(disabled=state)
            button.configure(disabled=state)
        
        for gate in self.gates:
            for node in gate.input_nodes + gate.output_nodes:
                node.configure(disabled=state)
        
        for wire in self.wires:
            for _, button in wire.wire_move_buttons:
                button.configure(disabled=state)
    
    def _update_wires_and_connections(self, display=True):
        for index in range(len(self.wires)):
            if index < len(self.wires):
                wire = self.wires[index]
                if display:
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
                                    
                                    if is_touching_a_connection:
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
                    
                wire.update()
                wire.configure(render=self.render, mouse_pos=self.mouse_pos)
                
                if display:
                    if self.removed_wire:
                        self.removed_wire = False
                        self._update_wires_and_connections()
    
    def _update_gates(self, display=True):
        for index in range(len(self.gates)):
            if index < len(self.gates):
                gate = self.gates[index]
                
                if display:
                    m_x = pygame.math.clamp(self.mouse_pos[0], self.nodes_box_offset, self.screen.get_width() - self.nodes_box_offset)
                    m_y = pygame.math.clamp(self.mouse_pos[1], self.nodes_box_offset + self.top_level, self.base_line)

                    gate.button.configure(on_right_mouse_button_clicked=self.make_remove_gate_func(index), render=self.render)
                
                    if gate in self.selected_gates:
                        index = self.selected_gates.index(gate)
                    else:
                        index = 0
                
                if display:
                    gate.mouse_pos = m_x, m_y
                    gate.new_mouse_pos = True
                
                if display:
                    gate.update(index, self.gate_options_hovered, True in list(self.wire_connected_trackers.values()))
                else:
                    gate.update(index, False, False)
                
                if display:
                    if self.removed_gate:
                        self.removed_gate = False
                        self._update_gates()
    
    def update_inputs(self, display=True):
        for index in range(len(self.input_node_objects)):
            if index < len(self.input_node_objects):
                ctrl, move_but, inp = self.input_node_objects[index]
                if display:
                    r = pygame.Rect(0, 0, *self.in_out_wire_size)
                    r.midleft = ctrl.rect.center
                    pygame.draw.rect(self.screen, 'grey', r)
                
                    ctrl.configure(render=self.render, mouse_pos=self.mouse_pos)
                    ctrl.update()
                
                    move_but.configure(render=self.render, mouse_pos=self.mouse_pos)
                    move_but.update()
                
                inp.configure(render=self.render, mouse_pos=self.mouse_pos)
                inp.update()
                
                if display:
                    if self.removed_input:
                        self.removed_input = False
                        self.update_inputs()
    
    def update_outputs(self, display=True):
        for index in range(len(self.output_node_objects)):
            if index < len(self.output_node_objects):
                out, move_but, but = self.output_node_objects[index]
                if display:
                    l_rect = pygame.Rect(0, 0, *self.in_out_wire_size)
                    l_rect.midleft = out.node_button.rect.center
                    pygame.draw.rect(self.screen, 'grey', l_rect)
                    
                    move_but.configure(render=self.render, mouse_pos=self.mouse_pos)
                    move_but.update()
                
                    but.configure(render=self.render, mouse_pos=self.mouse_pos)
                    but.update()
                
                out.configure(render=self.render, mouse_pos=self.mouse_pos)
                out.update()
                
                if display:
                    if self.removed_output:
                        self.removed_output = False
                        self.update_outputs()
    
    def _update_logic(self):
        self._update_wires_and_connections()
        self._update_gates()
    
    def gate_update_logic(self):
        self.update_inputs(False)
        self._update_wires_and_connections(False)
        self._update_gates(False)
        self.update_outputs(False)
    
    def gate_update(self):
        for gate in self.gates:
            gate.button.set_pos(bottomright=(-200, -200))
        
        for wire in self.wires:
            for index in range(len(wire.breakpoints)):
                wire.breakpoints[index][0] = [-200, -200]
                wire.breakpoints[index][1] = [-200, -200]
        
        for node in self._get_all_nodes():
            node.node_button.set_pos(bottomright=(-200, -200))
        
        for button, move_but, node in self.input_node_objects:
            button.set_pos(bottomright=(-200, -200))
            move_but.set_pos(bottomright=(-200, -200))
            node.node_button.set_pos(bottomright=(-200, -200))
        
        for node, move_but, button in self.output_node_objects:
            button.set_pos(bottomright=(-200, -200))
            move_but.set_pos(bottomright=(-200, -200))
            node.node_button.set_pos(bottomright=(-200, -200))
        
        self.render = False
        self._set_all_buttons_disable_state(True)
        self.gate_update_logic()
    
    def update(self, gate_options_hovered: bool, selected_gates: list[GateBaseClass], base_line: int):
        self.selected_gates = selected_gates
        self.gate_options_hovered = gate_options_hovered
        self.base_line = base_line
        
        self.render = True
        self.mouse_pos = pygame.mouse.get_pos()
        self.grid_mouse_pos = tuple(list((i - (i % GRID_SIZE)) for i in self.mouse_pos))
        
        self.any_input_node_hovered = bool(sum([int(move_but.rect.collidepoint(self.mouse_pos)) for _, move_but, _ in self.input_node_objects]))
        self.any_output_node_hovered = bool(sum([int(move_but.rect.collidepoint(self.mouse_pos)) for _, move_but, _ in self.output_node_objects]))
        
        m_y = pygame.math.clamp(self.mouse_pos[1], self.nodes_box_offset + self.top_level, self.base_line)
        
        if True in list(self.wire_connected_trackers.values()):
            for gate in self.selected_gates:
                gate.selected = False
        
        if self.selected_input_node_button_index != -1 and self.selected_input_node_button_index < len(self.input_node_objects):
            but, move_but, node = self.input_node_objects[self.selected_input_node_button_index]
            but.set_pos(center=(but.rect.centerx, m_y))
            move_but.set_pos(center=(move_but.rect.centerx, m_y))
            node.node_button.set_pos(center=(node.node_button.rect.centerx, m_y))
            
            if pygame.mouse.get_pressed()[0]:
                if not self.any_input_node_hovered:
                    self.selected_input_node_button_index = -1
        elif self.selected_output_node_button_index != -1 and self.selected_output_node_button_index < len(self.output_node_objects):
            node, move_but, but = self.output_node_objects[self.selected_output_node_button_index]
            node.node_button.set_pos(center=(node.node_button.rect.centerx, m_y))
            move_but.set_pos(center=(move_but.rect.centerx, m_y))
            but.set_pos(center=(but.rect.centerx, m_y))
            
            if pygame.mouse.get_pressed()[0]:
                if  not self.any_output_node_hovered:
                    self.selected_output_node_button_index = -1
        
        if not self.has_circuit_set_state:
            self._set_all_buttons_disable_state(False)
            self.has_circuit_set_state = True
        
        self._update_logic()
        
        if self.update_input_button_removal:
            for i, (button, _, _) in enumerate(self.input_node_objects):
                button.configure(on_right_mouse_button_clicked=self._make_remove_input_func(i))
            self.update_input_button_removal = False
        
        if self.update_output_button_removal:
            for i, (_, _, button) in enumerate(self.output_node_objects):
                button.configure(on_right_mouse_button_clicked=self._make_remove_output_func(i))
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

