import pytest
from app.services.quiz_grading import validate_feedback, recommendation_key
from app.services.quiz_grading import grade_questions, GradingUnavailable
from types import SimpleNamespace


def test_feedback_requires_exact_question_set_and_bounded_scores():
    valid={'questions':[dict(question_id='q1',answer_score=25,reasoning_score=40,feedback='Trace each iteration.',misconception='Included the stop value.')]}
    assert validate_feedback(valid,{'q1'})['questions'][0]['answer_score']==25
    with pytest.raises(ValueError): validate_feedback(valid,{'q2'})
    with pytest.raises(ValueError): validate_feedback({'questions':valid['questions']*2},{'q1'})
    valid['questions'][0]['reasoning_score']=101
    with pytest.raises(ValueError): validate_feedback(valid,{'q1'})


def test_weak_topics_precede_unassessed_then_stronger_topics():
    courses=[dict(id='strong',score=90,position=0),dict(id='new',score=None,position=1),dict(id='loops',score=25,position=2),dict(id='conditions',score=45,position=3)]
    assert [c['id'] for c in sorted(courses,key=recommendation_key)]==['loops','conditions','new','strong']


@pytest.mark.parametrize('envelope',[{'candidates':[None]},{'candidates':[{'finishReason':'STOP','content':{'parts':[None]}}]}])
def test_malformed_provider_envelope_becomes_retryable_feedback_error(monkeypatch,envelope):
    import httpx
    monkeypatch.setattr('app.services.quiz_grading.get_settings',lambda:SimpleNamespace(gemini_api_key='test-only',gemini_model='test-model'))
    monkeypatch.setattr(httpx.Client,'post',lambda *a,**k:httpx.Response(200,json=envelope))
    with pytest.raises(GradingUnavailable,match='INVALID_FEEDBACK'):
        grade_questions([dict(question_id='q1')])
