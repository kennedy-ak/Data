from pathlib import Path
from django.shortcuts import render
from django.conf import settings


DOMAIN_DISPLAY_NAMES = {
    'CCISO v3 - Domain 1': 'Domain 1: Governance, Risk & Compliance',
    'CCISO v3 - Domain 2': 'Domain 2: Security Controls & Frameworks',
    'CCISO v3 - Domain 3': 'Domain 3: Security Operations',
    'CCISO v3 - Domain 4': 'Domain 4: Scenarios & Misc',
    'CCISO v3 - Domain 5': 'Domain 5: Strategy & Management',
    'Exam Prep Challenge': 'Exam Prep Challenges',
    'Exam Prep Challenge2': 'Exam Prep Challenges (Advanced)',
}


def parse_cciso_file(filepath):
    sections = []
    current_section = None
    current_question = None

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    for raw_line in lines:
        line = raw_line.strip()

        # New section
        if line.startswith('Quiz title:'):
            if current_section is not None:
                if current_question is not None:
                    current_section['questions'].append(current_question)
                    current_question = None
                sections.append(current_section)
            current_section = {
                'title': line[len('Quiz title:'):].strip(),
                'description': '',
                'questions': [],
            }
            continue

        if current_section is None:
            continue

        if line.startswith('Quiz description:'):
            current_section['description'] = line[len('Quiz description:'):].strip()
            continue

        # Explanation line
        if line.startswith('...'):
            if current_question is not None:
                current_question['explanation'] = line[3:].strip()
            continue

        # Question line: "N.  text"
        if line and line[0].isdigit():
            dot_pos = line.find('.  ')
            if dot_pos > 0:
                num_str = line[:dot_pos]
                if num_str.isdigit():
                    if current_question is not None:
                        current_section['questions'].append(current_question)
                    current_question = {
                        'number': int(num_str),
                        'text': line[dot_pos + 3:].strip(),
                        'explanation': '',
                        'options': [],
                        'correct': '',
                    }
                    continue

        # Option line: "[*]A)  text"
        if line:
            is_correct = line.startswith('*')
            check = line.lstrip('*')
            if check and check[0] in 'ABCD' and len(check) > 1 and check[1] == ')':
                letter = check[0]
                text = check[2:].strip()
                if current_question is not None:
                    current_question['options'].append({
                        'letter': letter,
                        'text': text,
                        'correct': is_correct,
                    })
                    if is_correct:
                        current_question['correct'] = letter

    # Flush the last section/question
    if current_section is not None:
        if current_question is not None:
            current_section['questions'].append(current_question)
        sections.append(current_section)

    return sections


def index(request):
    txt_path = Path(settings.BASE_DIR) / 'CCISO Comp.txt'
    sections = parse_cciso_file(str(txt_path))

    for section in sections:
        section['display_name'] = DOMAIN_DISPLAY_NAMES.get(
            section['title'], section['title']
        )

    return render(request, 'cisco/index.html', {'sections': sections})
