import sys
from App import App

file_path = None
new_file = False
if len(sys.argv) > 1:
    file_path = sys.argv[1]
    new_file = bool(int(sys.argv[2]))

def main():
    game = App(file_path, __file__, new_file)
    game.run()

if __name__ == '__main__':
    main()



