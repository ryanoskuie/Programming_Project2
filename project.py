"""A tic-tac-toe game built with Python and Tkinter."""

import tkinter as tk
from itertools import cycle
from tkinter import font
from typing import NamedTuple
import random


class Player(NamedTuple):
    label: str
    color: str
    isAi: bool


class Move(NamedTuple):
    row: int
    col: int
    label: str = ""


BOARD_SIZE = 3
DEFAULT_PLAYERS = (
    Player(label="X", color="blue", isAi=False),  # Human Player
    Player(label="O", color="green", isAi=True),  # AI Player
)


class TicTacToeGame:
    def __init__(self, players=DEFAULT_PLAYERS, board_size=BOARD_SIZE):
        self._players = cycle(players)
        self.board_size = board_size
        self.current_player = next(self._players)
        self.winner_combo = []
        self._current_moves = []
        self._has_winner = False
        self._winning_combos = []
        self._setup_board()

        self.debug_minmax = True # Turn this on/off to control Minimax debug output

    def _setup_board(self):
        self._current_moves = [
            [Move(row, col) for col in range(self.board_size)]
            for row in range(self.board_size)
        ]
        self._winning_combos = self._get_winning_combos()

    def _get_winning_combos(self):
        rows = [
            [(move.row, move.col) for move in row]
            for row in self._current_moves
        ]
        columns = [list(col) for col in zip(*rows)]
        first_diagonal = [row[i] for i, row in enumerate(rows)]
        second_diagonal = [col[j] for j, col in enumerate(reversed(columns))]
        return rows + columns + [first_diagonal, second_diagonal]

    def toggle_player(self):
        """Return a toggled player."""
        self.current_player = next(self._players)

    def is_valid_move(self, move):
        """Return True if move is valid, and False otherwise."""
        row, col = move.row, move.col
        move_was_not_played = self._current_moves[row][col].label == ""
        no_winner = not self._has_winner
        return no_winner and move_was_not_played

    def process_move(self, move):
        """Process the current move and check if it's a win."""
        row, col = move.row, move.col
        self._current_moves[row][col] = move
        for combo in self._winning_combos:
            results = set(self._current_moves[n][m].label for n, m in combo)
            is_win = (len(results) == 1) and ("" not in results)
            if is_win:
                self._has_winner = True
                self.winner_combo = combo
                break

    def has_winner(self):
        """Return True if the game has a winner, and False otherwise."""
        return self._has_winner

    def is_tied(self):
        """Return True if the game is tied, and False otherwise."""
        no_winner = not self._has_winner
        played_moves = (
            move.label for row in self._current_moves for move in row
        )
        return no_winner and all(played_moves)

    def reset_game(self):
        """Reset the game state to play again."""
        for row, row_content in enumerate(self._current_moves):
            for col, _ in enumerate(row_content):
                row_content[col] = Move(row, col)
        self._has_winner = False
        self.winner_combo = []

    def get_random_move(self):
        possible_moves = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self._current_moves[row][col].label == "":
                    possible_moves.append((row, col))
        if possible_moves:
            move = random.choice(possible_moves)
            return move
        return None

    # ---------- Minimax helpers ----------

    def _check_winner_for_label(self, label):
        """Check if the given label has a winning combo on the CURRENT board."""
        for combo in self._winning_combos:
            if all(self._current_moves[r][c].label == label for (r, c) in combo):
                return True
        return False

    def _board_full(self):
        """Return True if there are no empty cells on the CURRENT board."""
        for row in self._current_moves:
            for move in row:
                if move.label == "":
                    return False
        return True

    def _minmax(self, is_maximizing, ai_label, opponent_label):
        """
        Core Minimax on the CURRENT board.

        Mutates self._current_moves temporarily and undoes moves after exploring.
        Returns:
            +1 if position is winning for ai_label
            -1 if winning for opponent_label
             0 if draw (with optimal play)
        """
        # Terminal checks on the current simulated board
        if self._check_winner_for_label(ai_label):
            return 1
        if self._check_winner_for_label(opponent_label):
            return -1
        if self._board_full():
            return 0

        if is_maximizing:
            best_score = -999
            # Try all possible moves for AI
            for r in range(self.board_size):
                for c in range(self.board_size):
                    if self._current_moves[r][c].label == "":
                        # Pretend AI plays here
                        self._current_moves[r][c] = Move(r, c, ai_label)
                        score = self._minmax(False, ai_label, opponent_label)
                        # Undo move
                        self._current_moves[r][c] = Move(r, c, "")
                        best_score = max(best_score, score)
            return best_score
        else:
            best_score = 999
            # Try all possible moves for opponent
            for r in range(self.board_size):
                for c in range(self.board_size):
                    if self._current_moves[r][c].label == "":
                        # Pretend opponent plays here
                        self._current_moves[r][c] = Move(r, c, opponent_label)
                        score = self._minmax(True, ai_label, opponent_label)
                        # Undo move
                        self._current_moves[r][c] = Move(r, c, "")
                        best_score = min(best_score, score)
            return best_score

    def get_minmax_move(self):
        """
        Compute the best (row, col) move for the CURRENT player using Minimax.

        This is the "entry point" that the AI uses on its turn.

        It works by:
          - Looping over every empty cell on the current board,
          - Temporarily placing the AI's move in that cell,
          - Calling _minmax(...) to evaluate how good that move is
            assuming both players play optimally afterwards,
          - Undoing the move,
          - Remembering which move gave the highest score.

        Returns:
            (row, col) tuple for the best move, or None if there are no moves.
        """
        # Label for the AI (whoever current_player is right now)
        ai_label = self.current_player.label

        # Assume a standard two-player Tic-Tac-Toe: the other mark is the opponent
        opponent_label = "O" if ai_label == "X" else "X"

        # Start with very low best_score so any real score will be better
        best_score = -999
        best_move = None

        # Try every empty square as a candidate move
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self._current_moves[r][c].label == "":
                    # Pretend the AI plays here
                    self._current_moves[r][c] = Move(r, c, ai_label)

                    # Now it's the opponent's turn, so is_maximizing=False
                    score = self._minmax(False, ai_label, opponent_label)

                    # Undo the move so we can test the next possibility
                    self._current_moves[r][c] = Move(r, c, "")

                    # If this move leads to a better outcome, remember it
                    if score > best_score:
                        best_score = score
                        best_move = (r, c)

        return best_move

