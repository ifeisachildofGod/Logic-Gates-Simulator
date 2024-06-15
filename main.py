
import pygame
import sys
from settings import *
from logic_circuits import CustomGate

class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCR_WIDTH, SCR_HEIGHT))
        pygame.display.set_caption('IFEs Circuit CAD')
        self.clock = pygame.time.Clock()
        
        self.font = pygame.font.Font(None, 25)
        
        self.test_gate = CustomGate(self.screen)
        
        self.BG_COLOR = 'black'
    
    def main_event_loop(self, event):
        self.keys = pygame.key.get_pressed()
        
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    
    def main_game_loop(self):
        self.fps_surf = self.font.render(f'FPS: {round(self.clock.get_fps())}', False, 'white')
        self.fps_rect = self.fps_surf.get_rect(topright=(SCR_WIDTH - 20, 20))
        self.mouse_pos = pygame.mouse.get_pos()
        
        self.test_gate.update()
        
        self.screen.blit(self.fps_surf, self.fps_rect)
        
    def run(self):
        while True:
            self.delta_time = self.clock.tick(FPS)
            self.screen.fill(self.BG_COLOR)
            
            for event in pygame.event.get():
                self.main_event_loop(event)
            
            self.main_game_loop()

            pygame.display.update()
 
def main():
    game = App()
    game.run()

if __name__ == '__main__':
    main()



