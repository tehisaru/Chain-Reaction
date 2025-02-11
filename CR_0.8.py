"""
Chain Reaction mäng - lihtsustatud ja loetavam versioon.
Bugid: kui tekib infinate animation, ei kuulutata kunagi võitjat
"""

import math
import sys
import time
from typing import List, Tuple
import pygame

# Pygame initsialiseeerimine
pygame.init()
# Suurendame rekursiooni limiiti ahelreaktsioonide jaoks

# Akna seaded
WINDOW_WIDTH = 466
WINDOW_HEIGHT = 600

# Mängulaua seaded
GRID_COLS = 7
GRID_ROWS = 9

# Arvutame ruudu suuruse nii, et mängulaud mahuks aknasse
CELL_WIDTH = WINDOW_WIDTH // GRID_COLS
CELL_HEIGHT = WINDOW_HEIGHT // GRID_ROWS
CELL_SIZE = min(CELL_WIDTH, CELL_HEIGHT)

# Täpi suurus ja animatsiooni seaded
DOT_RADIUS = CELL_SIZE // 6
SHAKE_AMOUNT = 3
SHAKE_SPEED = 10
ANIMATION_DURATION = 0.3  # sekundites

# Mängijate värvid
RED = (153, 0, 0)
BLUE = (0, 153, 180)

# Taustavärvid
BACKGROUND_RED = (255, 204, 204)
BACKGROUND_BLUE = (204, 255, 255)
GRID_COLOR = (200, 200, 200)

# Akna loomine
GAME_WINDOW = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Chain Reaction Classic")


class Cell:
    """Mängulaua ühe ruudu klass."""

    def __init__(self):
        """Loob tühja ruudu."""
        self.dot_count = 0
        self.color = None

    def is_empty(self) -> bool:
        """Kontrollib, kas ruut on tühi."""
        return self.dot_count == 0

    def add_dot(self, player_color: Tuple[int, int, int]):
        """Lisab ruudusse ühe täpi."""
        self.dot_count += 1
        self.color = player_color

    def clear(self):
        """Eemaldab kõik täpid ruudust."""
        self.dot_count = 0
        self.color = None


