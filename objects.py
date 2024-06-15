from copy import deepcopy
import math
import threading
import time
from typing import Any, Callable, Literal
import pygame
from settings import *


class Button:
    def __init__(self,
                 screen: pygame.Surface,
                 pos: tuple,
                 size: tuple,
                 bg_color,
                 hover: bool = True,
                 on_hover: Callable = None,
                 on_not_hover: Callable = None,
                 on_left_mouse_button_clicked: Callable = None,
                 on_middle_mouse_button_clicked: Callable = None,
                 on_right_mouse_button_clicked: Callable = None,
                 on_not_left_mouse_button_clicked: Callable = None,
                 on_not_middle_mouse_button_clicked: Callable = None,
                 on_not_right_mouse_button_clicked: Callable = None,
                 many_actions_one_click: bool = False,
                 border_radius: int = 4,
                 on_hover_shade_val: float = 150,
                 on_click_shade_val: float = 200,
                 image: pygame.Surface = None,
                 scale_img: bool = False,
                 img_offset: int = 0,
                 invisible: bool = False) -> None:
        
        self.pos = pos
        self.size = size
        self.screen = screen
        self.on_hover = on_hover
        self.bg_color = bg_color
        self.scale_img = scale_img
        self.invisible = invisible
        self.img_offset = img_offset
        self.on_not_hover = on_not_hover
        self.border_radius = border_radius
        self.image_surf = self.image = image
        self.hover = self.orig_hover_state = hover
        self.on_hover_shade_val = on_hover_shade_val
        self.on_click_shade_val = on_click_shade_val
        self.many_actions_one_click = many_actions_one_click
        self.on_left_mouse_button_clicked = on_left_mouse_button_clicked
        self.on_middle_mouse_button_clicked = on_middle_mouse_button_clicked
        self.on_right_mouse_button_clicked = on_right_mouse_button_clicked
        self.on_not_left_mouse_button_clicked = on_not_left_mouse_button_clicked
        self.on_not_middle_mouse_button_clicked = on_not_middle_mouse_button_clicked
        self.on_not_right_mouse_button_clicked = on_not_right_mouse_button_clicked
        
        self.mouse_pos = pygame.mouse.get_pos()
        
        self.disabled = False
        self.left_mouse_clicked = False
        self.middle_mouse_clicked = False
        self.right_mouse_clicked = False
        self.start_left_click_check = True
        self.start_middle_click_check = True
        self.start_right_click_check = True
        self.start_playing_hover_sound = True
        self.left_mouse_clicked_outside = True
        self.middle_mouse_clicked_outside = True
        self.right_mouse_clicked_outside = True
        
        self.curr_button_opacity = 255
        self.SCR_WIDTH, self.SCR_HEIGHT = self.screen.get_size()
        
        self.rect = pygame.Rect(*self.pos, *self.size)
        
        if self.image is not None:
            if self.scale_img:
                self.image_surf = pygame.transform.scale(self.image, (self.size[0] - self.img_offset, self.size[1] - self.img_offset))
            self.img_rect = self.image_surf.get_rect(center=self.rect.center)
        else:
            self.image_surf = None
    
    def copy(self):
        return Button(screen = self.screen,
                      pos = self.pos,
                      size = self.size,
                      hover=self.hover,
                      bg_color = self.bg_color,
                      on_hover = self.on_hover,
                      on_not_hover = self.on_not_hover,
                      on_left_mouse_button_clicked = self.on_left_mouse_button_clicked,
                      on_right_mouse_button_clicked = self.on_right_mouse_button_clicked,
                      on_not_left_mouse_button_clicked = self.on_not_left_mouse_button_clicked,
                      on_not_right_mouse_button_clicked = self.on_not_right_mouse_button_clicked,
                      many_actions_one_click = self.many_actions_one_click,
                      border_radius = self.border_radius,
                      image = self.image,
                      scale_img = self.scale_img,
                      img_offset = self.img_offset,
                      invisible = self.invisible)
    
    def set_pos(self, **kwargs):
        pos = (0, 0)
        if kwargs:
            args = ['topleft', 'topright',
                    'bottomleft', 'bottomright',
                    'midleft', 'midright',
                    'midtop', 'midbottom',
                    'center', 'centerx', 'centery',
                    'left', 'right',
                    'top', 'bottom',
                    'x', 'y']
            pos = None
            for a in args:
                dest_pos = kwargs.get(a)
                if dest_pos:
                    if a in ('x', 'left'):
                        pos = dest_pos, self.pos[1]
                    elif a in ('y', 'top'):
                        pos = self.pos[0], dest_pos
                    elif a == 'right':
                        pos = dest_pos - self.rect.width, self.pos[1]
                    elif a == 'bottom':
                        pos = self.pos[0], dest_pos - self.rect.height
                    elif a == 'centerx':
                        pos = dest_pos - (self.rect.width / 2), self.pos[1]
                    elif a == 'centery':
                        pos = self.pos[0], dest_pos - (self.rect.height / 2)
                    elif a == 'topleft':
                        pos = dest_pos
                    elif a == 'topright':
                        pos = dest_pos[0] - self.rect.width, dest_pos[1]
                    elif a == 'bottomleft':
                        pos = dest_pos[0], dest_pos[1] - self.rect.height
                    elif a == 'bottomright':
                        pos = dest_pos[0] - self.rect.width, dest_pos[1] - self.rect.height
                    elif a == 'midleft':
                        pos = dest_pos[0], dest_pos[1] - (self.rect.height / 2)
                    elif a == 'midright':
                        pos = dest_pos[0] - self.rect.width, dest_pos[1] - (self.rect.height / 2)
                    elif a == 'midtop':
                        pos = dest_pos[0] - (self.rect.width / 2), dest_pos[1]
                    elif a == 'midbottom':
                        pos = dest_pos[0] - (self.rect.width / 2), dest_pos[1] - self.rect.height
                    elif a == 'center':
                        pos = dest_pos[0] - (self.rect.width / 2), dest_pos[1] - (self.rect.height / 2)
                    break
            if pos == None:
                raise TypeError(f'Invalid keyword argument passed: ({tuple(kwargs)})')
        if pos != self.pos:
            self.pos = pos
            self._set_topleft(self.pos)
    
    def configure(self, **kwargs):
        bg_color = kwargs.get('bg_color')
        if bg_color is not None:
            self.bg_color = bg_color
        
        hover = kwargs.get('hover')
        if hover is not None:
            self.hover = hover
        
        on_hover = kwargs.get('on_hover')
        if on_hover is not None:
            self.on_hover = on_hover
        
        on_not_hover = kwargs.get('on_not_hover')
        if on_not_hover is not None:
            self.on_not_hover = on_not_hover
        
        on_left_mouse_button_clicked = kwargs.get('on_left_mouse_button_clicked')
        if on_left_mouse_button_clicked is not None:
            self.on_left_mouse_button_clicked = on_left_mouse_button_clicked
        
        on_middle_mouse_button_clicked = kwargs.get('on_middle_mouse_button_clicked')
        if on_middle_mouse_button_clicked is not None:
            self.on_middle_mouse_button_clicked = on_middle_mouse_button_clicked
        
        on_right_mouse_button_clicked = kwargs.get('on_right_mouse_button_clicked')
        if on_right_mouse_button_clicked is not None:
            self.on_right_mouse_button_clicked = on_right_mouse_button_clicked
        
        on_not_left_mouse_button_clicked = kwargs.get('on_not_left_mouse_button_clicked')
        if on_not_left_mouse_button_clicked is not None:
            self.on_not_left_mouse_button_clicked = on_not_left_mouse_button_clicked
        
        on_not_middle_mouse_button_clicked = kwargs.get('on_not_middle_mouse_button_clicked')
        if on_not_middle_mouse_button_clicked is not None:
            self.on_not_middle_mouse_button_clicked = on_not_middle_mouse_button_clicked
        
        on_not_right_mouse_button_clicked = kwargs.get('on_not_right_mouse_button_clicked')
        if on_not_right_mouse_button_clicked is not None:
            self.on_not_right_mouse_button_clicked = on_not_right_mouse_button_clicked
        
        many_actions_one_click = kwargs.get('many_actions_one_click')
        if many_actions_one_click is not None:
            self.many_actions_one_click = many_actions_one_click
        
        on_hover_shade_val = kwargs.get('on_hover_shade_val')
        if on_hover_shade_val is not None:
            self.on_hover_shade_val = on_hover_shade_val
        
        on_click_shade_val = kwargs.get('on_click_shade_val')
        if on_click_shade_val is not None:
            self.on_click_shade_val = on_click_shade_val
        
        border_radius = kwargs.get('border_radius')
        if border_radius is not None:
            self.border_radius = border_radius
        
        img_offset = kwargs.get('img_offset')
        if img_offset is not None:
            self.img_offset = img_offset
            self.image_surf = pygame.transform.scale(self.image, (self.size[0] - self.img_offset, self.size[1] - self.img_offset))
            self.img_rect = self.image_surf.get_rect(center=self.rect.center)
        
        image = kwargs.get('image')
        if image is not None:
            self.image_surf = self.image = image
            if self.scale_img:
                self.image_surf = pygame.transform.scale(self.image, (self.size[0] - self.img_offset, self.size[1] - self.img_offset))
            self.img_rect = self.image_surf.get_rect(center=self.rect.center)
        
        scale_img = kwargs.get('scale_img')
        if scale_img is not None:
            self.scale_img = scale_img
            if self.scale_img:
                self.image_surf = pygame.transform.scale(self.image, (self.size[0] - self.img_offset, self.size[1] - self.img_offset))
                self.img_rect = self.image_surf.get_rect(center=self.rect.center)
        
        size = kwargs.get('size')
        if size is not None:
            self.size = size
            self.rect.size = self.size
            if self.image_surf:
                if self.scale_img:
                    self.image_surf = pygame.transform.scale(self.image, (self.size[0] - self.img_offset, self.size[1] - self.img_offset))
                self.img_rect = self.image_surf.get_rect(center=self.rect.center)
        
        invisible = kwargs.get('invisible')
        if invisible is not None:
            self.invisible = invisible
        
        mouse_pos = kwargs.get('mouse_pos')
        if mouse_pos is not None:
            self.mouse_pos = mouse_pos
    
    def _set_color(self, color, opacity: int, hex_: bool = True):
        assert self._is_color(color), f'"{color}" is not a valid color'
        
        if isinstance(color, str):
            if '#' in color:
                color_tuple = [(abs(255 - (col * 255)) / 255) for col in pygame.Color(color).cmy]
            else:
                color_tuple = [i/255 for i in pygame.colordict.THECOLORS[color]]
        elif isinstance(color, tuple | list | pygame.color.Color):
            color_tuple = [i/255 for i in color]
        elif isinstance(color, int):
            color_tuple = [i/255 for i in pygame.Color(color)]
        else:
            raise Exception('Invalid color argument')

        for i in color_tuple[:3]:
            black = i == 0
            if not black:
                break
        
        color = [255 - opacity for _ in color_tuple] if black else [i * opacity for i in color_tuple]
        
        if len(color) >= 4:
            color = color[:3]
        
        return color
    
    def _rgb_to_hex(self, rgb):
        rgb = tuple(int(max(0, min(255, component))) for component in rgb)
        hex_color = "#{:02X}{:02X}{:02X}".format(*rgb)
        
        return hex_color
    
    def _is_color(self, color):
        try:
            pygame.colordict.THECOLORS[color]
        except:
            try:
                pygame.Color(color).cmy
            except:
                return False
            return True
        return True
    
    def _set_topleft(self, pos):
        self.rect.x, self.rect.y = pos
        if self.image_surf is not None:
            self.img_rect.center = self.rect.center
    
    def _isclicked(self,
                   mouse_rect: pygame.Rect,
                   target: pygame.Rect,
                   left_mouse_clicked: bool,
                   middle_mouse_clicked: bool,
                   right_mouse_clicked: bool,
                   hover_func: Callable,
                   not_hover_func: Callable,
                   left_click_func: Callable,
                   middle_click_func: Callable,
                   right_click_func: Callable,
                   left_not_clicked_func: Callable,
                   middle_not_clicked_func: Callable,
                   right_not_clicked_func: Callable):
        mouse_collission = mouse_rect.colliderect(target)
        
        if mouse_collission:
            hover_func()
        else:
            not_hover_func()
        
        if left_mouse_clicked and mouse_collission:
            self.left_mouse_clicked = True
        if not left_mouse_clicked:
            self.left_mouse_clicked = False
        if not self.left_mouse_clicked and not mouse_collission:
            self.left_mouse_clicked_outside = False
        if not left_mouse_clicked:
            self.left_mouse_clicked_outside = True
        
        if middle_mouse_clicked and mouse_collission:
            self.middle_mouse_clicked = True
        if not middle_mouse_clicked:
            self.middle_mouse_clicked = False
        if not self.middle_mouse_clicked and not mouse_collission:
            self.middle_mouse_clicked_outside = False
        if not middle_mouse_clicked:
            self.middle_mouse_clicked_outside = True
        
        
        if right_mouse_clicked and mouse_collission:
            self.right_mouse_clicked = True
        if not right_mouse_clicked:
            self.right_mouse_clicked = False
        if not self.right_mouse_clicked and not mouse_collission:
            self.right_mouse_clicked_outside = False
        if not right_mouse_clicked:
            self.right_mouse_clicked_outside = True
        
        left_mouse_clicked = self.left_mouse_clicked and self.left_mouse_clicked_outside
        middle_mouse_clicked = self.middle_mouse_clicked and self.middle_mouse_clicked_outside
        right_mouse_clicked = self.right_mouse_clicked and self.right_mouse_clicked_outside

        if left_mouse_clicked:
            left_click_func()
        else:
            left_not_clicked_func()
        
        if middle_mouse_clicked:
            middle_click_func()
        else:
            middle_not_clicked_func()
        
        if right_mouse_clicked:
            right_click_func()
        else:
            right_not_clicked_func()
        
        return left_mouse_clicked, middle_mouse_clicked, right_mouse_clicked, mouse_collission
    
    def _clicking(self, click_call_info: tuple[str, Callable], many_actions_one_click: bool = False):
        call_type, call_func = click_call_info
        match call_type:
            case 'on right clicked':
                self.curr_button_opacity = self.on_click_shade_val
                if self.start_right_click_check:
                    if call_func is not None:
                        call_func()
                    self.start_right_click_check = False
                    self.start_right_click_check = self.start_right_click_check or many_actions_one_click
            case 'on middle clicked':
                self.curr_button_opacity = self.on_click_shade_val
                if self.start_middle_click_check:
                    if call_func is not None:
                        call_func()
                    self.start_middle_click_check = False
                    self.start_middle_click_check = self.start_middle_click_check or many_actions_one_click
            case 'on left clicked':
                self.curr_button_opacity = self.on_click_shade_val
                if self.start_left_click_check:
                    if call_func is not None:
                        call_func()
                    self.start_left_click_check = False
                    self.start_left_click_check = self.start_left_click_check or many_actions_one_click
            case 'on not left clicked':
                self.start_left_click_check = True
                if call_func is not None:
                    call_func()
            case 'on not middle clicked':
                self.start_middle_click_check = True
                if call_func is not None:
                    call_func()
            case 'on not right clicked':
                self.start_right_click_check = True
                if call_func is not None:
                    call_func()
            case 'on not hover':
                self.curr_button_opacity = 255 if not self.disabled else 125
                if call_func is not None:
                    call_func()
            case 'on hover':
                if self.hover:
                    self.curr_button_opacity = self.on_hover_shade_val
                if call_func is not None:
                    call_func()
    
    def disable(self):
        self.disabled = True
        self.orig_hover_state = self.hover
        self.hover = False
    
    def enable(self):
        self.disabled = False
        self.hover = self.orig_hover_state
    
    def _draw(self):
        if not self.invisible:
            pygame.draw.rect(self.screen, self._set_color(self.bg_color, self.curr_button_opacity), self.rect, 0, self.border_radius)
        if self.image_surf is not None:
            self.screen.blit(self.image_surf, self.img_rect)
    
    def update(self):
        clicked_info = []
        
        if not self.disabled:
            mouse_rect = pygame.Rect(*self.mouse_pos, 1, 1)
            left_mouse_clicked = pygame.mouse.get_pressed()[0]
            middle_mouse_clicked = pygame.mouse.get_pressed()[1]
            right_mouse_clicked = pygame.mouse.get_pressed()[2]
            
            clicked_info = self._isclicked( mouse_rect,
                                            self.rect,
                                            left_mouse_clicked,
                                            middle_mouse_clicked,
                                            right_mouse_clicked,
                                            hover_func              =  lambda: self._clicking(click_call_info=('on hover', self.on_hover)),
                                            not_hover_func          =  lambda: self._clicking(click_call_info=('on not hover', self.on_not_hover)),
                                            left_click_func         =  lambda: self._clicking(click_call_info=('on left clicked', self.on_left_mouse_button_clicked), many_actions_one_click=self.many_actions_one_click),
                                            middle_click_func        =  lambda: self._clicking(click_call_info=('on middle clicked', self.on_middle_mouse_button_clicked)),
                                            right_click_func        =  lambda: self._clicking(click_call_info=('on right clicked', self.on_right_mouse_button_clicked)),
                                            left_not_clicked_func   =  lambda: self._clicking(click_call_info=('on not left clicked', self.on_not_left_mouse_button_clicked)),
                                            middle_not_clicked_func  =  lambda: self._clicking(click_call_info=('on not middle clicked', self.on_not_middle_mouse_button_clicked)),
                                            right_not_clicked_func  =  lambda: self._clicking(click_call_info=('on not right clicked', self.on_not_right_mouse_button_clicked)),
                            )
        
        self._draw()
        
        self.mouse_pos = pygame.mouse.get_pos()
        
        return clicked_info


