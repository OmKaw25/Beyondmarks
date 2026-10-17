"""Authored probes with deliberately overlapping predictions, never causal proof."""


def probes(topic, hypotheses, uid):
    key = topic['slug']
    wrong, misread, correct = topic['answers']
    variants = {
        'variables': (
            'first = 4\nsecond = first\nfirst = 9\nprint(second)',
            'Which variable does the print statement ask you to report?', 'second', 'first',
            'original = 6\ncopy = original\noriginal = 10\nprint(copy)', '6', '10'),
        'conditionals': (
            'score = 10\nif score >= 10:\n    print("pass")\nelse:\n    print("retry")',
            'Which comparison is actually written in the condition?', '>=', '>',
            'level = 7\nif level > 7:\n    print("above")\nelse:\n    print("not above")', 'not above', 'above'),
        'loops': (
            'total = 1\nfor step in range(2, 6):\n    total = total + step\nprint(total)',
            'Which variable is printed after the loop?', 'total', 'step',
            'visits = 0\nfor item in range(3, 6):\n    visits = visits + 1\nprint(visits)', '3', '4'),
    }
    read_code, read_prompt, read_correct, read_wrong, untimed_code, untimed_correct, untimed_wrong = variants[key]
    specs = [
        ('output', 'What does this short program print?', topic['follow_code'],
         [wrong, misread, correct, 'not_finished'], correct,
         dict(concept=wrong, reading=misread, understood=correct, time_pressure=correct, incomplete='not_finished'),
         'This output separates a concept error from reporting the wrong value. A correct response cannot by itself distinguish understanding from an earlier time constraint.'),
        ('reading', read_prompt, read_code, [read_correct, read_wrong, 'not_finished'], read_correct,
         dict(concept=read_correct, reading=read_wrong, understood=read_correct, time_pressure=read_correct, incomplete='not_finished'),
         'This question checks what the instructions ask, without requiring a complete trace. Correct reading does not establish conceptual understanding.'),
        ('unhurried', 'Take the time you need. What does this new program print?', untimed_code,
         [untimed_correct, untimed_wrong, 'not_finished'], untimed_correct,
         dict(concept=untimed_wrong, reading=untimed_correct, understood=untimed_correct, time_pressure=untimed_correct, incomplete='not_finished'),
         'An unhurried attempt checks whether the same difficulty persists. Improvement is consistent with a time constraint, but does not prove what caused the earlier response.'),
    ]
    result = []
    for index, (kind, prompt, code, answers, answer, predictions, explanation) in enumerate(specs):
        result.append(dict(id=uid(f'{key}/diagnostic-v2/followup/{kind}'), prompt=prompt, code=code,
                           choices=[dict(value=a, label='I have not finished working this out' if a == 'not_finished' else a) for a in answers],
                           correct_choice=answer, predictions={h['id']: predictions[h['key']] for h in hypotheses},
                           burden=index * 10, effort=20 if index != 2 else 40, priority=index, active=True,
                           explanation=explanation))
    return result
