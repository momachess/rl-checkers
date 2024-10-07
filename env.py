import pygame
import random

import numpy as np
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
HILIGHT_MOVE = (  0, 255,   0, 128)
HILIGHT_JUMP = (255,   0,   0, 128)
KING         = (255, 255,   0)
WHITE_PRE    = (192, 192, 192)
BLACK_PRE    = (128, 128, 128)
WHITE_VIA    = (  0, 255,   0)
BLACK_VIA    = (  0,   0, 255)


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

        self.white_pieces = 12
        self.black_pieces = 12

        self.pieces = [[], [], [], [], [], [], [], []]
        self._setup()

        self.moves = []
        self.step_move = False
        self.jumps = []
        self.step_jump = False

        self.last_white_move = None
        self.last_black_move = None

    def step(self, action):
        end_game = False
        winner = None

        self.last_white_move = None
        self.last_black_move = None

        reward = 0.0

        # action has 64 float evaluation values to be used to get the best move
        best = [0.0, -1, -1, -1, -1]
        if self.step_jump:
            if len(self.jumps) == 1:
                (old_row, old_col, _, _, new_row, new_col, link) = self.jumps[0]
                best[1] = old_row
                best[2] = old_col
                best[3] = new_row
                best[4] = new_col
                best[0] = action[new_row][new_col]
            else:
                for (old_row, old_col, _, _, new_row, new_col, link) in self.jumps:
                    eval = action[new_row][new_col]
                    if link == False and eval > 0.0 and eval >= best[0]:
                        best[1] = old_row
                        best[2] = old_col
                        best[3] = new_row
                        best[4] = new_col
                        best[0] = eval
        elif self.step_move:
            if len(self.moves) == 1:
                (old_row, old_col, new_row, new_col) = self.moves[0]
                best[1] = old_row
                best[2] = old_col
                best[3] = new_row
                best[4] = new_col
                best[0] = action[new_row][new_col]
            else:
                for (old_row, old_col, new_row, new_col) in self.moves:
                    eval = action[new_row][new_col]
                    if eval > 0.0 and eval >= best[0]:
                        best[1] = old_row
                        best[2] = old_col
                        best[3] = new_row
                        best[4] = new_col
                        best[0] = eval

        # make white move
        if self.step_jump and best[1] != -1:
            jump_done = False
            promote_row = -1
            promote_col = -1
            for (old_row, old_col, via_row, via_col, new_row, new_col, link) in self.jumps:
                if jump_done == False:
                    if best[1] == old_row and best[2] == old_col and best[3] == new_row and best[4] == new_col:
                        promote_row = new_row
                        promote_col = new_col
                        self._make_jump(old_row, old_col, via_row, via_col, new_row, new_col)
                        self.black_pieces -= 1
                        jump_done = True
                        self.last_white_move = (old_col, old_row, via_col, via_row, new_col, new_row)
                else:
                    if link == True:
                        promote_row = new_row
                        promote_col = new_col
                        self._make_jump(old_row, old_col, via_row, via_col, new_row, new_col)
                        self.black_pieces -= 1
                        self.last_white_move = (old_col, old_row, via_col, via_row, new_col, new_row)
                    else:
                        jump_done = False
            self._promote(promote_row, promote_col)
            reward += 2.0
        elif self.moves != []:
            for (old_row, old_col, new_row, new_col) in self.moves:
                if best[1] == old_row and best[2] == old_col and best[3] == new_row and best[4] == new_col:
                    self._make_move(old_row, old_col, new_row, new_col)
                    self._promote(new_row, new_col)
                    reward += 1.0
                    self.last_white_move = (old_col, old_row, -1, -1, new_col, new_row)

        self.step_jump = False
        self.step_move = False

        if best[1] != -1:
            if self.black_pieces == 0:
                end_game = True
                winner = 'white'
                reward = +100.0

            # make black move (if not end game)
            if self.end_game == False:
                self.turn = 'black'

                self._find_valid_moves()
                if self.jumps != []:
                    sel = -1
                    while True:
                        sel = random.randint(0, len(self.jumps) - 1)
                        if self.jumps[sel][6] == False:
                            break
                    assert sel != -1
                    self._make_jump(self.jumps[sel][0], self.jumps[sel][1], self.jumps[sel][2], self.jumps[sel][3], self.jumps[sel][4], self.jumps[sel][5])
                    self.white_pieces -= 1
                    self.last_black_move = (self.jumps[sel][1], self.jumps[sel][0], self.jumps[sel][3], self.jumps[sel][2], self.jumps[sel][5], self.jumps[sel][4])
                    while True:
                        if sel < len(self.jumps) - 1:
                            sel += 1
                            if self.jumps[sel][6] == True:
                                self._make_jump(self.jumps[sel][0], self.jumps[sel][1], self.jumps[sel][2], self.jumps[sel][3], self.jumps[sel][4], self.jumps[sel][5])
                                self.white_pieces -= 1
                                self.last_black_move = (self.jumps[sel][1], self.jumps[sel][0], self.jumps[sel][3], self.jumps[sel][2], self.jumps[sel][5], self.jumps[sel][4])
                            else:
                                break
                        else:
                            break
                    self._promote(self.jumps[sel][4], self.jumps[sel][5])
                    reward -= 2
                elif self.moves != []:
                    sel = random.randint(0, len(self.moves)-1)
                    self._make_move(self.moves[sel][0], self.moves[sel][1], self.moves[sel][2], self.moves[sel][3])
                    self._promote(self.moves[sel][2], self.moves[sel][3])
                    reward -= 1
                    self.last_black_move = (self.moves[sel][1], self.moves[sel][0], -1, -1, self.moves[sel][3], self.moves[sel][2])

                # check end game
                if self.white_pieces == 0:
                    end_game = True
                    winner = 'black'
                    reward = -100.0
                if self.moves == [] and self.jumps == []:
                    end_game = True
                    winner = 'white'
                    reward = +100.0

        # fill state (observations)
        state = [[[0 for _ in range(8)] for _ in range(8)] for _ in range(4)]
        if end_game == False:
            self.turn = 'white'

            # first observation layer is white positions
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    if self.pieces[row][col].color == 'white':
                        state[0][row][col] = 1

            # first observation layer is black positions
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    if self.pieces[row][col].color == 'black':
                        state[1][row][col] = 1

            # third observation layer is empty positions
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    if self.pieces[row][col].color == 'empty':
                        state[2][row][col] = 1

            self._find_valid_moves()
            if self.jumps != []:
                self.step_jump = True
                for (_, _, _, _, new_row, new_col, _) in self.jumps:
                    state[3][new_row][new_col] = 1
            elif self.moves != []:
                self.step_move = True
                for (_, _, new_row, new_col) in self.moves:
                    state[3][new_row][new_col] = 1

            if self.moves == [] and self.jumps == []:
                end_game = True
                winner = 'black'
                reward = -100

        return state, reward, end_game, winner

    def reset(self):
        self.end_game = False

        self.white_pieces = 12
        self.black_pieces = 12

        self.pieces = [[], [], [], [], [], [], [], []]
        self._setup()

        # make first game move
        self.turn = 'black'
        self._find_valid_moves()
        if self.jumps != []:
            sel = random.randint(0, len(self.jumps) - 1)
            self._make_jump(self.jumps[sel][0], self.jumps[sel][1], self.jumps[sel][2], self.jumps[sel][3], self.jumps[sel][4], self.jumps[sel][5])
            self.white_pieces -= 1
            while True:
                if sel < len(self.jumps) - 1:
                    sel += 1
                    if self.jumps[sel][6] == True:
                        self._make_jump(self.jumps[sel][0], self.jumps[sel][1], self.jumps[sel][2], self.jumps[sel][3], self.jumps[sel][4], self.jumps[sel][5])
                        self.white_pieces -= 1
                    else:
                        break
                else:
                    break
            self._promote(self.jumps[sel][4], self.jumps[sel][5])
        elif self.moves != []:
            sel = random.randint(0, len(self.moves)-1)
            self._make_move(self.moves[sel][0], self.moves[sel][1], self.moves[sel][2], self.moves[sel][3])
            self._promote(self.moves[sel][2], self.moves[sel][3])

        self.moves = []
        self.step_move = False
        self.jumps = []
        self.step_jump = False

        # fill state (observations)
        state = [[[0 for _ in range(8)] for _ in range(8)] for _ in range(4)]
        self.turn = 'white'

        # first observation layer is white positions
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.pieces[row][col].color == 'white':
                    state[0][row][col] = 1

        # first observation layer is black positions
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.pieces[row][col].color == 'black':
                    state[1][row][col] = 1

        # third observation layer is empty positions
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.pieces[row][col].color == 'empty':
                    state[2][row][col] = 1

        self._find_valid_moves()
        if self.jumps != []:
            self.step_jump = True
            for (_, _, _, _, new_row, new_col, _) in self.jumps:
                state[3][new_row][new_col] = 1
        elif self.moves != []:
            self.step_move = True
            for (_, _, new_row, new_col) in self.moves:
                state[3][new_row][new_col] = 1

        return state

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

        if self.last_white_move is not None:
            if self.last_white_move[2] == -1:
                pygame.draw.circle(surf, WHITE_PRE, [self.last_white_move[0]*SQUARE_SIZE + SQUARE_SIZE // 2, self.last_white_move[1]*SQUARE_SIZE + SQUARE_SIZE // 2], PIECE_SIZE)
                pygame.draw.line(surf, WHITE, [self.last_white_move[0]*SQUARE_SIZE + SQUARE_SIZE // 2, self.last_white_move[1]*SQUARE_SIZE + SQUARE_SIZE // 2], [self.last_white_move[4]*SQUARE_SIZE + SQUARE_SIZE // 2, self.last_white_move[5]*SQUARE_SIZE + SQUARE_SIZE // 2])
            else:
                pygame.draw.circle(surf, WHITE_PRE, [self.last_white_move[0]*SQUARE_SIZE + SQUARE_SIZE // 2, self.last_white_move[1]*SQUARE_SIZE + SQUARE_SIZE // 2], PIECE_SIZE)
                pygame.draw.circle(surf, WHITE_VIA, [self.last_white_move[2]*SQUARE_SIZE + SQUARE_SIZE // 2, self.last_white_move[3]*SQUARE_SIZE + SQUARE_SIZE // 2], PIECE_SIZE)
                pygame.draw.line(surf, WHITE, [self.last_white_move[0]*SQUARE_SIZE + SQUARE_SIZE // 2, self.last_white_move[1]*SQUARE_SIZE + SQUARE_SIZE // 2], [self.last_white_move[2]*SQUARE_SIZE + SQUARE_SIZE // 2, self.last_white_move[3]*SQUARE_SIZE + SQUARE_SIZE // 2])
                pygame.draw.line(surf, WHITE, [self.last_white_move[2]*SQUARE_SIZE + SQUARE_SIZE // 2, self.last_white_move[3]*SQUARE_SIZE + SQUARE_SIZE // 2], [self.last_white_move[4]*SQUARE_SIZE + SQUARE_SIZE // 2, self.last_white_move[5]*SQUARE_SIZE + SQUARE_SIZE // 2])

        if self.last_black_move is not None:
            if self.last_black_move[2] == -1:
                pygame.draw.circle(surf, BLACK_PRE, [self.last_black_move[0]*SQUARE_SIZE + SQUARE_SIZE // 2, self.last_black_move[1]*SQUARE_SIZE + SQUARE_SIZE // 2], PIECE_SIZE)
                pygame.draw.line(surf, BLACK, [self.last_black_move[0]*SQUARE_SIZE + SQUARE_SIZE // 2, self.last_black_move[1]*SQUARE_SIZE + SQUARE_SIZE // 2], [self.last_black_move[4]*SQUARE_SIZE + SQUARE_SIZE // 2, self.last_black_move[5]*SQUARE_SIZE + SQUARE_SIZE // 2])
            else:
                pygame.draw.circle(surf, BLACK_PRE, [self.last_black_move[0]*SQUARE_SIZE + SQUARE_SIZE // 2, self.last_black_move[1]*SQUARE_SIZE + SQUARE_SIZE // 2], PIECE_SIZE)
                pygame.draw.circle(surf, BLACK_VIA, [self.last_black_move[2]*SQUARE_SIZE + SQUARE_SIZE // 2, self.last_black_move[3]*SQUARE_SIZE + SQUARE_SIZE // 2], PIECE_SIZE)
                pygame.draw.line(surf, BLACK, [self.last_black_move[0]*SQUARE_SIZE + SQUARE_SIZE // 2, self.last_black_move[1]*SQUARE_SIZE + SQUARE_SIZE // 2], [self.last_black_move[2]*SQUARE_SIZE + SQUARE_SIZE // 2, self.last_black_move[3]*SQUARE_SIZE + SQUARE_SIZE // 2])
                pygame.draw.line(surf, BLACK, [self.last_black_move[2]*SQUARE_SIZE + SQUARE_SIZE // 2, self.last_black_move[3]*SQUARE_SIZE + SQUARE_SIZE // 2], [self.last_black_move[4]*SQUARE_SIZE + SQUARE_SIZE // 2, self.last_black_move[5]*SQUARE_SIZE + SQUARE_SIZE // 2])

    def update(self):
        self._find_valid_moves()
        if self.jumps != []:
            sel = -1
            while True:
                sel = random.randint(0, len(self.jumps) - 1)
                if self.jumps[sel][6] == False:
                    break
            assert sel != -1
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

        self.end_game = False
        self.winner = None

        if self.turn == 'white':
            if self.black_pieces == 0:
                self.end_game = True
                self.winner = 'white'
            if  self.moves == [] and self.jumps == []:
                self.end_game = True
                self.winner = 'black'
        else:
            if self.white_pieces == 0:
                self.end_game = True
                self.winner = 'black'
            if self.moves == [] and self.jumps == []:
                self.end_game = True
                self.winner = 'white'

        if self.end_game == False:
            if self.turn == 'white':
                self.turn = 'black'
            else:
                self.turn = 'white'

        return self.end_game, self.winner

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
        if self._check_move(row, col, row - 1, col - 1):
            self.moves.append((row, col, row - 1, col - 1))
        if self._check_move(row, col, row - 1, col + 1):
            self.moves.append((row, col, row - 1, col + 1))

    def _find_white_man_jumps(self, row, col, link):
        if self._check_jump(row, col, row - 1, col - 1, row - 2, col - 2, 'white'):
            self.jumps.append((row, col, row - 1, col -1, row - 2, col - 2, link))
            if (row - 2) != 0:
                self._find_white_man_jumps(row - 2, col - 2, True)
        if self._check_jump(row, col, row - 1, col + 1, row - 2, col + 2, 'white'):
            self.jumps.append((row, col, row - 1, col + 1, row - 2, col + 2, link))
            if (row - 2) != 0:
                self._find_white_man_jumps(row - 2, col + 2, True)

    def _find_white_king_moves(self, row, col):
        if self._check_move(row, col, row - 1, col - 1):
            self.moves.append((row, col, row - 1, col - 1))
        if self._check_move(row, col, row - 1, col + 1):
            self.moves.append((row, col, row - 1, col + 1))
        if self._check_move(row, col, row + 1, col - 1):
            self.moves.append((row, col, row + 1, col - 1))
        if self._check_move(row, col, row + 1, col + 1):
            self.moves.append((row, col, row + 1, col + 1))

    def _find_white_king_jumps(self, row, col, link):
        for (_, _, _, _, new_row, new_col, _) in self.jumps:
            if row == new_row and col == new_col:
                return
        if self._check_jump(row, col, row - 1, col - 1, row - 2, col - 2, 'white'):
            self.jumps.append((row, col, row - 1, col - 1, row - 2, col - 2, link))
            self._find_white_king_jumps(row - 2, col - 2, True)
        if self._check_jump(row, col, row - 1, col + 1, row - 2, col + 2, 'white'):
            self.jumps.append((row, col, row - 1, col + 1, row - 2, col + 2, link))
            self._find_white_king_jumps(row - 2, col + 2, True)
        if self._check_jump(row, col, row + 1, col - 1, row + 2, col - 2, 'white'):
            self.jumps.append((row, col, row + 1, col - 1, row + 2, col - 2, link))
            self._find_white_king_jumps(row + 2, col - 2, True)
        if self._check_jump(row, col, row + 1, col + 1, row + 2, col + 2, 'white'):
            self.jumps.append((row, col, row + 1, col + 1, row + 2, col + 2, link))
            self._find_white_king_jumps(row + 2, col + 2, True)

    def _find_black_man_moves(self, row, col):
        if self._check_move(row, col, row + 1, col + 1):
            self.moves.append((row, col, row + 1, col + 1))
        if self._check_move(row, col, row + 1, col - 1):
            self.moves.append((row, col, row + 1, col - 1))

    def _find_black_man_jumps(self, row, col, link):
        if self._check_jump(row, col, row + 1, col + 1, row + 2, col + 2, 'black'):
            self.jumps.append((row, col, row + 1, col + 1, row + 2, col + 2, link))
            if (row + 2) != 7:
                self._find_black_man_jumps(row + 2, col + 2, True)
        if self._check_jump(row, col, row + 1, col - 1, row + 2, col - 2, 'black'):
            self.jumps.append((row, col, row + 1, col - 1, row + 2, col - 2, link))
            if (row + 2) != 7:
                self._find_black_man_jumps(row + 2, col - 2, True)

    def _find_black_king_moves(self, row, col):
        if self._check_move(row, col, row - 1, col - 1):
            self.moves.append((row, col, row - 1, col - 1))
        if self._check_move(row, col, row - 1, col + 1):
            self.moves.append((row, col, row - 1, col + 1))
        if self._check_move(row, col, row + 1, col - 1):
            self.moves.append((row, col, row + 1, col - 1))
        if self._check_move(row, col, row + 1, col + 1):
            self.moves.append((row, col, row + 1, col + 1))

    def _find_black_king_jumps(self, row, col, link):
        for (_, _, _, _, new_row, new_col, _) in self.jumps:
            if row == new_row and col == new_col:
                return
        if self._check_jump(row, col, row - 1, col - 1, row - 2, col - 2, 'black'):
            self.jumps.append((row, col, row - 1, col - 1, row - 2, col - 2, link))
            self._find_black_king_jumps(row - 2, col - 2, True)
        if self._check_jump(row, col, row - 1, col + 1, row - 2, col + 2, 'black'):
            self.jumps.append((row, col, row - 1, col + 1, row - 2, col + 2, link))
            self._find_black_king_jumps(row - 2, col + 2, True)
        if self._check_jump(row, col, row + 1, col - 1, row + 2, col - 2, 'black'):
            self.jumps.append((row, col, row + 1, col - 1, row + 2, col - 2, link))
            self._find_black_king_jumps(row + 2, col - 2, True)
        if self._check_jump(row, col, row + 1, col + 1, row + 2, col + 2, 'black'):
            self.jumps.append((row, col, row + 1, col + 1, row + 2, col + 2, link))
            self._find_black_king_jumps(row + 2, col + 2, True)

    def _check_move(self, old_row, old_col, new_row, new_col):
        if new_row > 7 or new_row < 0:
            return False
        if new_col > 7 or new_col < 0:
            return False
        if self.pieces[new_row][new_col].color != 'empty':
            return False
        return True

    def _check_jump(self, old_row, old_col, via_row, via_col, new_row, new_col, color):
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
    metadata = {"render_modes": ["human"] }

    def __init__(self, render_mode: Optional[str] = None, render_fps: Optional[int] = 60):

        self.action_space = gym.spaces.Box(low=0.0, high=1.0, shape=(BOARD_SIZE, BOARD_SIZE), dtype=np.float32)
        self.observation_space = gym.spaces.Box(low=0, high=1, shape=(4, BOARD_SIZE, BOARD_SIZE), dtype=np.uint8)

        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode
        self.render_fps = render_fps

        # rendering components

        self.screen = None
        self.clock = None

        # checkers board

        self.board = Board()

        self.episodes = -1
        self.steps = 0
        self.reward = 0.0
        self.score = -999.0

        self.white_wins = 0
        self.black_wins = 0

    def step(self, action):

        state, reward, terminated, winner = self.board.step(action)

        if terminated == False:
            self.steps += 1
            if self.steps == 1024:
                terminated = True
        else:
            if winner == 'white':
                self.white_wins += 1
            elif winner == 'black':
                self.black_wins += 1

        self.reward += reward
        self.render()

        return state, reward, terminated, False, {}

    def close(self):
        if self.screen is not None:
            pygame.display.quit()
            pygame.quit()

    def reset(self, *, seed: Optional[int] = None, options: Optional[dict] = None):
        super().reset(seed=seed)

        self.episodes += 1
        self.steps = 0
        if self.episodes > 0:
            self.score = max(self.score, self.reward)
        self.reward = 0.0

        state = self.board.reset()

        self.render()

        return state, {}

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
        font = pygame.font.Font(pygame.font.get_default_font(), 12)
        
        text = font.render("Episodes: %04i" % self.episodes, True, LIGHTBROWN, DARKBROWN)
        text_rect = text.get_rect()
        text_rect.center = (64, 20)
        surf_info.blit(text, text_rect)

        text = font.render("Steps: %04i" % self.steps, True, LIGHTBROWN, DARKBROWN)
        text_rect = text.get_rect()
        text_rect.center = (160, 20)
        surf_info.blit(text, text_rect)

        text = font.render("Score: %04.1f" % self.score, True, LIGHTBROWN, DARKBROWN)
        text_rect = text.get_rect()
        text_rect.center = (256, 20)
        surf_info.blit(text, text_rect)

        text = font.render("Reward: %04.1f" % self.reward, True, LIGHTBROWN, DARKBROWN)
        text_rect = text.get_rect()
        text_rect.center = (352, 20)
        surf_info.blit(text, text_rect)

        text = font.render("White Win: %04i" % self.white_wins, True, LIGHTBROWN, DARKBROWN)
        text_rect = text.get_rect()
        text_rect.center = (448, 20)
        surf_info.blit(text, text_rect)

        text = font.render("Black Win: %04i" % self.black_wins, True, LIGHTBROWN, DARKBROWN)
        text_rect = text.get_rect()
        text_rect.center = (544, 20)
        surf_info.blit(text, text_rect)

        self.screen.blit(surf_info, (80, 724))

        pygame.event.pump()
        pygame.display.update()

        self.clock.tick(self.render_fps)
