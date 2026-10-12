#include "calculator.hpp"
#include <cmath>
#include <limits>
#include <stdexcept>

double Calculator::add(double a, double b) const {
    validateFinite(a, "a");
    validateFinite(b, "b");
    double result = a + b;
    validateFinite(result, "result");
    return result;
}

double Calculator::subtract(double a, double b) const {
    validateFinite(a, "a");
    validateFinite(b, "b");
    double result = a - b;
    validateFinite(result, "result");
    return result;
}

double Calculator::multiply(double a, double b) const {
    validateFinite(a, "a");
    validateFinite(b, "b");
    double result = a * b;
    validateFinite(result, "result");
    return result;
}

double Calculator::divide(double a, double b) const {
    validateFinite(a, "a");
    validateFinite(b, "b");
    if (std::abs(b) < std::numeric_limits<double>::epsilon()) {
        throw std::domain_error("Division by zero");
    }
    double result = a / b;
    validateFinite(result, "result");
    return result;
}

double Calculator::power(double base, int exponent) const {
    validateFinite(base, "base");
    if (exponent == 0) {
        return 1.0;
    }
    double result = std::pow(base, exponent);
    validateFinite(result, "result");
    return result;
}

double Calculator::sqrt(double value) const {
    validateFinite(value, "value");
    if (value < 0.0) {
        throw std::domain_error("Square root of negative number");
    }
    return std::sqrt(value);
}

void Calculator::validateFinite(double value, const std::string& name) const {
    if (!std::isfinite(value)) {
        throw std::domain_error(name + " is not a finite number");
    }
}