class ScrollableSurface:
    def __init__(self, screen: pygame.Surface, sub_surf: pygame.Surface, sub_surf_pos: tuple, blit_surf_pos: tuple, blit_surf_size: tuple, blit_surf_color=None, scroll_wheel_color='white', scroll_wheel_size: int = 5, scroll_wheel_border_x_offset: float = 4, scroll_wheel_border_y_offset: float = 4, orientation: Literal['x', 'y', 'both'] = 'x') -> None:
        self.screen = screen
        
        self.orientation = orientation
        
        self.scroll_wheel_size = scroll_wheel_size
        self.scroll_wheel_border_x_offset = scroll_wheel_border_x_offset
        self.scroll_wheel_border_y_offset = scroll_wheel_border_y_offset
        
        self.sub_surf = sub_surf
        self.sub_surf_pos = sub_surf_pos
        self.sub_surf_rect = self.sub_surf.get_rect(topleft=sub_surf_pos)
        
        self.blit_surf = pygame.Surface(blit_surf_size)
        self.blit_rect = self.blit_surf.get_rect(topleft=blit_surf_pos)
        if blit_surf_color is not None:
            self.blit_surf.fill(blit_surf_color)
        
        self.show_x_slider = self.orientation in ('x', 'both') and self.sub_surf.get_width() > self.blit_surf.get_width()
        self.show_y_slider = self.orientation in ('y', 'both') and self.sub_surf.get_height() > self.blit_surf.get_height()
        
        self.scroll_wheel_x = Button(self.screen, (0, 0), (0, self.scroll_wheel_size), scroll_wheel_color, on_left_mouse_button_clicked=self._on_move_surface_x, on_not_left_mouse_button_clicked=self._on_not_move_surface_x, many_actions_one_click=True)
        self.scroll_wheel_x.set_pos(bottomleft=(self.blit_rect.left + self.scroll_wheel_border_x_offset, self.blit_rect.bottom - self.scroll_wheel_border_y_offset))
        self.scroll_wheel_y = Button(self.screen, (0, 0), (self.scroll_wheel_size, 0), scroll_wheel_color, on_left_mouse_button_clicked=self._on_move_surface_y, on_not_left_mouse_button_clicked=self._on_not_move_surface_y, many_actions_one_click=True)
        self.scroll_wheel_y.set_pos(topright=(self.blit_rect.right - self.scroll_wheel_border_x_offset, self.blit_rect.top + self.scroll_wheel_border_y_offset))
    
    def configure(self, **kwargs):
        sub_surf = kwargs.get('sub_surf')
        if sub_surf is not None:
            self.sub_surf = sub_surf
        
        blit_surf_size = kwargs.get('blit_surf_size')
        if blit_surf_size is not None:
            self.blit_surf_size = blit_surf_size
            self.blit_surf = pygame.Surface(self.blit_surf_size)
        
        sub_surf_pos = kwargs.get('sub_surf_pos')
        if sub_surf_pos is not None:
            self.sub_surf_pos = sub_surf_pos
            self.sub_surf_rect.topleft = self.sub_surf_pos
        
        blit_surf_pos = kwargs.get('blit_surf_pos')
        if blit_surf_pos is not None:
            self.blit_surf_pos = blit_surf_pos
            self.blit_rect.topleft = self.blit_surf_pos
        
        blit_surf_color = kwargs.get('blit_surf_color')
        if blit_surf_color is not None:
            self.blit_surf_color = blit_surf_color
            self.blit_surf.fill(blit_surf_color)
        
        scroll_wheel_color = kwargs.get('scroll_wheel_color')
        if scroll_wheel_color is not None:
            self.scroll_wheel_color = scroll_wheel_color
            self.scroll_wheel_x.configure(bg_color=self.scroll_wheel_color)
            self.scroll_wheel_y.configure(bg_color=self.scroll_wheel_color)
        
        scroll_wheel_size = kwargs.get('scroll_wheel_size')
        if scroll_wheel_size is not None:
            self.scroll_wheel_size = scroll_wheel_size
            self.scroll_wheel_x.configure(size=(self.scroll_wheel_size, self.scroll_wheel_x.rect.height))
            self.scroll_wheel_y.configure(size=(self.scroll_wheel_y.rect.width, self.scroll_wheel_size))
        
        scroll_wheel_border_x_offset = kwargs.get('scroll_wheel_border_x_offset')
        if scroll_wheel_border_x_offset is not None:
            self.scroll_wheel_border_x_offset = scroll_wheel_border_x_offset
        
        scroll_wheel_border_y_offset = kwargs.get('scroll_wheel_border_y_offset')
        if scroll_wheel_border_y_offset is not None:
            self.scroll_wheel_border_y_offset = scroll_wheel_border_y_offset
        
        orientation = kwargs.get('orientation')
        if orientation is not None:
            self.orientation = orientation
        
        self.show_x_slider = self.orientation in ('x', 'both') and self.sub_surf.get_width() > self.blit_surf.get_width()
        self.show_y_slider = self.orientation in ('y', 'both') and self.sub_surf.get_height() > self.blit_surf.get_height()
    
    def _on_move_surface_x(self):
        mouse_x = pygame.mouse.get_pos()[0]
        half_length = self.scroll_wheel_border_x_offset + (self.scroll_wheel_x.rect.width / 2)
        x = pygame.math.clamp(self.prev_x + (mouse_x - self.prev_mouse_x), self.blit_rect.x + half_length, self.blit_rect.right - half_length)
        self.scroll_wheel_x.set_pos(center=(x, self.scroll_wheel_x.rect.centery))
        try:
            scroll_wheel_pos_ratio = (self.scroll_wheel_x.rect.left - (self.blit_rect.left + self.scroll_wheel_border_x_offset)) / (self.blit_rect.width - self.scroll_wheel_x.rect.width - (self.scroll_wheel_border_x_offset * 2))
        except ZeroDivisionError:
            scroll_wheel_pos_ratio = 1
        self.sub_surf_rect.x = self.sub_surf_pos[0] - (scroll_wheel_pos_ratio * (self.sub_surf_rect.width - self.blit_rect.width))
    
    def _on_move_surface_y(self):
        mouse_y = pygame.mouse.get_pos()[1]
        half_height = self.scroll_wheel_border_y_offset + (self.scroll_wheel_y.rect.height / 2)
        y = pygame.math.clamp(self.prev_y + (mouse_y - self.prev_mouse_y), self.blit_rect.y + half_height, self.blit_rect.bottom - half_height)
        self.scroll_wheel_y.set_pos(center=(self.scroll_wheel_y.rect.centerx, y))
        try:
            scroll_wheel_pos_ratio = (self.scroll_wheel_y.rect.top - (self.blit_rect.top + self.scroll_wheel_border_y_offset)) / (self.blit_rect.height - self.scroll_wheel_y.rect.height - (self.scroll_wheel_border_y_offset * 2))
        except ZeroDivisionError:
            scroll_wheel_pos_ratio = 1
        self.sub_surf_rect.y = self.sub_surf_pos[1] - (scroll_wheel_pos_ratio * (self.sub_surf_rect.height - self.blit_rect.height))
    
    def _on_not_move_surface_x(self):
        self.prev_x = self.scroll_wheel_x.rect.centerx
        self.prev_mouse_x = pygame.mouse.get_pos()[0]
    
    def _on_not_move_surface_y(self):
        self.prev_y = self.scroll_wheel_y.rect.centery
        self.prev_mouse_y = pygame.mouse.get_pos()[1]
    
    def draw(self):
        self.blit_surf.blit(self.sub_surf, self.sub_surf_rect)
        self.screen.blit(self.blit_surf, self.blit_rect)
    
    def update(self):
        self.draw()
        self.sub_surf_rect = self.sub_surf.get_rect(topleft=self.sub_surf_rect.topleft)
        
        if self.show_x_slider:
            sw_x_width = min((self.blit_rect.width / self.sub_surf_rect.width) * self.blit_rect.width, self.blit_rect.width - (self.scroll_wheel_border_x_offset * 2))
            self.scroll_wheel_x.configure(size=(sw_x_width, self.scroll_wheel_size))
            self.scroll_wheel_x.update()
        if self.show_y_slider:
            sw_y_height = min((self.blit_rect.height / self.sub_surf_rect.height) * self.blit_rect.height, self.blit_rect.height - (self.scroll_wheel_border_y_offset * 2))
            self.scroll_wheel_y.configure(size=(self.scroll_wheel_size, sw_y_height))
            self.scroll_wheel_y.update()


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
        assert index < len(self.breakpoints), f'{index} is out of range'
        self.breakpoints[index][0] = pos
        if index > 0:
            self.breakpoints[index - 1][1] = pos
    
    def move_breakpoint_ending_point(self, index: int, pos: list):
        index = len(self.breakpoints) - 1 if index == -1 else index
        assert index < len(self.breakpoints), f'{index} is out of range'
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
            self.input_node = node
            self.input_connected = True
        if node.is_output:
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

