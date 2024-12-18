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
SHAKE_AMPLITUDE = 3
SHAKE_SPEED = 10
HQ_HEALTH = 5
RED_HQ_POS = (0, GRID_COLS // 2)
BLUE_HQ_POS = (GRID_ROWS - 1, GRID_COLS // 2)
POWERUP_SPAWN_CHANCE = 1 / (5 + random.random() * 2)
POWERUP_STAR = "star"
POWERUP_HEART = "heart"
MAX_POWERUP_SPAWNS = 20  # Maximum number of powerups that can spawn in a game
EXPLOSION_DURATION = 0.5  # seconds
EXPLOSION_PARTICLES = 600

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
pygame.display.set_caption("Ahelreaktsioon")

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
        for _ in range(EXPLOSION_PARTICLES):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 5)
            self.particles.append({
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'size': random.uniform(2, 4)
            })

    def draw(self, window):
        current_time = time.time()
        progress = (current_time - self.start_time) / EXPLOSION_DURATION
        
        if progress >= 1:
            return True

        for particle in self.particles:
            particle_x = self.x + particle['dx'] * progress * CELL_SIZE
            particle_y = self.y + particle['dy'] * progress * CELL_SIZE
            size = particle['size'] * (1 - progress)
            pygame.draw.circle(window, self.color, 
                             (int(particle_x), int(particle_y)), 
                             int(size))
        return False

class Game:
    def __init__(self):
        self.grid = [[Cell() for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.current_player = RED
        self.game_over = False
        self.winner = None
        self.turns_played = 0
        self.red_hq_health = HQ_HEALTH
        self.blue_hq_health = HQ_HEALTH
        self.powerup_spawns = 0  # Add this line to track number of powerups spawned
        self.explosions: List[Explosion] = []

        red_row, red_col = RED_HQ_POS
        blue_row, blue_col = BLUE_HQ_POS
        self.grid[red_row][red_col] = HQCell(RED, self.red_hq_health)
        self.grid[blue_row][blue_col] = HQCell(BLUE, self.blue_hq_health)

    def get_all_neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < GRID_ROWS and 0 <= new_col < GRID_COLS:
                    neighbors.append((new_row, new_col))
        return neighbors

    def is_valid_move(self, row: int, col: int) -> bool:
        if not (0 <= row < GRID_ROWS and 0 <= col < GRID_COLS):
            return False
        if (row, col) in [RED_HQ_POS, BLUE_HQ_POS]:
            return False

        # Allow placing in HQ row
        if self.current_player == RED and row == RED_HQ_POS[0]:
            return True
        if self.current_player == BLUE and row == BLUE_HQ_POS[0]:
            return True

        if self.turns_played < 2:
            if self.current_player == RED:
                return row == 1
            else:
                return row == GRID_ROWS - 2
        if not self.grid[row][col].is_empty() and self.grid[row][col].color == self.current_player:
            return True
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
        if (row in [0, GRID_ROWS - 1]) and (col in [0, GRID_COLS - 1]):
            return 2
        if row in [0, GRID_ROWS - 1] or col in [0, GRID_COLS - 1]:
            return 3
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

    def chain_reaction(game, row, col, moving_blobs):
        if game.grid[row][col].dots >= game.get_critical_mass(row, col):
            color = game.grid[row][col].color
            game.grid[row][col].clear()

            for neighbor_row, neighbor_col in game.get_neighbors(row, col):
                start_pos = (col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2)
                end_pos = (neighbor_col * CELL_SIZE + CELL_SIZE // 2, neighbor_row * CELL_SIZE + CELL_SIZE // 2)

                # Check for powerup *before* adding the moving blob
                if game.grid[neighbor_row][neighbor_col].has_powerup():
                    original_player = game.current_player
                    game.current_player = color # Set the current player to the color of the chain reaction
                    handle_powerup(game, neighbor_row, neighbor_col, moving_blobs)
                    game.current_player = original_player # Reset the current player
                    game.grid[neighbor_row][neighbor_col].powerup = None # Clear the powerup

                else:
                    moving_blobs.append(MovingBlob(start_pos, end_pos, color, time.time()))


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
    dot_positions = []

    if cell.dots == 1:
        dot_positions = [(0, 0)]
    elif cell.dots == 2:
        dot_positions = [(-1.5, 0), (1.5, 0)]
    elif cell.dots == 3:
        dot_positions = [(0, -1.5), (-1.5, 1), (1.5, 1)]

    for dx, dy in dot_positions:
        x = center_x + dx * DOT_RADIUS + shake_offset_x
        y = center_y + dy * DOT_RADIUS + shake_offset_y
        pygame.draw.circle(window, cell.color, (int(x), int(y)), DOT_RADIUS)

def draw_powerup(window, powerup_type, center_x, center_y, angle):
    size = DOT_RADIUS * 2
    if powerup_type == POWERUP_STAR:
        points = []
        for i in range(5):
            angle_rad = math.radians(angle + i * 72)
            x = center_x + size * math.cos(angle_rad)
            y = center_y + size * math.sin(angle_rad)
            points.append((x, y))
        pygame.draw.polygon(window, GREEN, points, 0)
    elif powerup_type == POWERUP_HEART:
        points = [
            (center_x, center_y + size/2),  # bottom point
            (center_x - size/2, center_y - size/4),  # left point
            (center_x, center_y - size),  # top point
            (center_x + size/2, center_y - size/4),  # right point
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

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x = col * CELL_SIZE
            y = row * CELL_SIZE
            pygame.draw.rect(WINDOW, GRAY, (x, y, CELL_SIZE, CELL_SIZE), 1)

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

    if game.game_over:
        font = pygame.font.Font(None, 74)
        winner_color = "Punane" if game.winner == RED else "Sinine"
        text = font.render(f"{winner_color} võitis!", True, winner_text_color)
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        WINDOW.blit(text, text_rect)

    for (row, col), color, health in [(RED_HQ_POS, RED, game.red_hq_health), (BLUE_HQ_POS, BLUE, game.blue_hq_health)]:
        x = col * CELL_SIZE
        y = row * CELL_SIZE
        pygame.draw.rect(WINDOW, color, (x, y, CELL_SIZE, CELL_SIZE))

        font = pygame.font.Font(None, 36)
        text = font.render(str(health), True, BLACK)
        text_rect = text.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
        WINDOW.blit(text, text_rect)

    # Draw explosions
    completed_explosions = []
    for explosion in game.explosions:
        if explosion.draw(WINDOW):
            completed_explosions.append(explosion)
    
    # Remove completed explosions
    for explosion in completed_explosions:
        game.explosions.remove(explosion)

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

    if not game.game_over and game.check_winner():
        game.game_over = True
        game.winner = RED if game.current_player == BLUE else BLUE

    for blob in moving_blobs:
        if blob.update_position(current_time):
            completed_blobs.append(blob)
            col = int(blob.end_pos[0] // CELL_SIZE)
            row = int(blob.end_pos[1] // CELL_SIZE)
            
            # Add dot and trigger chain reaction only if there is no powerup
            if not game.grid[row][col].has_powerup():
                if game.add_dot_to_cell(row, col, blob.color):
                    cells_to_check.add((row, col))

    for blob in completed_blobs:
        moving_blobs.remove(blob)

    for row, col in cells_to_check:
        chain_reaction(game, row, col, moving_blobs)

def handle_powerup(game, row, col, moving_blobs):
    """Käsitle võimendi efekte"""
    color = game.current_player
    powerup_type = game.grid[row][col].powerup

    if powerup_type == POWERUP_STAR:
        powerup_cells = []
        for r in range(GRID_ROWS):
            if not isinstance(game.grid[r][col], HQCell):
                if game.grid[r][col].has_powerup():
                    powerup_cells.append((r, col))

                if game.grid[r][col].is_empty() or game.grid[r][col].color == color:
                    game.grid[r][col].color = color
                    game.grid[r][col].dots += 1

        for r, c in powerup_cells:
            if game.grid[r][c].has_powerup():
                temp_powerup = game.grid[r][c].powerup
                game.grid[r][c].powerup = None
                if temp_powerup == POWERUP_HEART:
                    opponent_color = BLUE if color == RED else RED
                    if opponent_color == RED:
                        if game.red_hq_health < HQ_HEALTH:
                            game.red_hq_health += 1
                    else:
                        if game.blue_hq_health < HQ_HEALTH:
                            game.blue_hq_health += 1

    elif powerup_type == POWERUP_HEART:
        opponent_color = BLUE if color == RED else RED
        if opponent_color == RED:
            if game.red_hq_health < HQ_HEALTH:
                game.red_hq_health += 1
        else:
            if game.blue_hq_health < HQ_HEALTH:
                game.blue_hq_health += 1

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

    if game.turns_played % int(1/POWERUP_SPAWN_CHANCE) == 0 :
        game.spawn_powerup()

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
