from __future__ import annotations

from logger import logger

from exceptions import EndOfGridReached, MaxRotationsReached
from typing import List
from tabulate import tabulate
import json
import math
from enum import Enum


class PieceSide(Enum):
    """
    An enum which defines a relation between 2 pieces.
    Mainly used to verify a puzzle piece placement
    """
    TOP = 1
    RIGHT = 2
    BOTTOM = 3
    LEFT = 4


class PuzzlePiece:
    def __init__(self, piece_id, sides: list):
        """
        Represents a puzzle piece.
        A puzzle pieces consists of an ID and 4 sides.

        :param piece_id: The ID of the given piece
        :param sides: All of the piece sides (top, right, bottom and left)
        """
        self.id = piece_id
        self.top, self.right, self.bottom, self.left = sides
        self._rotate_count = 0

    @property
    def rotations(self):
        return self._rotate_count

    def rotate(self, internal_rotation=False):
        if not internal_rotation and self._rotate_count == 3:
            raise MaxRotationsReached()

        _ = self.left
        self.left = self.bottom
        self.bottom = self.right
        self.right = self.top
        self.top = _
        if not internal_rotation:
            self._rotate_count += 1

    def reset_rotations(self):
        original_rotate_count = self._rotate_count
        for i in range(4 - original_rotate_count):
            self.rotate(internal_rotation=True)

        self._rotate_count = 0

    def verify_piece(self, piece: PuzzlePiece, side_of_second_piece: PieceSide):
        if side_of_second_piece == PieceSide.TOP:
            return self.top == piece.bottom
        elif side_of_second_piece == PieceSide.RIGHT:
            return self.right == piece.left
        elif side_of_second_piece == PieceSide.BOTTOM:
            return self.bottom == piece.top
        elif side_of_second_piece == PieceSide.LEFT:
            return self.left == piece.right

    def __repr__(self):
        return f"{self.top}, {self.right}, {self.bottom}, {self.left}"


class PuzzleIterator:
    def __init__(self, puzzle: Puzzle):
        """
        An iterator for the puzzle, allows to iterate over all of the puzzle pieces
        :param puzzle: The puzzle object
        """
        self._puzzle = puzzle
        self._current_row = 0
        self._current_column = 0
        self._end_reached = False

    def __iter__(self):
        return self

    def __next__(self):
        if self._end_reached:
            raise StopIteration

        old_row, old_column = self._current_row, self._current_column
        try:
            self._current_row, self._current_column = self._puzzle.next_piece_coordinate(self._current_row,
                                                                                         self._current_column)
        except EndOfGridReached:
            self._end_reached = True

        return self._puzzle.get_piece(old_row, old_column)


