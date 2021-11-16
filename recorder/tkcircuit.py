from tkgpio import TkCircuit

BOARD_CONFIG = {
    "width": 200,
    "height": 100,
    "leds": [
        {"x": 50, "y": 40, "name": "status", "pin": 17}
    ],
    "buttons": [
        {"x": 100, "y": 40, "name": "Rec/Stop", "pin": 2},
    ]
}


circuit = TkCircuit(BOARD_CONFIG)
@circuit.run
def test_board():
    from recorder.server import main
    main()
