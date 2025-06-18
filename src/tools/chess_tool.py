from PIL import Image
from board_to_fen.predict import get_fen_from_image
import chess as c
import chess.engine as ce
import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
STOCKFISH_EXECUTABLE_PATH = (
    "external/chess-engines/stockfish/stockfish-ubuntu-x86-64-avx2"
)


def extract_fen_position(path_to_chess_img: str) -> str:
    """
    GET the FEN position from chess 2D board.

    Parameters
    ----------
    path_to_chess_img : str
        Description

    Returns:
        str: Predicted Chess position in FEN notation

    Example:
        >>> extract_fen_position("chess_board.png)
        'r1bqkbnr/pppp1ppp/2n5/4p3/1b2P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 2 4'
    """
    img = Image.open(path_to_chess_img)
    fen = get_fen_from_image(img, black_view=True)
    return fen


def predict_next_best_move(
    fen_position: str, path_to_stockfish: str = STOCKFISH_EXECUTABLE_PATH
) -> str:
    """
    Leverage Stockfish 17.1 to predict the next best move.

    Parameters
    ----------
    fen_position : str
        FEN notation for the Chess Image

    Returns:
        str: Predicted next best move in FEN notation

    Example:
        >>> predict_next_best_move('r1bqkbnr/pppp1ppp/2n5/4p3/1b2P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 2 4')
        'O-O'
    """
    # Init Chess Board
    board = c.Board(fen_position)

    # Get Stockfish model
    chess_engine = ce.SimpleEngine.popen_uci(path_to_stockfish)

    # Predict next best move
    stockfish_player = chess_engine.play(board=board, limit=ce.Limit(time=10))
    best_move_uci = stockfish_player.move
    best_move = board.san(
        move=best_move_uci
    )  # Convert from Universal Chess interface to Standard Algebraic Notation
    return best_move


if __name__ == "__main__":
    print("\n", "=" * 30, "\n")
    chess_img_path = input("Please type the path to Chess Board img: ")
    fen = extract_fen_position(path_to_chess_img=chess_img_path)
    usr_res = input(
        f"\nThe predicted FEN is {fen}\nif you want to correct it, please type the correction, otherwise type Enter: "
    )
    fen = usr_res if len(usr_res) > 1 else fen
    best_move = predict_next_best_move(fen_position=fen)
    print(f"The next best move is: {best_move}")

# TODO: Clean TF Warnings regarding CPU Usage