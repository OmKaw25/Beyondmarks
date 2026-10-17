"""Validated programming templates. Answers are derived, never executed from input."""
from app.content.catalog import choices, uid
from app.content.challenges import task

SUPPORTED = {'variables', 'conditionals', 'loops'}


def rotate(items, index):
    offset = index % len(items)
    return items[offset:] + items[:offset]


def support_variant(slug, index):
    if slug not in SUPPORTED or index < 0:
        raise ValueError('Unsupported practice template')
    n = index + 5
    if slug == 'variables':
        name = ['stock', 'points', 'reading'][index % 3]
        target = 'saved' if index % 2 == 0 else name
        code = f'{name} = {n}\nsaved = {name}\n{name} = {name} + 2\nprint({target})'
        answer = n if target == 'saved' else n + 2
        alternatives = [n, n + 2, n - 2]
        explanation = 'An assignment copies the current value. Track the original and the saved value separately; updating one does not update the other.'
    elif slug == 'conditionals':
        value = n + index % 3 - 1
        op = '>=' if index % 2 == 0 else '>'
        passed = value >= n if op == '>=' else value > n
        code = f'points = {value}\nif points {op} {n}:\n    print({n + 2})\nelse:\n    print({n - 2})'
        answer = n + 2 if passed else n - 2
        alternatives = [n + 2, n - 2, n]
        explanation = 'Read the comparison exactly. >= includes equality; > does not. Only the branch whose condition is satisfied runs.'
    else:
        code = f'total = 0\nfor number in range({n}, {n + 2}):\n    total = total + number\nprint(total)'
        answer = 2 * n + 1
        alternatives = [answer, answer + n + 2, n + 1]
        explanation = 'List the values visited by range first. The stop value is excluded. Then update the total once for each visited value.'
    return dict(title='A fresh practice question', explanation=explanation,
                worked_example=code, prediction_prompt='Trace this short example. What does it print?',
                choices_json=rotate(choices(*alternatives), index), correct_choice=str(answer),
                feedback_correct='You applied the idea to a new example. Next, check it independently.',
                feedback_incorrect='Trace each step using the rule above. We will try a different short example before the next check.')


def task_variant(slug, phase, index):
    if slug not in SUPPORTED or phase not in {'transfer', 'independent', 'reflection'} or index < 0:
        raise ValueError('Unsupported verification template')
    n = index + 11
    if slug == 'variables':
        reason = 'Each assignment uses the current value; a saved copy does not change automatically.'
        wrong = 'Updating the original also updates every copy of its value.'
        if phase == 'transfer':
            prompt = 'Repair a saved inventory count after a delivery.'
            code = f'stock = {n}\nsaved = stock\nstock = stock + 2\n# YOUR CHANGE\nprint(saved)'
            answer, output = 'saved = stock', str(n + 2)
            options = ['saved = stock', 'stock = saved', 'saved = saved']
            instruction = f'The saved count should include the delivery and print {n + 2}.'
        elif phase == 'independent':
            prompt = 'Track the current reading and a separately updated saved reading.'
            code = f'reading = {n}\nsaved = reading\nreading = reading - 2\nsaved = saved + 3\nprint(reading)\nprint(saved)'
            output = f'{n - 2}\n{n + 3}'
        else:
            prompt = 'Challenge the claim that changing a number automatically changes its saved copy.'
            selected = n if index % 2 == 0 else -n
            code = 'number = CHOSEN_VALUE\nsaved = number\nnumber = number * number\nprint(saved, number)'
            answer, output = str(selected), f'{selected} {selected * selected}'
            options = ['0', '1', answer]
            instruction = 'Choose a starting value that makes the two printed values different.'
    elif slug == 'conditionals':
        reason = 'Each comparison uses its exact operator and the value at that step.'
        wrong = 'A strict comparison includes equality and ignores earlier updates.'
        if phase == 'transfer':
            prompt = 'Repair the eligibility check at the minimum qualifying score.'
            code = f'score = {n}\n# YOUR CHANGE\n    print("eligible")\nelse:\n    print("wait")'
            answer, output = f'if score >= {n}:', 'eligible'
            options = [answer, f'if score > {n}:', f'if score < {n}:']
            instruction = f'A score of {n} or more qualifies. Include the boundary.'
        elif phase == 'independent':
            value = n + index % 2
            prompt = 'Check a score again after a deduction. Give both final results.'
            code = f'score = {value}\nif score >= {n}:\n    score = score - 1\nif score >= {n}:\n    label = "ready"\nelse:\n    label = "wait"\nprint(score)\nprint(label)'
            output = f'{value - 1}\n' + ('ready' if value - 1 >= n else 'wait')
        else:
            prompt = 'Find a counterexample to the claim that > and >= always make the same decision.'
            first, second = ('>=', '>') if index % 2 == 0 else ('>', '>=')
            code = f'value = CHOSEN_VALUE\nif value {first} {n}:\n    first = "yes"\nelse:\n    first = "no"\nif value {second} {n}:\n    second = "yes"\nelse:\n    second = "no"\nprint(first, second)'
            answer, output = str(n), ('yes no' if first == '>=' else 'no yes')
            options = [str(n - 1), answer, str(n + 1)]
            instruction = 'Choose the input where the two comparisons disagree.'
    else:
        reason = 'The stop is excluded; only visited values change the accumulators.'
        wrong = 'The stop value is included as an additional iteration.'
        if phase == 'transfer':
            prompt = 'Repair the loop to count the requested numbered boxes once each.'
            code = 'total = 0\n# YOUR CHANGE\n    total = total + box\nprint(total)'
            answer, output = f'for box in range({n}, {n + 3}):', str(3 * n + 3)
            options = [answer, f'for box in range({n}, {n + 2}):', f'for box in range({n + 1}, {n + 3}):']
            instruction = f'Include box numbers {n}, {n + 1}, and {n + 2}. Print their total.'
        elif phase == 'independent':
            visits = 2 + index % 2
            prompt = 'Trace the accumulated value and visit count across a stepped range.'
            code = f'total = 2\nvisits = 0\nfor number in range({n}, {n + 2 * visits}, 2):\n    total = total + number\n    visits = visits + 1\nprint(total)\nprint(visits)'
            output = f'{2 + visits * n + visits * (visits - 1)}\n{visits}'
        else:
            prompt = 'Challenge the claim that a positive stop always makes a loop run.'
            code = f'stop = CHOSEN_VALUE\nvisits = 0\nfor number in range({n}, stop):\n    visits = visits + 1\nprint(visits)'
            answer, output = str(n), '0'
            options = [str(n + 1), answer, str(n + 2)]
            instruction = 'Choose the boundary case where the body never runs.'
    if phase == 'independent':
        interaction = dict(format='multi-output', instruction='Work through the whole program and give both printed results.',
                           answer_fields=['First printed value', 'Second printed value'])
    else:
        interaction = dict(format='repair' if phase == 'transfer' else 'counterexample', instruction=instruction,
                           answer_label='Which change meets the requirement?' if phase == 'transfer' else 'Which input challenges the claim?',
                           choices=rotate(choices(*options), index), correct_answer=answer)
    result = task(slug, phase, index, prompt, code, output, reason, wrong, **interaction)
    result.update(id=uid(f'{slug}/practice-v3/{phase}/{index}'), priority=1000 + index)
    result['reasoning_options'] = rotate(result['reasoning_options'], index)
    # The chosen input is part of the question; include it in the display so
    # reflection variants do not look identical when their options change.
    if slug == 'variables' and phase == 'reflection':
        result['prompt'] += f' Consider starting values 0, 1, and {answer}.'
    return result
