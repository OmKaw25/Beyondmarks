"""Authored curriculum, not generated tutoring or a simulated database."""
from uuid import NAMESPACE_URL, uuid5
from app.content.challenges import bank
from app.content.diagnostic_probes import probes


def uid(key: str) -> str:
    return str(uuid5(NAMESPACE_URL, 'beyond-marks/' + key))


def choices(*values):
    return [dict(value=str(v), label=str(v)) for v in values]


TOPICS = [
    dict(slug='variables', name='Variables & state', title='A value is not a live link',
         prompt='A learner claims that changing boxes also changes saved. Investigate their explanation.',
         code='boxes = 2\nsaved = boxes\nboxes = 5\nprint(saved)', expected_output='2',
         flaw='saved stays connected to boxes, so changing boxes updates saved to 5.',
         explanation='Assignment copies the current value. A later assignment to boxes does not change saved.',
         broad='Execution', reason='state_update', false_reason='output_format',
         follow_code='tickets = 3\nkept = tickets\ntickets = 8\nprint(kept)', answers=['8', '11', '3'],
         support_code='a = 4\nb = a\na = 9\nprint(b)', support_answer='4',
         task_codes=[('Track the number of seats saved before a booking update.', 'seats = 7\nsaved = seats\nseats = seats - 2\nprint(saved)', '7'),
                     ('Track the score after an explicit reassignment.', 'score = 6\ncopy = score\ncopy = copy + 1\nprint(score)', '6'),
                     ('Track the original stock after a separate counter changes.', 'stock = 9\nremaining = stock\nremaining = remaining - 4\nprint(stock)', '9'),
                     ('Track two updates in a sensor record.', 'reading = 3\nprevious = reading\nreading = reading + 7\nprevious = previous + 2\nprint(previous)', '5')],
         reasoning='I tracked each variable separately after every assignment.'),
    dict(slug='conditionals', name='Conditions & boundaries', title='What happens at the boundary?',
         prompt='A learner explains which branch runs when the value is exactly the threshold. Find the flaw.',
         code='temperature = 20\nif temperature > 20:\n    print("warm")\nelse:\n    print("cool")', expected_output='cool',
         flaw='20 is at the threshold, so temperature > 20 is true and the program prints warm.',
         explanation='The > operator is strict: equality is false. The >= operator includes equality.',
         broad='Missing case', reason='boundary_case', false_reason='output_format',
         follow_code='age = 18\nif age > 18:\n    print("A")\nelse:\n    print("B")', answers=['A', '18', 'B'],
         support_code='points = 10\nif points >= 10:\n    print("yes")\nelse:\n    print("no")', support_answer='yes',
         task_codes=[('Check a free-shipping boundary with a changed condition.', 'total = 50\nif total <= 50:\n    print("fee")\nelse:\n    print("free")', 'fee'),
                     ('Determine the access label at exactly the minimum.', 'height = 120\nif height >= 120:\n    label = "enter"\nelse:\n    label = "wait"\nprint(label)', 'enter'),
                     ('Decide whether a strict capacity check passes.', 'count = 8\nlimit = 8\nif count < limit:\n    print("space")\nelse:\n    print("full")', 'full'),
                     ('Read the equality case in a reversed condition.', 'balance = 0\nif balance != 0:\n    print("active")\nelse:\n    print("empty")', 'empty')],
         reasoning='I evaluated the exact comparison, including the equality case.'),
    dict(slug='loops', name='Loops & execution', title='The stop value is not an iteration',
         prompt='A learner includes the stop value of range in a trace. Investigate their explanation.',
         code='total = 0\nfor step in range(1, 4):\n    total = total + step\nprint(total)', expected_output='6',
         flaw='range(1, 4) visits 1, 2, 3 and 4, so the final total is 10.',
         explanation='range(start, stop) includes start and excludes stop. Trace each visited value and update the total in order.',
         broad='Logic', reason='loop_boundary', false_reason='output_format',
         follow_code='count = 0\nfor item in range(2, 5):\n    count = count + 1\nprint(count)', answers=['4', '5', '3'],
         support_code='total = 0\nfor n in range(1, 3):\n    total = total + n\nprint(total)', support_answer='3',
         task_codes=[('Count points earned across a changed range and update.', 'points = 1\nfor day in range(3):\n    points = points + 2\nprint(points)', '7'),
                     ('Calculate the remaining stock after a fixed number of sales.', 'stock = 10\nfor sale in range(2, 5):\n    stock = stock - 1\nprint(stock)', '7'),
                     ('Count visits using a step of two.', 'visits = 0\nfor stop in range(1, 6, 2):\n    visits = visits + 1\nprint(visits)', '3'),
                     ('Trace the output when the range is empty.', 'value = 9\nfor index in range(4, 4):\n    value = value + 1\nprint(value)', '9')],
         reasoning='I listed the visited values, excluded the stop, and tracked each update.'),
]


