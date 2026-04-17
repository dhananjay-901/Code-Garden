#include <iostream>
using namespace std;
// STL container - a data structure that can store and manage a collection of elements. It provides various functionalities such as insertion, deletion, and access to the elements. Examples of STL containers include vector, list, set, map, etc.
/*custom stl container
 * step 0 -
 * i want a box that - stores elements, grows when needed and lets me access items and also also works in loops.
 */

//formation of dynamic array to store data from the custom stl container execution
template <typename T>
class Box {
    private:
    T* data;
    int size;
    int capacity;


// where elements will be stored - data
// how many elements are stored - size
public:
Box(){
    data = new T[10]; // inital size of 10
    size = 0;
    capacity = 10;
}

//when i will insert where does it go - push_back
//what if array is full - grow the array
void push_back(T value){
    if(size == capacity){
        resize();
    }else{
        data[size] = value;
        size++;
    }
}

//resize the array when it is full
void resize(){
    int newsize = size * 2; // double the size
    T* newdata = new T[newsize]; // create new array
    for(int i =0;i <size; i++){
        newdata[i] = data[i];
    }

    delete[] data;
    data = newdata;
    size = newsize;
}

//how do i access elements - operator[]
T& operator[](int index){
    return data[index];
}
//when i need to kno the size or emptiness of the my custom stl container - size and empty
int getsize(){
    return size;
}
bool empty(){
    if (size == 0){
        cout << "Box is empty" << endl;
        return true;
    }else{
        cout << "Box is not empty" << endl;
        return false;
    }
}
//iteratoes maint hat will allow us to loop through the elements of the box
T* begin(){
    return data;
}
T* end(){
    return data + size;
    }
};

int main(){
    Box<int> myBox;
    myBox.push_back(1);
    myBox.push_back(2);
    myBox.push_back(3);

    for (auto x: myBox){
        cout << x << " ";
    }

    cout  << "size: " << myBox.getsize() << endl;
    return 0;
}
