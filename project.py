import random

def print_board(board):
    for row in board:
        print(" | ".join(row))
        print("-" * 9)

def check_winner(board, player):
    # Check rows, columns, and diagonals
    for i in range(3):
        if all([cell == player for cell in board[i]]):
            return True
        if all([board[j][i] == player for j in range(3)]):
            return True
    if all([board[i][i] == player for i in range(3)]):
        return True
    if all([board[i][2 - i] == player for i in range(3)]):
        return True
    return False

def get_empty_cells(board):
    return [(i, j) for i in range(3) for j in range(3) if board[i][j] == " "]

def user_move(board):
    while True:
        try:
            move = input("Enter your move (row and column: 1 1): ")
            row, col = map(int, move.split())
            row -= 1
            col -= 1

            if row not in range(3) or col not in range(3):
                print("Row and column must be between 1 and 3.")
                continue

            if board[row][col] == " ":
                board[row][col] = "X"
                break
            else:
                print("Cell already taken. Try again.")
        except ValueError:
            print("Invalid input. Enter row and column numbers like: 1 1")

def ai_move(board):
    empty = get_empty_cells(board)
    if empty:
        row, col = random.choice(empty)
        board[row][col] = "O"

def main():
    board = [[" " for _ in range(3)] for _ in range(3)]
    print("Welcome to Tic-Tac-Toe! You are X, AI is O.")
    print_board(board)
    while True:
        user_move(board)
        print_board(board)
        if check_winner(board, "X"):
            print("Congratulations! You win!")
            break
        if not get_empty_cells(board):
            print("It's a draw!")
            break
        ai_move(board)
        print("AI's move:")
        print_board(board)
        if check_winner(board, "O"):
            print("AI wins!")
            break
        if not get_empty_cells(board):
            print("It's a draw!")
            break

if __name__ == "__main__":
    main()
