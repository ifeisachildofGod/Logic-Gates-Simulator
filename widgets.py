import pygame
from typing import Callable, Literal

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
                 border_top_left_radius: int = -1,
                 border_top_right_radius: int = -1,
                 border_bottom_left_radius: int = -1,
                 border_bottom_right_radius: int = -1,
                 on_hover_shade_val: float = 150,
                 on_click_shade_val: float = 200,
                 image: pygame.Surface = None,
                 scale_img: bool = False,
                 img_offset: int = 0,
                 render: bool = True) -> None:
        
        self.pos = pos
        self.size = size
        self.screen = screen
        self.on_hover = on_hover
        self.bg_color = bg_color
        self.scale_img = scale_img
        self.render = render
        self.img_offset = img_offset
        self.on_not_hover = on_not_hover
        self.border_radius = border_radius
        self.image_surf = self.image = image
        self.hover = self.orig_hover_state = hover
        self.on_hover_shade_val = on_hover_shade_val
        self.on_click_shade_val = on_click_shade_val
        self.many_actions_one_click = many_actions_one_click
        self.border_top_left_radius = border_top_left_radius
        self.border_top_right_radius = border_top_right_radius
        self.border_bottom_left_radius = border_bottom_left_radius
        self.border_bottom_right_radius = border_bottom_right_radius
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
                      border_top_left_radius = self.border_top_left_radius,
                      border_top_right_radius = self.border_top_right_radius,
                      border_bottom_left_radius = self.border_bottom_left_radius,
                      border_bottom_right_radius = self.border_bottom_right_radius,
                      image = self.image,
                      scale_img = self.scale_img,
                      img_offset = self.img_offset,
                      render = self.render)
    
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
        screen = kwargs.get('screen')
        if screen is not None:
            self.screen = screen
        
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
        
        border_top_left_radius = kwargs.get('border_top_left_radius')
        if border_top_left_radius is not None:
            self.border_top_left_radius = border_top_left_radius
        
        border_top_right_radius = kwargs.get('border_top_right_radius')
        if border_top_right_radius is not None:
            self.border_top_right_radius = border_top_right_radius
        
        border_bottom_left_radius = kwargs.get('border_bottom_left_radius')
        if border_bottom_left_radius is not None:
            self.border_bottom_left_radius = border_bottom_left_radius
        
        border_bottom_right_radius = kwargs.get('border_bottom_right_radius')
        if border_bottom_right_radius is not None:
            self.border_bottom_right_radius = border_bottom_right_radius
        
        img_offset = kwargs.get('img_offset')
        if img_offset is not None:
            self.img_offset = img_offset
            self.image_surf = pygame.transform.scale(self.image, (self.size[0] - self.img_offset, self.size[1] - self.img_offset))
            self.img_rect = self.image_surf.get_rect(center=self.rect.center)
        
        image = kwargs.get('image')
        if 'image' in kwargs:
            if image is not None:
                self.image_surf = self.image = image
                if self.scale_img:
                    self.image_surf = pygame.transform.scale(self.image, (self.size[0] - self.img_offset, self.size[1] - self.img_offset))
                self.img_rect = self.image_surf.get_rect(center=self.rect.center)
            else:
                self.image_surf = self.image = None
        
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
        
        render = kwargs.get('render')
        if render is not None:
            self.render = render
        
        disabled = kwargs.get('disabled')
        if disabled is not None:
            self.disabled = disabled
            if self.disabled:
                self.orig_hover_state = self.hover
                self.hover = False
            else:
                self.hover = self.orig_hover_state
        
        mouse_pos = kwargs.get('mouse_pos')
        if mouse_pos is not None:
            self.mouse_pos = mouse_pos
    
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
        
        if self.render:
            self._draw()
        
        self.mouse_pos = pygame.mouse.get_pos()
        
        return clicked_info
    
    def _set_color(self, color, opacity: int):
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
    
    def _draw(self):
        pygame.draw.rect(self.screen, self._set_color(self.bg_color, self.curr_button_opacity), self.rect, 0, self.border_radius, self.border_top_left_radius, self.border_top_right_radius, self.border_bottom_left_radius, self.border_bottom_right_radius)
        if self.image_surf is not None:
            self.screen.blit(self.image_surf, self.img_rect)
    