class GateBaseClass:
    def __init__(self, name: str, screen: pygame.Surface, pos: tuple, input_amt, output_amt, logic_func: Callable[[list], list], node_on_click_func: Callable[[Node], None]) -> None:
        self.name = name
        self.screen = screen
        self.font = pygame.font.SysFont('Times New Roman', 20)
        
        self.node_pin_size = 5, 2
        self.gate_border_radius = 5
        self.node_size = NODE_SIZE, NODE_SIZE
        self.text_color = 'white'
        self.gate_color = '#222222'
        self.node_pin_color = 'white'
        self.node_on_color = 'pink'
        self.node_off_color = 'grey'
        
        text_surf = self.font.render(self.name, True, self.text_color)
        
        self.input_amt = input_amt
        self.output_amt = output_amt
        self.node_on_click_func = node_on_click_func
        self.logic_func = logic_func
        
        self.prev_pos = (0, 0)
        self.prev_mouse_pos = (0, 0)
        
        self.button = Button(self.screen,
                             pos,
                             (text_surf.get_width() + (GATE_TEXT_BORDER_OFFSET_X * 2),
                              max((GATE_TEXT_BORDER_OFFSET_Y + NODE_SIZE) * max(self.input_amt, self.output_amt), text_surf.get_height() + (GATE_TEXT_BORDER_OFFSET_Y * 2))),
                             self.gate_color,
                             hover=False,
                             many_actions_one_click=True,
                             on_left_mouse_button_clicked=self._on_move,
                             on_not_left_mouse_button_clicked=self._on_not_move,
                             image=text_surf
                             )
        
        def get_half_length(amt):
            node_spacing = (0 if amt == 1 else (self.button.rect.height - (NODE_SIZE * 2)) / (amt - 1))
            half_length = (((self.button.rect.height - ((amt - 1) * (self.node_size[1] + node_spacing))) / 2) - (amt * (self.node_size[1] / 2))) + (self.node_size[1] / 2)
            if amt == 1:
                half_length = (self.button.rect.height / 2) - (self.node_size[1] / 2)
            return node_spacing, half_length
        
        self.input_node_spacing, input_half_height = get_half_length(self.input_amt)
        self.input_amt
        
        self.input_nodes = [Node(self.screen,
                                 (self.button.rect.left - self.node_size[0] - self.node_pin_size[0],
                                  (self.button.rect.top + (ni / (self.input_amt - (1 + 0.000000001))) * self.button.rect.height) - self.node_size[1] * (ni / (self.input_amt - (1 + 0.000000001)))),#(self.node_pin_size[1] if ni else 0)),
                                #   input_half_height + self.button.rect.top + (ni * (self.node_size[1] + self.input_node_spacing))),
                                 self.node_size,
                                 color_on=self.node_on_color,
                                 color_off=self.node_off_color,
                                 static=False,
                                 is_input=True,
                                 border_radius=max(self.node_size) * 5,
                                 is_click_toogleable=False,
                                 on_click_func=self.node_on_click_func) for ni in range(self.input_amt)]
        
        self.output_node_spacing, output_half_height = get_half_length(self.output_amt)
        self.output_nodes = [Node(self.screen,
                                  (self.button.rect.right + self.node_pin_size[0],
                                   output_half_height + self.button.rect.top + (no * (self.node_size[1] + self.output_node_spacing))),
                                  self.node_size,
                                  color_on=self.node_on_color,
                                  color_off=self.node_off_color,
                                  static=False,
                                  is_input=False,
                                  border_radius=max(self.node_size) * 5,
                                  is_click_toogleable=False,
                                  on_click_func=self.node_on_click_func) for no in range(self.output_amt)]
    
    def _on_move(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        x = self.prev_pos[0] + (mouse_x - self.prev_mouse_pos[0])
        y = self.prev_pos[1] + (mouse_y - self.prev_mouse_pos[1])
        self.set_pos((x, y))
    
    def _on_not_move(self):
        self.prev_pos = self.button.rect.centerx, self.button.rect.centery
        self.prev_mouse_pos = pygame.mouse.get_pos()
    
    def copy(self):
        return GateBaseClass(name=self.name,
                             screen=self.screen,
                             pos= self.button.rect.topleft,
                             input_amt=self.input_amt,
                             output_amt=self.output_amt,
                             logic_func=self.logic_func,
                             node_on_click_func=self.node_on_click_func)
    
    def disconnect_all_nodes(self):
        for node in self.input_nodes:
            node.disconnect_all()
        for node in self.output_nodes:
            node.disconnect_all()
    
    def set_pos(self, pos):
        prev_x, prev_y = self.button.rect.x, self.button.rect.y
        self.button.set_pos(center=pos)
        for node in self.input_nodes:
            node.set_pos(pos=(node.get_rect().x + (self.button.rect.x - prev_x), node.get_rect().y + (self.button.rect.y - prev_y)))
        for node in self.output_nodes:
            node.set_pos(pos=(node.get_rect().x + (self.button.rect.x - prev_x), node.get_rect().y + (self.button.rect.y - prev_y)))
    
    def get_input_nodes(self):
        return self.input_nodes
    
    def get_output_nodes(self):
        return self.output_nodes
    
    def get_output(self):
        return [node.get_state() for node in self.output_nodes]
    
    def draw(self):
        for node_in in self.input_nodes:
            pygame.draw.rect(self.screen, self.node_pin_color, (self.button.rect.left - self.node_pin_size[0], node_in.get_rect().centery - self.node_pin_size[1] / 2, *self.node_pin_size))
            node_in.update()
        
        for node_out in self.output_nodes:
            pygame.draw.rect(self.screen, self.node_pin_color, (self.button.rect.right, node_out.get_rect().centery - self.node_pin_size[1] / 2, *self.node_pin_size))
            node_out.update()
    
    def logic(self):
        outputs = self.logic_func([node.get_state() for node in self.input_nodes])
        for index, state in enumerate(outputs):
            self.output_nodes[index].set_state(state)
    
    def update(self):
        self.logic()
        self.draw()
        self.button.update()

class AndGate(GateBaseClass):
    def __init__(self, screen, pos, on_click_func) -> None:
        super().__init__('And', screen, pos, 2, 1, lambda inputs: [inputs[0] and inputs[1]], on_click_func)

class NotGate(GateBaseClass):
    def __init__(self, screen, pos, on_click_func) -> None:
        super().__init__('Not', screen, pos, 1, 1, lambda inputs: [not inputs[0]], on_click_func)

class CustomGate:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font = pygame.font.SysFont('Arial', 50)
        
        self.in_out_wire_size = 10, 20
        
        self.added_and_gate = False
        self.added_not_gate = False
        self.update_input_button_removals = False
        self.update_output_button_removals = False
        self.add_wire_breakpoint = False
        self.right_mouse_pressed = True
        self.left_mouse_pressed = True
        
        self.border_offset = 30
        
        self.add_input_button = Button(self.screen, (0, 0), (30, 30), 'yellow', image=self.font.render('+', True, 'green'), on_left_mouse_button_clicked=self._add_input, border_radius=20)
        self.add_input_button.set_pos(midbottom=(self.border_offset, self.screen.get_height() - self.border_offset))
        self.add_output_button = Button(self.screen, (0, 0), (30, 30), 'yellow', image=self.font.render('+', True, 'green'), on_left_mouse_button_clicked=self._add_output, border_radius=20)
        self.add_output_button.set_pos(midbottom=(self.screen.get_width() - self.border_offset, self.screen.get_height() - self.border_offset))
        
        self.input_node_objects = []
        self.output_node_objects = []
        
        self.wire_connected_trackers = {}
        
        self.wires: list[Wire] = []
        self.gates: list[GateBaseClass] = []
        self.gate_options: list[GateBaseClass] = [AndGate(self.screen, (0, 0), self._on_node_clicked),
                                                  NotGate(self.screen, (0, 0), self._on_node_clicked)]
        
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
                                  (display_gate.button.rect.x + width, 0),
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
            self.wires.append(wire)
            self.wire_connected_trackers[wire] = True
    
    def _make_input_remove_node_func(self, index):
        def func():
            if index != 0:
                self.update_input_button_removals = True
                node = self.input_node_objects[index][1]
                connected_wires = node.connected_inputs.copy() + node.connected_inputs.copy()
                node.disconnect_all()
                for i, wire in enumerate(connected_wires):
                    self.wires.remove(wire)
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
                    self.wires.remove(wire)
                self.output_node_objects.pop(index)
                self._set_output_node_positions(True)
        
        return func
    
    def _make_remove_gate_func(self, index: int):
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
    
    def _make_remove_gate_option_func(self, gate: GateBaseClass):
        def func():
            self._remove_gate(gate)
        
        return func
    
    def _remove_wire_func(self, wire: Wire):
        if wire.input_node is not None:
            wire.input_node.set_state(0)
        wire.disconnect_all()
        self.wires.remove(wire)
    
    def make_gate(self):
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
        
        new_gate = GateBaseClass('Random', self.screen, (0, 0), len(self.input_node_objects), len(self.output_node_objects), lambda inputs: input_mapping[tuple(inputs)], self._on_node_clicked)
        
        for i, (_, node) in enumerate(self.input_node_objects):
            node.set_state(init_inp_vals[i])
        
        self.gate_options.append(new_gate)
        
        self._add_gate_to_viewer(new_gate)

    def _add_gate_to_viewer(self, gate: GateBaseClass):
        display_gate = gate.copy()
        
        gates_surf_width = sum((gate.output_nodes[0].get_rect().right - gate.input_nodes[0].get_rect().left) for gate in self.gate_options) + (self.gate_display_spacing * len(self.gate_options))
        node_size_offset = self.gate_options[0].output_nodes[0].get_rect().width + self.gate_options[0].node_pin_size[0]
        new_gate_surf = pygame.Surface((gates_surf_width, self.gates_surf.get_height()))
        display_gate.__init__(display_gate.name,
                              new_gate_surf,
                              (self.gates_surf.get_width() + node_size_offset, 0),
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
            self.gates.append(gate.copy())
        
        return func
    
    def update_addition_of_gates(self):
        for index, gate in enumerate(self.gate_options):
            new_gate = gate.copy()
            if self.gate_key_index_map.get(index) is None:
                self.gate_key_index_map[index] = False
            if self.keys[pygame.K_a + index]:
                if not self.gate_key_index_map[index]:
                    new_gate.set_pos(pygame.mouse.get_pos())
                    self.gates.append(new_gate.copy())
                    self.gate_key_index_map[index] = True
            else:
                self.gate_key_index_map[index] = False
    
    def update_wires(self):
        for wire in self.wires:
            if self.wire_connected_trackers[wire]:
                if pygame.mouse.get_pressed()[2]:
                    if not self.right_mouse_pressed:
                        if wire.input_connected:
                            wire.input_node.disconnect(wire)
                        elif wire.output_connected:
                            wire.output_node.disconnect(wire)
                        self.wires.remove(wire)
                        self.wire_connected_trackers[wire] = False
                    self.right_mouse_pressed = True
                else:
                    self.right_mouse_pressed = False
                
                if pygame.mouse.get_pressed()[0]:
                    if not self.left_mouse_pressed:
                        gate_nodes = []
                        for gate in self.gates:
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
        for index, gate in enumerate(self.gates):
            gate.button.configure(on_right_mouse_button_clicked=self._make_remove_gate_func(index))
            gate.update()
    
    def update_inputs(self):
        self.add_output_button.update()
        for ctrl, out in self.input_node_objects:
            pygame.draw.line(self.screen, 'grey', ctrl.rect.center, out.node_button.rect.center)
            ctrl.update()
            out.update()
    
    def update_outputs(self):
        self.add_input_button.update()
        for out in self.output_node_objects:
            out.update()
    
    def update(self):
        
        self.keys = pygame.key.get_pressed()
        self.mouse_pos = pygame.mouse.get_pos()
        
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
        
        if self.keys[pygame.K_RETURN]:
            if not self.made_gate:
                self.make_gate()
                self.made_gate = True
        else:
            self.made_gate = False
        
        self.update_addition_of_gates()



