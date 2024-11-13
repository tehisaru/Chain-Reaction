"""Chain Reaction mäng - PEP 8 versioon."""

import math
import sys
import time
from typing import List, Tuple

import pygame


# Pygame initsialiseeerimine
pygame.init()
# Põhikonstandid
WINDOW_WIDTH = 700
WINDOW_HEIGHT = 900
GRID_COLS = 7
GRID_ROWS = 9
CELL_SIZE = min(
    WINDOW_WIDTH // GRID_COLS,
    WINDOW_HEIGHT // GRID_ROWS
)  # Arvutame ruudu suuruse
DOT_RADIUS = CELL_SIZE // 6  # Täpi raadius on 1/6 ruudu suurusest
SHAKE_AMPLITUDE = 3  # Värisemise amplituud
SHAKE_SPEED = 10    # Värisemise kiirus

# Värvid
BLACK = (0, 0, 0)
RED = (153, 0, 0)      # Punase mängija värv
BLUE = (0, 153, 180)   # Sinise mängija värv
PASTEL_RED = (255, 204, 204)    # Taustavärv punase mängija käigu ajal
PASTEL_BLUE = (204, 255, 255)   # Taustavärv sinise mängija käigu ajal
GRAY = (200, 200, 200)

# Akna loomine
WINDOW = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Ahelreaktsioon")


class Cell:
    """Mängulaua ühe ruudu klass."""

    def __init__(self):
        """Teeb tühja ruudu."""
        self.dots = 0      # Täppide arv ruudus
        self.color = None  # ruudu värv (punane või sinine)

    def is_empty(self) -> bool:
        """Tagastab True, kui ruut on tühi."""
        return self.dots == 0

    def add_dot(self, color: Tuple[int, int, int]):
        """Lisab ruutu ühe täpi."""
        self.dots += 1
        self.color = color

    def clear(self):
        """Tühjendab ruudu."""
        self.dots = 0
        self.color = None


