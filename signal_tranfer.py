import pygame
from copy import deepcopy
from typing import Any, Callable
from widgets import Button

class SignalTransporter:
    def __init__(self, screen, color_on, color_off) -> None:
        self.screen = screen
        self.state = 0
        self.color_on = color_on
        self.color_off = color_off
    
    def draw(self):
        pass
    
    def update(self):
        self.draw()
    
    def set_state(self, state: bool):
        self.state = state
    
    def get_state(self):
        return int(self.state)

class Node(SignalTransporter):
    def __init__(self, screen: pygame.Surface, pos: tuple, size: tuple, color_on, color_off, is_input, border_radius: int = 5, static: bool = True, is_click_toogleable: bool = True, on_click_func: Callable[[Any], None] = None) -> None:
        super().__init__(screen, color_on, color_off)
        self.pos = pos
        self.size = size
        self.border_radius = border_radius
        self.static = static
        self.is_input = is_input
        self.is_output = not is_input
        # if is_input is None:
        #     self.is_input = True
        #     self.is_output = True
        self.is_click_toogleable = is_click_toogleable
        
        def func():
            if self.is_click_toogleable:
                if not self.static:
                    self.set_state(0 if self.state else 1)
            if on_click_func is not None:
                on_click_func(self)
        
        self.node_button = Button(self.screen,
                                  self.pos,
                                  self.size,
                                  self.color_off if self.state else self.color_off,
                                  hover = not self.static,
                                  on_left_mouse_button_clicked=func,
                                  border_radius=self.border_radius)
        
        self.connected_outputs = []
        self.connected_inputs = []
    
    def set_pos(self, pos):
        self.node_button.set_pos(topleft=pos)
    
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
                wire.disconnect_all()
            self.connected_inputs.clear()
        if self.is_output:
            for wire in self.connected_outputs:
                wire.disconnect_all()
            self.connected_outputs.clear()
    
    def get_rect(self):
        return self.node_button.rect
    
    def draw(self):
        self.node_button.update()
        self.node_button.configure(bg_color=self.color_on if self.state else self.color_off, hover = not self.static and self.state, on_click_shade_val = 255 if self.static else 200)
    
    def update(self):
        super().update()
        
        if self.is_input:
            self.set_state(max([wire.get_state() for wire in self.connected_inputs] if self.connected_inputs else [self.state]))
        if self.is_output:
            for wire in self.connected_outputs:
                wire.set_state(self.get_state())