class Puzzle:
    def __init__(self, pieces: List[PuzzlePiece]):
        """
        This class represents a puzzle board.
        It holds the puzzle pieces, contains their coordinates and solves the puzzle
        :param pieces: A list of puzzle pieces
        """
        self._puzzle_grid = None
        self.grid_size = None
        self._load_pieces_to_grid(pieces)

    def _load_pieces_to_grid(self, pieces: List[PuzzlePiece]):
        """
        Loads a list puzzle pieces to the puzzle board
        :param pieces: A list of puzzle pieces
        :type pieces: List[PuzzlePiece]
        """
        zero_piece = PuzzlePiece(0, [0, 0, 0, 0])
        grid_size = int(math.sqrt(len(pieces)))
        self.grid_size = grid_size
        # Generate the grid with the right edge length, the +2 is for the zero pieces
        self._puzzle_grid = [[zero_piece] * (grid_size + 2) for _ in range(grid_size + 2)]
        for idx, piece in enumerate(pieces):
            piece_row = int(idx / grid_size)
            piece_column = int(idx % grid_size)

            self._puzzle_grid[1 + piece_row][1 + piece_column] = piece  # The +1 is because of the zero pieces

    def print_grid(self):
        """
        Prints the grid in a table format
        """
        logger.info(tabulate(self._puzzle_grid))

    def dump_grid(self):
        """
        Dumps the grid in the desired solution format
        :return: The solution string of all of the pieces locations and rotations
        """
        return "; ".join([f"{piece.id},{piece.rotations}" for piece in iter(self)])

    def get_piece(self, row, column) -> PuzzlePiece:
        """
        Retrieves the piece object which resides in a certain row and column

        :return: The requested piece
        :rtype: PuzzlePiece
        """
        return self._puzzle_grid[row + 1][column + 1]

    def _set_piece(self, row, column, piece: PuzzlePiece):
        """
        Sets a piece in a given coordinate

        :type piece: PuzzlePiece
        """
        self._puzzle_grid[row + 1][column + 1] = piece

    def check_piece_placement(self, row, column):
        """
        Verifies that a given piece is placed correctly in the puzzle.
        It checks if the upper and left piece match the given puzzle piece.

        :param row: The row of the piece to check
        :param column: The column of the piece to check
        :return: Whether the piece was places correctly
        """
        # TODO: Add support to get piece by it's relative position to the current piece
        result = self.get_piece(row, column).verify_piece(self.get_piece(row - 1, column), PieceSide.TOP)
        return result & self.get_piece(row, column).verify_piece(self.get_piece(row, column - 1), PieceSide.LEFT)

    def swap_pieces(self, row1, column1, row2, column2):
        """
        Swaps two pieces with each other
        """
        first_piece = self.get_piece(row1, column1)
        self._set_piece(row1, column1, self.get_piece(row2, column2))
        self._set_piece(row2, column2, first_piece)

    def next_piece_coordinate(self, row, column):
        """
        Returns the next coordinate (row, column) of a given piece
        :param row: The current piece row
        :param column: The current piece column
        :return: The next piece coordinates (row, column)
        """
        # TODO: Make pieces coordinates a namedtuple
        column += 1
        if column == self.grid_size:
            row += 1
            column = 0
        if row == self.grid_size:
            raise EndOfGridReached()
        return row, column

    def solve_piece(self, solving_row, solving_column):
        """
        This is the main function for solving the puzzle.
        It is used to solve from a certain coordinate on the puzzle and ahead (top left to bottom right)
        Most of the times this function will be called recursively

        :param solving_row: The row of the piece to solve the puzzle from
        :param solving_column: The column of the piece to solve the puzzle from
        :return: Whether we managed to solve the puzzle for this piece placement
        """
        next_swap_piece = (solving_row, solving_column)
        solving_piece = self.get_piece(solving_row, solving_column)
        logger.debug(f"Now trying to solve piece ({solving_row}, {solving_column})")
        while True:
            for idx in range(4):
                if self.check_piece_placement(solving_row, solving_column):
                    if solving_row + 1 == self.grid_size and solving_column + 1 == self.grid_size:
                        return True

                    logger.info(f"Solved! {solving_row}, {solving_column}")
                    if not self.solve_piece(*self.next_piece_coordinate(solving_row, solving_column)):
                        # We didn't manage to find any possible solution for the current placement
                        # Let's continue the flow like it never even worked
                        logger.debug(f"Could not solve the puzzle for ({solving_row}, {solving_column}) "
                                     f"with {solving_piece}")
                        break
                    else:
                        return True

                if idx == 3:
                    break
                logger.debug(f"Rotating {solving_row}, {solving_column}")
                solving_piece.rotate()

            solving_piece.reset_rotations()
            self.swap_pieces(*next_swap_piece, solving_row, solving_column)
            try:
                next_swap_piece = self.next_piece_coordinate(*next_swap_piece)
            except EndOfGridReached:
                return False
            logger.debug(f"Swapping ({solving_row}, {solving_column}) with ({next_swap_piece[0]}, {next_swap_piece[1]})")
            self.swap_pieces(solving_row, solving_column, *next_swap_piece)
            solving_piece = self.get_piece(solving_row, solving_column)

    def solve(self):
        """
        Solves the current puzzle.
        This function solves the puzzle from the top left to the bottom right.
        """
        # Find a part which fits to be the first, try to solve with it

        if self.solve_piece(0, 0):
            logger.info("The puzzle is solved!")
        else:
            logger.warning("The puzzle couldn't be solved!")

    def __iter__(self):
        return PuzzleIterator(self)


class PuzzleUtils:
    """
    General utilities which are used for the puzzle handling
    """
    PIECES_SEPARATOR = ";"
    NAME_VALUE_SEPARATOR = ","

    @staticmethod
    def _parse_puzzle_file(puzzle_file):
        puzzle_content = puzzle_file.read()
        pieces = puzzle_content.split(PuzzleUtils.PIECES_SEPARATOR)
        puzzle_pieces = []
        for piece in pieces:
            piece_id, sides = piece.split(PuzzleUtils.NAME_VALUE_SEPARATOR, 1)
            puzzle_piece = PuzzlePiece(int(piece_id), json.loads(sides))
            puzzle_pieces.append(puzzle_piece)
        return puzzle_pieces

    @staticmethod
    def load_puzzle(puzzle_file):
        puzzle_pieces = PuzzleUtils._parse_puzzle_file(puzzle_file)
        return Puzzle(puzzle_pieces)