# ---------- Console Debugs Generated by ChatGPT ----------
    def _debug(self, msg, depth=0):
        """Small helper to print Minimax debug messages with indentation."""
        if self.debug_minmax:
            indent = "  " * depth
            print(f"{indent}[MM d={depth}] {msg}")

    def _debug_board(self, depth=0):
        """Print the current board layout for debugging."""
        if not self.debug_minmax:
            return
        indent = "  " * depth
        print(f"{indent}Board:")
        for r in range(self.board_size):
            row_labels = [
                (self._current_moves[r][c].label or " ")
                for c in range(self.board_size)
            ]
            print(f"{indent}  " + " | ".join(row_labels))
        print(f"{indent}" + "-" * 10)

    
class TicTacToeBoard(tk.Tk):
    def __init__(self, game):
        super().__init__()
        self.title("Tic-Tac-Toe Game")
        self._cells = {}
        self._game = game
        self._create_menu()
        self._create_board_display()
        self._create_board_grid()

    def _create_menu(self):
        menu_bar = tk.Menu(master=self)
        self.config(menu=menu_bar)
        file_menu = tk.Menu(master=menu_bar)
        file_menu.add_command(label="Play Again", command=self.reset_board)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=quit)
        file_menu.add_command(label="Random", command=self._ai_play_random)
        file_menu.add_command(label="Minimax", command=self._ai_play_minmax)
        menu_bar.add_cascade(label="File", menu=file_menu)

    def _create_board_display(self):
        display_frame = tk.Frame(master=self)
        display_frame.pack(fill=tk.X)
        self.display = tk.Label(
            master=display_frame,
            text="Ready?",
            font=font.Font(size=28, weight="bold"),
        )
        self.display.pack()

    def _create_board_grid(self):
        grid_frame = tk.Frame(master=self)
        grid_frame.pack()
        for row in range(self._game.board_size):
            self.rowconfigure(row, weight=1, minsize=50)
            self.columnconfigure(row, weight=1, minsize=75)
            for col in range(self._game.board_size):
                button = tk.Button(
                    master=grid_frame,
                    text="",
                    font=font.Font(size=36, weight="bold"),
                    fg="black",
                    width=5,
                    height=2,
                    highlightbackground="lightblue",
                )
                self._cells[button] = (row, col)
                button.bind("<ButtonPress-1>", self.play)
                button.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

    def play(self, event):
        """Handle a player's move."""
        clicked_btn = event.widget
        row, col = self._cells[clicked_btn]
        move = Move(row, col, self._game.current_player.label)
        if self._game.is_valid_move(move):
            self._update_button(clicked_btn)
            self._game.process_move(move)
            if self._game.is_tied():
                self._update_display(msg="Tied game!", color="red")
            elif self._game.has_winner():
                self._highlight_cells()
                msg = f'Player "{self._game.current_player.label}" won!'
                color = self._game.current_player.color
                self._update_display(msg, color)
            else:
                self._game.toggle_player()
                msg = f"{self._game.current_player.label}'s turn"
                self._update_display(msg)
                if self._game.current_player.isAi:
                    # Use Minimax AI instead of random
                    self._ai_play_minmax()

    def _ai_play_random(self):
        """Handle AI moves (random)."""
        print("AI's turn (Random)")
        rand_move = self._game.get_random_move()
        if rand_move is None:
            return
        row, col = rand_move
        move = Move(row, col, self._game.current_player.label)
        if move and self._game.is_valid_move(move):
            for button, (btn_row, btn_col) in self._cells.items():
                if (btn_row, btn_col) == (move.row, move.col):
                    self._update_button(button)
                    self._game.process_move(move)
                    break
        self._game.toggle_player()
        msg = f"{self._game.current_player.label}'s turn"
        self._update_display(msg)

    def _ai_play_minmax(self):
        """Handle AI moves using the Minimax algorithm."""
        print("AI (Minimax) turn")

        best_move = self._game.get_minmax_move()
        if best_move is None:
            return  # No possible moves (full/terminal board)

        row, col = best_move
        move = Move(row, col, self._game.current_player.label)

        if self._game.is_valid_move(move):
            # Find the matching button for this move
            for button, (btn_row, btn_col) in self._cells.items():
                if (btn_row, btn_col) == (move.row, move.col):
                    self._update_button(button)
                    self._game.process_move(move)
                    break

            # After AI moves, check game state just like in `play`
            if self._game.is_tied():
                self._update_display(msg="Tied game!", color="red")
            elif self._game.has_winner():
                self._highlight_cells()
                msg = f'Player "{self._game.current_player.label}" won!'
                color = self._game.current_player.color
                self._update_display(msg, color)
            else:
                self._game.toggle_player()
                msg = f"{self._game.current_player.label}'s turn"
                self._update_display(msg)

    def _update_button(self, clicked_btn):
        clicked_btn.config(text=self._game.current_player.label)
        clicked_btn.config(fg=self._game.current_player.color)

    def _update_display(self, msg, color="black"):
        self.display["text"] = msg
        self.display["fg"] = color

    def _highlight_cells(self):
        for button, coordinates in self._cells.items():
            if coordinates in self._game.winner_combo:
                button.config(highlightbackground="red")

    def reset_board(self):
        """Reset the game's board to play again."""
        self._game.reset_game()
        self._update_display(msg="Ready?")
        for button in self._cells.keys():
            button.config(highlightbackground="lightblue")
            button.config(text="")
            button.config(fg="black")


def main():
    """Create the game's board and run its main loop."""
    game = TicTacToeGame()
    board = TicTacToeBoard(game)
    board.mainloop()


if __name__ == "__main__":
    main()
