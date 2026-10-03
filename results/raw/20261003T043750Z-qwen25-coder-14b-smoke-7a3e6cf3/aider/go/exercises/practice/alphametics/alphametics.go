package alphametics

import (
	"errors"
	"regexp"
)

func Solve(puzzle string) (map[string]int, error) {
	// Extract words and the result from the puzzle
	re := regexp.MustCompile(`([A-Z]+)`)
	words := re.FindAllString(puzzle, -1)
	if len(words) < 3 {
		return nil, errors.New("invalid puzzle format")
	}

	// Separate the words and the result
	var leftWords []string
	rightWords := words[len(words)-1]
	for i := 0; i < len(words)-1; i++ {
		if words[i] == "+" {
			continue
		}
		leftWords = append(leftWords, words[i])
	}

	// Collect all unique letters
	uniqueLetters := make(map[string]bool)
	for _, word := range words {
		for _, letter := range word {
			if letter != '+' && letter != '=' {
				uniqueLetters[string(letter)] = true
			}
		}
	}

	// Convert map to slice for easier permutation generation
	letters := make([]string, 0, len(uniqueLetters))
	for letter := range uniqueLetters {
		letters = append(letters, letter)
	}

	// Generate all permutations of digits for the letters
	if !permute(letters, 0, leftWords, rightWords) {
		return nil, errors.New("no solution found")
	}

	return nil, nil
}

func permute(letters []string, index int, leftWords []string, rightWords string) bool {
	if index == len(letters) {
		// Check if the current permutation satisfies the equation
		letterToDigit := make(map[string]int)
		for i, letter := range letters {
			letterToDigit[letter] = i
		}

		// Ensure no leading zeros
		for _, word := range leftWords {
			if letterToDigit[string(word[0])] == 0 {
				return false
			}
		}
		if letterToDigit[string(rightWords[0])] == 0 {
			return false
		}

		// Calculate the left side of the equation
		leftSum := 0
		for _, word := range leftWords {
			leftSum += wordToNumber(word, letterToDigit)
		}

		// Calculate the right side of the equation
		rightSum := wordToNumber(rightWords, letterToDigit)

		// Check if the equation holds
		return leftSum == rightSum
	}

	// Generate permutations
	for i := index; i < len(letters); i++ {
		// Swap
		letters[index], letters[i] = letters[i], letters[index]
		if permute(letters, index+1, leftWords, rightWords) {
			return true
		}
		// Swap back
		letters[index], letters[i] = letters[i], letters[index]
	}

	return false
}

func wordToNumber(word string, letterToDigit map[string]int) int {
	number := 0
	for _, letter := range word {
		number = number*10 + letterToDigit[string(letter)]
	}
	return number
}
