import click
import click_log
from src.logger import logger
from src.puzzle import PuzzleUtils

click_log.basic_config(logger)

PUZZLE_FILE_KEY = "puzzle_file"


@click.group()
@click_log.simple_verbosity_option(logger)
@click.option("--puzzle-file", "-p",
              type=click.File(),
              help="The file which contains the puzzle content")
@click.pass_context
def main(ctx, puzzle_file):
    ctx.obj = {
        PUZZLE_FILE_KEY: puzzle_file
    }


@main.command()
@click.pass_context
def print_puzzle(ctx):
    """
    Prints a given puzzle
    """
    puzzle = PuzzleUtils.load_puzzle(ctx.obj[PUZZLE_FILE_KEY])
    puzzle.print_grid()


@main.command()
@click.pass_context
def solve_puzzle(ctx):
    """
    Solves a given puzzle
    """
    puzzle = PuzzleUtils.load_puzzle(ctx.obj[PUZZLE_FILE_KEY])
    puzzle.solve()
    logger.info(puzzle.dump_grid())


if __name__ == "__main__":
    main()
