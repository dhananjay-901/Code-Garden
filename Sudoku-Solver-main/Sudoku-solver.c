#include <stdio.h>
#include <stdbool.h>

#define SIZE 9
// final code
void printGrid(int grid[SIZE][SIZE]) {
    for (int i = 0; i < SIZE; i++) {
        for (int j = 0; j < SIZE; j++)
            printf("%d ", grid[i][j]);
        printf("\n");
    }
}

bool isSafe(int grid[SIZE][SIZE], int row, int col, int num) {
    for (int x = 0; x < SIZE; x++) {
        if (grid[row][x] == num || grid[x][col] == num)
            return false;
    }

    int startRow = row - row % 3;
    int startCol = col - col % 3;

    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 3; j++)
            if (grid[startRow + i][startCol + j] == num)
                return false;

    return true;
}

bool findEmpty(int grid[SIZE][SIZE], int *row, int *col) {
    for (*row = 0; *row < SIZE; (*row)++)
        for (*col = 0; *col < SIZE; (*col)++)
            if (grid[*row][*col] == 0)
                return true;

    return false;
}

bool solveSudoku(int grid[SIZE][SIZE]) {
    int row, col;

    if (!findEmpty(grid, &row, &col))
        return true;

    for (int num = 1; num <= 9; num++) {
        if (isSafe(grid, row, col, num)) {
            grid[row][col] = num;

            if (solveSudoku(grid))
                return true;

            grid[row][col] = 0;
        }
    }
    return false;
}

int main() {
    int grid[SIZE][SIZE] = {0};
    int a, b, c;

    printf("Enter inputs as: x y value (1-based, origin bottom-left)\n");
    printf("Enter -1 -1 -1 to stop\n");

    while (1) {
        scanf("%d %d %d", &a, &b, &c);

        if (a == -1 && b == -1 && c == -1)
            break;

        if (a < 1 || a > 9 || b < 1 || b > 9 || c < 1 || c > 9) {
            printf("Invalid input!\n");
            continue;
        }

        // Convert (1-based bottom-left) -----> array index
        int row = SIZE - b;
        int col = a - 1;

        grid[row][col] = c;
    }

    if (solveSudoku(grid)) {
        printf("\nSolved Sudoku:\n");
        printGrid(grid);
    } else {
        printf("No solution exists.\n");
    }

    return 0;
}
