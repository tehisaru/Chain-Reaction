import pygame
import sys
import math
import time
import random
from typing import List, Tuple, Optional

# Constants
WINDOW_WIDTH = 700
WINDOW_HEIGHT = 700
GRID_COLS = 9
GRID_ROWS = 9
CELL_SIZE = min(WINDOW_WIDTH // GRID_COLS, WINDOW_HEIGHT // GRID_ROWS)
DOT_RADIUS = CELL_SIZE // 6
HALF_CELL_SIZE = CELL_SIZE // 2
POWERUP_SIZE = DOT_RADIUS * 2
SHAKE_AMPLITUDE = 3
SHAKE_SPEED = 10
HQ_HEALTH = 5
RED_HQ_POS = (0, GRID_COLS // 2)
BLUE_HQ_POS = (GRID_ROWS - 1, GRID_COLS // 2)
POWERUP_SPAWN_CHANCE = 1 / (5 + random.random() * 2)
POWERUP_STAR = "star"
POWERUP_HEART = "heart"
MAX_POWERUP_SPAWNS = 60  # Maximum number of powerups that can spawn in a game
EXPLOSION_DURATION = 0.5  # seconds
EXPLOSION_PARTICLES = 300

# Colors
BLACK = (0, 0, 0)
RED = (153, 0, 0)
BLUE = (0, 153, 180)
PASTEL_RED = (255, 204, 204)
PASTEL_BLUE = (204, 255, 255)
GRAY = (200, 200, 200)
GREEN = (48, 169, 64)
DARK_RED = (139, 0, 0)  # Color for the heart powerup

# Create the window
pygame.init()  # Initialize all pygame modules
pygame.font.init()  # Explicitly initialize the font module
WINDOW = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Chain Base")

# Cache common calculations
NEIGHBOR_OFFSETS = [(0, 1), (1, 0), (0, -1), (-1, 0)]
ALL_NEIGHBOR_OFFSETS = [(dx, dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if dx != 0 or dy != 0]

class Cell:
    def __init__(self):
        self.dots = 0
        self.color = None
        self.powerup = None

    def is_empty(self) -> bool:
        return self.dots == 0

    def add_dot(self, color: Tuple[int, int, int]):
        self.dots += 1
        self.color = color
        self.powerup = None

    def clear(self):
        self.dots = 0
        self.color = None
        self.powerup = None

    def has_powerup(self):
        return self.powerup is not None

class HQCell(Cell):
    def __init__(self, color, health):
        super().__init__()
        self.color = color
        self.health = health
        self.dots = 0

    def is_empty(self) -> bool:
        return False

    def clear(self):
        pass

    def add_dot(self, color):
        pass

    def has_powerup(self):
        return False

class Explosion:
    def __init__(self, x: int, y: int, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.color = color
        self.start_time = time.time()
        self.particles = []
        self.completed = False
        
        # Pre-calculate particle data
        for _ in range(EXPLOSION_PARTICLES):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.3, 3)
            self.particles.append({
                'dx': math.cos(angle) * speed * CELL_SIZE,  # Pre-multiply by CELL_SIZE
                'dy': math.sin(angle) * speed * CELL_SIZE,
                'size': random.uniform(2, 6),
                'final_x': 0,
                'final_y': 0
            })

    def draw(self, window, offset_x=0, offset_y=0) -> None:
        current_time = time.time()
        progress = (current_time - self.start_time) / EXPLOSION_DURATION

        if progress >= 1 and not self.completed:
            for particle in self.particles:
                particle['final_x'] = self.x + particle['dx']
                particle['final_y'] = self.y + particle['dy']
            self.completed = True

        if not self.completed:
            for particle in self.particles:
                particle_x = self.x + particle['dx'] * progress + offset_x
                particle_y = self.y + particle['dy'] * progress + offset_y
                size = particle['size'] * (1 - progress * 0.5)
                pygame.draw.circle(window, self.color, 
                                 (int(particle_x), int(particle_y)), 
                                 int(size))
        else:
            # Draw all particles in one call using draw.circles if possible
            for particle in self.particles:
                pygame.draw.circle(window, self.color, 
                                 (int(particle['final_x'] + offset_x), 
                                  int(particle['final_y'] + offset_y)), 
                                 int(particle['size'] * 0.5))

class Game:
    def __init__(self):
        self.grid = [[Cell() for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.current_player = BLUE
        self.game_over = False
        self.winner = None
        self.turns_played = 0
        self.red_hq_health = HQ_HEALTH
        self.blue_hq_health = HQ_HEALTH
        self.powerup_spawns = 0  # Add this line to track number of powerups spawned
        self.explosions: List[Explosion] = []
        self.turn_pending = False

        red_row, red_col = RED_HQ_POS
        blue_row, blue_col = BLUE_HQ_POS
        self.grid[red_row][red_col] = HQCell(RED, self.red_hq_health)
        self.grid[blue_row][blue_col] = HQCell(BLUE, self.blue_hq_health)

    def get_neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        return [(row + dr, col + dc) for dr, dc in NEIGHBOR_OFFSETS 
                if 0 <= row + dr < GRID_ROWS and 0 <= col + dc < GRID_COLS]

    def get_all_neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        return [(row + dr, col + dc) for dr, dc in ALL_NEIGHBOR_OFFSETS 
                if 0 <= row + dr < GRID_ROWS and 0 <= col + dc < GRID_COLS]

    def is_valid_move(self, row: int, col: int) -> bool:
        if not (0 <= row < GRID_ROWS and 0 <= col < GRID_COLS):
            return False
        if (row, col) in [RED_HQ_POS, BLUE_HQ_POS]:
            return False

        # Check HQ rows - allow only empty cells or own dots
        if (self.current_player == RED and row == RED_HQ_POS[0]) or \
           (self.current_player == BLUE and row == BLUE_HQ_POS[0]):
            return self.grid[row][col].is_empty() or self.grid[row][col].color == self.current_player

        if self.turns_played < 2:
            if self.current_player == RED:
                return row == 1
            else:
                return row == GRID_ROWS - 2

        # Normal move rules for other cases
        if not self.grid[row][col].is_empty():
            return self.grid[row][col].color == self.current_player
        
        has_neighbor = False
        for n_row, n_col in self.get_all_neighbors(row, col):
            cell = self.grid[n_row][n_col]
            if not cell.is_empty() and cell.color == self.current_player:
                has_neighbor = True
                break
            if (self.current_player == RED and (n_row, n_col) == RED_HQ_POS) or \
               (self.current_player == BLUE and (n_row, n_col) == BLUE_HQ_POS):
                has_neighbor = True
                break
        return self.grid[row][col].is_empty() and has_neighbor

    def get_critical_mass(self, row: int, col: int) -> int:
        if (row in (0, GRID_ROWS - 1)) and (col in (0, GRID_COLS - 1)):
            return 2
        if row in (0, GRID_ROWS - 1) or col in (0, GRID_COLS - 1):
            return 3
        return 4

    def is_near_critical(self, row: int, col: int) -> bool:
        if self.grid[row][col].is_empty():
            return False
        return self.grid[row][col].dots == self.get_critical_mass(row, col) - 1

    def add_dot_to_cell(self, row, col, color):
        if isinstance(self.grid[row][col], HQCell):
            if (row, col) == RED_HQ_POS and color == BLUE:
                self.add_explosion(row, col, RED)
                self.red_hq_health -= 1
                return False
            elif (row, col) == BLUE_HQ_POS and color == RED:
                self.add_explosion(row, col, BLUE)
                self.blue_hq_health -= 1
                return False
            return False

        # Check for powerup before adding dot
        if self.grid[row][col].has_powerup():
            handle_powerup(self, row, col, [])
            self.grid[row][col].powerup = None  # Clear the powerup after using it

        self.grid[row][col].color = color
        self.grid[row][col].dots += 1
        return self.grid[row][col].dots >= self.get_critical_mass(row, col)

    def remove_dots_from_cell(self, row, col):
        dots = self.grid[row][col].dots
        color = self.grid[row][col].color
        self.grid[row][col].clear()
        return dots, color

    def chain_reaction(self, row: int, col: int):
        """Käsitle ahelreaktsiooni"""
        if self.grid[row][col].dots >= self.get_critical_mass(row, col):
            color = self.grid[row][col].color  # This is the color/player causing the chain reaction
            self.grid[row][col].clear()

            # Kontrolli kõiki naabreid
            for neighbor_row, neighbor_col in self.get_neighbors(row, col):
                # Lisa plahvatus enne kahju tegemist
                if (neighbor_row, neighbor_col) == RED_HQ_POS and color == BLUE:
                    self.add_explosion(neighbor_row, neighbor_col, RED)
                    self.red_hq_health -= 1
                elif (neighbor_row, neighbor_col) == BLUE_HQ_POS and color == RED:
                    self.add_explosion(neighbor_row, neighbor_col, BLUE)
                    self.blue_hq_health -= 1
                elif not isinstance(self.grid[neighbor_row][neighbor_col], HQCell):
                    # Kontrolli võimendit enne täpi lisamist
                    if self.grid[neighbor_row][neighbor_col].has_powerup():
                        # Save the current player temporarily
                        original_player = self.current_player
                        # Set current player to the color causing the chain reaction
                        self.current_player = color
                        handle_powerup(self, neighbor_row, neighbor_col, [])
                        # Restore the original player
                        self.current_player = original_player

                    self.grid[neighbor_row][neighbor_col].color = color
                    self.grid[neighbor_row][neighbor_col].dots += 1
                    self.chain_reaction(neighbor_row, neighbor_col)

    def check_winner(self) -> bool:
        if self.red_hq_health <= 0:
            self.winner = BLUE
            return True
        if self.blue_hq_health <= 0:
            self.winner = RED
            return True
        return False

    def spawn_powerup(self):
        if self.powerup_spawns >= MAX_POWERUP_SPAWNS:
            return  # Stop spawning after reaching the limit

        empty_cells = []
        for row in range(1, GRID_ROWS - 1):
            for col in list(range(0, (GRID_COLS//2 - 1))) + list(range((GRID_COLS//2 + 2), GRID_COLS)):
                cell = self.grid[row][col]
                if cell.is_empty():
                    has_neighbor = False
                    for n_row, n_col in self.get_all_neighbors(row, col):
                        if not self.grid[n_row][n_col].is_empty():
                            has_neighbor = True
                            break
                    if not has_neighbor:
                        empty_cells.append((row, col))

        if empty_cells:
            row, col = random.choice(empty_cells)
            self.grid[row][col].powerup = random.choice([POWERUP_STAR, POWERUP_HEART])
            self.powerup_spawns += 1

    def add_explosion(self, row: int, col: int, color: Tuple[int, int, int]):
        x = col * CELL_SIZE + CELL_SIZE // 2
        y = row * CELL_SIZE + CELL_SIZE // 2
        self.explosions.append(Explosion(x, y, color))

def draw_dot_pattern(window, cell, center_x, center_y, shake_offset_x=0, shake_offset_y=0):
    # Pre-calculated dot positions
    DOT_PATTERNS = {
        1: [(0, 0)],
        2: [(-1.5, 0), (1.5, 0)],
        3: [(0, -1.5), (-1.5, 1), (1.5, 1)]
    }
    
    if cell.dots in DOT_PATTERNS:
        for dx, dy in DOT_PATTERNS[cell.dots]:
            x = center_x + dx * DOT_RADIUS + shake_offset_x
            y = center_y + dy * DOT_RADIUS + shake_offset_y
            pygame.draw.circle(window, cell.color, (int(x), int(y)), DOT_RADIUS)

def draw_powerup(window, powerup_type, center_x, center_y, angle):
    if powerup_type == POWERUP_STAR:
        points = [(center_x + POWERUP_SIZE * math.cos(math.radians(angle + i * 72)),
                  center_y + POWERUP_SIZE * math.sin(math.radians(angle + i * 72)))
                 for i in range(5)]
        pygame.draw.polygon(window, GREEN, points, 0)
    elif powerup_type == POWERUP_HEART:
        points = [
            (center_x, center_y + POWERUP_SIZE/2),
            (center_x - POWERUP_SIZE/2, center_y - POWERUP_SIZE/4),
            (center_x, center_y - POWERUP_SIZE),
            (center_x + POWERUP_SIZE/2, center_y - POWERUP_SIZE/4),
        ]
        pygame.draw.polygon(window, GREEN, points, 0)

def draw_game(game: Game):
    if game.game_over:
        pastel_color = PASTEL_RED if game.winner == RED else PASTEL_BLUE
        winner_text_color = RED if game.winner == RED else BLUE
    else:
        pastel_color = PASTEL_RED if game.current_player == RED else PASTEL_BLUE
    WINDOW.fill(pastel_color)

    current_time = time.time()

    # Draw grid lines
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x = col * CELL_SIZE
            y = row * CELL_SIZE
            pygame.draw.rect(WINDOW, GRAY, (x, y, CELL_SIZE, CELL_SIZE), 1)

    # Draw explosions first (so they appear under dots)
    for explosion in game.explosions:
        explosion.draw(WINDOW)

    # Then draw dots and powerups
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cell = game.grid[row][col]
            if not cell.is_empty():
                center_x = col * CELL_SIZE + CELL_SIZE // 2
                center_y = row * CELL_SIZE + CELL_SIZE // 2

                shake_offset_x = shake_offset_y = 0
                if game.is_near_critical(row, col):
                    shake_offset_x = math.sin(current_time * SHAKE_SPEED) * SHAKE_AMPLITUDE
                    shake_offset_y = math.cos(current_time * SHAKE_SPEED) * SHAKE_AMPLITUDE

                draw_dot_pattern(WINDOW, cell, center_x, center_y, shake_offset_x, shake_offset_y)
            if cell.has_powerup():
                center_x = col * CELL_SIZE + CELL_SIZE // 2
                center_y = row * CELL_SIZE + CELL_SIZE // 2
                angle = current_time * 50
                draw_powerup(WINDOW, cell.powerup, center_x, center_y, angle)

    # Draw HQ squares and game over text
    if game.game_over:
        font = pygame.font.Font(None, 74)
        winner_color = "Punane" if game.winner == RED else "Sinine"
        text = font.render(f"{winner_color} võitis!", True, winner_text_color)
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        WINDOW.blit(text, text_rect)

    for (row, col), color, health in [(RED_HQ_POS, RED, game.red_hq_health), (BLUE_HQ_POS, BLUE, game.blue_hq_health)]:
        x = col * CELL_SIZE
        y = row * CELL_SIZE
        
        # Calculate size reduction based on health
        health_ratio = health / HQ_HEALTH
        size_reduction = (1 - health_ratio) * (CELL_SIZE * 0.4)  # 0.4 controls max shrink
        
        # Center the smaller square
        adjusted_x = x + (size_reduction / 2)
        adjusted_y = y + (size_reduction / 2)
        adjusted_size = CELL_SIZE - size_reduction
        
        pygame.draw.rect(WINDOW, color, (adjusted_x, adjusted_y, adjusted_size, adjusted_size))

        # Adjust text position to center of new square
        font = pygame.font.Font(None, 36)
        text = font.render(str(health), True, BLACK)
        text_rect = text.get_rect(center=(adjusted_x + adjusted_size // 2, adjusted_y + adjusted_size // 2))
        WINDOW.blit(text, text_rect)

    pygame.display.flip()

class MovingBlob:
    def __init__(self, start_pos, end_pos, color, start_time, duration=0.3):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.color = color
        self.start_time = start_time
        self.duration = duration
        self.current_pos = start_pos

    def update_position(self, current_time):
        elapsed_time = current_time - self.start_time
        if elapsed_time >= self.duration:
            self.current_pos = self.end_pos
            return True
        t = elapsed_time / self.duration
        self.current_pos = (
            self.start_pos[0] + t * (self.end_pos[0] - self.start_pos[0]),
            self.start_pos[1] + t * (self.end_pos[1] - self.start_pos[1])
        )
        return False

def draw_moving_blobs(window, moving_blobs):
    for blob in moving_blobs:
        pygame.draw.circle(window, blob.color, (int(blob.current_pos[0]), int(blob.current_pos[1])), DOT_RADIUS)

def chain_reaction(game, row, col, moving_blobs):
    if game.grid[row][col].dots >= game.get_critical_mass(row, col):
        dots, color = game.remove_dots_from_cell(row, col)

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

    for blob in moving_blobs:
        if blob.update_position(current_time):
            completed_blobs.append(blob)
            col = int(blob.end_pos[0] // CELL_SIZE)
            row = int(blob.end_pos[1] // CELL_SIZE)
            if game.add_dot_to_cell(row, col, blob.color):
                cells_to_check.add((row, col))

    for blob in completed_blobs:
        moving_blobs.remove(blob)

    for row, col in cells_to_check:
        chain_reaction(game, row, col, moving_blobs)

    # Check for winner before switching turns
    if not game.game_over and (game.red_hq_health <= 0 or game.blue_hq_health <= 0):
        game.game_over = True
        print(game.current_player, "lol")
        game.winner = game.current_player  # Winner is the current player who made the winning move

    # Only switch turns when animations complete and turn is pending
    if not moving_blobs and hasattr(game, 'turn_pending') and game.turn_pending:
        game.current_player = BLUE if game.current_player == RED else RED
        game.turn_pending = False

def handle_powerup(game, row, col, moving_blobs):
    color = game.current_player
    powerup_type = game.grid[row][col].powerup

    if powerup_type == POWERUP_STAR:
        # Store cells with powerups to process after the star effect
        powerup_cells = []
        # Process the column first
        for r in range(GRID_ROWS):
            if not isinstance(game.grid[r][col], HQCell):
                # Store cells with powerups for later processing
                if game.grid[r][col].has_powerup():
                    powerup_cells.append((r, col))

                # Only add dot if cell is empty, same color, or not near critical
                if (game.grid[r][col].is_empty() or 
                    game.grid[r][col].color == color or 
                    not game.is_near_critical(r, col)):
                    # Don't add dot if enemy color
                    if game.grid[r][col].color is None or game.grid[r][col].color == color:
                        game.grid[r][col].color = color
                        game.grid[r][col].dots += 1

        # Now process all found powerups
        for r, c in powerup_cells:
            if game.grid[r][c].has_powerup():  # Check again in case it was already processed
                temp_powerup = game.grid[r][c].powerup
                game.grid[r][c].powerup = None
                if temp_powerup == POWERUP_STAR:
                    # Recursively handle additional stars
                    handle_powerup(game, r, c, moving_blobs)
                elif temp_powerup == POWERUP_HEART:  # Handle heart powerup
                    if color == RED:
                        if game.red_hq_health < HQ_HEALTH:
                            game.red_hq_health += 1
                        else:
                            game.blue_hq_health -= 1
                            game.add_explosion(BLUE_HQ_POS[0], BLUE_HQ_POS[1], BLUE)
                            if game.blue_hq_health <= 0:
                                game.game_over = True
                                print('punane on game_winner')
                                game.winner = RED
                    else:  # BLUE
                        if game.blue_hq_health < HQ_HEALTH:
                            game.blue_hq_health += 1
                        else:
                            game.red_hq_health -= 1
                            game.add_explosion(RED_HQ_POS[0], RED_HQ_POS[1], RED)
                            if game.red_hq_health <= 0:
                                game.game_over = True
                                print('sinine on game_winner')
                                game.winner = BLUE

    elif powerup_type == POWERUP_HEART:
        if color == RED:
            if game.red_hq_health < HQ_HEALTH:
                game.red_hq_health += 1
            else:
                game.blue_hq_health -= 1
                game.add_explosion(BLUE_HQ_POS[0], BLUE_HQ_POS[1], BLUE)
                if game.blue_hq_health <= 0:
                    game.game_over = True
                    game.winner = RED
        else:  # BLUE
            if game.blue_hq_health < HQ_HEALTH:
                game.blue_hq_health += 1
            else:
                game.red_hq_health -= 1
                game.add_explosion(RED_HQ_POS[0], RED_HQ_POS[1], RED)
                if game.red_hq_health <= 0:
                    game.game_over = True
                    game.winner = BLUE

def make_move(game, row, col, moving_blobs):
    if game.game_over or not game.is_valid_move(row, col) or moving_blobs:
        return False

    cell = game.grid[row][col]
    if cell.has_powerup():
        handle_powerup(game, row, col, moving_blobs)
        cell.powerup = None
    else:
        if game.add_dot_to_cell(row, col, game.current_player):
            chain_reaction(game, row, col, moving_blobs)
    game.turns_played += 1

    if game.turns_played % int(1/POWERUP_SPAWN_CHANCE) == 0:
        game.spawn_powerup()

    # If there are no animations, switch turns immediately
    if not moving_blobs:
        game.current_player = BLUE if game.current_player == RED else RED
    else:
        # Set a flag to switch turns after animations complete
        game.turn_pending = True
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