class Game:
    """Mängu põhiloogika klass."""

    def __init__(self):
        """Alustab uue mängu."""
        self.chain_reaction_in_progress = False
        # Loome tühja mängulaua
        self.grid = []
        for _ in range(GRID_ROWS):
            row = [Cell() for _ in range(GRID_COLS)]
            self.grid.append(row)
        # Mängu oleku muutujad
        self.current_player = RED
        self.is_chain_reacting = False
        self.game_over = False
        self.winner = None
        self.turns_played = 0

    def is_valid_move(self, row: int, col: int) -> bool:
        """Kontrollib, kas käik on lubatud."""
        # Kontrolli, kas positsioon on mängulaua piirides
        if row < 0 or row >= GRID_ROWS:
            return False
        if col < 0 or col >= GRID_COLS:
            return False

        target_cell = self.grid[row][col]
        
        # Käik on lubatud, kui:
        # 1. ruut on tühi VÕI
        # 2. ruudus on sama värvi täpid
        return (target_cell.is_empty() or 
                target_cell.color == self.current_player)

    def get_critical_mass(self, row: int, col: int) -> int:
        """Tagastab ruudu plahvatamiseks vajaliku täppide arvu."""
        # Kontrolli, kas tegu on nurgaruuduga
        is_corner = (row in [0, GRID_ROWS-1] and 
                    col in [0, GRID_COLS-1])
        if is_corner:
            return 2

        # Kontrolli, kas tegu on ääreruuduga
        is_edge = (row in [0, GRID_ROWS-1] or 
                  col in [0, GRID_COLS-1])
        if is_edge:
            return 3

        # Tegu on tavalise ruuduga
        return 4
    
    def is_about_to_explode(self, row: int, col: int) -> bool:
        """Kontrollib, kas ruut on ühe täpi kaugusel plahvatusest."""
        cell = self.grid[row][col]
        
        if cell.is_empty():
            return False
            
        dots_needed_to_explode = self.get_critical_mass(row, col)
        return cell.dot_count == dots_needed_to_explode - 1

    def get_neighbor_positions(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Tagastab ruudu naabrite koordinaadid (üles, alla, vasakule, paremale)."""
        neighbor_positions = []
        possible_neighbors = [
            (row - 1, col),  # üles
            (row + 1, col),  # alla
            (row, col - 1),  # vasakule
            (row, col + 1)   # paremale
        ]
        
        for new_row, new_col in possible_neighbors:
            # Lisa naaber ainult siis, kui ta on mängulaua piirides
            if (0 <= new_row < GRID_ROWS and 
                0 <= new_col < GRID_COLS):
                neighbor_positions.append((new_row, new_col))
                
        return neighbor_positions

    def add_dot(self, row: int, col: int, color: Tuple[int, int, int]) -> bool:
        """Lisab täpi ruudusse ja tagastab True, kui tekib plahvatus."""
        target_cell = self.grid[row][col]
        target_cell.color = color
        target_cell.dot_count += 1
        
        dots_needed_to_explode = self.get_critical_mass(row, col)
        return target_cell.dot_count >= dots_needed_to_explode

    def remove_dots(self, row: int, col: int) -> Tuple[int, Tuple[int, int, int]]:
        """Eemaldab täpid ruudust ja tagastab nende arvu ja värvi."""
        cell = self.grid[row][col]
        dot_count = cell.dot_count
        dot_color = cell.color
        
        cell.clear()
        return dot_count, dot_color

    def trigger_chain_reaction(self, row: int, col: int):
        """Käivitab ahelreaktsiooni antud ruudus."""
        cell = self.grid[row][col]
        dots_needed_to_explode = self.get_critical_mass(row, col)
        
        # Kontrolli, kas ruudus on piisavalt täppe plahvatuseks
        if cell.dot_count < dots_needed_to_explode:
            return
            
        # Salvesta täppide värv enne ruudu tühjendamist
        exploding_color = cell.color
        cell.clear()
        
        # Levita täpid naaberruudutesse
        for neighbor_row, neighbor_col in self.get_neighbor_positions(row, col):
            neighbor = self.grid[neighbor_row][neighbor_col]
            neighbor.color = exploding_color
            neighbor.dot_count += 1
            
            # Kontrolli rekursiivselt, kas tekib uusi plahvatusi
            self.trigger_chain_reaction(neighbor_row, neighbor_col)

    def make_move(self, row: int, col: int) -> bool:
        """Teeb käigu antud positsioonile."""
        # Kontrolli, kas käik on lubatud
        if self.game_over:
            return False
        if not self.is_valid_move(row, col):
            return False
            
        # Lisa täpp valitud ruudusse
        target_cell = self.grid[row][col]
        target_cell.add_dot(self.current_player)
        self.is_chain_reacting = True
        # Käivita võimalik ahelreaktsioon
        self.trigger_chain_reaction(row, col)
        
        self.turns_played += 1
        
        # Kontrolli võitu alates teisest käigust

        self.current_player = BLUE if self.current_player == RED else RED
            
        return True

    def check_winner(self) -> bool:
        """Kontrollib, kas keegi on võitnud."""
        active_colors = set()
        dots_exist = False
        
        # Kontrolli kõiki ruutusid
        for row in self.grid:
            for cell in row:
                if not cell.is_empty():
                    active_colors.add(cell.color)
                    dots_exist = True
        
        # Võitja on selgunud kui:
        # 1. Laual on täppe
        # 2. Kõik täpid on sama värvi
        print(active_colors)
        only_one_color_left = len(active_colors) == 1
        
        return (dots_exist and 
                only_one_color_left)


    def get_dot_positions(self) -> List[Tuple[int, int]]:
        """Tagastab kõikide täppide asukohad laual."""
        dot_positions = []
        
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                if not self.grid[row][col].is_empty():
                    dot_positions.append((row, col))
                    
        return dot_positions
    
def draw_dot_pattern(
    window: pygame.Surface,
    cell: Cell,
    center_x: int,
    center_y: int,
    shake_x: float = 0,
    shake_y: float = 0
):
    """Joonistab täppide mustri vastavalt nende arvule lahtris."""
    # Määra täppide asukohad vastavalt nende arvule
    dot_positions = []
    
    if cell.dot_count == 1:
        # Üks täpp keskel
        dot_positions = [(0, 0)]
        
    elif cell.dot_count == 2:
        # Kaks täppi horisontaalselt
        spacing = 1.5 * DOT_RADIUS
        dot_positions = [
            (-spacing, 0),  # Vasak täpp
            (spacing, 0)    # Parem täpp
        ]
        
    elif cell.dot_count == 3:
        # Kolm täppi kolmnurgas
        spacing = 1.5 * DOT_RADIUS
        dot_positions = [
            (0, -spacing),      # Ülemine täpp
            (-spacing, spacing), # Alumine vasak
            (spacing, spacing)   # Alumine parem
        ]
    
    # Joonista iga täpp arvutatud positsioonile
    for offset_x, offset_y in dot_positions:
        # Lisa värisemisefekt põhipositsioonile
        final_x = center_x + offset_x + shake_x
        final_y = center_y + offset_y + shake_y
        
        pygame.draw.circle(
            window,
            cell.color,
            (int(final_x), int(final_y)),
            DOT_RADIUS
        )


def draw_game_state(game: Game):
    """Joonistab mänguseisu."""
    # Määra taustavärv vastavalt aktiivsele mängijale või võitjale
    if game.game_over:
        background_color = (
            BACKGROUND_RED if game.winner == RED else BACKGROUND_BLUE
        )
        winner_text_color = RED if game.winner == RED else BLUE
    else:
        background_color = (
            BACKGROUND_RED if game.current_player == RED else BACKGROUND_BLUE
        )
    
    # Joonista taust
    GAME_WINDOW.fill(background_color)
    
    # Joonista mängulaua ruudustik
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            # Arvuta lahtri positsioon
            cell_x = col * CELL_SIZE
            cell_y = row * CELL_SIZE
            
            # Joonista lahtri piirjoon
            pygame.draw.rect(
                GAME_WINDOW,
                GRID_COLOR,
                (cell_x, cell_y, CELL_SIZE, CELL_SIZE),
                1
            )
    
    # Joonista täpid koos värisemisefektiga
    current_time = time.time()
    
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cell = game.grid[row][col]
            
            if cell.is_empty():
                continue
                
            # Arvuta lahtri keskpunkt
            center_x = col * CELL_SIZE + CELL_SIZE // 2
            center_y = row * CELL_SIZE + CELL_SIZE // 2
            
            # Lisa värisemisefekt, kui lahter on plahvatuse lähedal
            shake_x = 0
            shake_y = 0
            
            if game.is_about_to_explode(row, col):
                # Arvuta värisemise suund trigonomeetriliselt
                shake_x = math.sin(current_time * SHAKE_SPEED) * SHAKE_AMOUNT
                shake_y = math.cos(current_time * SHAKE_SPEED) * SHAKE_AMOUNT
            
            # Joonista täpid
            draw_dot_pattern(
                GAME_WINDOW,
                cell,
                center_x,
                center_y,
                shake_x,
                shake_y
            )
    
    # Kui mäng on läbi, näita võitja teksti
    if game.game_over:
        font = pygame.font.Font(None, 74)
        winner_name = "Punane" if game.winner == RED else "Sinine"
        
        text_surface = font.render(
            f"{winner_name} Võidab!",
            True,
            winner_text_color
        )
        
        # Paiguta tekst ekraani keskele
        text_position = text_surface.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50)
        )
        
        GAME_WINDOW.blit(text_surface, text_position)


class MovingDot:
    """Liikuva täpi klass animatsioonide jaoks."""

    def __init__(
        self,
        start_pos: Tuple[float, float],
        end_pos: Tuple[float, float],
        color: Tuple[int, int, int],
        start_time: float,
        duration: float = ANIMATION_DURATION
    ):
        """Loob uue liikuva täpi."""
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.color = color
        self.start_time = start_time
        self.duration = duration
        self.current_pos = start_pos

    def update_position(self, current_time: float) -> bool:
        """Uuendab täpi positsiooni ja tagastab True, kui animatsioon on läbi."""
        elapsed_time = current_time - self.start_time
        
        # Kontrolli, kas animatsioon on lõppenud
        if elapsed_time >= self.duration:
            self.current_pos = self.end_pos
            return True
        
        # Arvuta, kui kaugel animatsioon on (0.0 kuni 1.0)
        progress = elapsed_time / self.duration
        
        # Arvuta uus positsioon
        start_x, start_y = self.start_pos
        end_x, end_y = self.end_pos
        
        current_x = start_x + (end_x - start_x) * progress
        current_y = start_y + (end_y - start_y) * progress
        
        self.current_pos = (current_x, current_y)
        return False
    
def draw_moving_dots(window: pygame.Surface, moving_dots: List[MovingDot]):
    """Joonistab kõik liikuvad täpid."""
    for dot in moving_dots:
        x_pos = int(dot.current_pos[0])
        y_pos = int(dot.current_pos[1])
        
        pygame.draw.circle(
            window,
            dot.color,
            (x_pos, y_pos),
            DOT_RADIUS
        )


def create_explosion_animation(
    game: Game,
    row: int,
    col: int,
    moving_dots: List[MovingDot]
):
    """Käivitab plahvatuse animatsiooni."""
    # Kontrolli, kas lahtris on piisavalt täppe plahvatuseks
    cell = game.grid[row][col]
    if cell.dot_count < game.get_critical_mass(row, col):
        return
        
    # Eemalda täpid plahvatavast lahtrist
    dot_count, dot_color = game.remove_dots(row, col)
    
    # Arvuta plahvatava lahtri keskpunkt
    start_x = col * CELL_SIZE + CELL_SIZE // 2
    start_y = row * CELL_SIZE + CELL_SIZE // 2
    start_pos = (start_x, start_y)
    
    # Loo animatsioon iga naabri jaoks
    for neighbor_row, neighbor_col in game.get_neighbor_positions(row, col):
        # Arvuta sihtlahtri keskpunkt
        end_x = neighbor_col * CELL_SIZE + CELL_SIZE // 2
        end_y = neighbor_row * CELL_SIZE + CELL_SIZE // 2
        end_pos = (end_x, end_y)
        
        # Lisa uus liikuv täpp
        new_dot = MovingDot(
            start_pos=start_pos,
            end_pos=end_pos,
            color=dot_color,
            start_time=time.time()
        )
        moving_dots.append(new_dot)


def update_game_state(game: Game, moving_dots: List[MovingDot]):
    """Uuendab mängu olekut ja animatsioone."""
    current_time = time.time()
    finished_dots = []
    cells_to_check = set()
    
    # Uuenda kõiki liikuvaid täppe
    for dot in moving_dots:
        if dot.update_position(current_time):
            finished_dots.append(dot)
            target_col = int(dot.end_pos[0] // CELL_SIZE)
            target_row = int(dot.end_pos[1] // CELL_SIZE)
            
            if game.add_dot(target_row, target_col, dot.color):
                cells_to_check.add((target_row, target_col))
    
    for dot in finished_dots:
        moving_dots.remove(dot)
    
    # Käivita uued plahvatused
    game.is_chain_reacting = bool(cells_to_check)
    for row, col in cells_to_check:
        create_explosion_animation(game, row, col, moving_dots)
    
    # Kontrolli võitjat PÄRAST kõiki reaktsioone
    if not moving_dots and not game.is_chain_reacting and game.check_winner() and game.turns_played > 1:
        game.game_over = True
        game.winner = next((c for c in [RED, BLUE] if any(cell.color == c for row in game.grid for cell in row)), None)

def handle_player_move(
    game: Game,
    row: int,
    col: int,
    moving_dots: List[MovingDot]
) -> bool:
    """Töötleb mängija käigu ja tagastab True, kui käik õnnestus."""
    # Kontrolli, kas käik on lubatud
    if game.game_over:
        return False
    if not game.is_valid_move(row, col):
        return False
    if moving_dots:  # Ära luba uut käiku, kui animatsioonid pole lõppenud
        return False
    
    # Lisa täpp valitud lahtrisse
    if game.add_dot(row, col, game.current_player):
        create_explosion_animation(game, row, col, moving_dots)
    
    # Lõpeta käik
    game.turns_played += 1
    game.current_player = BLUE if game.current_player == RED else RED
    return True


def main():
    """Mängu põhiprogramm."""
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
                # Arvuta klikitud lahtri koordinaadid
                mouse_x, mouse_y = pygame.mouse.get_pos()
                clicked_col = mouse_x // CELL_SIZE
                clicked_row = mouse_y // CELL_SIZE
                
                handle_player_move(game, clicked_row, clicked_col, moving_dots)
            
            # Mängu taaskäivitamine R klahviga
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                game = Game()
                moving_dots.clear()
        
        # Uuenda mängu olekut
        update_game_state(game, moving_dots)
        
        # Joonista mäng
        draw_game_state(game)
        draw_moving_dots(GAME_WINDOW, moving_dots)
        
        # Uuenda ekraani
        pygame.display.flip()
        
        # Piira kaadrisagedust
        clock.tick(60)


if __name__ == "__main__":
    main()
