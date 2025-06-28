# from PIL import Image
from board_to_fen.predict import get_fen_from_image_path
import chess as c
import chess.engine as ce

import easyocr
from langchain.tools import tool

import os
import numpy as np
import cv2
from typing import Dict

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STOCKFISH_EXECUTABLE_PATH = os.path.join(
    BASE_DIR,
    '../../external/chess-modules/stockfish/stockfish-ubuntu-x86-64-avx2'
)

STOCKFISH_EXECUTABLE_PATH = os.path.normpath(STOCKFISH_EXECUTABLE_PATH)


@tool
def grab_board_view(chess_img_path: str) -> Dict:
    """
    Identify the chess board view from its related filepath (.png, .jpg or .jpeg)

    Parameters
    ----------
    chess_img_path: str
        File path to Chess Board Image. It must point to a 2D board image

    Returns:
        Dict: {"board_view", board_view}  # Where board_view in (True, False, "Unknown")

    Example:
        >>> grab_board_view("chess_board.png")
        {"board_view", True}
    """
    cropped_square_path = "temp-square.png"
    # Read Chess Board Img and Crop the bottom-left square
    img_bgr = cv2.imread(chess_img_path)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    img_np = np.array(img_rgb)
    img_np_shape = img_np.shape
    img_rows, img_cols = img_np_shape[:2]
    img_cropped = img_np[img_rows // 8 * 7 :, : img_cols // 8 * 1, :]
    img_cropped = cv2.cvtColor(img_cropped, cv2.COLOR_BGR2RGB)
    cv2.imwrite(cropped_square_path, img_cropped)

    # Wrap text from image path
    reader = easyocr.Reader(["en"], gpu=False)
    results = reader.readtext(image=cropped_square_path)
    results.reverse()

    # Grab text
    left_bottom_cell = ""
    for _, text_temp, _ in results:
        left_bottom_cell += text_temp

    # Identify black view
    if left_bottom_cell in ("h8", "8h", "h", "8"):
        black_view = True
    elif left_bottom_cell in ("a1", "1a", "a", "1"):
        black_view = False
    else:
        black_view = "Unknown"

    # delete temp image
    if os.path.isfile(cropped_square_path):
        os.remove(cropped_square_path)

    return {"black_view": black_view}


@tool
def extract_fen_position(path_to_chess_img: str, black_view: bool = True) -> str:
    """
    Get the FEN position from chess 2D board.

    Parameters
    ----------
    path_to_chess_img : str
        file path to chess board, must have png, jpg, jpeg formats

    black_view: bool
        Set to True iff the board is viewed from Black's perspective.

    Returns:
        str: Predicted Chess position in FEN notation

    Example:
        >>> extract_fen_position("chess_board.png")
        'r1bqkbnr/pppp1ppp/2n5/4p3/1b2P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 2 4'
    """
    fen = get_fen_from_image_path(path_to_chess_img, black_view=black_view)
    return fen


@tool
def predict_next_best_move(
    fen_position: str, path_to_stockfish: str = STOCKFISH_EXECUTABLE_PATH
) -> str:
    """
    Leverage Stockfish 17.1 to predict the next best move.

    Parameters
    ----------
    fen_position : str
        FEN notation for the Chess Image. Must have the following syntax
        syntax: [Piece Placement] [Active Color] [Castling Availability] [En Passant Target Square] [Halfmove Clock] [Fullmove Number]


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
    #result = grab_board_view(chess_img_path="/home/santiagoal/.cache/huggingface/hub/datasets--gaia-benchmark--GAIA/snapshots/897f2dfbb5c952b5c3c1509e648381f9c7b70316/2023/validation/cca530fc-4052-43b2-b130-b30968d8aa44.png")
    #print(result)
    #print("\n", "=" * 30, "\n")
    #chess_img_path = input("Please type the path to Chess Board img: ")
    #fen = extract_fen_position(path_to_chess_img=chess_img_path)
    #usr_res = input(
    #    f"\nThe predicted FEN is {fen}\nif you want to correct it, please type the correction, otherwise type Enter: "
    #)
    usr_res = input("Pass FEN: ")
    fen = usr_res if len(usr_res) > 1 else fen
    best_move = predict_next_best_move(fen_position=fen)
    print(f"The next best move is: {best_move}")

# TODO: Address warnings
