# CAPTCHA Solver

## Summary
A lightweight browser-based CAPTCHA solver implementation that generates and validates simple CAPTCHA challenges. This project demonstrates basic CAPTCHA functionality with a clean, responsive interface and includes repository status checks for license and documentation validation.

## Setup
1. Clone or download the repository
2. Open `index.html` in any modern web browser
3. No additional dependencies or setup required

## Usage
1. The application will automatically generate a CAPTCHA code on page load
2. Type the displayed CAPTCHA code into the input field
3. Click "Submit" to validate your answer
4. Use the "Refresh" button to generate a new CAPTCHA if needed
5. Results will display immediately indicating success or failure

## Code Explanation
The project consists of a single HTML file with embedded CSS and JavaScript:

- **HTML Structure**: Contains the CAPTCHA display, input field, control buttons, and repository status panel
- **CSS Styling**: Provides a clean, modern interface with visual feedback for validation results
- **JavaScript Functions**:
  - `generateCaptcha()`: Creates a 6-character random code using alphanumeric characters
  - `validateCaptcha()`: Compares user input against the generated code
  - `checkRepoStatus()`: Simulates repository validation checks (MIT license and README status)
- **Security Features**: Includes visual distortion techniques (background pattern, letter spacing, and special font) to prevent easy OCR reading
- **Repository Checks**: Demonstrates how license and documentation validation could be implemented in a real project