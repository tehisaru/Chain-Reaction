import pygame
import sys
import math
import time
from typing import List, Tuple

# Initialize Pygame
pygame.init()
sys.setrecursionlimit(2000)

# Constants
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 900
GRID_COLS = 2
GRID_ROWS = 3
CELL_SIZE = min(WINDOW_WIDTH // GRID_COLS, WINDOW_HEIGHT // GRID_ROWS)
DOT_RADIUS = CELL_SIZE // 6
SHAKE_AMPLITUDE = 3
SHAKE_SPEED = 10

# Colors
BLACK = (0, 0, 0)
RED = (153, 0, 0)
BLUE = (0, 153, 153)
PASTEL_RED = (255, 204, 204)
PASTEL_BLUE = (204, 255, 255)
GRAY = (200, 200, 200)

# Create the window
WINDOW = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Ahelreaktsioon")

class Cell:
    def __init__(self):
        self.dots = 0
        self.color = None
        
    def is_empty(self) -> bool:
        return self.dots == 0
    
    def add_dot(self, color: Tuple[int, int, int]):
        self.dots += 1
        self.color = color
        
    def clear(self):
        self.dots = 0
        self.color = None

class Game:
    def __init__(self):
        self.grid = [[Cell() for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.current_player = RED
        self.game_over = False
        self.winner = None
        self.turns_played = 0
        self.pending_turn_change = False  # New flag to track when we should change turns
        
    def is_valid_move(self, row: int, col: int) -> bool:
        if not (0 <= row < GRID_ROWS and 0 <= col < GRID_COLS):
            return False
        return self.grid[row][col].is_empty() or self.grid[row][col].color == self.current_player
    
    def get_critical_mass(self, row: int, col: int) -> int:
        # Corner cells
        if (row in [0, GRID_ROWS-1]) and (col in [0, GRID_COLS-1]):
            return 2
        # Edge cells
        if row in [0, GRID_ROWS-1] or col in [0, GRID_COLS-1]:
            return 3
        # Center cells
        return 4
    
    def is_near_critical(self, row: int, col: int) -> bool:
        if self.grid[row][col].is_empty():
            return False
        return self.grid[row][col].dots == self.get_critical_mass(row, col) - 1
    
    def get_neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        neighbors = []
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < GRID_ROWS and 0 <= new_col < GRID_COLS:
                neighbors.append((new_row, new_col))
        return neighbors
    
    def add_dot_to_cell(self, row, col, color):
        self.grid[row][col].color = color
        self.grid[row][col].dots += 1
        return self.grid[row][col].dots >= self.get_critical_mass(row, col)

    def remove_dots_from_cell(self, row, col):
        dots = self.grid[row][col].dots
        color = self.grid[row][col].color
        self.grid[row][col].clear()
        return dots, color

    def chain_reaction(self, row: int, col: int):
        if self.grid[row][col].dots >= self.get_critical_mass(row, col):
            color = self.grid[row][col].color
            dots = self.grid[row][col].dots
            self.grid[row][col].clear()
            
            for neighbor_row, neighbor_col in self.get_neighbors(row, col):
                self.grid[neighbor_row][neighbor_col].color = color
                self.grid[neighbor_row][neighbor_col].dots += 1
                self.chain_reaction(neighbor_row, neighbor_col)
    
    def make_move(self, row: int, col: int):
        if self.game_over or not self.is_valid_move(row, col):
            return False
        
        self.grid[row][col].add_dot(self.current_player)
        self.chain_reaction(row, col)
        self.turns_played += 1
        
        if self.turns_played > 1 and self.check_winner():
            self.game_over = True
            self.winner = self.current_player
        else:
            self.current_player = BLUE if self.current_player == RED else RED
        return True
    
    def check_winner(self) -> bool:
        colors = set()
        has_dots = False
        for row in self.grid:
            for cell in row:
                if not cell.is_empty():
                    colors.add(cell.color)
                    has_dots = True
        # Only check for winner if there are dots on the board
        return has_dots and len(colors) == 1
    
    def get_all_dots(self) -> List[Tuple[int, int]]:
        dots = []
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                if not self.grid[row][col].is_empty():
                    dots.append((row, col))
        return dots

def draw_dot_pattern(window, cell, center_x, center_y, shake_offset_x=0, shake_offset_y=0):
    dot_positions = []
    
    if cell.dots == 1:
        dot_positions = [(0, 0)]
    elif cell.dots == 2:
        dot_positions = [(-1.5, 0), (1.5, 0)]
    elif cell.dots == 3:
        dot_positions = [
            (0, -1.5),  # Top
            (-1.5, 1),  # Bottom left
            (1.5, 1)   # Bottom right
        ]
    
    for dx, dy in dot_positions:
        x = center_x + dx * DOT_RADIUS + shake_offset_x
        y = center_y + dy * DOT_RADIUS + shake_offset_y
        pygame.draw.circle(window, cell.color, (int(x), int(y)), DOT_RADIUS)

def draw_game(game: Game):
    # Choose the pastel color based on the winner if game is over,
    # otherwise based on current player
    if game.game_over:
        pastel_color = PASTEL_RED if game.winner == RED else PASTEL_BLUE
    else:
        pastel_color = PASTEL_RED if game.current_player == RED else PASTEL_BLUE

    # Fill the window with the selected pastel color
    WINDOW.fill(pastel_color)

    current_time = time.time()
    
    # Draw grid
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x = col * CELL_SIZE
            y = row * CELL_SIZE
            pygame.draw.rect(WINDOW, GRAY, (x, y, CELL_SIZE, CELL_SIZE), 1)
    
    # Draw dots
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cell = game.grid[row][col]
            if not cell.is_empty():
                center_x = col * CELL_SIZE + CELL_SIZE // 2
                center_y = row * CELL_SIZE + CELL_SIZE // 2
                
                # Add shaking effect for cells near critical mass
                shake_offset_x = shake_offset_y = 0
                if game.is_near_critical(row, col):
                    shake_offset_x = math.sin(current_time * SHAKE_SPEED) * SHAKE_AMPLITUDE
                    shake_offset_y = math.cos(current_time * SHAKE_SPEED) * SHAKE_AMPLITUDE
                
                draw_dot_pattern(WINDOW, cell, center_x, center_y, shake_offset_x, shake_offset_y)
    
    
    # Draw game over message
    if game.game_over:
        font = pygame.font.Font(None, 74)
        winner_color = "Sinine" if game.winner == RED else "Punane"
        text = font.render(f"{winner_color} Võidab!", True, game.winner)
        text_rect = text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 50))
        WINDOW.blit(text, text_rect)
    
    pygame.display.flip()

class MovingBlob:
    def __init__(self, start_pos, end_pos, color, start_time, duration=0.4):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.color = color
        self.start_time = start_time
        self.duration = duration
        self.current_pos = start_pos # current position of the blob lol

    def update_position(self, current_time):
        elapsed_time = current_time - self.start_time
        if elapsed_time >= self.duration:
            self.current_pos = self.end_pos
            return True  # Animation complete
        t = elapsed_time / self.duration
        self.current_pos = (
            self.start_pos[0] + t * (self.end_pos[0] - self.start_pos[0]),
            self.start_pos[1] + t * (self.end_pos[1] - self.start_pos[1])
        )
        return False  # Animation ongoing

def draw_moving_blobs(window, moving_blobs):
    for blob in moving_blobs:
        pygame.draw.circle(window, blob.color, (int(blob.current_pos[0]), int(blob.current_pos[1])), DOT_RADIUS)

def chain_reaction(game, row, col, moving_blobs):
    if game.grid[row][col].dots >= game.get_critical_mass(row, col):
        dots, color = game.remove_dots_from_cell(row, col)
        
        # Create a blob for each dot that needs to move
        for neighbor_row, neighbor_col in game.get_neighbors(row, col):
            start_pos = (col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2)
            end_pos = (neighbor_col * CELL_SIZE + CELL_SIZE // 2, neighbor_row * CELL_SIZE + CELL_SIZE // 2)
            moving_blobs.append(MovingBlob(start_pos, end_pos, color, time.time()))

def update_game(game, moving_blobs):
    if game.turns_played == 0:
        return

    current_time = time.time()
    completed_blobs = []
    cells_to_check = set()
    
    # Update positions and collect completed animations
    for blob in moving_blobs:
        if blob.update_position(current_time):
            completed_blobs.append(blob)
            col = int(blob.end_pos[0] // CELL_SIZE)
            row = int(blob.end_pos[1] // CELL_SIZE)
            if game.add_dot_to_cell(row, col, blob.color):
                cells_to_check.add((row, col))
                game.pending_turn_change = True  # Set flag when chain reaction occurs
    
    # Remove completed blobs
    for blob in completed_blobs:
        moving_blobs.remove(blob)
    
    # Process chain reactions for completed movements
    for row, col in cells_to_check:
        chain_reaction(game, row, col, moving_blobs)
    
    # Only check for winner and handle turn change when ALL animations are complete
    if not moving_blobs and not cells_to_check:
        if game.turns_played > 1 and game.check_winner():
            game.game_over = True
            game.winner = game.current_player
        elif game.pending_turn_change:  # Change turns only if flag is set
            game.current_player = BLUE if game.current_player == RED else RED
            game.pending_turn_change = False  # Reset the flag

def make_move(game, row, col, moving_blobs):
    if game.game_over or not game.is_valid_move(row, col):
        return False
    
    # Add dot to the selected cell
    if game.add_dot_to_cell(row, col, game.current_player):
        chain_reaction(game, row, col, moving_blobs)
        game.pending_turn_change = True  # Set flag for turn change after animations
    else:
        # If no chain reaction, change turns immediately
        game.current_player = BLUE if game.current_player == RED else RED
    
    game.turns_played += 1
    return True

def main():
    game = Game()
    clock = pygame.time.Clock()
    moving_blobs = []
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN and not game.game_over:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                col = mouse_x // CELL_SIZE
                row = mouse_y // CELL_SIZE
                if game.is_valid_move(row, col):  # Only make move if valid
                    make_move(game, row, col, moving_blobs)
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                game = Game()
                moving_blobs.clear()
        
        update_game(game, moving_blobs)
        draw_game(game)
        draw_moving_blobs(WINDOW, moving_blobs)
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()