#!/usr/bin/env python3
"""
Terminal Tetris - Enhanced Classic Tetris game for Linux terminal
Author: Sagar Jadhav
Version: 2.0 - Optimized & Enhanced
"""

import os
import sys
import time
import random
import keyboard
import threading
from collections import deque

# Game constants
WIDTH = 10
HEIGHT = 20
EMPTY = '·'
BLOCK = '█'

# Optimized Tetromino shapes (pre-computed)
SHAPES = {
    'I': [['▓▓▓▓']],
    'O': [['▓▓', '▓▓']],
    'T': [['▓▓▓', '·▓·']],
    'S': [['·▓▓', '▓▓·']],
    'Z': [['▓▓·', '·▓▓']],
    'J': [['▓··', '▓▓▓']],
    'L': [['··▓', '▓▓▓']],
}

# ANSI Colors (optimized)
COLORS = {
    'I': '\033[96m',  # Cyan
    'O': '\033[93m',  # Yellow
    'T': '\033[95m',  # Purple
    'S': '\033[92m',  # Green
    'Z': '\033[91m',  # Red
    'J': '\033[94m',  # Blue
    'L': '\033[33m',  # Orange
}
RESET = '\033[0m'
SHADOW_COLOR = '\033[90m'  # Gray for ghost piece

# Scoring system (enhanced)
SCORING = {
    1: 100,
    2: 300,
    3: 500,
    4: 800,  # Tetris!
    5: 1200,  # Multiple Tetris
}