class Wire(SignalTransporter):
    def __init__(self, screen: pygame.Surface, init_starting_pos: list, init_ending_pos: list, width: int, color_on, color_off, delete_func: Callable) -> None:
        super().__init__(screen, color_on, color_off)
        self.width = width
        self.wire_move_buttons = []
        self.delete_func = delete_func
        self.curr_color = self.color_on if self.state else self.color_off
        
        self.breakpoints = [[init_starting_pos, init_ending_pos]]
        
        self.starting_point = self.breakpoints[0][0]
        self.ending_point = self.breakpoints[-1][1]
        
        self.first_pos_tracker = [init_starting_pos, init_ending_pos]
        
        self.input_node = None
        self.output_node = None
        
        self.input_connected = False
        self.output_connected = False
        
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
    
    def _move_breakpoint(self, index, button: Button):
        def func():
            button.set_pos(center=pygame.mouse.get_pos())
            self.move_breakpoint_ending_point(index, pygame.mouse.get_pos())
        return func
    
    def _add_breakpoint_buttons(self, index):
        button = Button(self.screen,
                        deepcopy(self.breakpoints[index][1]),
                        (self.width, self.width),
                        self.curr_color,
                        many_actions_one_click=True,
                        border_radius=self.width * 2,
                        on_right_mouse_button_clicked=self.remove_breakpoint(index))
        
        button.set_pos(center=deepcopy(self.breakpoints[index][1]))
        
        button.configure(on_left_mouse_button_clicked=self._move_breakpoint(index, button))
        
        self.wire_move_buttons.append([index - 1, button])
    
    def is_clicked(self,
                   mouse_rect: pygame.Rect,
                   line_target: list[list[int, int], list[int, int]] | pygame.Rect,
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
        mouse_collission = True if len(mouse_rect.clipline(line_target)) else False
        
        line_target_key = repr(line_target)
        
        if line_target_key not in self.left_mouse_clicked_dict:
            self.left_mouse_clicked_dict[line_target_key] = False
        if line_target_key not in self.left_mouse_clicked_outside_dict:
            self.left_mouse_clicked_outside_dict[line_target_key] = False
        if line_target_key not in self.middle_mouse_clicked_dict:
            self.middle_mouse_clicked_dict[line_target_key] = False
        if line_target_key not in self.middle_mouse_clicked_outside_dict:
            self.middle_mouse_clicked_outside_dict[line_target_key] = False
        if line_target_key not in self.right_mouse_clicked_dict:
            self.right_mouse_clicked_dict[line_target_key] = False
        if line_target_key not in self.right_mouse_clicked_outside_dict:
            self.right_mouse_clicked_outside_dict[line_target_key] = False
        
        if line_target_key not in self.left_mouse_tracker_clicked_dict:
            self.left_mouse_tracker_clicked_dict[line_target_key] = False
        if line_target_key not in self.left_mouse_tracker_not_clicked_dict:
            self.left_mouse_tracker_not_clicked_dict[line_target_key] = False
        if line_target_key not in self.middle_mouse_tracker_clicked_dict:
            self.middle_mouse_tracker_clicked_dict[line_target_key] = False
        if line_target_key not in self.middle_mouse_tracker_not_clicked_dict:
            self.middle_mouse_tracker_not_clicked_dict[line_target_key] = False
        if line_target_key not in self.right_mouse_tracker_clicked_dict:
            self.right_mouse_tracker_clicked_dict[line_target_key] = False
        if line_target_key not in self.right_mouse_tracker_not_clicked_dict:
            self.right_mouse_tracker_not_clicked_dict[line_target_key] = False
        
        if line_target_key not in self.hover_tracker_dict:
            self.hover_tracker_dict[line_target_key] = False
        if line_target_key not in self.not_hover_tracker_dict:
            self.not_hover_tracker_dict[line_target_key] = False
        
        if mouse_collission:
            self.not_hover_tracker_dict[line_target_key] = False
            if not self.hover_tracker_dict[line_target_key] or hover_many_actions_one_click:
                if hover_func is not None:
                    hover_func()
                self.hover_tracker_dict[line_target_key] = True
        else:
            self.hover_tracker_dict[line_target_key] = False
            if not self.not_hover_tracker_dict[line_target_key] or not_hover_many_actions_one_click:
                if not_hover_func is not None:
                    not_hover_func()
                self.not_hover_tracker_dict[line_target_key] = True
        
        if left_mouse_clicked and mouse_collission:
            self.left_mouse_clicked_dict[line_target_key] = True
        if not left_mouse_clicked:
            self.left_mouse_clicked_dict[line_target_key] = False
        if not self.left_mouse_clicked_dict[line_target_key] and not mouse_collission:
            self.left_mouse_clicked_outside_dict[line_target_key] = False
        if not left_mouse_clicked:
            self.left_mouse_clicked_outside_dict[line_target_key] = True
        
        if middle_mouse_clicked and mouse_collission:
            self.middle_mouse_clicked_dict[line_target_key] = True
        if not middle_mouse_clicked:
            self.middle_mouse_clicked_dict[line_target_key] = False
        if not self.middle_mouse_clicked_dict[line_target_key] and not mouse_collission:
            self.middle_mouse_clicked_outside_dict[line_target_key] = False
        if not middle_mouse_clicked:
            self.middle_mouse_clicked_outside_dict[line_target_key] = True
        
        if right_mouse_clicked and mouse_collission:
            self.right_mouse_clicked_dict[line_target_key] = True
        if not right_mouse_clicked:
            self.right_mouse_clicked_dict[line_target_key] = False
        if not self.right_mouse_clicked_dict[line_target_key] and not mouse_collission:
            self.right_mouse_clicked_outside_dict[line_target_key] = False
        if not right_mouse_clicked:
            self.right_mouse_clicked_outside_dict[line_target_key] = True
        
        left_mouse_clicked = self.left_mouse_clicked_dict[line_target_key] and self.left_mouse_clicked_outside_dict[line_target_key]
        middle_mouse_clicked = self.middle_mouse_clicked_dict[line_target_key] and self.middle_mouse_clicked_outside_dict[line_target_key]
        right_mouse_clicked = self.right_mouse_clicked_dict[line_target_key] and self.right_mouse_clicked_outside_dict[line_target_key]
        
        if left_mouse_clicked:
            self.left_mouse_tracker_not_clicked_dict[line_target_key] = False
            if not self.left_mouse_tracker_clicked_dict[line_target_key] or left_many_actions_one_click:
                if on_left_clicked_func is not None:
                    on_left_clicked_func()
                self.left_mouse_tracker_clicked_dict[line_target_key] = True
        else:
            self.left_mouse_tracker_clicked_dict[line_target_key] = False
            if not self.left_mouse_tracker_not_clicked_dict[line_target_key] or left_many_actions_one_not_click:
                if on_not_left_clicked_func is not None:
                    on_not_left_clicked_func()
                self.left_mouse_tracker_not_clicked_dict[line_target_key] = True
        
        if middle_mouse_clicked:
            self.middle_mouse_tracker_not_clicked_dict[line_target_key] = False
            if not self.middle_mouse_tracker_clicked_dict[line_target_key] or middle_many_actions_one_click:
                if on_middle_clicked_func is not None:
                    on_middle_clicked_func()
                self.middle_mouse_tracker_clicked_dict[line_target_key] = True
        else:
            self.middle_mouse_tracker_clicked_dict[line_target_key] = False
            if not self.middle_mouse_tracker_not_clicked_dict[line_target_key] or middle_many_actions_one_not_click:
                if on_not_middle_clicked_func is not None:
                    on_not_middle_clicked_func()
                self.middle_mouse_tracker_not_clicked_dict[line_target_key] = True
        
        if right_mouse_clicked:
            self.right_mouse_tracker_not_clicked_dict[line_target_key] = False
            if not self.right_mouse_tracker_clicked_dict[line_target_key] or right_many_actions_one_click:
                if on_right_clicked_func is not None:
                    on_right_clicked_func()
                self.right_mouse_tracker_clicked_dict[line_target_key] = True
        else:
            self.right_mouse_tracker_clicked_dict[line_target_key] = False
            if not self.right_mouse_tracker_not_clicked_dict[line_target_key] or right_many_actions_one_not_click:
                if on_not_right_clicked_func is not None:
                    on_not_right_clicked_func()
                self.right_mouse_tracker_not_clicked_dict[line_target_key] = True
        
        return left_mouse_clicked, middle_mouse_clicked, right_mouse_clicked, mouse_collission
    
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
            for i in range(len(self.wire_move_buttons)):
                self.wire_move_buttons[i][0] = i
                self.wire_move_buttons[i][1].configure(on_right_mouse_button_clicked=self.remove_breakpoint(i))
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
            for i in range(len(self.wire_move_buttons)):
                self.wire_move_buttons[i][0] = i
                button = self.wire_move_buttons[i][1]
                button.configure(on_right_mouse_button_clicked=lambda: self.remove_breakpoint(i + 1), on_left_mouse_button_clicked=self._move_breakpoint(i + 1, button))
    
    def connected_to(self, node: Node):
        if node.is_input:
            assert not self.input_connected, 'An input has already been connected to this wire'
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
                    self.breakpoints[i][0] = pygame.mouse.get_pos()
                    self.breakpoints.insert(i - 1, [self.breakpoints[i - 1][1], pygame.mouse.get_pos()])
                else:
                    self.breakpoints.insert(0, [tuple(prev_starting_pos), pygame.mouse.get_pos()])
                    self.breakpoints[1][0] = pygame.mouse.get_pos()
    
    def draw(self):
        mouse_rect = pygame.Rect(0, 0, 4, 4)
        mouse_rect.center = pygame.mouse.get_pos()
        
        for starting_point, stopping_point in self.breakpoints:
            line_pos = (tuple(starting_point), tuple(stopping_point))
            
            self.is_clicked(mouse_rect,
                            line_pos,
                            on_middle_clicked_func=lambda: self.break_line((starting_point, stopping_point)),
                            on_right_clicked_func=lambda: self.delete_func(self))
            pygame.draw.line(self.screen, self.curr_color, starting_point, stopping_point, self.width)
    
    def update(self):
        self.curr_color = self.color_on if self.state else self.color_off

        super().update()
        self.starting_point = self.breakpoints[0][0]
        self.ending_point = self.breakpoints[-1][1]
        for index, button in self.wire_move_buttons:
            button.update()
            button.configure(bg_color='red')#self.curr_color)
            button.set_pos(center=self.breakpoints[index][1])
        
        for i in range(len(self.wire_move_buttons)):
            self.wire_move_buttons[i][0] = i
            button = self.wire_move_buttons[i][1]
            button.configure(on_right_mouse_button_clicked=self.remove_breakpoint(i))
        
        if self.input_node is not None:
            self.breakpoints[-1][1] = self.input_node.node_button.rect.center
        if self.output_node is not None:
            self.breakpoints[0][0] = self.output_node.node_button.rect.center

