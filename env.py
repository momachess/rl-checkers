import pygame
import random

import gymnasium as gym

from typing import Optional

BOARD_SIZE = 8
SQUARE_SIZE = 80
PIECE_SIZE = 32
KING_SIZE = 16

WHITE        = (255, 255, 255)
BLACK        = (  0,   0,   0)
LIGHTBROWN   = (200, 157, 124)
DARKBROWN    = ( 78,  53,  36)
HILIGHT_MOVE = (  0, 255,   0)
HILIGHT_JUMP = (255,   0,   0)
KING         = (255, 255,   0)


class Piece:
    def __init__(self, row, col, color):
        self.row = row
        self.col = col
        self.color = color
        self.king = False

    def render(self, surf):
        if self.color == 'empty':
            return
        color = WHITE
        if self.color == 'black':
            color = BLACK
        pygame.draw.circle(surf, color, [self.col * SQUARE_SIZE + SQUARE_SIZE // 2, self.row * SQUARE_SIZE + SQUARE_SIZE // 2], PIECE_SIZE)
        if self.king:
            pygame.draw.circle(surf, KING, [self.col * SQUARE_SIZE + SQUARE_SIZE // 2, self.row * SQUARE_SIZE + SQUARE_SIZE // 2], KING_SIZE)


class Board:
    def __init__(self):
        
        self.turn = 'black'
        self.end_game = False

        self.white_pieces = 12
        self.black_pieces = 12

        self.pieces = [[], [], [], [], [], [], [], []]
        self._setup()

        self.moves = []
        self.jumps = []

    def step(self):
        self._find_valid_moves()
        if self.jumps != []:
            sel = random.randint(0, len(self.jumps) - 1)
            self._make_jump(self.jumps[sel][0], self.jumps[sel][1], self.jumps[sel][2], self.jumps[sel][3], self.jumps[sel][4], self.jumps[sel][5])
            while True:
                if sel < len(self.jumps) - 1:
                    sel += 1
                    if self.jumps[sel][6] == True:
                        self._make_jump(self.jumps[sel][0], self.jumps[sel][1], self.jumps[sel][2], self.jumps[sel][3], self.jumps[sel][4], self.jumps[sel][5])
                    else:
                        break
                else:
                    break
            self._promote(self.jumps[sel][4], self.jumps[sel][5])
            if self.turn == 'white':
                self.black_pieces -= 1
            else:
                self.white_pieces -= 1
        elif self.moves != []:
            sel = random.randint(0, len(self.moves)-1)
            self._make_move(self.moves[sel][0], self.moves[sel][1], self.moves[sel][2], self.moves[sel][3])
            self._promote(self.moves[sel][2], self.moves[sel][3])

        self.end = False
        if self.turn == 'white' and self.black_pieces == 0:
            self.end = True
        if self.turn == 'black' and self.white_pieces == 0:
            self.end = True
        if self.moves == [] and self.jumps == []:
            self.end = True

        if self.turn == 'white':
            self.turn = 'black'
        else:
            self.turn = 'white'

        return self.end

    def reset(self):
        self.turn = 'black'
        self.end_game = False

        self.white_pieces = 12
        self.black_pieces = 12

        self.pieces = [[], [], [], [], [], [], [], []]
        self._setup()

        self.moves = []
        self.jumps = []

    def render(self, surf):
        surf.fill(DARKBROWN)
        for row in range(BOARD_SIZE):
            for col in range(row % 2, BOARD_SIZE, 2):
                pygame.draw.rect(surf, LIGHTBROWN, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        
        for move in self.moves:
            pygame.draw.rect(surf, HILIGHT_MOVE, (move[3]*SQUARE_SIZE + 4, move[2]*SQUARE_SIZE + 4, SQUARE_SIZE - 8, SQUARE_SIZE - 8))
        for jump in self.jumps:
            pygame.draw.rect(surf, HILIGHT_JUMP, (jump[5]*SQUARE_SIZE + 4, jump[4]*SQUARE_SIZE + 4, SQUARE_SIZE - 8, SQUARE_SIZE - 8))

        for row in self.pieces:
            for col in range(BOARD_SIZE):
                row[col].render(surf)

    def _setup(self):
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                self.pieces[row].append(Piece(row, col, 'empty'))
        for row in range(3):
            for col in range(BOARD_SIZE):
                if (row + col) % 2 == 1:
                    self.pieces[row][col].color = 'black'
        for row in range(5, BOARD_SIZE, 1):
            for col in range(BOARD_SIZE):
                if (row + col) % 2 == 1:
                    self.pieces[row][col].color = 'white'

    def _make_move(self, old_row, old_col, new_row, new_col):
        self.pieces[new_row][new_col].color = self.pieces[old_row][old_col].color
        self.pieces[new_row][new_col].king = self.pieces[old_row][old_col].king
        self.pieces[old_row][old_col].color = 'empty'
        self.pieces[old_row][old_col].king = False

    def _make_jump(self, old_row, old_col, via_row, via_col, new_row, new_col):
        self.pieces[new_row][new_col].color = self.pieces[old_row][old_col].color
        self.pieces[new_row][new_col].king = self.pieces[old_row][old_col].king
        self.pieces[old_row][old_col].color = 'empty'
        self.pieces[old_row][old_col].king = 'empty'
        self.pieces[via_row][via_col].color = 'empty'
        self.pieces[via_row][via_col].king = 'empty'

    def _promote(self, row, col):
        if (self.pieces[row][col].color == 'white') and (row == 0):
            self.pieces[row][col].king = True
        if (self.pieces[row][col].color == 'black') and (row == 7):
            self.pieces[row][col].king = True

    def _find_valid_moves(self):
        self.moves = []
        self.jumps = []
        if self.turn == 'white':
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    if self.pieces[row][col].color == 'white':
                        if self.pieces[row][col].king == False:
                            self._find_white_man_moves(row, col)
                            self._find_white_man_jumps(row, col, False)
                        else:
                            self._find_white_king_moves(row, col)
                            self._find_white_king_jumps(row, col, False)
        else:
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    if self.pieces[row][col].color == 'black':
                        if self.pieces[row][col].king == False:
                            self._find_black_man_moves(row, col)
                            self._find_black_man_jumps(row, col, False)
                        else:
                            self._find_black_king_moves(row, col)
                            self._find_black_king_jumps(row, col, False)

    def _find_white_man_moves(self, row, col):
        if self._check_moves(row, col, row - 1, col - 1):
            self.moves.append((row, col, row - 1, col - 1))
        if self._check_moves(row, col, row - 1, col + 1):
            self.moves.append((row, col, row - 1, col + 1))

    def _find_white_man_jumps(self, row, col, link):
        if self._check_jumps(row, col, row - 1, col - 1, row - 2, col - 2, 'white'):
            self.jumps.append((row, col, row - 1, col -1, row - 2, col - 2, link))
            if (row - 2) != 0:
                self._find_white_man_jumps(row - 2, col - 2, True)
        if self._check_jumps(row, col, row - 1, col + 1, row - 2, col + 2, 'white'):
            self.jumps.append((row, col, row - 1, col + 1, row - 2, col + 2, link))
            if (row - 2) != 0:
                self._find_white_man_jumps(row - 2, col + 2, True)

    def _find_white_king_moves(self, row, col):
        if self._check_moves(row, col, row - 1, col - 1):
            self.moves.append((row, col, row - 1, col - 1))
        if self._check_moves(row, col, row - 1, col + 1):
            self.moves.append((row, col, row - 1, col + 1))
        if self._check_moves(row, col, row + 1, col - 1):
            self.moves.append((row, col, row + 1, col - 1))
        if self._check_moves(row, col, row + 1, col + 1):
            self.moves.append((row, col, row + 1, col + 1))

    def _find_white_king_jumps(self, row, col, link):
        if self._check_jumps(row, col, row - 1, col - 1, row - 2, col - 2, 'white'):
            self.jumps.append((row, col, row - 1, col - 1, row - 2, col - 2, link))
            self._find_white_king_jumps(row - 2, col - 2, True)
        if self._check_jumps(row, col, row - 1, col + 1, row - 2, col + 2, 'white'):
            self.jumps.append((row, col, row - 1, col + 1, row - 2, col + 2, link))
            self._find_white_king_jumps(row - 2, col + 2, True)
        if self._check_jumps(row, col, row + 1, col - 1, row + 2, col - 2, 'white'):
            self.jumps.append((row, col, row + 1, col - 1, row + 2, col - 2, link))
            self._find_white_king_jumps(row + 2, col - 2, True)
        if self._check_jumps(row, col, row + 1, col + 1, row + 2, col + 2, 'white'):
            self.jumps.append((row, col, row + 1, col + 1, row + 2, col + 2, link))
            self._find_white_king_jumps(row + 2, col + 2, True)

    def _find_black_man_moves(self, row, col):
        if self._check_moves(row, col, row + 1, col + 1):
            self.moves.append((row, col, row + 1, col + 1))
        if self._check_moves(row, col, row + 1, col - 1):
            self.moves.append((row, col, row + 1, col - 1))

    def _find_black_man_jumps(self, row, col, link):
        if self._check_jumps(row, col, row + 1, col + 1, row + 2, col + 2, 'black'):
            self.jumps.append((row, col, row + 1, col + 1, row + 2, col + 2, link))
            if (row + 2) != 7:
                self._find_black_man_jumps(row + 2, col + 2, True)
        if self._check_jumps(row, col, row + 1, col - 1, row + 2, col - 2, 'black'):
            self.jumps.append((row, col, row + 1, col - 1, row + 2, col - 2, link))
            if (row + 2) != 7:
                self._find_black_man_jumps(row + 2, col - 2, True)

    def _find_black_king_moves(self, row, col):
        if self._check_moves(row, col, row - 1, col - 1):
            self.moves.append((row, col, row - 1, col - 1))
        if self._check_moves(row, col, row - 1, col + 1):
            self.moves.append((row, col, row - 1, col + 1))
        if self._check_moves(row, col, row + 1, col - 1):
            self.moves.append((row, col, row + 1, col - 1))
        if self._check_moves(row, col, row + 1, col + 1):
            self.moves.append((row, col, row + 1, col + 1))

    def _find_black_king_jumps(self, row, col, link):
        if self._check_jumps(row, col, row - 1, col - 1, row - 2, col - 2, 'black'):
            self.jumps.append((row, col, row - 1, col - 1, row - 2, col - 2, link))
            self._find_black_king_jumps(row - 2, col - 2, True)
        if self._check_jumps(row, col, row - 1, col + 1, row - 2, col + 2, 'black'):
            self.jumps.append((row, col, row - 1, col + 1, row - 2, col + 2, link))
            self._find_black_king_jumps(row - 2, col + 2, True)
        if self._check_jumps(row, col, row + 1, col - 1, row + 2, col - 2, 'black'):
            self.jumps.append((row, col, row + 1, col - 1, row + 2, col - 2, link))
            self._find_black_king_jumps(row + 2, col - 2, True)
        if self._check_jumps(row, col, row + 1, col + 1, row + 2, col + 2, 'black'):
            self.jumps.append((row, col, row + 1, col + 1, row + 2, col + 2, link))
            self._find_black_king_jumps(row + 2, col + 2, True)

    def _check_moves(self, old_row, old_col, new_row, new_col):
        if new_row > 7 or new_row < 0:
            return False
        if new_col > 7 or new_col < 0:
            return False
        if self.pieces[new_row][new_col].color != 'empty':
            return False
        return True

    def _check_jumps(self, old_row, old_col, via_row, via_col, new_row, new_col, color):
        if new_row > 7 or new_row < 0:
            return False
        if new_col > 7 or new_col < 0:
            return False
        if self.pieces[via_row][via_col].color == 'empty':
            return False
        if self.pieces[via_row][via_col].color == color:
            return False
        if self.pieces[new_row][new_col].color != 'empty':
            return False
        return True


class CheckersEnv(gym.Env):
    metadata = {"render_modes": ["human"], "render_fps": 0.5}

    def __init__(self, render_mode: Optional[str] = None):

        self.action_space = gym.spaces.Box(low=0, high=1, shape=(1,), dtype="int32")
        self.observation_space = gym.spaces.Box(low=0, high=1, shape=(1,), dtype="int32")
        self.state = None

        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode

        # rendering components

        self.screen = None
        self.clock = None

        # checkers board

        self.board = Board()

    def step(self, action):

        # step checkers board
        terminated = self.board.step()

        # define state
        self.state = []

        # define reward
        step_reward = 0

        self.render()

        return self.state, step_reward, terminated, False, {}

    def close(self):
        if self.screen is not None:
            pygame.display.quit()
            pygame.quit()

    def reset(self, *, seed: Optional[int] = None, options: Optional[dict] = None):
        super().reset(seed=seed)

        self.state = []

        self.board.reset()

        self.render()

        return self.state, {}

    def render(self):
        if self.render_mode == "human":
            self._render_frame()

    def _render_frame(self):
        pygame.font.init()
        if self.screen is None:
            pygame.init()
            pygame.display.init()
            pygame.display.set_caption("Reinforcement Learning")
            self.screen = pygame.display.set_mode((800, 800))
        if self.clock is None:
            self.clock = pygame.time.Clock()

        surf_board = pygame.Surface((640, 640))
        surf_info = pygame.Surface((640, 40))
        surf_info.fill(DARKBROWN)

        self.board.render(surf_board)
        self.screen.blit(surf_board, (80, 80))
        self.screen.blit(surf_info, (80, 724))

        pygame.event.pump()
        pygame.display.update()

        self.clock.tick(self.metadata["render_fps"])
