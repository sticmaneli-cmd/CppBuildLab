#include "calculator.hpp"
#include <gtest/gtest.h>
#include <cmath>
#include <limits>

class CalculatorTest : public ::testing::Test {
protected:
    Calculator calc;
};

TEST_F(CalculatorTest, Add_Basic) {
    EXPECT_DOUBLE_EQ(calc.add(2.0, 3.0), 5.0);
    EXPECT_DOUBLE_EQ(calc.add(-1.0, 1.0), 0.0);
    EXPECT_DOUBLE_EQ(calc.add(0.0, 0.0), 0.0);
}

TEST_F(CalculatorTest, Add_LargeNumbers) {
    EXPECT_DOUBLE_EQ(calc.add(1e100, 1e100), 2e100);
}

TEST_F(CalculatorTest, Subtract_Basic) {
    EXPECT_DOUBLE_EQ(calc.subtract(5.0, 3.0), 2.0);
    EXPECT_DOUBLE_EQ(calc.subtract(0.0, 5.0), -5.0);
}

TEST_F(CalculatorTest, Multiply_Basic) {
    EXPECT_DOUBLE_EQ(calc.multiply(3.0, 4.0), 12.0);
    EXPECT_DOUBLE_EQ(calc.multiply(-2.0, 3.0), -6.0);
    EXPECT_DOUBLE_EQ(calc.multiply(0.0, 100.0), 0.0);
}

TEST_F(CalculatorTest, Divide_Basic) {
    EXPECT_DOUBLE_EQ(calc.divide(10.0, 2.0), 5.0);
    EXPECT_DOUBLE_EQ(calc.divide(7.0, 2.0), 3.5);
}

TEST_F(CalculatorTest, Divide_ByZero) {
    EXPECT_THROW(calc.divide(10.0, 0.0), std::domain_error);
    EXPECT_THROW(calc.divide(1.0, 1e-300), std::domain_error);
}

TEST_F(CalculatorTest, Power_Basic) {
    EXPECT_DOUBLE_EQ(calc.power(2.0, 3), 8.0);
    EXPECT_DOUBLE_EQ(calc.power(5.0, 0), 1.0);
    EXPECT_DOUBLE_EQ(calc.power(2.0, -2), 0.25);
}

TEST_F(CalculatorTest, Sqrt_Basic) {
    EXPECT_DOUBLE_EQ(calc.sqrt(16.0), 4.0);
    EXPECT_DOUBLE_EQ(calc.sqrt(0.0), 0.0);
    EXPECT_NEAR(calc.sqrt(2.0), std::sqrt(2.0), 1e-10);
}

TEST_F(CalculatorTest, Sqrt_Negative) {
    EXPECT_THROW(calc.sqrt(-1.0), std::domain_error);
    EXPECT_THROW(calc.sqrt(-1e-10), std::domain_error);
}

TEST_F(CalculatorTest, ValidateFinite_NaN) {
    EXPECT_THROW(calc.add(std::numeric_limits<double>::quiet_NaN(), 1.0), std::domain_error);
    EXPECT_THROW(calc.add(1.0, std::numeric_limits<double>::quiet_NaN()), std::domain_error);
}

TEST_F(CalculatorTest, ValidateFinite_Infinity) {
    EXPECT_THROW(calc.add(std::numeric_limits<double>::infinity(), 1.0), std::domain_error);
    EXPECT_THROW(calc.add(1.0, -std::numeric_limits<double>::infinity()), std::domain_error);
}

TEST_F(CalculatorTest, Overflow) {
    EXPECT_THROW(calc.add(1e308, 1e308), std::domain_error);
    EXPECT_THROW(calc.multiply(1e200, 1e200), std::domain_error);
}