from typing import Callable
import pygame

def is_color(color):
    try:
        pygame.colordict.THECOLORS[color]
    except:
        try:
            pygame.Color(color).cmy
        except:
            return False
        return True
    return True

def set_color(color, opacity: int):
    assert is_color(color), f'"{color}" is not a valid color'
    
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


_left_mouse_clicked_dict = {}
_left_mouse_clicked_outside_dict = {}
_middle_mouse_clicked_dict = {}
_middle_mouse_clicked_outside_dict = {}
_right_mouse_clicked_dict = {}
_right_mouse_clicked_outside_dict = {}

_left_mouse_tracker_clicked_dict = {}
_left_mouse_tracker_not_clicked_dict = {}
_middle_mouse_tracker_clicked_dict = {}
_middle_mouse_tracker_not_clicked_dict = {}
_right_mouse_tracker_clicked_dict = {}
_right_mouse_tracker_not_clicked_dict = {}

_hover_tracker_dict = {}
_not_hover_tracker_dict = {}

def is_clicked(mouse_rect: pygame.Rect,
               target_rect: pygame.Rect,
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

    global _left_mouse_clicked_dict, _left_mouse_clicked_outside_dict, _middle_mouse_clicked_dict, _middle_mouse_clicked_outside_dict, _right_mouse_clicked_dict, _right_mouse_clicked_outside_dict, _left_mouse_tracker_clicked_dict, _left_mouse_tracker_not_clicked_dict, _middle_mouse_tracker_clicked_dict, _middle_mouse_tracker_not_clicked_dict, _right_mouse_tracker_clicked_dict, _right_mouse_tracker_not_clicked_dict, _hover_tracker_dict, _not_hover_tracker_dict

    left_mouse_clicked, middle_mouse_clicked, right_mouse_clicked = pygame.mouse.get_pressed()
    mouse_collission = mouse_rect.colliderect(target_rect)
    
    target_rect_key = repr(target_rect)
    
    if target_rect_key not in _left_mouse_clicked_dict:
        _left_mouse_clicked_dict[target_rect_key] = False
    if target_rect_key not in _left_mouse_clicked_outside_dict:
        _left_mouse_clicked_outside_dict[target_rect_key] = False
    if target_rect_key not in _middle_mouse_clicked_dict:
        _middle_mouse_clicked_dict[target_rect_key] = False
    if target_rect_key not in _middle_mouse_clicked_outside_dict:
        _middle_mouse_clicked_outside_dict[target_rect_key] = False
    if target_rect_key not in _right_mouse_clicked_dict:
        _right_mouse_clicked_dict[target_rect_key] = False
    if target_rect_key not in _right_mouse_clicked_outside_dict:
        _right_mouse_clicked_outside_dict[target_rect_key] = False
    
    if target_rect_key not in _left_mouse_tracker_clicked_dict:
        _left_mouse_tracker_clicked_dict[target_rect_key] = False
    if target_rect_key not in _left_mouse_tracker_not_clicked_dict:
        _left_mouse_tracker_not_clicked_dict[target_rect_key] = False
    if target_rect_key not in _middle_mouse_tracker_clicked_dict:
        _middle_mouse_tracker_clicked_dict[target_rect_key] = False
    if target_rect_key not in _middle_mouse_tracker_not_clicked_dict:
        _middle_mouse_tracker_not_clicked_dict[target_rect_key] = False
    if target_rect_key not in _right_mouse_tracker_clicked_dict:
        _right_mouse_tracker_clicked_dict[target_rect_key] = False
    if target_rect_key not in _right_mouse_tracker_not_clicked_dict:
        _right_mouse_tracker_not_clicked_dict[target_rect_key] = False
    
    if target_rect_key not in _hover_tracker_dict:
        _hover_tracker_dict[target_rect_key] = False
    if target_rect_key not in _not_hover_tracker_dict:
        _not_hover_tracker_dict[target_rect_key] = False
    
    if mouse_collission:
        _not_hover_tracker_dict[target_rect_key] = False
        if not _hover_tracker_dict[target_rect_key] or hover_many_actions_one_click:
            if hover_func is not None:
                hover_func()
            _hover_tracker_dict[target_rect_key] = True
    else:
        _hover_tracker_dict[target_rect_key] = False
        if not _not_hover_tracker_dict[target_rect_key] or not_hover_many_actions_one_click:
            if not_hover_func is not None:
                not_hover_func()
            _not_hover_tracker_dict[target_rect_key] = True
    
    if left_mouse_clicked and mouse_collission:
        _left_mouse_clicked_dict[target_rect_key] = True
    if not left_mouse_clicked:
        _left_mouse_clicked_dict[target_rect_key] = False
    if not _left_mouse_clicked_dict[target_rect_key] and not mouse_collission:
        _left_mouse_clicked_outside_dict[target_rect_key] = False
    if not left_mouse_clicked:
        _left_mouse_clicked_outside_dict[target_rect_key] = True
    
    if middle_mouse_clicked and mouse_collission:
        _middle_mouse_clicked_dict[target_rect_key] = True
    if not middle_mouse_clicked:
        _middle_mouse_clicked_dict[target_rect_key] = False
    if not _middle_mouse_clicked_dict[target_rect_key] and not mouse_collission:
        _middle_mouse_clicked_outside_dict[target_rect_key] = False
    if not middle_mouse_clicked:
        _middle_mouse_clicked_outside_dict[target_rect_key] = True
    
    if right_mouse_clicked and mouse_collission:
        _right_mouse_clicked_dict[target_rect_key] = True
    if not right_mouse_clicked:
        _right_mouse_clicked_dict[target_rect_key] = False
    if not _right_mouse_clicked_dict[target_rect_key] and not mouse_collission:
        _right_mouse_clicked_outside_dict[target_rect_key] = False
    if not right_mouse_clicked:
        _right_mouse_clicked_outside_dict[target_rect_key] = True
    
    left_mouse_clicked = _left_mouse_clicked_dict[target_rect_key] and _left_mouse_clicked_outside_dict[target_rect_key]
    middle_mouse_clicked = _middle_mouse_clicked_dict[target_rect_key] and _middle_mouse_clicked_outside_dict[target_rect_key]
    right_mouse_clicked = _right_mouse_clicked_dict[target_rect_key] and _right_mouse_clicked_outside_dict[target_rect_key]
    
    if left_mouse_clicked:
        _left_mouse_tracker_not_clicked_dict[target_rect_key] = False
        if not _left_mouse_tracker_clicked_dict[target_rect_key] or left_many_actions_one_click:
            if on_left_clicked_func is not None:
                on_left_clicked_func()
            _left_mouse_tracker_clicked_dict[target_rect_key] = True
    else:
        _left_mouse_tracker_clicked_dict[target_rect_key] = False
        if not _left_mouse_tracker_not_clicked_dict[target_rect_key] or left_many_actions_one_not_click:
            if on_not_left_clicked_func is not None:
                on_not_left_clicked_func()
            _left_mouse_tracker_not_clicked_dict[target_rect_key] = True
    
    if middle_mouse_clicked:
        _middle_mouse_tracker_not_clicked_dict[target_rect_key] = False
        if not _middle_mouse_tracker_clicked_dict[target_rect_key] or middle_many_actions_one_click:
            if on_middle_clicked_func is not None:
                on_middle_clicked_func()
            _middle_mouse_tracker_clicked_dict[target_rect_key] = True
    else:
        _middle_mouse_tracker_clicked_dict[target_rect_key] = False
        if not _middle_mouse_tracker_not_clicked_dict[target_rect_key] or middle_many_actions_one_not_click:
            if on_not_middle_clicked_func is not None:
                on_not_middle_clicked_func()
            _middle_mouse_tracker_not_clicked_dict[target_rect_key] = True
    
    if right_mouse_clicked:
        _right_mouse_tracker_not_clicked_dict[target_rect_key] = False
        if not _right_mouse_tracker_clicked_dict[target_rect_key] or right_many_actions_one_click:
            if on_right_clicked_func is not None:
                on_right_clicked_func()
            _right_mouse_tracker_clicked_dict[target_rect_key] = True
    else:
        _right_mouse_tracker_clicked_dict[target_rect_key] = False
        if not _right_mouse_tracker_not_clicked_dict[target_rect_key] or right_many_actions_one_not_click:
            if on_not_right_clicked_func is not None:
                on_not_right_clicked_func()
            _right_mouse_tracker_not_clicked_dict[target_rect_key] = True
    
    return left_mouse_clicked, middle_mouse_clicked, right_mouse_clicked, mouse_collission