class ScrollableSurface:
    def __init__(self, screen: pygame.Surface, sub_surf: pygame.Surface, sub_surf_pos: tuple, blit_surf_pos: tuple, blit_surf_size: tuple, blit_surf_color=None, scroll_wheel_color='white', scroll_wheel_size: int = 5, scroll_wheel_border_x_offset: float = 4, scroll_wheel_border_y_offset: float = 4, orientation: Literal['x', 'y', 'both'] = 'x') -> None:
        self.screen = screen
        
        self.orientation = orientation
        
        self.scroll_wheel_size = scroll_wheel_size
        self.scroll_wheel_border_x_offset = scroll_wheel_border_x_offset
        self.scroll_wheel_border_y_offset = scroll_wheel_border_y_offset
        
        self.sub_surf = sub_surf
        self.sub_surf_pos = sub_surf_pos
        self.blit_surf_pos = blit_surf_pos
        self.sub_surf_rect = self.sub_surf.get_rect(topleft=self.sub_surf_pos)
        
        self.blit_surf = pygame.Surface(blit_surf_size, pygame.SRCALPHA)
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
        screen = kwargs.get('screen')
        if screen is not None:
            self.screen = screen
            self.scroll_wheel_x.configure(screen=self.screen)
            self.scroll_wheel_y.configure(screen=self.screen)
        
        blit_surf_color = kwargs.get('blit_surf_color')
        if 'blit_surf_color' in kwargs:
            self.blit_surf_color = blit_surf_color
            if blit_surf_color is not None:
                self.blit_surf.fill(self.blit_surf_color)
            else:
                self.blit_surf = pygame.Surface(blit_surf_size, pygame.SRCALPHA)
        
        blit_surf_size = kwargs.get('blit_surf_size')
        if blit_surf_size is not None:
            self.blit_surf_size = blit_surf_size
            self.blit_surf = pygame.Surface(self.blit_surf_size, pygame.SRCALPHA)
            self.blit_rect = self.blit_surf.get_rect(topleft=self.blit_surf_pos)
        
        blit_surf_pos = kwargs.get('blit_surf_pos')
        if blit_surf_pos is not None:
            self.blit_surf_pos = blit_surf_pos
            self.blit_rect = self.blit_surf.get_rect(topleft=self.blit_surf_pos)
        
        sub_surf_pos = kwargs.get('sub_surf_pos')
        if sub_surf_pos is not None:
            self.sub_surf_pos = sub_surf_pos
            self.sub_surf_rect.topleft = self.sub_surf_pos
        
        sub_surf = kwargs.get('sub_surf')
        if sub_surf is not None:
            self.sub_surf = sub_surf
            self.sub_surf_rect = self.sub_surf.get_rect(topleft=self.sub_surf_pos)
        
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
        self.blit_surf.fill(pygame.Color(0, 0, 0, 0))
        self.blit_surf.blit(self.sub_surf, self.sub_surf_rect)
        self.screen.blit(self.blit_surf, self.blit_rect)
    
    def update(self):
        self.draw()
        
        self.sub_surf_rect = self.sub_surf.get_rect(topleft=self.sub_surf_rect.topleft)
        self.blit_rect = self.blit_surf.get_rect(topleft=self.blit_surf_pos)
        
        if self.show_x_slider:
            sw_x_width = min((self.blit_rect.width / self.sub_surf_rect.width) * self.blit_rect.width, self.blit_rect.width - (self.scroll_wheel_border_x_offset * 2))
            self.scroll_wheel_x.configure(size=(sw_x_width, self.scroll_wheel_size))
            self.scroll_wheel_x.update()
        if self.show_y_slider:
            sw_y_height = min((self.blit_rect.height / self.sub_surf_rect.height) * self.blit_rect.height, self.blit_rect.height - (self.scroll_wheel_border_y_offset * 2))
            self.scroll_wheel_y.configure(size=(self.scroll_wheel_size, sw_y_height))
            self.scroll_wheel_y.update()

