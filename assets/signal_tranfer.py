import pygame
from copy import deepcopy
from typing import Callable
from assets.settings import *
from assets.widgets import Button
from assets.modules import is_clicked, set_color

class SignalTransporter:
    def __init__(self, screen, color_on, color_off) -> None:
        self.screen = screen
        self.state = 0
        self.color_on = color_on
        self.color_off = color_off
        self.render = True
    
    def configure(self, **kwargs):
        screen = kwargs.get('screen')
        if screen is not None:
            self.screen = screen
        
        color_on = kwargs.get('color_on')
        if color_on is not None:
            self.color_on = color_on
        
        color_off = kwargs.get('color_off')
        if color_off is not None:
            self.color_off = color_off
        
        mouse_pos = kwargs.get('mouse_pos')
        if mouse_pos is not None:
            self.mouse_pos = mouse_pos
        
        render = kwargs.get('render')
        if render is not None:
            self.render = render
    
    def draw(self):
        pass
    
    def update(self):
        self.draw()
    
    def set_state(self, state: bool):
        self.state = state
    
    def get_state(self):
        return int(self.state)

class Node(SignalTransporter):
    def __init__(self, screen: pygame.Surface, pos: tuple, size: tuple, color_on, color_off, is_input, border_radius: int = 5, static: bool = True, is_click_toogleable: bool = True, on_click_func: Callable = None) -> None:
        super().__init__(screen, color_on, color_off)
        self.pos = pos
        self.size = size
        self.border_radius = border_radius
        self.static = static
        self.is_input = is_input
        self.is_output = not self.is_input
        self.on_click_func = on_click_func
        
        self.mouse_pos = pygame.mouse.get_pos()
        
        self.is_click_toogleable = is_click_toogleable
        
        self.node_button = Button(self.screen,
                                  self.pos,
                                  self.size,
                                  self.color_off if self.state else self.color_off,
                                  hover = not self.static,
                                  border_radius=self.border_radius)
        self._update_click_func()
        
        self.connected_outputs = []
        self.connected_inputs = []
    
    def get_dict(self):
        return {
            'pos': self.get_rect().topleft,
            'size': self.get_rect().size,
            'color_on': self.color_on,
            'color_off': self.color_off,
            'is_input': self.is_input,
            'border_radius': self.border_radius,
            'static': self.static,
            'is_click_toogleable': self.is_click_toogleable
        }
    
    def set_dict(self, d: dict):
        self.configure(**d)
    
    def copy(self):
        return Node(self.screen,
                    self.node_button.rect.topleft,
                    self.node_button.rect.size,
                    self.color_on,
                    self.color_off,
                    self.is_input,
                    self.border_radius,
                    self.static,
                    self.is_click_toogleable,
                    self.on_click_func)
    
    def configure(self, **kwargs):
        super().configure(**kwargs)
        
        screen = kwargs.get('screen')
        if screen is not None:
            self.node_button.configure(screen=self.screen)
        
        render = kwargs.get('render')
        if render is not None:
            self.render = render
        
        pos = kwargs.get('pos')
        if pos is not None:
            self.pos = pos
            self.node_button.set_pos(topleft=self.pos)
        
        size = kwargs.get('size')
        if size is not None:
            self.size = size
            self.node_button.configure(size=self.size)
        
        is_input = kwargs.get('is_input')
        if is_input is not None:
            self.is_input = is_input
            self.is_output = not self.is_input
        
        border_radius = kwargs.get('border_radius')
        if border_radius is not None:
            self.border_radius = border_radius
        
        static = kwargs.get('static')
        if static is not None:
            self.static = static
            self._update_click_func()
        
        is_click_toogleable = kwargs.get('is_click_toogleable')
        if is_click_toogleable is not None:
            self.is_click_toogleable = is_click_toogleable
            self._update_click_func()
        
        if 'on_click_func' in kwargs:
            on_click_func = kwargs.get('on_click_func')
            self.on_click_func = on_click_func
            self._update_click_func()
    
    def _update_click_func(self):
        def func():
            if self.is_click_toogleable:
                if not self.static:
                    self.set_state(0 if self.state else 1)
            if self.on_click_func is not None:
                self.on_click_func(self)
        
        self.node_button.configure(on_left_mouse_button_clicked=func)
    
    def connect(self, wire):
        if wire not in self.connected_outputs + self.connected_inputs:
            wire.connected_to(self)
        
        if self.is_input:
            if wire not in self.connected_inputs:
                self.connected_inputs.append(wire)
        if self.is_output:
            if wire not in self.connected_outputs:
                self.connected_outputs.append(wire)
    
    def disconnect(self, wire):
        if wire in self.connected_outputs + self.connected_inputs:
            wire.disconnected_from(self)
        
        if self.is_input:
            if wire in self.connected_inputs:
                self.connected_inputs.remove(wire)
        if self.is_output:
            if wire in self.connected_outputs:
                self.connected_outputs.remove(wire)
    
    def disconnect_all(self):
        if self.is_input:
            for wire in self.connected_inputs:
                self.disconnect(wire)
                wire.disconnect_all()
            self.connected_inputs.clear()
        if self.is_output:
            for wire in self.connected_outputs:
                self.disconnect(wire)
                wire.disconnect_all()
            self.connected_outputs.clear()
    
    def get_rect(self):
        return self.node_button.rect
    
    def draw(self):
        self.node_button.update()
        self.node_button.configure(bg_color=self.color_on if self.state else self.color_off,
                                   hover = not self.static and self.state,
                                   on_click_shade_val = 255 if self.static else 200,
                                   render=self.render,
                                   mouse_pos=self.mouse_pos)
    
    def update(self):
        super().update()
        
        if self.is_input:
            self.set_state(max([wire.get_state() for wire in self.connected_inputs] if self.connected_inputs else [self.state]))
        if self.is_output:
            for wire in self.connected_outputs:
                wire.set_state(self.get_state())
        
        self.mouse_pos = pygame.mouse.get_pos()

