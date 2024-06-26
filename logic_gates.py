
import time
from typing import Callable
import pygame
import pygame.draw_py
from settings import *
from widgets import Button
from signal_tranfer import Node

class GateBaseClass:
    def __init__(self, name: str, screen: pygame.Surface, pos: tuple, input_amt, output_amt, logic_func: Callable[[list], list], node_on_click_func: Callable[[Node], None]) -> None:
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
        self.node_on_color = 'pink'
        self.node_off_color = 'grey'
        
        self.mouse_pos = pygame.mouse.get_pos()
        self.grid_mouse_pos = tuple(list((i - (i % GRID_SIZE)) for i in self.mouse_pos))
        
        text_surf = self.font.render(self.name, True, self.text_color)
        
        self.input_amt = input_amt
        self.output_amt = output_amt
        self.node_on_click_func = node_on_click_func
        self.logic_func = logic_func
        
        self.prev_pos = (0, 0)
        self.prev_mouse_pos = (0, 0)
        
        self.button_size = text_surf.get_width() + (GATE_TEXT_BORDER_OFFSET_X * 2), max((GATE_TEXT_BORDER_OFFSET_Y + NODE_SIZE) * max(self.input_amt, self.output_amt), text_surf.get_height() + (GATE_TEXT_BORDER_OFFSET_Y * 2))
        
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
                node.configure(pos=self._get_node_pos(self.input_amt, index))
        
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
        
        logic_func = kwargs.get('logic_func')
        if logic_func is not None:
            self.logic_func = logic_func
        
        render = kwargs.get('render')
        if render is not None:
            self.render = render
        
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
                             logic_func=self.logic_func,
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
            node.set_pos(pos=(node.get_rect().x + (self.button.rect.x - prev_x), node.get_rect().y + (self.button.rect.y - prev_y)))
    
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
        
        for node_out in self.output_nodes:
            if self.render:
                pygame.draw.rect(self.screen, self.node_pin_color, (self.button.rect.right, node_out.get_rect().centery - self.node_pin_size[1] / 2, *self.node_pin_size))
            node_out.update()
            node_out.configure(render=self.render)
    
    def logic(self, input_states):
        outputs = self.logic_func(input_states)
        for index, state in enumerate(outputs):
            self.output_nodes[index].set_state(state)
    
    def update(self):
        input_states = [node.get_state() for node in self.input_nodes]
        self.logic(input_states)
        self.draw()
        self.button.update()
        self.button.configure(render=self.render)

        self.mouse_pos = pygame.mouse.get_pos()
        self.grid_mouse_pos = tuple(list((i - (i % GRID_SIZE)) for i in self.mouse_pos))

class AndGate(GateBaseClass):
    def __init__(self, screen, pos, on_click_func) -> None:
        super().__init__('And', screen, pos, 2, 1, lambda inputs: [inputs[0] and inputs[1]], on_click_func)

class NotGate(GateBaseClass):
    def __init__(self, screen, pos, on_click_func) -> None:
        super().__init__('Not', screen, pos, 1, 1, lambda inputs: [not inputs[0]], on_click_func)

class TimerGate(GateBaseClass):
    def __init__(self, screen, pos, on_click_func) -> None:
        super().__init__('Timer', screen, pos, 0, 1, self._logic_func, on_click_func)
    
    def _logic_func(self, inputs):
        t = [int(time.time()) % 2]
        return t
