package alphametics

import (
	"errors"
	"sort"
	"strings"
)

func Solve(puzzle string) (map[string]int, error) {
	// Remove spaces and split the puzzle into words
	puzzle = strings.ReplaceAll(puzzle, " ", "")
	words := strings.Split(puzzle, "==")[0]
	words = strings.Split(words, "+")

	// Extract unique letters and the result
	letters := make(map[rune]bool)
	for _, word := range words {
		for _, letter := range word {
			letters[letter] = true
		}
	}
	result := strings.Split(puzzle, "==")[1]
	for _, letter := range result {
		letters[letter] = true
	}

	// Convert letters to a slice for sorting
	lettersSlice := make([]rune, 0, len(letters))
	for letter := range letters {
		lettersSlice = append(lettersSlice, letter)
	}

	// Sort letters to ensure consistent digit assignment
	sort.Slice(lettersSlice, func(i, j int) bool {
		return lettersSlice[i] < lettersSlice[j]
	})

	// Generate all possible digit assignments
	digits := make([]int, len(letters))
	for i := 0; i < len(digits); i++ {
		digits[i] = i
	}

	// Try all permutations of digits
	for {
		// Create a map from letter to digit
		letterToDigit := make(map[rune]int)
		for i, letter := range lettersSlice {
			letterToDigit[letter] = digits[i]
		}

		// Check if the digit assignment is valid
		if isValidAssignment(words, result, letterToDigit) {
			return letterToDigit, nil
		}

		// Generate the next permutation of digits
		if !nextPermutation(digits) {
			break
		}
	}

	return nil, errors.New("no solution")
}

func isValidAssignment(words []string, result string, letterToDigit map[rune]int) bool {
	// Convert words and result to numbers
	wordNumbers := make([]int, len(words))
	resultNumber := 0
	for i, word := range words {
		wordNumber := 0
		for _, letter := range word {
			wordNumber = wordNumber*10 + letterToDigit[letter]
		}
		wordNumbers[i] = wordNumber
	}
	for _, letter := range result {
		resultNumber = resultNumber*10 + letterToDigit[letter]
	}

	// Check if the equation is satisfied
	sum := 0
	for _, wordNumber := range wordNumbers {
		sum += wordNumber
	}
	return sum == resultNumber
}

func nextPermutation(digits []int) bool {
	n := len(digits)
	i := n - 2
	for i >= 0 && digits[i] >= digits[i+1] {
		i--
	}
	if i < 0 {
		return false
	}
	j := n - 1
	for digits[j] <= digits[i] {
		j--
	}
	digits[i], digits[j] = digits[j], digits[i]
	reverse(digits, i+1, n-1)
	return true
}

func reverse(digits []int, start, end int) {
	for start < end {
		digits[start], digits[end] = digits[end], digits[start]
		start++
		end--
	}
}
