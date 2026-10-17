from contextlib import redirect_stdout
from io import StringIO
from app.content.catalog import catalog
from app.services.assessment_service import evaluate_task
from app.services.journey_rules import public_task


def test_each_concept_has_distinct_progressively_harder_interactions():
    for e in catalog():
        assert {t['interaction_json']['format'] for t in e['transfer']} == {'repair'}
        assert {t['interaction_json']['format'] for t in e['independent']} == {'multi-output'}
        assert {t['interaction_json']['format'] for t in e['reflection']} == {'counterexample'}
        assert len(e['reflection']) >= 3


def test_authored_repairs_and_counterexamples_are_correct():
    for e in catalog():
        for t in [*e['transfer'], *e['independent'], *e['reflection']]:
            config=t['interaction_json']
            answer=config.get('correct_answer',t['expected_output'])
            code=t['code']
            if config['format']=='repair':
                code=code.replace('# YOUR CHANGE',answer)
            elif config['format']=='counterexample':
                code=code.replace('CHOSEN_VALUE',answer)
            output=StringIO()
            with redirect_stdout(output):
                exec(code,{'__builtins__':{'print':print,'range':range}})
            assert output.getvalue().strip()==t['expected_output'], t['prompt']
            assert evaluate_task(t,dict(answer=answer,explanation='I checked the exact changes.',reasoning_tag=t['correct_tag']))['passed']
            exposed=public_task(t)
            assert 'correct_answer' not in str(exposed) and 'expected_output' not in exposed


def test_both_independent_results_and_reasoning_are_required():
    task=catalog()[0]['independent'][0]
    response=dict(answer=task['expected_output'].splitlines()[0],explanation='Only the first value.',reasoning_tag='trace')
    assert not evaluate_task(task,response)['passed']
    response['answer']=task['expected_output'];response['reasoning_tag']='guess'
    assert not evaluate_task(task,response)['passed']
