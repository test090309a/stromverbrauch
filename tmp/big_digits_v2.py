def big_digits(number):
    digits = {
        '0': [
            '█████',
            '█   █',
            '█   █',
            '█   █',
            '█████'
        ],
        '1': [
            '  █  ',
            ' ██  ',
            '  █  ',
            '  █  ',
            ' ███ '
        ],
        '2': [
            '█████',
            '    █',
            '█████',
            '█    ',
            '█████'
        ],
        '3': [
            '█████',
            '    █',
            '█████',
            '    █',
            '█████'
        ],
        '4': [
            '█   █',
            '█   █',
            '█████',
            '    █',
            '    █'
        ],
        '5': [
            '█████',
            '█    ',
            '█████',
            '    █',
            '█████'
        ],
        '6': [
            '█████',
            '█    ',
            '█████',
            '█   █',
            '█████'
        ],
        '7': [
            '█████',
            '    █',
            '   █ ',
            '  █  ',
            ' █   '
        ],
        '8': [
            '█████',
            '█   █',
            '█████',
            '█   █',
            '█████'
        ],
        '9': [
            '█████',
            '█   █',
            '█████',
            '    █',
            '█████'
        ],
        '.': [
            ' ',
            ' ',
            ' ',
            ' ',
            '█'
        ],
        '€': [
            '█████',
            '█    ',
            '████ ',
            '█    ',
            '█████'
        ],
        'w': [
            ' ',
            ' ',
            '█ █ █',
            '█████',
            '█   █'
        ]
    }
    lines = [''] * 5
    for digit in number:
        if digit not in digits:
            digit = ' '  # Fallback für unbekannte Zeichen
        for i in range(5):
            lines[i] += digits[digit][i] + ' '  # Einheitlicher Abstand
    return lines