def catalog():
    result = []
    for topic in TOPICS:
        key = topic['slug']
        hs = []
        specs = [
            ('concept', 'The concept may need another look', 'The structured response may reflect a conceptual gap.', [('missed_flaw', 3), ('wrong_reason', 2), ('caught_flaw', -1), ('independent_failed', 3), ('independent_passed', -3)]),
            ('reading', 'The task may have been misread', 'Some reasoning is present; interpreting the task may be the difficulty.', [('caught_flaw', 1), ('wrong_reason', 1), ('independent_failed', 1)]),
            ('understood', 'Understanding is emerging', 'The response supports understanding; independent checks are still needed.', [('caught_flaw', 2), ('correct_reason', 3), ('missed_flaw', -2), ('independent_failed', -5), ('independent_passed', 3)]),
            ('time_pressure', 'Time pressure may have affected this response', 'A time constraint is one possible context, not an inferred fact. A fresh unhurried response and your perspective can help us investigate.', []),
            ('incomplete', 'The work may not have been finished', 'An unfinished trace can look like a conceptual error. More evidence is needed before choosing an explanation.', [])]
        for name, label, description, rules in specs:
            rules = rules + [(k.replace('independent_', 'reflection_'), w) for k,w in rules if k.startswith('independent_')]
            hid = uid(f'{key}/hypothesis/{name}')
            hs.append(dict(id=hid, key=name, label=label, description=description, prior=1,
                           rules=[dict(key=k, weight=w) for k,w in rules] + [dict(key=f'predicts:{hid}', weight=3), dict(key=f'challenge:{hid}', weight=.5)]))
        segments = [dict(id=uid(f'{key}/segment/0'), text='The program executes the statements in the order shown.', is_flawed=False),
                    dict(id=uid(f'{key}/segment/1'), text=topic['flaw'], is_flawed=True)]
        followups = probes(topic, hs, uid)
        modules = []
        for h in [None, *hs]:
            hid = h['id'] if h else None
            name = h['key'] if h else 'general'
            for variant in range(3):
                modules.append(dict(id=uid(f'{key}/support/{name}/{variant}'), hypothesis_id=hid, priority=variant,
                                    title=['Make the reasoning visible', 'Try a step-by-step trace', 'Check the boundary yourself'][variant],
                                    explanation=topic['explanation'] + (' Read the task condition first, then compare it with the code.' if name == 'reading' else '') +
                                    [' Write down the state before and after each step.', ' Use a two-column trace: current statement and resulting state.', ' Predict first, then justify the exact step that determines the result.'][variant],
                                    worked_example=topic['support_code'], prediction_prompt='What does this worked example print?',
                                    choices=choices(topic['support_answer'], '0', 'It cannot be determined'), correct_choice=topic['support_answer'],
                                    feedback_correct='Your prediction matches the trace. Next, test the idea in a different situation.',
                                    feedback_incorrect='Compare the exact condition or assignment at each step. ' + topic['explanation']))
        result.append(dict(topic, id=uid(f'{key}/exercise'), concept_id=uid(f'{key}/concept'), segments=segments,
                           categories={topic['broad']: [dict(value=topic['reason'], label=topic['reason'].replace('_',' ').capitalize())],
                                       'Output': [dict(value=topic['false_reason'], label='The output formatting is wrong')]},
                           hypotheses=hs, followups=followups, support=modules, **bank(key)))
    return result
