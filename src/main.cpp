#include "calculator.hpp"
#include <iostream>
#include <iomanip>

int main() {
    Calculator calc;

    std::cout << "=== Calculator Demo ===" << std::endl;
    std::cout << std::fixed << std::setprecision(4);

    std::cout << "Add: 10.5 + 5.3 = " << calc.add(10.5, 5.3) << std::endl;
    std::cout << "Subtract: 10.5 - 5.3 = " << calc.subtract(10.5, 5.3) << std::endl;
    std::cout << "Multiply: 10.5 * 5.3 = " << calc.multiply(10.5, 5.3) << std::endl;
    std::cout << "Divide: 10.5 / 5.3 = " << calc.divide(10.5, 5.3) << std::endl;
    std::cout << "Power: 2.5 ^ 3 = " << calc.power(2.5, 3) << std::endl;
    std::cout << "Sqrt: sqrt(16) = " << calc.sqrt(16.0) << std::endl;

    std::cout << "\n=== Edge Cases ===" << std::endl;
    try {
        std::cout << "Divide by zero: ";
        calc.divide(10.0, 0.0);
    } catch (const std::exception& e) {
        std::cout << "Caught: " << e.what() << std::endl;
    }

    try {
        std::cout << "Sqrt of negative: ";
        calc.sqrt(-4.0);
    } catch (const std::exception& e) {
        std::cout << "Caught: " << e.what() << std::endl;
    }

    std::cout << "\n=== Large Numbers ===" << std::endl;
    std::cout << "1e100 + 1e100 = " << calc.add(1e100, 1e100) << std::endl;

    return 0;
}