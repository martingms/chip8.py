##
## chip8.py -- A CHIP-8 emulator by Martin Gammelsæter (martigam@stud.ntnu.no)
##
## Resources used:
## http://www.codeslinger.co.uk/pages/projects/chip8/
## http://en.wikipedia.org/wiki/CHIP-8

class Screen:
    "TODO docstring"
    def __init__(self):
        self.screen = [[0 for _ in range(32) ] for _ in range(64)]

    def clear(self):
        # TODO: This can probably be done in a better way...
        self.screen = [[0 for _ in range(32) ] for _ in range(64)]

class MMU:
    def __init__(self):
        self.mem = [] # There's no easy way in python to force size...

    def read(self, address):
        return self.mem[address]

    def write(self, address, data):
        self.mem[address] = data

class CPU:
    def __init__(self):
        "Initializes the CPU with all needed variables"
        self.registers = {
            # 8-bit data registers
            'V0': 0, 'V1': 0, 'V2': 0, 'V3': 0,
            'V4': 0, 'V5': 0, 'V6': 0, 'V7': 0,
            'V8': 0, 'V9': 0, 'VA': 0, 'VB': 0,
            'VC': 0, 'VD': 0, 'VE': 0, 'VF': 0 # VF doubles as carry
        }

        self.I = 0 # 16-bit address register
        self.PC = 0 # 16-bit program counter

        self.stack = [] # Only to be accessed through append and pop.
                        # Could perhaps abstract this, but meh.

        self.mmu = MMU()
        self.screen = Screen()

    def reset(self):
        "Resets the CPU to default boot-values"
        self.I = 0

        # On the CHIP8, 0x0 -> 0x1FF is for the interpreter,
        # so any code is loaded into memory starting at 0x200.
        self.PC = 0x200

        self.screen.clear()

        for key in self.registers:
            self.registers[key] = 0

    def get_next_opcode(self):
        "Combines two 1-byte words starting at PC into one 2-byte opcode"
        # Reads first byte and shifts it left 8 bits,
        # then logically ORs first byte with the second.
        res = (self.mmu.read(self.PC) << 8) | self.mmu.read(self.PC + 1)

        # Increases PC to point to next opcode
        self.PC += 2
        return res

    def execute_next_opcode(self):
        "Gets the next opcode and executes it"
        opcodes = {
            0x0000: decode_opcode_0,
            0x1000: opcode_1NNN,
            0x2000: opcode_2NNN,
            0x3000: opcode_3XNN,
            0x4000: opcode_4XNN,
            0x5000: opcode_5XY0,
            0x6000: opcode_6XNN,
            0x7000: opcode_7XNN,
            0x8000: decode_opcode_8
            0x9000: opcode_9XY0,
            0xA000: opcode_ANNN,
            0xB000: opcode_BNNN,
            0xC000: opcode_CXNN,
            0xD000: opcode_DXYN,
            0xE000: decode_opcode_E,
            0xF000: decode_opcode_F
        }

        opcode = get_next_opcode()

        # AND-ing the opcode with 0xF000 to get only the first number,
        # before calling the function handling that opcode.
        opcodes[opcode & 0xF000](opcode)

    def decode_opcode_0(self, opcode):
        "Decodes opcodes beginning in 0"
        opcodes = {
            # NOTE: The opcode 0x0NNN is unsupported, see wikipedia.
            0x0: self.screen.clear,
            0xE: opcode_00EE
        }

        # AND-ing the opcode with 0xF to get only last number,
        # which is enough to distinguish what opcode it is.
        opcodes[opcode & 0xF]()

    def opcode_00EE(self):
        "Returns from a subroutine."
        self.PC = self.stack.pop()

    def opcode_1NNN(self, opcode):
        "Jumps to address NNN."
        self.PC = opcode & 0x0FFF

    def opcode_2NNN(self, opcode):
        "Calls subroutine at NNN."
        self.stack.append(self.PC)
        self.PC = opcode & 0x0FFF

    # FIXME/TODO: The following two opcodes are very similar, DRY etc...
    def opcode_3XNN(self, opcode):
        "Skips the next instruction if VX equals NN."
        X = (opcode & 0x0F00) >> 8
        NN = opcode & 0x00FF

        if self.registers['V'+str(X)] == NN: # FIXME
            self.PC += 2

    def opcode_4XNN(self, opcode):
        "Skips the next instruction if VX doesn't equal NN."
        X = (opcode & 0x0F00) >> 8
        NN = opcode & 0x00FF

        if self.registers['V'+str(X)] != NN: # FIXME
            self.PC += 2

    def opcode_5XY0(self, opcode):
        "Skips the next instruction if VX equals VY."
        X = (opcode & 0x0F00) >> 8
        Y = (opcode & 0x00F0) >> 4

        if self.registers['V'+str(X)] == self.registers['V'+str(Y)]:
            self.PC += 2

    def opcode_6XNN(self, opcode):
        "Sets VX to NN."
        X = (opcode & 0x0F00) >> 8
        NN = opcode & 0x00FF

        self.registers['V'+str(X)] = NN


    # TODO: Handle overflows since overflow is not happening here...
    def opcode_7XNN(self, opcode):
        "Adds NN to VX."
        X = (opcode & 0x0F00) >> 8
        NN = opcode & 0x00FF

        self.registers['V'+str(X)] += NN

    def decode_opcode_8(self, opcode):
        "Decodes opcodes beginning in 8"
        opcodes = {
            0x0: opcode_8XY0,
            0x1: opcode_8XY1,
            0x2: opcode_8XY2,
            0x3: opcode_8XY3,
            0x4: opcode_8XY4,
            0x5: opcode_8XY5,
            0x6: opcode_8XY6,
            0x7: opcode_8XY7,
            0xE: opcode_8XYE,
        }

        # AND-ing the opcode with 0xF to get only last number,
        # which is enough to distinguish what opcode it is.
        opcodes[opcode & 0xF](opcode)

    def opcode_8XY0(self, opcode):
        "Sets VX to the value of VY."
        X = (opcode & 0x0F00) >> 8
        Y = (opcode & 0x00F0) >> 4

        self.registers['V'+str(X)] = self.registers['V'+str(Y)]

    def opcode_8XY1(self, opcode):
        "Sets VX to VX or VY."
        X = (opcode & 0x0F00) >> 8
        Y = (opcode & 0x00F0) >> 4

        VX = self.registers['V'+str(X)]
        VX = VX | self.registers['V'+str(Y)]

    def opcode_8XY2(self, opcode):
        "Sets VX to VX and VY."
        X = (opcode & 0x0F00) >> 8
        Y = (opcode & 0x00F0) >> 4

        VX = self.registers['V'+str(X)]
        VX = VX & self.registers['V'+str(Y)]

    def opcode_8XY3(self, opcode):
        "Sets VX to VX xor VY."
        X = (opcode & 0x0F00) >> 8
        Y = (opcode & 0x00F0) >> 4

        VX = self.registers['V'+str(X)]
        VX = VX ^ self.registers['V'+str(Y)]
