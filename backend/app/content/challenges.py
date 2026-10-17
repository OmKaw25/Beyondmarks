"""Version 2: repair, multi-step verification, and counterexample challenges."""
from uuid import NAMESPACE_URL, uuid5


def task(slug, phase, index, prompt, code, output, reason, wrong, **interaction):
    return dict(id=str(uuid5(NAMESPACE_URL,f'beyond-marks/{slug}/v2/{phase}/{index}')),
                phase=phase, prompt=prompt, code=code, expected_output=output,
                explanation_prompt={'transfer':'Explain how your change meets the requirement.',
                                    'independent':'Explain the key steps connecting your two results.',
                                    'reflection':'Explain why this case challenges the claim, and state a better rule.'}[phase],
                reasoning_options=[dict(value='trace',label=reason),dict(value='alternative',label=wrong),
                                   dict(value='guess',label='The result stays the same for every possible input.')],
                correct_tag='trace',priority=-100+index,
                interaction_json=dict(version=2,difficulty={'transfer':'Apply','independent':'Challenge','reflection':'Stretch'}[phase],**interaction))


def bank(slug):
    transfer=[]; independent=[]; reflection=[]
    if slug=='variables':
        transfer.append(task(slug,'transfer',0,
            'A shop needs its saved stock count to include a new delivery. Add one line before printing.',
            'stock = 7\nsaved = stock\nstock = stock + 3\n# YOUR CHANGE\nprint(saved)','10',
            'The saved value must be assigned again after stock changes.',
            'Changing stock automatically changes every variable copied from it.',
            format='repair',instruction='The receipt should show the updated stock count: 10.',answer_label='Which line completes the repair?',
            choices=[dict(value='saved = stock',label='saved = stock'),dict(value='stock = saved',label='stock = saved'),dict(value='saved = saved',label='saved = saved')],correct_answer='saved = stock'))
        examples=[
            ('Track two snapshots of an account balance.','balance = 12\nsaved = balance\nbalance = balance - 5\nsaved = saved + 2\nprint(balance)\nprint(saved)','7\n14'),
            ('Track a changing sensor reading and its earlier snapshot.','reading = 8\nprevious = reading\nreading = reading + 4\nprevious = previous - 3\nprint(reading)\nprint(previous)','12\n5'),
            ('Follow a reassignment between two independent counters.','left = 9\nright = left\nleft = left - 4\nright = right + left\nprint(left)\nprint(right)','5\n14')]
        for i,(prompt,code,out) in enumerate(examples):
            independent.append(task(slug,'independent',i,prompt,code,out,
                'Each assignment uses the values present at that exact step.',
                'A copied variable remains connected to its original variable.',
                format='multi-output',instruction='Work through all updates and give both printed results.',answer_fields=['First printed value','Second printed value']))
        for i,(name,selected) in enumerate([('number','2'),('reading','-1'),('amount','3')]):
            reflection.append(task(slug,'reflection',i,
                'Challenge this claim: “After copying a value, changing the original also changes the copy.”',
                f'{name} = CHOSEN_VALUE\nsaved = {name}\n{name} = {name} * {name}\nprint(saved, {name})',f'{selected} {int(selected)**2}',
                'The two values can differ because saved retains the earlier value.',
                'Matching values for one input prove the variables stay linked.',
                format='counterexample',instruction='Choose an input that makes the printed values differ. The other inputs can hide the mistake.',
                answer_label='Which starting value exposes the mistake?',choices=[dict(value=v,label=v) for v in ['0','1',selected]],correct_answer=selected))
    elif slug=='conditionals':
        transfer.append(task(slug,'transfer',0,
            'A delivery is free at 50 or more. Complete the condition so the boundary is included.',
            'total = 50\n# YOUR CHANGE\n    print("free")\nelse:\n    print("fee")','free',
            'At least 50 includes equality, so the comparison must include 50.',
            'A strict greater-than comparison includes the boundary value.',
            format='repair',instruction='Orders below 50 pay a fee; orders of exactly 50 qualify for free delivery.',answer_label='Which line implements that rule?',
            choices=[dict(value=v,label=v) for v in ['if total >= 50:','if total > 50:','if total < 50:']],correct_answer='if total >= 50:'))
        examples=[
            ('Follow two decisions after a value changes.','score = 10\nif score >= 10:\n    score = score - 1\nif score > 9:\n    label = "high"\nelse:\n    label = "low"\nprint(score)\nprint(label)','9\nlow'),
            ('Check a balance before and after a fee.','balance = 5\nif balance > 0:\n    balance = balance - 5\nif balance >= 1:\n    label = "active"\nelse:\n    label = "empty"\nprint(balance)\nprint(label)','0\nempty'),
            ('Decide which branch runs before checking the updated count.','count = 4\nif count >= 4:\n    count = count + 1\nelse:\n    count = count + 10\nif count == 5:\n    label = "ready"\nelse:\n    label = "wait"\nprint(count)\nprint(label)','5\nready')]
        for i,(prompt,code,out) in enumerate(examples):
            independent.append(task(slug,'independent',i,prompt,code,out,
                'The second condition uses the updated value and its exact operator.',
                'Both conditions always use the value from the first line.',
                format='multi-output',instruction='Evaluate the decisions in order. Give the final value and label.',answer_fields=['Final numeric value','Final printed label']))
        for i,limit in enumerate([10,20,5]):
            reflection.append(task(slug,'reflection',i,
                'Challenge this claim: “Replacing >= with > never changes the decision.”',
                f'value = CHOSEN_VALUE\nif value >= {limit}:\n    first = "yes"\nelse:\n    first = "no"\nif value > {limit}:\n    second = "yes"\nelse:\n    second = "no"\nprint(first, second)','yes no',
                'Equality is included by >= and excluded by >.',
                'Both comparisons include equality.',
                format='counterexample',instruction='Find the input where these two decisions disagree.',answer_label='Which value disproves the claim?',
                choices=[dict(value=str(v),label=str(v)) for v in [limit-1,limit,limit+1]],correct_answer=str(limit)))
    else:
        transfer.append(task(slug,'transfer',0,
            'A reward program must count days 1 through 4 exactly once. Complete its loop.',
            'points = 0\n# YOUR CHANGE\n    points = points + day\nprint(points)','10',
            'The stop is excluded, so it must be one beyond the final day.',
            'Both the start and stop of range are included.',
            format='repair',instruction='Count rewards for days 1, 2, 3, and 4; the total should be 10.',answer_label='Which loop header meets the requirement?',
            choices=[dict(value=v,label=v) for v in ['for day in range(1, 5):','for day in range(1, 4):','for day in range(2, 5):']],correct_answer='for day in range(1, 5):'))
        examples=[
            ('Track both the accumulated value and the number of visits.','total = 2\nvisits = 0\nfor n in range(1, 5, 2):\n    total = total + n\n    visits = visits + 1\nprint(total)\nprint(visits)','6\n2'),
            ('Track a changing stock count and the number of updates.','stock = 15\nvisits = 0\nfor sold in range(2, 7, 2):\n    stock = stock - sold\n    visits = visits + 1\nprint(stock)\nprint(visits)','3\n3'),
            ('Trace two accumulators across the same range.','total = 0\nlast = 9\nfor n in range(2, 5):\n    total = total + n\n    last = n\nprint(total)\nprint(last)','9\n4')]
        for i,(prompt,code,out) in enumerate(examples):
            independent.append(task(slug,'independent',i,prompt,code,out,
                'Only visited values contribute; every variable updates in order.',
                'The stop value also contributes one final update.',
                format='multi-output',instruction='Track both results, including the range boundaries and step.',answer_fields=['First printed value','Second printed value']))
        for i,start in enumerate([1,2,4]):
            reflection.append(task(slug,'reflection',i,
                f'Challenge this claim: “With a positive stop value, range({start}, stop) always runs at least once.”',
                f'stop = CHOSEN_VALUE\nvisits = 0\nfor n in range({start}, stop):\n    visits = visits + 1\nprint(visits)','0',
                'When start equals stop, the range is empty and the body never runs.',
                'A positive stop guarantees that the body runs.',
                format='counterexample',instruction='Select the boundary case that produces no loop iterations.',answer_label='Which stop value disproves the claim?',
                choices=[dict(value=str(v),label=str(v)) for v in [start+1,start,start+2]],correct_answer=str(start)))
    return dict(transfer=transfer,independent=independent,reflection=reflection)