class Tetris:
    """Optimized Tetris game engine"""
    
    def __init__(self):
        # Use list comprehension for faster initialization
        self.board = [[EMPTY for _ in range(WIDTH)] for _ in range(HEIGHT)]
        self.score = 0
        self.level = 1
        self.lines = 0
        self.game_over = False
        self.paused = False
        self.current_piece = None
        self.current_pos = [0, 0]
        self.hold_piece = None
        self.can_hold = True
        self.next_piece = self.random_piece()
        self.shadow = []
        self.combo = 0
        self.total_cleared = 0
        
        # Performance: Pre-compute fallback shapes
        self._shape_cache = {}
        
    def random_piece(self):
        """Optimized random piece selection"""
        return random.choice(list(SHAPES.keys()))
    
    def new_piece(self):
        """Spawn new piece with optimized positioning"""
        self.current_piece = self.next_piece
        self.next_piece = self.random_piece()
        
        # Center the piece
        shape_width = len(SHAPES[self.current_piece][0])
        self.current_pos = [0, max(0, WIDTH // 2 - shape_width // 2)]
        
        # Calculate shadow immediately
        self.shadow = self.get_shadow()
        self.can_hold = True
        
        # Check game over
        if self.check_collision(0, 0, self.current_piece):
            self.game_over = True
    
    def get_shadow(self):
        """Optimized ghost piece calculation"""
        shadow_row = self.current_pos[0]
        while not self.check_collision(shadow_row + 1, self.current_pos[1], self.current_piece):
            shadow_row += 1
            if shadow_row >= HEIGHT:
                break
        return [shadow_row, self.current_pos[1]]
    
    def rotate(self):
        """Wall kick rotation system"""
        old_shape = SHAPES[self.current_piece]
        rotated = list(zip(*old_shape[::-1]))
        
        # Try basic rotation
        if not self.check_collision(0, 0, rotated):
            SHAPES[self.current_piece] = [list(row) for row in rotated]
            self.shadow = self.get_shadow()
            return True
        
        # Wall kick attempts (SRS-inspired)
        kicks = [(-1, 0), (1, 0), (0, -1), (-2, 0), (2, 0)]
        for dx, dy in kicks:
            if not self.check_collision(dy, dx, rotated):
                SHAPES[self.current_piece] = [list(row) for row in rotated]
                self.current_pos[1] += dx
                self.current_pos[0] += dy
                self.shadow = self.get_shadow()
                return True
        
        return False
    
    def move(self, dx, dy):
        """Optimized collision-checked movement"""
        if not self.check_collision(dy, dx, self.current_piece):
            self.current_pos[1] += dx
            self.current_pos[0] += dy
            self.shadow = self.get_shadow()
            return True
        return False
    
    def check_collision(self, dy, dx, piece=None):
        """Optimized collision detection"""
        if piece is None:
            piece = self.current_piece
        shape = SHAPES[piece]
        
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell != '·':
                    new_y = self.current_pos[0] + y + dy
                    new_x = self.current_pos[1] + x + dx
                    
                    # Boundary checks
                    if new_x < 0 or new_x >= WIDTH or new_y >= HEIGHT:
                        return True
                    if new_y >= 0 and self.board[new_y][new_x] != EMPTY:
                        return True
        return False
    
    def hold(self):
        """Hold current piece for later"""
        if not self.can_hold:
            return False
            
        if self.hold_piece is None:
            self.hold_piece = self.current_piece
            self.new_piece()
        else:
            self.hold_piece, self.current_piece = self.current_piece, self.hold_piece
            shape_width = len(SHAPES[self.current_piece][0])
            self.current_pos = [0, WIDTH // 2 - shape_width // 2]
            self.shadow = self.get_shadow()
        
        self.can_hold = False
        return True
    
    def lock_piece(self):
        """Lock piece to board with optimized clearing"""
        shape = SHAPES[self.current_piece]
        color = COLORS[self.current_piece]
        
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell != '·':
                    board_y = self.current_pos[0] + y
                    board_x = self.current_pos[1] + x
                    if 0 <= board_y < HEIGHT:
                        self.board[board_y][board_x] = f"{color}█{RESET}"
        
        self.clear_lines()
        self.new_piece()
    
    def clear_lines(self):
        """Optimized line clearing with scoring"""
        lines_cleared = 0
        
        # Find completed lines (iterate backwards for safety)
        for y in range(HEIGHT - 1, -1, -1):
            if all(cell != EMPTY for cell in self.board[y]):
                self.board.pop(y)
                self.board.insert(0, [EMPTY for _ in range(WIDTH)])
                lines_cleared += 1
        
        # Enhanced scoring
        if lines_cleared > 0:
            # Combo system
            if lines_cleared >= 4:
                self.combo += 1
                bonus = self.combo * 50
            else:
                self.combo = 0
                bonus = 0
            
            base_score = SCORING.get(lines_cleared, lines_cleared * 100)
            self.score += (base_score + bonus) * self.level
            self.lines += lines_cleared
            self.total_cleared += lines_cleared
            
            # Level up every 10 lines
            new_level = self.total_cleared // 10 + 1
            if new_level > self.level:
                self.level = new_level
    
    def draw(self):
        """Optimized rendering with double buffering concept"""
        # Create display buffer
        display = [row[:] for row in self.board]
        
        # Draw shadow (ghost piece)
        if self.current_piece:
            shape = SHAPES[self.current_piece]
            for y, row in enumerate(shape):
                for x, cell in enumerate(row):
                    if cell != '·':
                        sy = self.shadow[0] + y
                        sx = self.shadow[1] + x
                        if 0 <= sy < HEIGHT and 0 <= sx < WIDTH:
                            display[sy][sx] = f"{SHADOW_COLOR}░{RESET}"
        
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
        
        # Clear screen and render
        os.system('clear')
        
        # Title
        print(f"\n  \033[1;36m╔{'═' * (WIDTH * 2 + 10)}╗")
        print(f"  ║  🎮 TERMINAL TETRIS v2.0  ║")
        print(f"  ╚{'═' * (WIDTH * 2 + 10)}╝\033[0m")
        
        # Game board
        print(f"  ╔{'═' * (WIDTH * 2 + 2)}╗")
        for row in display:
            print("  ║" + " ".join(row) + " ║")
        print(f"  ╚{'═' * (WIDTH * 2 + 2)}╝")
        
        # Stats panel
        print(f"\n  \033[1;33mScore:\033[0m {self.score:,}")
        print(f"  \033[1;32mLevel:\033[0m {self.level}")
        print(f"  \033[1;34mLines:\033[0m {self.lines}")
        print(f"  \033[1;35mNext:\033[0m {self.next_piece}")
        
        if self.hold_piece:
            print(f"  \033[1;31mHold:\033[0m {self.hold_piece}")
        
        if self.combo > 1:
            print(f"  \033[1;37m🔥 Combo x{self.combo}!\033[0m")
        
        if self.game_over:
            print("\n  \033[1;31m╔═══════════════╗")
            print("  ║   GAME OVER   ║")
            print("  ╚═══════════════╝\033[0m")
            print(f"\n  \033[1;32mFinal Score: {self.score:,}\033[0m")
        
        print("\n  \033[90mControls: ← → ↓ | ↑ rotate | H hold | P pause | Q quit\033[0m")


def game_loop(tetris):
    """Optimized game loop with level-based speed"""
    base_speed = 0.5
    
    while not tetris.game_over:
        # Speed increases with level
        fall_speed = max(0.05, base_speed - (tetris.level - 1) * 0.03)
        time.sleep(fall_speed)
        
        if not tetris.paused:
            if not tetris.move(0, 1):
                tetris.lock_piece()
                if tetris.game_over:
                    break


def main():
    """Enhanced main game loop"""
    tetris = Tetris()
    tetris.new_piece()
    
    # Start game thread
    game_thread = threading.Thread(target=game_loop, args=(tetris,), daemon=True)
    game_thread.start()
    
    print("\n\033[1;36m🎮 Welcome to Terminal Tetris v2.0! 🎮\033[0m")
    print("\033[90mPress any key to start...\033[0m")
    keyboard.read_key()
    
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
                tetris.score += 1  # Soft drop bonus
            elif key == 'up':
                tetris.rotate()
            elif key == 'h':
                tetris.hold()
            elif key == 'p':
                tetris.paused = not tetris.paused
            elif key == 'q':
                break
                
    except KeyboardInterrupt:
        pass
    
    print(f"\n\033[1;32mThanks for playing! Final Score: {tetris.score:,}\033[0m\n")
    time.sleep(2)


if __name__ == '__main__':
    main()
