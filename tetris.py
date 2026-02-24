#!/usr/bin/env python3
"""
Terminal Tetris - Classic Tetris game for Linux terminal
Author: Sagar Jadhav
"""

import os
import sys
import time
import random
import keyboard
from threading import Thread

# Game constants
WIDTH = 10
HEIGHT = 20
EMPTY = '·'
BLOCK = '█'

# Tetromino shapes
SHAPES = {
    'I': [['▓▓▓▓']],
    'O': [['▓▓', '▓▓']],
    'T': [['▓▓▓', '·▓·']],
    'S': [['·▓▓', '▓▓·']],
    'Z': [['▓▓·', '·▓▓']],
    'J': [['▓··', '▓▓▓']],
    'L': [['··▓', '▓▓▓']],
}

COLORS = {
    'I': '\033[96m',  # Cyan
    'O': '\033[93m',  # Yellow
    'T': '\033[95m',  # Purple
    'S': '\033[92m',  # Green
    'Z': '\033[91m',  # Red
    'J': '\033[94m',  # Blue
    'L': '\033[96m',  # Orange
}
RESET = '\033[0m'

class Tetris:
    def __init__(self):
        self.board = [[EMPTY for _ in range(WIDTH)] for _ in range(HEIGHT)]
        self.score = 0
        self.level = 1
        self.lines = 0
        self.game_over = False
        self.paused = False
        self.current_piece = None
        self.current_pos = [0, 0]
        self.hold_piece = None
        self.next_piece = self.random_piece()
        self.shadow = []
        
    def random_piece(self):
        return random.choice(list(SHAPES.keys()))
    
    def new_piece(self):
        self.current_piece = self.next_piece
        self.next_piece = self.random_piece()
        self.current_pos = [0, WIDTH // 2 - len(SHAPES[self.current_piece][0]) // 2]
        self.shadow = self.get_shadow()
        
        if self.check_collision(0, 0, self.current_piece):
            self.game_over = True
    
    def get_shadow(self):
        shadow_row = self.current_pos[0]
        while not self.check_collision(shadow_row + 1, self.current_pos[1], self.current_piece):
            shadow_row += 1
        return [shadow_row, self.current_pos[1]]
    
    def rotate(self):
        old_shape = SHAPES[self.current_piece]
        rotated = list(zip(*old_shape[::-1]))
        if not self.check_collision(0, 0, rotated):
            SHAPES[self.current_piece] = [list(row) for row in rotated]
            self.shadow = self.get_shadow()
    
    def move(self, dx, dy):
        if not self.check_collision(dy, dx, self.current_piece):
            self.current_pos[1] += dx
            self.current_pos[0] += dy
            self.shadow = self.get_shadow()
            return True
        return False
    
    def check_collision(self, dy, dx, piece=None):
        if piece is None:
            piece = self.current_piece
        shape = SHAPES[piece]
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell != '·':
                    new_y = self.current_pos[0] + y + dy
                    new_x = self.current_pos[1] + x + dx
                    if new_x < 0 or new_x >= WIDTH or new_y >= HEIGHT:
                        return True
                    if new_y >= 0 and self.board[new_y][new_x] != EMPTY:
                        return True
        return False
    
    def lock_piece(self):
        shape = SHAPES[self.current_piece]
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell != '·':
                    board_y = self.current_pos[0] + y
                    board_x = self.current_pos[1] + x
                    if board_y >= 0:
                        self.board[board_y][board_x] = self.current_piece
        
        self.clear_lines()
        self.new_piece()
    
    def clear_lines(self):
        lines_cleared = 0
        for y in range(HEIGHT):
            if all(cell != EMPTY for cell in self.board[y]):
                self.board.pop(y)
                self.board.insert(0, [EMPTY for _ in range(WIDTH)])
                lines_cleared += 1
        
        if lines_cleared > 0:
            self.score += [0, 100, 300, 500, 800][lines_cleared] * self.level
            self.lines += lines_cleared
            self.level = self.lines // 10 + 1
    
    def draw(self):
        display = self.board.copy()
        
        # Draw shadow
        if self.current_piece:
            shape = SHAPES[self.current_piece]
            for y, row in enumerate(shape):
                for x, cell in enumerate(row):
                    if cell != '·':
                        sy = self.shadow[0] + y
                        sx = self.shadow[1] + x
                        if 0 <= sy < HEIGHT and 0 <= sx < WIDTH:
                            display[sy][sx] = '░'
        
        # Draw current piece
        if self.current_piece:
            shape = SHAPES[self.current_piece]
            color = COLORS[self.current_piece]
            for y, row in enumerate(shape):
                for x, cell in enumerate(row):
                    if cell != '·':
                        py = self.current_pos[0] + y
                        px = self.current_pos[1] + x
                        if 0 <= py < HEIGHT and 0 <= px < WIDTH:
                            display[py][px] = f"{color}█{RESET}"
        
        # Build output
        os.system('clear')
        print(f"\n╔{'═' * (WIDTH * 2 + 2)}╗")
        for row in display:
            print("║" + " ".join(row) + " ║")
        print(f"╚{'═' * (WIDTH * 2 + 2)}╝")
        
        print(f"\n  Score: {self.score}")
        print(f"  Level: {self.level}")
        print(f"  Lines: {self.lines}")
        print(f"  Next: {self.next_piece}")
        
        if self.game_over:
            print("\n  ╔═══════════════╗")
            print("  ║   GAME OVER   ║")
            print("  ╚═══════════════╝")
        
        print("\n  Controls: ← → ↓ | ↑ rotate | P pause | Q quit")

def game_loop(tetris):
    fall_speed = 0.5
    while not tetris.game_over:
        time.sleep(fall_speed / tetris.level)
        if not tetris.paused:
            if not tetris.move(0, 1):
                tetris.lock_piece()
                fall_speed = 0.5

def main():
    tetris = Tetris()
    tetris.new_piece()
    
    game_thread = Thread(target=game_loop, args=(tetris,))
    game_thread.daemon = True
    game_thread.start()
    
    try:
        while not tetris.game_over:
            tetris.draw()
            key = keyboard.read_key()
            
            if key == 'left':
                tetris.move(-1, 0)
            elif key == 'right':
                tetris.move(1, 0)
            elif key == 'down':
                tetris.move(0, 1)
                tetris.score += 1
            elif key == 'up':
                tetris.rotate()
            elif key == 'p':
                tetris.paused = not tetris.paused
            elif key == 'q':
                break
    except KeyboardInterrupt:
        pass
    
    print(f"\nFinal Score: {tetris.score}")

if __name__ == '__main__':
    main()
