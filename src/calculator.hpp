#pragma once

#include <stdexcept>
#include <string>

class Calculator {
public:
    Calculator() = default;
    ~Calculator() = default;

    double add(double a, double b) const;
    double subtract(double a, double b) const;
    double multiply(double a, double b) const;
    double divide(double a, double b) const;
    double power(double base, int exponent) const;
    double sqrt(double value) const;

private:
    void validateFinite(double value, const std::string& name) const;
};