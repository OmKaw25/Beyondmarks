import pytest
from app.services.diagnostic_engine import assess
from app.services.followup_engine import select_followup
from app.services.assessment_service import evaluate_task
from app.services.support_engine import choose_support


def hypotheses():
    return [dict(id='a', label='Concept', prior=1, rules=[dict(key='concept', weight=3)]),
            dict(id='b', label='Reading', prior=1, rules=[dict(key='concept', weight=-1)])]


def test_evidence_changes_ranking_and_explains_score():
    result = assess(hypotheses(), ['concept'])
    assert result['hypotheses'][0]['id'] == 'a'
    assert result['hypotheses'][0]['score'] == 1
    assert result['hypotheses'][0]['supporting_evidence'] == ['concept']
    assert not result['uncertain']


def test_equal_and_nonpositive_scores_remain_uncertain():
    result = assess(hypotheses(), [])
    assert result['uncertain']
    assert [h['score'] for h in result['hypotheses']] == [.5, .5]
    result = assess([dict(id='a', label='A', prior=-1, rules=[]), dict(id='b', label='B', prior=0, rules=[])], [])
    assert result['uncertain']
    assert [h['score'] for h in result['hypotheses']] == [.5, .5]


def test_duplicate_evidence_does_not_inflate_score():
    assert assess(hypotheses(), ['concept']) == assess(hypotheses(), ['concept', 'concept'])


def test_no_hypotheses_is_inconclusive():
    assert assess([], []) == {'hypotheses': [], 'uncertain': True}


@pytest.mark.parametrize('prior,expected', [(3, 'High'), (1, 'Medium'), (.5, 'Low')])
def test_confidence_boundaries(prior, expected):
    result = assess([dict(id='a', label='A', prior=prior, rules=[]), dict(id='b', label='B', prior=1, rules=[])], [])
    assert next(h for h in result['hypotheses'] if h['id'] == 'a')['confidence'] == expected


def candidate(id='one', predictions=None, burden=0, priority=0):
    return dict(id=id, active=True, predictions=predictions or {'a': '1', 'b': '2'}, burden=burden, effort=10, priority=priority)


def test_followup_separation_and_burden():
    chosen = select_followup([candidate('expensive', burden=10), candidate('short')], ['a', 'b'], [])
    assert chosen['id'] == 'short'
    assert chosen['divergence'] == 1
    assert chosen['selection_score'] == 100
    assert chosen['rationale']


def test_followup_rejects_redundant_answered_and_incomplete():
    candidates = [candidate('same', {'a': '1', 'b': '1'}), candidate('missing', {'a': '1'}), candidate('done')]
    assert select_followup(candidates, ['a', 'b'], ['done']) is None
    assert select_followup([candidate()], ['a'], []) is None
    assert select_followup([], [], []) is None


def test_followup_authored_priority_then_id():
    chosen = select_followup([candidate('z', priority=1), candidate('b'), candidate('a')], ['a', 'b'], [])
    assert chosen['id'] == 'a'


def test_correct_answer_with_wrong_reasoning_does_not_pass():
    task = dict(expected_output='6', correct_tag='trace')
    assert not evaluate_task(task, dict(answer='6', explanation='I guessed', reasoning_tag='guess'))['passed']
    assert evaluate_task(task, dict(answer=' 6 ', explanation='I traced each iteration.', reasoning_tag='trace'))['passed']


def test_adaptation_changes_support_even_with_same_hypothesis():
    modules = [dict(id='first', hypothesis_id='a', priority=0), dict(id='second', hypothesis_id='a', priority=1)]
    assert choose_support('a', modules, ['first'])['id'] == 'second'
    assert choose_support('a', modules, ['first', 'second']) is None
