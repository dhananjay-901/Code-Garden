#include <SFML/Graphics.hpp>
#include <vector>
#include <optional>
using namespace std;

const int cellsize = 20;
const int gridwidth =30;
const int gridheight = 30;

void spawnfood(sf::Vector2i& food, std::vector<sf::Vector2i>& snake) {
    bool valid = false;

    while (!valid) {
        valid = true;

        food.x = rand() % gridwidth;
        food.y = rand() % gridheight;

        for (auto& segment : snake) {
            if (segment == food) {
                valid = false;
                break;
            }
        }
    }
}

int main(){
    sf::RenderWindow window(sf::VideoMode(sf::Vector2u(gridwidth * cellsize, gridheight * cellsize)), "Snake Game");
    bool valid = false;
    sf::Vector2i direction(1, 0); // moving right
    sf::Vector2i food(10, 10);
    sf::Clock clock;
    float timer = 0;
    float delay = 0.2f;

    vector<sf::Vector2i> snake = {
        {5, 5},
        {4, 5},
        {3, 5}
    };

    while(window.isOpen()){
        while(auto event = window.pollEvent()){
            if (auto keyEvent = event->getIf<sf::Event::KeyPressed>()) {
                auto key = keyEvent->code;

                if (key == sf::Keyboard::Key::Up && direction.y != 1)
                    direction = {0, -1};

                if (key == sf::Keyboard::Key::Down && direction.y != -1)
                    direction = {0, 1};

                if (key == sf::Keyboard::Key::Left && direction.x != 1)
                    direction = {-1, 0};

                if (key == sf::Keyboard::Key::Right && direction.x != -1)
                    direction = {1, 0};
            }
            if(event->is<sf::Event::Closed>()){
                window.close();
            }
        }

        float time = clock.restart().asSeconds();
        timer += time;
        if (timer > delay) {
            timer = 0;
            sf::Vector2i newHead = snake[0] + direction;

            if(newHead.x < 0 || newHead.x >= gridwidth || newHead.y < 0 || newHead.y >= gridheight) {
                window.close();
            }

            for(int i=1;i<snake.size();i++){
                if(snake[i] == newHead) {
                    window.close();
                }
            }

            snake.insert(snake.begin(), newHead);
            if(newHead == food){
                spawnfood(food, snake);
            }else{
                snake.pop_back();
            }
        }

        window.clear();
        //draw one block
        for(auto& segment : snake){
            sf::RectangleShape block(sf::Vector2f(cellsize, cellsize));
            block.setFillColor(sf::Color::Green);
            block.setPosition(sf::Vector2f(segment.x * cellsize, segment.y * cellsize));
            window.draw(block);
        }

        sf::RectangleShape foodShape(sf::Vector2f(cellsize, cellsize));
        foodShape.setFillColor(sf::Color::Red);
        foodShape.setPosition(sf::Vector2f(food.x * cellsize, food.y * cellsize));
        window.draw(foodShape);
        window.display();
    }
}