class Wire(SignalTransporter):
    def __init__(self, screen: pygame.Surface, init_starting_pos: list, init_ending_pos: list, width: int, color_on, color_off, delete_func: Callable[[SignalTransporter], None]) -> None:
        super().__init__(screen, color_on, color_off)
        self.width = width
        self.wire_move_buttons = []
        self.delete_func = delete_func
        self.curr_color = self.color_on if self.state else self.color_off

        self.first_pos_tracker = [init_starting_pos, init_ending_pos]
        self.breakpoints = [self.first_pos_tracker]
        
        self.starting_point = self.breakpoints[0][0]
        self.ending_point = self.breakpoints[-1][1]
                
        self.mouse_pos = pygame.mouse.get_pos()
        self.grid_mouse_pos = tuple(list((i - (i % GRID_SIZE)) for i in self.mouse_pos))
        
        self.input_node = None
        self.output_node = None
        
        self.input_connected = False
        self.output_connected = False
    
    def get_dict(self):
        return {
            'breakpoints': self.breakpoints,
            'first_pos_tracker': self.first_pos_tracker,
            'width': self.width,
            'color_on': self.color_on,
            'color_off': self.color_off,
        }
    
    def set_dict(self, d: dict):
        self.breakpoints = [d['first_pos_tracker']]
        self.wire_move_buttons.clear()
        b_p = d['breakpoints']
        for _, end in b_p:
            self.add_breakpoint(end)
        self.configure(**d)
    
    def copy(self):
        return Wire(self.screen,
                    self.breakpoints[0][0],
                    self.breakpoints[0][1],
                    self.width,
                    self.color_on,
                    self.color_off,
                    self.delete_func)
    
    def configure(self, **kwargs):
        super().configure(**kwargs)
        
        init_starting_pos = kwargs.get('init_starting_pos')
        if init_starting_pos is not None:
            self.breakpoints[0][0] = init_starting_pos
        
        init_ending_pos = kwargs.get('init_ending_pos')
        if init_ending_pos is not None:
            self.breakpoints[0][1] = init_ending_pos
        
        width = kwargs.get('width')
        if width is not None:
            self.width = width
        
        delete_func = kwargs.get('delete_func')
        if delete_func is not None:
            self.delete_func = delete_func
    
    def get_move_buttons(self):
        return [button for _, button in self.wire_move_buttons]
    
    def is_connected_to(self, node: Node):
        return (self.input_node is node) or (self.output_node is node)
    
    def _move_breakpoint(self, index, button: Button):
        def func():
            button.set_pos(center=self.grid_mouse_pos)
            self.move_breakpoint_ending_point(index, self.grid_mouse_pos)
        return func
    
    def _add_breakpoint_buttons(self, index):
        button = Button(self.screen,
                        (0, 0),
                        (self.width * 1.5, self.width * 1.5),
                        self.curr_color,
                        many_actions_one_click=True,
                        border_radius=self.width * 2)
        
        button.set_pos(center=deepcopy(self.breakpoints[index][1]))
        
        self.wire_move_buttons.append([0, button])
        
        for i, (_, button) in enumerate(self.wire_move_buttons):
            self.wire_move_buttons[i][0] = i
            self.wire_move_buttons[i][1].configure(on_right_mouse_button_clicked=self.remove_breakpoint(i), on_left_mouse_button_clicked=self._move_breakpoint(i, button))
    
    def move_breakpoint_starting_point(self, index: int, pos: list):
        index = len(self.breakpoints) - 1 if index == -1 else index
        self.breakpoints[index][0] = pos
        if index > 0:
            self.breakpoints[index - 1][1] = pos
    
    def move_breakpoint_ending_point(self, index: int, pos: list):
        index = len(self.breakpoints) - 1 if index == -1 else index
        self.breakpoints[index][1] = pos
        if index != len(self.breakpoints) - 1:
            self.breakpoints[index + 1][0] = pos
    
    def remove_breakpoint(self, index: int):
        def func():
            if index + 1 < len(self.breakpoints):
                if index > 0:
                    self.breakpoints[index + 1][0] = self.breakpoints[index - 1][1]
                else:
                    self.breakpoints[index + 1][0] = self.breakpoints[index][0]
            else:
                self.breakpoints[index - 1][1] = self.breakpoints[index][1]
            self.wire_move_buttons.pop(index)
            
            for i, (_, button) in enumerate(self.wire_move_buttons):
                self.wire_move_buttons[i][0] = i
                self.wire_move_buttons[i][1].configure(on_right_mouse_button_clicked=self.remove_breakpoint(i), on_left_mouse_button_clicked=self._move_breakpoint(i, button))
            
            self.breakpoints.pop(index)
        
        return func
    
    def add_breakpoint(self, point: list):
        if self.output_connected:
            pos = [deepcopy(self.breakpoints[-1][1]), point]
            self.breakpoints.append(pos)
            self._add_breakpoint_buttons(self.breakpoints.index(pos))
        elif self.input_connected:
            pos = [point, deepcopy(self.breakpoints[0][0])]
            self.breakpoints.insert(0, pos)
            
            self._add_breakpoint_buttons(self.breakpoints.index(pos))
    
    def connected_to(self, node: Node):
        if node.is_input:
            assert not self.input_connected, f'An input has already been connected to this wire'
            self.input_node = node
            self.input_connected = True
        if node.is_output:
            assert not self.output_connected, 'An output has already been connected to this wire'
            self.output_node = node
            self.output_connected = True
    
    def disconnected_from(self, node: Node):
        if node.is_input:
            self.input_node = None
            self.input_connected = False
        if node.is_output:
            self.output_node = None
            self.output_connected = False
    
    def disconnect_all(self):
        if self.input_node is not None:
            self.input_node.disconnect(self)
        if self.output_node is not None:
            self.output_node.disconnect(self)
    
    def break_line(self, line):
        if self.output_connected and self.input_connected:
            line_form = list(line) if isinstance(self.breakpoints[0], list) else tuple(line)
            if line_form in self.breakpoints:
                i = self.breakpoints.index(line_form)
                self._add_breakpoint_buttons(i)
                prev_starting_pos = list(self.breakpoints[i][0]).copy()
                if i != 0:
                    self.breakpoints[i][0] = self.grid_mouse_pos
                    self.breakpoints.insert(i - 1, [self.breakpoints[i - 1][1], self.grid_mouse_pos])
                else:
                    self.breakpoints.insert(0, [tuple(prev_starting_pos), self.grid_mouse_pos])
                    self.breakpoints[1][0] = self.grid_mouse_pos
    
    def draw(self):
        mouse_rect = pygame.Rect(0, 0, 8, 8)
        mouse_rect.center = self.grid_mouse_pos
        
        for starting_point, stopping_point in self.breakpoints:
            line_pos = (tuple(starting_point), tuple(stopping_point))
            
            is_clicked(mouse_rect,
                       line_pos,
                       on_middle_clicked_func=lambda: self.break_line((starting_point, stopping_point)),
                       on_right_clicked_func=lambda: self.delete_func(self))
            if self.render:
                pygame.draw.line(self.screen, self.curr_color, starting_point, stopping_point, self.width)
    
    def update(self):
        self.curr_color = self.color_on if self.state else self.color_off
        
        super().update()
        self.starting_point = self.breakpoints[0][0]
        self.ending_point = self.breakpoints[-1][1]
        for index, button in self.wire_move_buttons:
            button.update()
            button.configure(bg_color=set_color(self.curr_color, 110), render=self.render)
            button.set_pos(center=self.breakpoints[index][1])
        
        if self.input_node is not None:
            self.breakpoints[-1][1] = self.input_node.node_button.rect.center
        if self.output_node is not None:
            self.breakpoints[0][0] = self.output_node.node_button.rect.center
        
        self.mouse_pos = pygame.mouse.get_pos()
        self.grid_mouse_pos = tuple(list((i - (i % GRID_SIZE)) for i in self.mouse_pos))

