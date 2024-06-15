
from typing import Final

SCR_WIDTH: Final = 1200
SCR_HEIGHT: Final = 550
FPS: Final = 60

GATE_WIDTH = 100
NODE_SIZE = 10
NODE_SPACING = 20

GATE_TEXT_BORDER_OFFSET_X = 20
GATE_TEXT_BORDER_OFFSET_Y = 5

CIRCUIT_WIRE_ID = 'circuit wires'
CIRCUIT_GATE_ID = 'circuit gates'
GATE_ID = 'gates'

DEFAULT_CIRCUIT: dict[str, list] = {
    CIRCUIT_WIRE_ID: [],
    CIRCUIT_GATE_ID: [],
    GATE_ID: None
}


