import pytest
from src.puzzle import PuzzlePiece, MaxRotationsReached

PIECE_SIDES = [1, 2, 3, 4]

REAL_MAX_ROTATIONS = 3


@pytest.fixture
def piece():
    return PuzzlePiece(1, PIECE_SIDES)


def test_zero_rotations(piece):
    assert piece.rotations == 0


def test_rotations_count_increase(piece):
    piece.rotate()
    assert piece.rotations == 1
    piece.rotate()
    assert piece.rotations == 2
    piece.rotate()
    assert piece.rotations == 3


def test_max_rotations_value(piece):
    return PuzzlePiece.MAX_ROTATIONS == REAL_MAX_ROTATIONS


def test_maximum_rotations_exception(piece):
    for _ in range(PuzzlePiece.MAX_ROTATIONS):
        piece.rotate()
    with pytest.raises(MaxRotationsReached) as e:
        piece.rotate()


def test_reset_rotations(piece):
    for rotations_count in range(PuzzlePiece.MAX_ROTATIONS):
        for _ in range(rotations_count + 1):
            piece.rotate()
        piece.reset_rotations()
        assert [piece.top, piece.right, piece.bottom, piece.left] == PIECE_SIDES
