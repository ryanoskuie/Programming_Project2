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
    Player(label="X", color="blue", isAi=False), # Human Player
    Player(label="O", color="green", isAi=True), # AI Player
)
POSITION_WEIGHTS = [
    [2, 1, 2],
    [1, 3, 1],
    [2, 1, 2]
]

class TicTacToeGame:
    def __init__(self, players=DEFAULT_PLAYERS, board_size=BOARD_SIZE):
        self._players = cycle(players)
        self.gamemode = "PvP"
        self.board_size = board_size
        self.current_player = next(self._players)
        self.winner_combo = []
        self._current_moves = []
        self._has_winner = False
        self._winning_combos = []
        self._setup_board()

        # Minimax debugging
        self.debug_minmax = True      # Set to False to silence Minimax debug output
        self._nodes_evaluated = 0     # Counts how many states Minimax checked last search

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
        """
        Return True if the given label ("X" or "O") currently has a winning
        combination on the board.

        This uses the same _winning_combos that process_move() relies on,
        but it does NOT modify any game state (no flags, no winner_combo).
        That makes it safe to call inside Minimax while we're "pretending"
        to place moves on the board.
        """
        for combo in self._winning_combos:
            if all(self._current_moves[r][c].label == label for (r, c) in combo):
                return True
        return False

    def _board_full(self):
        """
        Return True if there are no empty cells ("") on the CURRENT board.

        Used by Minimax to detect a draw (no more moves left) in the
        simulated game tree.
        """
        for row in self._current_moves:
            for move in row:
                if move.label == "":
                    return False
        return True

    def _minmax(self, is_maximizing, ai_label, opponent_label, alpha, beta, depth):
        """
        Core Minimax on the CURRENT board.

        This function recursively explores all possible future moves for both
        players and evaluates the final outcome assuming optimal play.

        It works by:
          - Temporarily placing a move on self._current_moves,
          - Recursively calling itself to explore deeper moves,
          - Undoing that move (restoring the previous state),
          - Tracking the best score seen for either the maximizing
            (AI) or minimizing (opponent) player.

        Args:
            is_maximizing (bool):
                True  -> it's the AI's turn (we try to MAXIMIZE the score)
                False -> it's the opponent's turn (we try to MINIMIZE the score)
            ai_label (str):
                The label used by the AI player, e.g. "O" (or "X").
            opponent_label (str):
                The label used by the opponent, e.g. "X" (or "O").

        Returns:
            int:
                +1  if this position is a win for ai_label
                -1  if this position is a win for opponent_label
                 0  if this position is a draw (with optimal play)
        """
        # Count this simulated node for debug stats
        self._nodes_evaluated += 1

        # --- 1. Terminal checks on the current simulated board ---
        if self._check_winner_for_label(ai_label):
            return 1000 + depth
        if self._check_winner_for_label(opponent_label):
            return -1000 - depth
        if self._board_full():
            return 0
        
        if depth == 0:
            return self.evaluate_board()

        # --- 2. Recursive case: explore all children moves ---
        if is_maximizing:
            best_score = -999
            # AI's turn: choose the move with the highest score
            for r in range(self.board_size):
                for c in range(self.board_size):
                    if self._current_moves[r][c].label == "":
                        
                        # Pretend AI plays here
                        self._current_moves[r][c] = Move(r, c, ai_label)
                        score = self._minmax(False, ai_label, opponent_label, alpha, beta, depth - 1)
                        
                        # Undo move
                        self._current_moves[r][c] = Move(r, c, "")
                        best_score = max(best_score, score)
                        
                        alpha = max(alpha, best_score)
                        if beta <= alpha:
                            return best_score
            return best_score
        else:
            best_score = 999
            # Opponent's turn: assume they try to minimize the AI's score
            for r in range(self.board_size):
                for c in range(self.board_size):
                    if self._current_moves[r][c].label == "":
                        
                        # Pretend opponent plays here
                        self._current_moves[r][c] = Move(r, c, opponent_label)
                        score = self._minmax(True, ai_label, opponent_label, alpha, beta, depth - 1)
                        
                        # Undo move
                        self._current_moves[r][c] = Move(r, c, "")
                        best_score = min(best_score, score)

                        beta = min(beta, best_score)
                        if beta <= alpha:
                            return best_score
            return best_score

    def get_minmax_move(self):
        """
        Compute the best (row, col) move for the CURRENT player using Minimax.

        Debug output:
          - prints the board before search,
          - prints each top-level move and its final score,
          - prints the chosen move and total nodes evaluated.
        """
        ai_label = self.current_player.label
        opponent_label = "O" if ai_label == "X" else "X"

        # Reset node counter for this search
        self._nodes_evaluated = 0

        # --- Configuration ---
        # Controls to what depth the AI can search to (9 is perfect play on a 3x3)
        max_depth = 4
        #----------------------
        if self.debug_minmax:
            print("\n=== Minimax search start ===")
            print(f"AI label      : {ai_label}")
            print(f"Opponent label: {opponent_label}")

        best_score = -9999
        best_move = None
        alpha = -9999
        beta = 9999

        # Top-level: try every empty square as the first AI move
        for r in range(self.board_size):
            for c in range(self.board_size):
                if self._current_moves[r][c].label == "":
                    if self.debug_minmax:
                        print(f"Top-level: try AI move at ({r}, {c})")

                    # Pretend AI plays here
                    self._current_moves[r][c] = Move(r, c, ai_label)

                    # Run Minimax assuming opponent moves next (MIN node)
                    score = self._minmax(False, ai_label, opponent_label, alpha, beta, max_depth - 1)

                    # Undo move
                    self._current_moves[r][c] = Move(r, c, "")

                    if self.debug_minmax:
                        print(f"  -> move ({r}, {c}) gets score {score}")

                    if score > best_score:
                        best_score = score
                        best_move = (r, c)
                        alpha = max(alpha, best_score)
                        if self.debug_minmax:
                            print(f"  -> NEW BEST move ({r}, {c}) with score {best_score}")

        if self.debug_minmax:
            print(f"Chosen move   : {best_move} with score {best_score}")
            print(f"Nodes checked : {self._nodes_evaluated}")
            print("=== Minimax search end ===\n")

        return best_move
    
    def evaluate_position(self):
        """
        Heuristic 1: Positional Values
        3 for center
        2 for corner
        1 for edges
        Returns net score of the board (AI score - Opp score)
        """
        ai_label = self.current_player.label
        opp_label = "O" if ai_label == "X" else "X"
        score = 0

        for r in range(self.board_size):
            for c in range(self.board_size):
                label = self._current_moves[r][c].label
                
                if r < 3 and c < 3:
                    cell_value = POSITION_WEIGHTS[r][c]
                else:
                    cell_value = 0 

                if label == ai_label:
                    score += cell_value
                elif label == opp_label:
                    score -= cell_value
        return score
    
    def evaluate_line(self, combo):
        """
        Heuristic 2: Line Counting
        Scoring (AI):                   Scoring (Opponent):
            +100 for 3 in a row             -100 for 3 in a row 
            +10 for 2 in a row              -10 for 2 in a row 
            +1 for 1 in a row               -1 for 1 in a row   
            0 if a line is blocked          0 if a line is blocked
        """
        ai_label = self.current_player.label
        opp_label = "O" if ai_label == "X" else "X"
        ai_count = 0
        opp_count = 0

        # Count amount of pieces in a row, col or diag
        for row, col in combo:
            label = self._current_moves[row][col].label
            if label == ai_label:
                ai_count += 1
            elif label == opp_label:
                opp_count += 1

        # Evaluate based on counts
        if ai_count > 0 and opp_count > 0:
            return 0
        
        if ai_count > 0:
            if ai_count == 3:
                return 100
            elif ai_count == 2:
                return 10
            else:
                return 1
            
        if opp_count > 0:
            if opp_count == 3:
                return -100
            elif opp_count == 2:
                return -10
            else:
                return -1
        return 0

    def evaluate_board(self):
        """
        Evaluation function: linear sum
        Runs the heuristic on every possible winning line and adds up all the scores
        Positive is AI advantage, negative is opponent advantage
        """
        threat_score = 0
        for combo in self._winning_combos:
            threat_score += self.evaluate_line(combo)
        
        position_score = self.evaluate_position()

        total_score = threat_score + position_score
        return total_score
    
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
        file_menu.add_command(label="PvP", command=self._change_gm_pvp)
        file_menu.add_command(label="Random", command=self._change_gm_ai_rand)
        file_menu.add_command(label="Minimax", command=self._change_gm_ai_minmax)
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

        self.tutor_btn = tk.Button(
            master=display_frame,
            text="Tutor Hint",
            font=font.Font(size=12),
            command=self._suggest_move
        )
        self.tutor_btn.pack(pady=5)

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
                    highlightthickness=4
                )
                self._cells[button] = (row, col)               
                button.bind("<ButtonPress-1>", self.play)
                button.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

    def _suggest_move(self):
        """Calculates the best move for the current player and highlights it."""
        if self._game.current_player.isAi:
            self._update_display("Not available", "red")
        
        best_move = self._game.get_minmax_move()
        if best_move:
            row, col = best_move
            for button, coords in self._cells.items():
                if coords == (row, col):
                    self._tutor_hint(button)
                    break

    def _tutor_hint(self, button):
        """Highlights a button to indicate a hint of the next best move"""
        current_symbol = self._game.current_player.label
        original_text = button.cget("text")
        button.config(text=current_symbol)
        self.after(500, lambda: button.config(text=original_text))

    def _change_gm_ai_rand(self):
        self._game.gamemode = "Random"
        self.reset_board()

    def _change_gm_ai_minmax(self):
        self._game.gamemode = "Minmax"
        self.reset_board()

    def _change_gm_pvp(self):
        self._game.gamemode = "PvP"
        self.reset_board()

    def play(self, event):
        """Handle a player's move."""
        if (self._game.gamemode == "Random"):
            self.after(1000, self._ai_play_random)
        elif (self._game.gamemode == "Minmax"):
            self.after(1000, self._ai_play_minmax)
        elif (self._game.gamemode == "PvP"):
            self._play_pvp(event)
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
    
    def _ai_play_random(self):
        """Handle AI moves."""
        rand_move = self._game.get_random_move()
        row, col = rand_move
        move = Move(row, col, self._game.current_player.label)
        if move and self._game.is_valid_move(move):

            for button, (row, col) in self._cells.items():
                if (row, col) == (move.row, move.col):
                    self._update_button(button)
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

    def _play_pvp(self, event):
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
