# CAPTCHA Solver

A lightweight web application for generating and validating CAPTCHAs with integrated repository validation checks.

## Summary

This project provides a client-side CAPTCHA generation and validation system. It features a clean, responsive interface for displaying CAPTCHA challenges and verifying user inputs. Additionally, it includes repository validation checks that verify MIT license presence and README quality using GitHub's API.

## Setup

1. Clone or download the project files
2. Open `index.html` in a web browser
3. No additional dependencies or installation required

## Usage

1. The application automatically generates a CAPTCHA on page load
2. Type the displayed CAPTCHA text into the input field
3. Click "Validate" to check your answer
4. Use "Refresh CAPTCHA" to generate a new challenge
5. Repository validation checks run automatically and display results below the CAPTCHA section

## Code Explanation

- **HTML Structure**: Contains the CAPTCHA display area, input field, validation buttons, and result containers
- **CSS Styling**: Provides a clean, modern interface with visual feedback for validation states
- **JavaScript Functions**:
  - `generateCaptcha()`: Creates a 6-character CAPTCHA using alphanumeric characters
  - `validateCaptcha()`: Compares user input with the generated CAPTCHA
  - `checkRepoRequirements()`: Uses GitHub API to verify MIT license and README quality
- **Repository Checks**:
  - Validates MIT license presence via GitHub API
  - Checks README quality based on file size (>500 characters)
  - Provides visual feedback (pass/fail) for each check