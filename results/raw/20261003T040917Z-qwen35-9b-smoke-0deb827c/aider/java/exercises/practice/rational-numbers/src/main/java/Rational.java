import java.util.Objects;

class Rational {
    private int numerator;
    private int denominator;
    
    Rational(int numerator, int denominator) {
        if (denominator == 0) {
            throw new IllegalArgumentException("Denominator cannot be zero");
        }
        
        // Calculate GCD and reduce to lowest terms
        int gcd = Math.abs(gcd(numerator, denominator));
        this.numerator = numerator / gcd;
        this.denominator = denominator / gcd;
        
        // Ensure standard form (denominator positive)
        if (this.denominator < 0) {
            this.numerator = -this.numerator;
            this.denominator = -this.denominator;
        }
    }
    
    private int gcd(int a, int b) {
        return b == 0 ? a : gcd(b, a % b);
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
            throw new IllegalArgumentException("Cannot divide by zero");
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
            int newNumerator = (int) Math.pow(this.numerator, power);
            int newDenominator = (int) Math.pow(this.denominator, power);
            return new Rational(newNumerator, newDenominator);
        } else {
            int m = Math.abs(power);
            int newNumerator = (int) Math.pow(this.denominator, m);
            int newDenominator = (int) Math.pow(this.numerator, m);
            return new Rational(newNumerator, newDenominator);
        }
    }
    
    double exp(double exponent) {
        // r^x = (a^x)/(b^x) where r = a/b
        double numPow = Math.pow(this.numerator, exponent);
        double denPow = Math.pow(this.denominator, exponent);
        return numPow / denPow;
    }
    
    @Override
    public String toString() {
        return String.format("%d/%d", this.getNumerator(), this.getDenominator());
    }
    
    @Override
    public boolean equals(Object obj) {
        if (obj instanceof Rational other) {
            return this.getNumerator() == other.getNumerator()
                    && this.getDenominator() == other.getDenominator();
        }
        
        return false;
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(this.getNumerator(), this.getDenominator());
    }
}