class Game:
    """Mängu põhiloogika klass."""

    def __init__(self):
        """Alustab uue mängu."""
        # Loome mängulaua kui 2D pinna Cell objektidest
        self.grid = [[Cell() for _ in range(GRID_COLS)] 
                    for _ in range(GRID_ROWS)]
        self.current_player = RED  # Punane alustab
        self.game_over = False
        self.winner = None
        self.turns_played = 0

    def is_valid_move(self, row: int, col: int) -> bool:
        """Kontrollib, kas käik on lubatud."""
        # Kontrollime, kas käik on lubatud:
        # 1. Peab olema mänguvälja piirides
        # 2. ruut peab olema tühi või sama värvi
        if not (0 <= row < GRID_ROWS and 0 <= col < GRID_COLS):
            return False
        return (self.grid[row][col].is_empty() or 
                self.grid[row][col].color == self.current_player)

    def get_critical_mass(self, row: int, col: int) -> int:
        """Tagastab ruudu kriitilise massi."""
        # Määrame kriitilise massi vastavalt ruudu asukohale:
        # - Nurgad: 2 täppi
        # - Ääred: 3 täppi
        # - Keskmine ala: 4 täppi
        if (row in [0, GRID_ROWS-1]) and (col in [0, GRID_COLS-1]):
            return 2  # Nurgaruudud
        if row in [0, GRID_ROWS-1] or col in [0, GRID_COLS-1]:
            return 3  # Ääreruudud
        return 4  # Keskruudud

    def is_near_critical(self, row: int, col: int) -> bool:
        """Kontrollib, kas ruut on ühe täpi kaugusel plahvatusest."""
        if self.grid[row][col].is_empty():
            return False
        return (self.grid[row][col].dots == 
                self.get_critical_mass(row, col) - 1)

    def get_neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Tagastab ruudu naabrite koordinaadid."""
        neighbors = []
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < GRID_ROWS and 0 <= new_col < GRID_COLS:
                neighbors.append((new_row, new_col))
        return neighbors

    def add_dot_to_cell(self, row: int, col: int, 
                       color: Tuple[int, int, int]) -> bool:
        """Lisab täpi ruutu ja kontrollib, kas tekib plahvatus.
        
        Tagastab True, kui ruudus on nüüd piisavalt täppe plahvatuseks."""
        self.grid[row][col].color = color
        self.grid[row][col].dots += 1
        return self.grid[row][col].dots >= self.get_critical_mass(row, col)

    def remove_dots_from_cell(self, row: int, col: int) -> Tuple[int, Tuple]:
        """Eemaldab kõik täpid ruudust.
        
        Tagastab eemaldatud täppide arvu ja värvi, mida kasutatakse
        plahvatuse animatsiooni jaoks."""
        dots = self.grid[row][col].dots
        color = self.grid[row][col].color
        self.grid[row][col].clear()
        return dots, color

    def chain_reaction(self, row: int, col: int):
        """Käivitab ahelreaktsiooni, kui ruudus on piisavalt täppe.
        
        Kui ruut plahvatab:
        1. Eemaldab täpid plahvatavast ruudust
        2. Lisab täpid kõikidesse naaberruutudesse
        3. Kontrollib rekursiivselt, kas tekib uusi plahvatusi"""
        if self.grid[row][col].dots >= self.get_critical_mass(row, col):
            color = self.grid[row][col].color
            self.grid[row][col].clear()
            
            # Liiguta täpid naaberruutudesse
            for neighbor_row, neighbor_col in self.get_neighbors(row, col):
                self.grid[neighbor_row][neighbor_col].color = color
                self.grid[neighbor_row][neighbor_col].dots += 1
                self.chain_reaction(neighbor_row, neighbor_col)

    def make_move(self, row: int, col: int) -> bool:
        """Teeb mängija käigu antud positsioonile.
        
        1. Kontrollib, kas käik on lubatud
        2. Lisab täpi valitud ruutu
        3. Käivitab võimaliku ahelreaktsiooni
        4. Kontrollib võitu
        5. Vahetab mängijat
        
        Tagastab True, kui käik õnnestus."""
        if self.game_over or not self.is_valid_move(row, col):
            return False
        
        self.grid[row][col].add_dot(self.current_player)
        self.chain_reaction(row, col)
        self.turns_played += 1
        
        # Kontrolli võitu alates teisest käigust
        if self.turns_played > 1 and self.check_winner():
            self.game_over = True
            self.winner = self.current_player
        else:
            self.current_player = BLUE if self.current_player == RED else RED
        return True

    def check_winner(self) -> bool:
        """Kontrollib, kas keegi on võitnud.
        
        Võit saavutatakse, kui:
        1. Mängualal on täppe
        2. Kõik täpid on sama värvi
        3. Mõlemad mängijad on teinud vähemalt ühe käigu"""
        colors = set()
        has_dots = False
        
        # Kogu info kõikide täppide kohta
        for row in self.grid:
            for cell in row:
                if not cell.is_empty():
                    colors.add(cell.color)
                    has_dots = True
        
        return has_dots and len(colors) == 1 and self.turns_played >= 2

    def get_all_dots(self) -> List[Tuple[int, int]]:
        """Tagastab kõikide täppide asukohad laual.
        
        Kasutatakse täppide joonistamiseks."""
        dots = []
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                if not self.grid[row][col].is_empty():
                    dots.append((row, col))
        return dots


def draw_dot_pattern(
    window: pygame.Surface,
    cell: Cell,
    center_x: int,
    center_y: int,
    shake_x: float = 0,
    shake_y: float = 0
):
    """Joonistab täppide mustri vastavalt nende arvule lahtris.
    
    Täppide asetus:
    - 1 täpp: keskel
    - 2 täppi: horisontaalselt
    - 3 täppi: kolmnurgas"""
    dot_positions = []
    
    if cell.dots == 1:
        dot_positions = [(0, 0)]  # Üks täpp keskel
    elif cell.dots == 2:
        dot_positions = [(-1.5, 0), (1.5, 0)]  # Kaks täppi horisontaalselt
    elif cell.dots == 3:
        dot_positions = [
            (0, -1.5),     # Ülemine täpp
            (-1.5, 1),     # Alumine vasak
            (1.5, 1)       # Alumine parem
        ]
    
    # Joonista iga täpp arvutatud positsioonile
    for dx, dy in dot_positions:
        x = center_x + dx * DOT_RADIUS + shake_x
        y = center_y + dy * DOT_RADIUS + shake_y
        pygame.draw.circle(window, cell.color, (int(x), int(y)), DOT_RADIUS)


def draw_game_state(game: Game):
    """Joonistab mänguseisu.
    
    1. Määrab taustavärvi vastavalt aktiivsele mängijale
    2. Joonistab mängulaua ruudustiku
    3. Joonistab täpid koos värisemisefektiga
    4. Näitab võitja teksti, kui mäng on läbi"""
    # Määra taustavärv
    if game.game_over:
        background_color = PASTEL_RED if game.winner == RED else PASTEL_BLUE
        winner_text_color = RED if game.winner == RED else BLUE
    else:
        background_color = PASTEL_RED if game.current_player == RED else PASTEL_BLUE
    
    WINDOW.fill(background_color)
    current_time = time.time()
    
    # Joonista ruudustik
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x = col * CELL_SIZE
            y = row * CELL_SIZE
            pygame.draw.rect(WINDOW, GRAY, (x, y, CELL_SIZE, CELL_SIZE), 1)
    
    # Joonista täpid
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cell = game.grid[row][col]
            if not cell.is_empty():
                center_x = col * CELL_SIZE + CELL_SIZE // 2
                center_y = row * CELL_SIZE + CELL_SIZE // 2
                
                # Lisa värisemisefekt vajadusel
                shake_x = shake_y = 0
                if game.is_near_critical(row, col):
                    shake_x = math.sin(current_time * SHAKE_SPEED) * SHAKE_AMPLITUDE
                    shake_y = math.cos(current_time * SHAKE_SPEED) * SHAKE_AMPLITUDE
                
                draw_dot_pattern(WINDOW, cell, center_x, center_y, shake_x, shake_y)
    
    # Näita võitja teksti
    if game.game_over:
        font = pygame.font.Font(None, 74)
        winner_name = "Punane" if game.winner == RED else "Sinine"
        text = font.render(f"{winner_name} Võidab!", True, winner_text_color)
        text_rect = text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 50))
        WINDOW.blit(text, text_rect)


class MovingDot:
    """Liikuva täpi klass animatsioonide jaoks.
    
    Haldab:
    - Täpi asukohta
    - Liikumise animatsiooni
    - Animatsiooni ajastust"""

    def __init__(
        self,
        start_pos: Tuple[float, float],
        end_pos: Tuple[float, float],
        color: Tuple[int, int, int],
        start_time: float,
        duration: float = 0.3
    ):
        """Loob uue liikuva täpi määratud algus- ja lõpp-positsiooniga."""
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.color = color
        self.start_time = start_time
        self.duration = duration
        self.current_pos = start_pos

    def update_position(self, current_time: float) -> bool:
        """Uuendab täpi positsiooni vastavalt möödunud ajale.
        
        Tagastab True, kui animatsioon on lõppenud."""
        elapsed_time = current_time - self.start_time
        if elapsed_time >= self.duration:
            self.current_pos = self.end_pos
            return True
        
        # Arvuta uus positsioon
        progress = elapsed_time / self.duration
        self.current_pos = (
            self.start_pos[0] + progress * (self.end_pos[0] - self.start_pos[0]),
            self.start_pos[1] + progress * (self.end_pos[1] - self.start_pos[1])
        )
        return False


def draw_moving_dots(window: pygame.Surface, moving_dots: List[MovingDot]):
    """Joonistab kõik liikuvad täpid nende praegustes asukohtades.
    
    Kasutatakse plahvatuse animatsiooni näitamiseks."""
    for dot in moving_dots:
        pygame.draw.circle(
            window,
            dot.color,
            (int(dot.current_pos[0]), int(dot.current_pos[1])),
            DOT_RADIUS
        )


def chain_reaction(game: Game, row: int, col: int, moving_dots: List[MovingDot]):
    """Käivitab ahelreaktsiooni koos animatsioonidega.
    
    1. Kontrollib, kas ruudus on piisavalt täppe plahvatuseks
    2. Eemaldab täpid plahvatavast ruudust
    3. Loob animatsioonid täppide liikumiseks naaberruutudesse"""
    if game.grid[row][col].dots >= game.get_critical_mass(row, col):
        # Eemalda täpid plahvatavast ruudust
        dots, color = game.remove_dots_from_cell(row, col)
        
        # Loo animatsioon iga naabri jaoks
        start_pos = (
            col * CELL_SIZE + CELL_SIZE // 2,
            row * CELL_SIZE + CELL_SIZE // 2
        )
        
        for neighbor_row, neighbor_col in game.get_neighbors(row, col):
            end_pos = (
                neighbor_col * CELL_SIZE + CELL_SIZE // 2,
                neighbor_row * CELL_SIZE + CELL_SIZE // 2
            )
            moving_dots.append(
                MovingDot(start_pos, end_pos, color, time.time())
            )


def update_game(game: Game, moving_dots: List[MovingDot]):
    """Uuendab mängu olekut ja animatsioone.
    
    1. Kontrollib võitjat
    2. Uuendab liikuvate täppide asukohti
    3. Käivitab uusi plahvatusi vajadusel"""
    if game.turns_played == 0:
        return

    current_time = time.time()
    completed_dots = []
    cells_to_check = set()
    
    # Kontrolli võitu
    if not game.game_over and game.check_winner():
        game.game_over = True
        game.winner = RED if game.current_player == BLUE else BLUE
    
    # Uuenda täppide asukohti
    for dot in moving_dots:
        if dot.update_position(current_time):
            completed_dots.append(dot)
            # Arvuta sihtruut
            col = int(dot.end_pos[0] // CELL_SIZE)
            row = int(dot.end_pos[1] // CELL_SIZE)
            # Kontrolli, kas tekib plahvatus
            if game.add_dot_to_cell(row, col, dot.color):
                cells_to_check.add((row, col))
    
    # Eemalda lõpetanud animatsioonid
    for dot in completed_dots:
        moving_dots.remove(dot)
    
    # Käivita uued plahvatused
    for row, col in cells_to_check:
        chain_reaction(game, row, col, moving_dots)


def make_move(game: Game, row: int, col: int, 
             moving_dots: List[MovingDot]) -> bool:
    """Teeb mängija käigu koos animatsioonidega.
    
    1. Kontrollib, kas käik on lubatud
    2. Lisab täpi valitud ruutu
    3. Käivitab plahvatuse animatsiooni vajadusel
    4. Vahetab mängijat
    
    Tagastab True, kui käik õnnestus."""
    # Kontrolli, kas käik on lubatud
    if game.game_over or not game.is_valid_move(row, col) or moving_dots:
        return False
    
    # Lisa täpp ja käivita võimalik plahvatus
    if game.add_dot_to_cell(row, col, game.current_player):
        chain_reaction(game, row, col, moving_dots)
    
    # Lõpeta käik
    game.turns_played += 1
    game.current_player = BLUE if game.current_player == RED else RED
    return True


def main():
    """Mängu põhiprogramm.
    
    1. Loob uue mängu
    2. Käivitab mängutsükli:
       - Töötleb sisendeid (hiireklõpsud, klahvivajutused)
       - Uuendab mängu olekut
       - Joonistab mänguseisu
       - Haldab kaadrisagedust"""
    game = Game()
    clock = pygame.time.Clock()
    moving_dots = []
    
    while True:
        # Töötle sündmusi
        for event in pygame.event.get():
            # Mängu sulgemine
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # Hiirekliki töötlemine
            if event.type == pygame.MOUSEBUTTONDOWN and not game.game_over:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                col = mouse_x // CELL_SIZE
                row = mouse_y // CELL_SIZE
                make_move(game, row, col, moving_dots)
            
            # Mängu taaskäivitamine R klahviga
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                game = Game()
                moving_dots.clear()
        
        # Uuenda ja joonista mängu
        update_game(game, moving_dots)
        draw_game_state(game)
        draw_moving_dots(WINDOW, moving_dots)
        pygame.display.flip()
        
        # Piira kaadrisagedust
        clock.tick(60)


if __name__ == "__main__":
    main()