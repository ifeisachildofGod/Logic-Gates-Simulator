import json
import sys
import pygame
from settings import SCR_WIDTH, SCR_HEIGHT, FPS
from logic_circuits import GateDisplay
from widgets import MenuBar

class App:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCR_WIDTH, SCR_HEIGHT))
        logo = pygame.image.load('logos/logo.png')
        pygame.display.set_icon(logo)
        pygame.display.set_caption('IFEs Logic Gate Simulator')
        self.clock = pygame.time.Clock()
        
        self.font = pygame.font.SysFont('Consolas', 20)
        
        with open('themes.json') as file:
            self.bg_colors = json.loads(file.read())
        
        self.BG_COLOR = self.bg_colors["0"]
        
        self.gate = GateDisplay(self.screen, 100)
        options = {
            "File": {
                'New': print,
                'Open': print,
                'Save': print,
                'Save As': print,
                'Close': print,
            },
            "Edit": {
                'Undo': print,
                'Redo': print,
                'Cut': print,
                'Copy': print,
                'Paste': print,
            }
        }
        self.menubar = MenuBar(self.screen, 0, 50, 25, 'blue', 'black', 2, 2, 2, options)
        self.gate_circuit_index_tracker = None
        
    def _app_loop(self):
        self.fps_surf = self.font.render(f'FPS: {round(self.clock.get_fps())}', False, 'white')
        self.fps_rect = self.fps_surf.get_rect(bottomright=(SCR_WIDTH - 20, SCR_HEIGHT))
        self.screen.blit(self.fps_surf, self.fps_rect)
        
        self.gate.update(self.events)
        self.menubar.update()
    
    def _event_loop(self, event):
        self.keys = pygame.key.get_pressed()
        
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    
    def run(self):
        while True:
            self.keys = pygame.key.get_pressed()
            self.mouse_pos = pygame.mouse.get_pos()
            self.delta_time = self.clock.tick(FPS)
            
            self.BG_COLOR = self.bg_colors[str(self.gate.circuit_index)]
            
            if self.gate_circuit_index_tracker != self.gate.circuit_index:
                self.gate.theme_color = self.BG_COLOR
            
            self.screen.fill(self.BG_COLOR)

            self.events = pygame.event.get()
            for event in self.events:
                self._event_loop(event)
            
            self._app_loop()

            pygame.display.update()
    

def main():
    game = App()
    game.run()

if __name__ == '__main__':
    main()



