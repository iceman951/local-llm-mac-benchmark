import java.util.Objects;

class Rational {

    private int numerator;
    private int denominator;

    Rational(int numerator, int denominator) {
        if (denominator == 0) {
            throw new IllegalArgumentException("Denominator cannot be zero.");
        }
        int gcd = gcd(numerator, denominator);
        this.numerator = numerator / gcd;
        this.denominator = denominator / gcd;
        if (this.denominator < 0) {
            this.numerator = -this.numerator;
            this.denominator = -this.denominator;
        }
    }

    int getNumerator() {
        return numerator;
    }

    int getDenominator() {
        return denominator;
    }

    Rational add(Rational other) {
        int newNumerator = this.numerator * other.denominator + other.numerator * this.denominator;
        int newDenominator = this.denominator * other.denominator;
        return new Rational(newNumerator, newDenominator);
    }

    Rational subtract(Rational other) {
        int newNumerator = this.numerator * other.denominator - other.numerator * this.denominator;
        int newDenominator = this.denominator * other.denominator;
        return new Rational(newNumerator, newDenominator);
    }

    Rational multiply(Rational other) {
        int newNumerator = this.numerator * other.numerator;
        int newDenominator = this.denominator * other.denominator;
        return new Rational(newNumerator, newDenominator);
    }

    Rational divide(Rational other) {
        if (other.numerator == 0) {
            throw new ArithmeticException("Division by zero.");
        }
        int newNumerator = this.numerator * other.denominator;
        int newDenominator = this.denominator * other.numerator;
        return new Rational(newNumerator, newDenominator);
    }

    Rational abs() {
        return new Rational(Math.abs(this.numerator), Math.abs(this.denominator));
    }

    Rational pow(int power) {
        if (power >= 0) {
            return new Rational((int) Math.pow(this.numerator, power), (int) Math.pow(this.denominator, power));
        } else {
            return new Rational((int) Math.pow(this.denominator, -power), (int) Math.pow(this.numerator, -power));
        }
    }

    double exp(double exponent) {
        return Math.pow((double) this.numerator, exponent) / Math.pow((double) this.denominator, exponent);
    }

    double exp(Rational exponent) {
        double base = (double) this.numerator / this.denominator;
        double result = Math.pow(base, exponent.numerator);
        return Math.pow(result, 1.0 / exponent.denominator);
    }

    @Override
    public String toString() {
        return String.format("%d/%d", this.numerator, this.denominator);
    }

    @Override
    public boolean equals(Object obj) {
        if (obj instanceof Rational other) {
            return this.numerator == other.numerator && this.denominator == other.denominator;
        }
        return false;
    }

    @Override
    public int hashCode() {
        return Objects.hash(this.numerator, this.denominator);
    }

    private int gcd(int a, int b) {
        while (b != 0) {
            int temp = b;
            b = a % b;
            a = temp;
        }
        return a;
    }
}
