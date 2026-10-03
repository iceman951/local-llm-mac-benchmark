package alphametics

import (
	"errors"
	"strings"
)

func Solve(puzzle string) (map[string]int, error) {
	// Parse the puzzle to extract words and letters
	parts := strings.Split(puzzle, " == ")
	if len(parts) != 2 {
		return nil, errors.New("invalid puzzle format")
	}
	
	leftSide := parts[0]
	rightSide := parts[1]
	
	// Extract all words from left side
	var leftWords []string
	for _, word := range strings.Fields(leftSide) {
		if word != "" {
			leftWords = append(leftWords, word)
		}
	}
	
	// Extract the result word from right side
	var rightWord string
	for _, word := range strings.Fields(rightSide) {
		if word != "" {
			rightWord = word
			break
		}
	}
	
	// Collect all unique letters
	letters := make(map[rune]bool)
	for _, word := range leftWords {
		for _, c := range word {
			letters[c] = true
		}
	}
	for _, c := range rightWord {
		letters[c] = true
	}
	
	if len(letters) > 10 {
		return nil, errors.New("too many unique letters")
	}
	
	// Identify leading letters (cannot be zero for multi-digit numbers)
	var leadingLetters []rune
	for _, word := range leftWords {
		if len(word) > 1 {
			leadingLetters = append(leadingLetters, []rune(word)[0])
		}
	}
	if len(rightWord) > 1 {
		leadingLetters = append(leadingLetters, []rune(rightWord)[0])
	}
	
	// Convert letters to slice for easier processing
	letterList := make([]rune, 0, len(letters))
	for c := range letters {
		letterList = append(letterList, c)
	}
	
	// Try all permutations of digit assignments using backtracking
	result := solveBacktrack(letters, letterList, leadingLetters, leftWords, rightWord)
	if result != nil {
		return result, nil
	}
	
	return nil, errors.New("no solution found")
}

func solveBacktrack(letters map[rune]bool, letterList []rune, leadingLetters []rune, leftWords []string, rightWord string) map[string]int {
	// Convert letters to a slice for easier indexing
	letterSlice := make([]rune, len(letterList))
	for i, c := range letterList {
		letterSlice[i] = c
	}
	
	// Create a mapping from letter to digit
	assignment := make(map[rune]int)
	usedDigits := make([]bool, 10)
	
	// Try all permutations using backtracking
	result := backtrack(0, assignment, usedDigits, letters, leadingLetters, leftWords, rightWord, letterSlice)
	if result != nil {
		// Convert rune keys to string keys for return
		stringResult := make(map[string]int)
		for k, v := range result {
			stringResult[string(k)] = v
		}
		return stringResult
	}
	
	return nil
}

func backtrack(index int, assignment map[rune]int, usedDigits []bool, letters map[rune]bool, leadingLetters []rune, leftWords []string, rightWord string, letterSlice []rune) map[rune]int {
	// Base case: all letters have been assigned
	if index == len(letterSlice) {
		return validate(assignment, leftWords, rightWord)
	}
	
	letter := letterSlice[index]
	
	// Try each digit from 0-9
	for digit := 0; digit <= 9; digit++ {
		// Skip if digit already used
		if usedDigits[digit] {
			continue
		}
		
		// Skip if this is a leading letter and digit is 0
		isLeading := false
		for _, l := range leadingLetters {
			if l == letter {
				isLeading = true
				break
			}
		}
		
		if isLeading && digit == 0 {
			continue
		}
		
		// Assign digit to letter
		assignment[letter] = digit
		usedDigits[digit] = true
		
		// Recurse
		result := backtrack(index+1, assignment, usedDigits, letters, leadingLetters, leftWords, rightWord, letterSlice)
		
		if result != nil {
			return result
		}
		
		// Backtrack: remove assignment
		delete(assignment, letter)
		usedDigits[digit] = false
	}
	
	return nil
}

func validate(assignment map[rune]int, leftWords []string, rightWord string) map[rune]int {
	// Calculate sum of left side words
	sum := 0
	
	for _, word := range leftWords {
		wordValue := calculateWordValue(word, assignment)
		sum += wordValue
	}
	
	// Calculate right side word value
	rightValue := calculateWordValue(rightWord, assignment)
	
	if sum == rightValue {
		return assignment
	}
	
	return nil
}

func calculateWordValue(word string, assignment map[rune]int) int {
	value := 0
	for _, c := range word {
		digit := assignment[c]
		value = value*10 + digit
	}
	return value
}
