#include <iostream>
#include <fstream>
#include <string>
#include <cstdio> // Required for remove() and rename()

using namespace std;

int main() {
    int nots;
    string task;
    int choice;

    cout << "1. Insert tasks in file" << endl;
    cout << "2. Display tasks from file" << endl;
    cout << "3. To delete a specific task" << endl;
    cout << "4. To exit" << endl;
    cout << "Enter choice: ";
    cin >> choice;
    cin.ignore();

    switch (choice) {
        case 1: { // Insert tasks
            // if you want to append to existing tasks instead of overwriting
            ofstream MyFile("to_do.txt", ios::app); 
            cout << "Enter number of tasks: ";
            cin >> nots;
            cin.ignore();

            for (int i = 0; i < nots; i++) {
                cout << "Enter task: ";
                getline(cin, task);
                MyFile << task << endl;
            }
            MyFile.close();
            break;
        }

        case 2: { // Display tasks
            ifstream MyFile("to_do.txt");
            string line;
            int count = 1;
            cout << "\n--- Your To-Do List ---" << endl;
            while (getline(MyFile, line)) {
                cout << count << ". " << line << endl;
                count++;
            }
            MyFile.close();
            break;
        }

        case 3: { // Delete a task
            ifstream MyFile("to_do.txt");
            ofstream TempFile("temp.txt");
            string line;
            int lineToDelete;
            int currentLine = 1;

            cout << "Enter the task number you want to delete: ";
            cin >> lineToDelete;

            bool found = false;
            while (getline(MyFile, line)) {
                // If the current line is NOT the one we want to delete, write it to temp
                if (currentLine != lineToDelete) {
                    TempFile << line << endl;
                } else {
                    found = true;
                }
                currentLine++;
            }

            MyFile.close();
            TempFile.close();

            // Delete the old file and rename the temporary one
            remove("to_do.txt");
            rename("temp.txt", "to_do.txt");

            if (found) {
                cout << "Task deleted successfully!" << endl;
            } else {
                cout << "Task number not found." << endl;
            }
            break;
        }

        case 4:
            return 0;

        default:
            cout << "Invalid choice!" << endl;
    }

    return 0;
}
