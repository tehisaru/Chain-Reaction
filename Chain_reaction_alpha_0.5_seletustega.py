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
GRID_COLS = 6
GRID_ROWS = 9
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
    """
    Represents one square in the game grid.
    Can hold multiple dots of the same color.
    Critical mass (max dots before explosion) depends on cell position.
    """
    def __init__(self):
        self.dots = 0      # Count of dots in this cell
        self.color = None  # Color of dots (None if empty)
    
    def is_empty(self) -> bool:
        # Simple check if cell has no dots
        return self.dots == 0
    
    def add_dot(self, color: Tuple[int, int, int]):
        # Adds one dot and sets/updates cell color
        self.dots += 1
        self.color = color
    
    def clear(self):
        # Resets cell to empty state (used after explosion)
        self.dots = 0
        self.color = None

class Game:
    def __init__(self):
        self.grid = [[Cell() for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.current_player = RED
        self.game_over = False
        self.winner = None
        self.turns_played = 0
        
    def is_valid_move(self, row: int, col: int) -> bool:
        """
        Checks if a move is valid:
        1. Position must be within grid bounds
        2. Cell must be either empty or owned by current player
        
        Example:
        if game.is_valid_move(0, 0):  # Checks if top-left cell is valid
            game.make_move(0, 0)
        """
        if not (0 <= row < GRID_ROWS and 0 <= col < GRID_COLS):
            return False
        return self.grid[row][col].is_empty() or self.grid[row][col].color == self.current_player
    
    def get_critical_mass(self, row: int, col: int) -> int:
        """
        Returns how many dots a cell needs to explode:
        - Corner cells (2 neighbors): 2 dots
        - Edge cells (3 neighbors): 3 dots
        - Center cells (4 neighbors): 4 dots
        
        Example:
        mass = game.get_critical_mass(0, 0)  # Returns 2 for corner
        mass = game.get_critical_mass(1, 1)  # Returns 4 for center
        """
        if (row in [0, GRID_ROWS-1]) and (col in [0, GRID_COLS-1]):
            return 2  # Corner cells
        if row in [0, GRID_ROWS-1] or col in [0, GRID_COLS-1]:
            return 3  # Edge cells
        return 4  # Center cells
    
    def is_near_critical(self, row: int, col: int) -> bool:
        """
        Checks if cell is one dot away from exploding.
        Used for shaking animation.
        
        Example:
        if game.is_near_critical(row, col):
            # Apply shaking effect to dots
        """
        if self.grid[row][col].is_empty():
            return False
        return self.grid[row][col].dots == self.get_critical_mass(row, col) - 1
    
    def get_neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        """
        Returns list of valid adjacent cells (up, right, down, left).
        Used for chain reactions.
        
        Example:
        neighbors = game.get_neighbors(0, 0)  # Returns [(0,1), (1,0)]
        """
        neighbors = []
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:  # Right, Down, Left, Up
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

    def chain_reaction(game, row, col, moving_blobs):
        """
        Handles explosion animations when a cell reaches critical mass.
        Creates moving blobs that animate to neighboring cells.
        
        Example: If a corner cell (critical mass 2) gets a third dot,
        it explodes and sends dots to its two neighbors.
        """
    if game.grid[row][col].dots >= game.get_critical_mass(row, col):
        dots, color = game.remove_dots_from_cell(row, col)
        
        # For each neighbor, create an animated dot moving from current cell
        for neighbor_row, neighbor_col in game.get_neighbors(row, col):
            # Calculate pixel positions for start and end of animation
            start_pos = (col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2)
            end_pos = (neighbor_col * CELL_SIZE + CELL_SIZE // 2, neighbor_row * CELL_SIZE + CELL_SIZE // 2)
            moving_blobs.append(MovingBlob(start_pos, end_pos, color, time.time()))

class MovingBlob:
    """
    Handles animation of dots moving between cells during chain reactions.
    Uses linear interpolation to smoothly move dots.
    """
    def __init__(self, start_pos, end_pos, color, start_time, duration=0.5):
        self.start_pos = start_pos    # Starting pixel coordinates
        self.end_pos = end_pos        # Ending pixel coordinates
        self.color = color            # Dot color
        self.start_time = start_time  # When animation started
        self.duration = duration      # How long animation should take
        self.current_pos = start_pos  # Current position during animation

    def update_position(self, current_time):
        """
        Updates dot position based on elapsed time.
        Returns True when animation is complete.
        Uses linear interpolation (lerp) for smooth movement.
        """
        elapsed_time = current_time - self.start_time
        if elapsed_time >= self.duration:
            self.current_pos = self.end_pos
            return True  # Animation complete
        
        # Calculate position using linear interpolation
        t = elapsed_time / self.duration  # Progress (0 to 1)
        self.current_pos = (
            self.start_pos[0] + t * (self.end_pos[0] - self.start_pos[0]),
            self.start_pos[1] + t * (self.end_pos[1] - self.start_pos[1])
        )
        return False  # Animation ongoing

def draw_dot_pattern(window, cell, center_x, center_y, shake_offset_x=0, shake_offset_y=0):
    """
    Draws dots in different patterns based on count (1-3 dots).
    Adds shaking effect when near critical mass.
    
    Patterns:
    1 dot: Center
    2 dots: Left and right
    3 dots: Triangle formation
    """
    dot_positions = []
    
    # Calculate dot positions relative to center
    if cell.dots == 1:
        dot_positions = [(0, 0)]  # Single center dot
    elif cell.dots == 2:
        dot_positions = [(-1.5, 0), (1.5, 0)]  # Two horizontal dots
    elif cell.dots == 3:
        dot_positions = [
            (0, -1.5),    # Top
            (-1.5, 1),    # Bottom left
            (1.5, 1)      # Bottom right
        ]
    
    # Draw each dot with shake offset if applicable
    for dx, dy in dot_positions:
        x = center_x + dx * DOT_RADIUS + shake_offset_x
        y = center_y + dy * DOT_RADIUS + shake_offset_y
        pygame.draw.circle(window, cell.color, (int(x), int(y)), DOT_RADIUS)
def draw_game(game: Game):
    # Choose the pastel color based on the current player
    if game.current_player == RED:
        pastel_color = PASTEL_RED
    else:
        pastel_color = PASTEL_BLUE

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
    def __init__(self, start_pos, end_pos, color, start_time, duration=0.2):
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
    """
    Handles explosion animations when a cell reaches critical mass.
    Creates moving blobs that animate to neighboring cells.
    
    Example: If a corner cell (critical mass 2) gets a third dot,
    it explodes and sends dots to its two neighbors.
    """
    if game.grid[row][col].dots >= game.get_critical_mass(row, col):
        dots, color = game.remove_dots_from_cell(row, col)
        
        # For each neighbor, create an animated dot moving from current cell
        for neighbor_row, neighbor_col in game.get_neighbors(row, col):
            # Calculate pixel positions for start and end of animation
            start_pos = (col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2)
            end_pos = (neighbor_col * CELL_SIZE + CELL_SIZE // 2, neighbor_row * CELL_SIZE + CELL_SIZE // 2)
            moving_blobs.append(MovingBlob(start_pos, end_pos, color, time.time()))

def update_game(game, moving_blobs):
    # Don't process anything if the game hasn't started
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
    
    # Remove completed blobs
    for blob in completed_blobs:
        moving_blobs.remove(blob)
    
    # Process chain reactions for completed movements
    for row, col in cells_to_check:
        chain_reaction(game, row, col, moving_blobs)
    
    # Only check for winner when all animations are complete
    if not moving_blobs and not cells_to_check and game.turns_played > 1:
        if game.check_winner():
            game.game_over = True
            game.winner = game.current_player

def make_move(game, row, col, moving_blobs):
    if game.game_over or not game.is_valid_move(row, col):
        return False
    
    # Add dot to the selected cell
    if game.add_dot_to_cell(row, col, game.current_player):
        chain_reaction(game, row, col, moving_blobs)
    
    game.turns_played += 1
    # Change turns immediately after a successful move
    game.current_player = BLUE if game.current_player == RED else RED
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
