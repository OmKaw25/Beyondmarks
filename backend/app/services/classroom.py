"""Teacher-owned learning content and enrollment-scoped visibility."""
from sqlalchemy import select, func, delete
from app import models as m
from app.errors import fail
from app.services.quiz_grading import recommendation_key


def teacher_ids(db, user):
    if user.role == 'teacher': return [user.id]
    return list(db.scalars(select(m.TeacherAssignment.teacher_id).join(m.User, m.User.id == m.TeacherAssignment.teacher_id)
                          .where(m.TeacherAssignment.learner_id == user.id, m.User.active == True)))


def subject_for(db, user, subject_id):
    subject = db.get(m.ClassSubject, subject_id)
    if not subject or subject.teacher_id not in teacher_ids(db,user):
        fail(404,'NOT_FOUND','This subject is not in your class.')
    return subject


def questions_for(db, quiz_id):
    return list(db.scalars(select(m.QuizQuestion).where(m.QuizQuestion.quiz_id == quiz_id).order_by(m.QuizQuestion.position)))


def quiz_for(db, user, quiz_id, lock=False):
    query = select(m.ClassQuiz).where(m.ClassQuiz.id == quiz_id)
    quiz = db.scalar(query.with_for_update() if lock else query)
    if not quiz or quiz.teacher_id not in teacher_ids(db,user) or (user.role == 'learner' and quiz.status != 'published'):
        fail(404,'NOT_FOUND','This quiz is not available in your class.')
    return quiz


def ensure_programming(db, teacher_id):
    from app.content.catalog import catalog, uid
    subject_id = uid(teacher_id + '/basic-programming')
    if db.get(m.ClassSubject, subject_id): return
    subject = m.ClassSubject(id=subject_id,teacher_id=teacher_id,title='Basic programming',description='Build understanding through code, reasoning, and practice.')
    db.add(subject);db.flush()
    for i, topic in enumerate(catalog()):
        db.add(m.ClassCourse(subject_id=subject.id,title=topic['name'],position=i,concept_id=topic['concept_id'],
                             content=topic['explanation']+'\n\nWorked example\n'+topic['support_code']+'\n\nExpected output: '+topic['support_answer']))
    db.flush()


def refresh_course_progress(db, learner_id):
    """Rebuild a learner's small read summary after grading or audited review."""
    from app.services.feedback_review import effective_evaluation
    db.scalar(select(m.User).where(m.User.id==learner_id).with_for_update())
    submissions=list(db.scalars(select(m.QuizSubmission).where(m.QuizSubmission.learner_id==learner_id,
        m.QuizSubmission.status=='graded').order_by(m.QuizSubmission.created_at.desc(),m.QuizSubmission.id)))
    questions={q.id:q for q in db.scalars(select(m.QuizQuestion).where(m.QuizQuestion.quiz_id.in_({s.quiz_id for s in submissions})))} if submissions else {}
    reviews={}
    if submissions:
        for review in db.scalars(select(m.TeacherReview).where(m.TeacherReview.submission_id.in_([s.id for s in submissions]))):
            reviews.setdefault(review.submission_id,[]).append(review)
    scores={}
    for submission in submissions:
        grouped={}
        evaluation=effective_evaluation(db,submission,reviews.get(submission.id,[]))
        for feedback in (evaluation or {}).get('questions',[]):
            if feedback.get('needs_review'): continue
            question=questions.get(feedback['question_id'])
            if question: grouped.setdefault(question.course_id,[]).append((feedback['answer_score']+feedback['reasoning_score'])/2)
        for course_id,values in grouped.items():
            if course_id not in scores: scores[course_id]=(round(sum(values)/len(values),1),submission.id)
    db.execute(delete(m.CourseProgress).where(m.CourseProgress.learner_id==learner_id))
    for course_id,(score,submission_id) in scores.items():
        db.add(m.CourseProgress(learner_id=learner_id,course_id=course_id,score=score,source_submission_id=submission_id))
    db.flush()
    return {course_id:score for course_id,(score,_) in scores.items()}


def course_scores(db, learner_id):
    return {row.course_id:row.score for row in db.scalars(select(m.CourseProgress).where(m.CourseProgress.learner_id==learner_id))}


def course_view(db, course, scores, exercises=None):
    if exercises is None:
        exercise=db.scalar(select(m.Exercise).where(m.Exercise.concept_id==course.concept_id,m.Exercise.active==True)) if course.concept_id else None
    else: exercise=exercises.get(course.concept_id)
    return dict(id=course.id,title=course.title,content=course.content,position=course.position,
                concept_id=course.concept_id,exercise_id=exercise.id if exercise else None,score=scores.get(course.id))


def page_info(total, limit, offset):
    has_more=offset+limit<total
    return dict(total=total,limit=limit,offset=offset,has_more=has_more,next_offset=offset+limit if has_more else None)


def overview(db, user, quiz_limit=20, quiz_offset=0):
    ids=teacher_ids(db,user)
    scores=course_scores(db,user.id) if user.role=='learner' else {}
    subject_rows=list(db.scalars(select(m.ClassSubject).where(m.ClassSubject.teacher_id.in_(ids)).order_by(m.ClassSubject.created_at,m.ClassSubject.id)))
    course_rows=list(db.scalars(select(m.ClassCourse).where(m.ClassCourse.subject_id.in_([s.id for s in subject_rows])).order_by(m.ClassCourse.position,m.ClassCourse.id))) if subject_rows else []
    concepts={c.concept_id for c in course_rows if c.concept_id}
    exercises={e.concept_id:e for e in db.scalars(select(m.Exercise).where(m.Exercise.concept_id.in_(concepts),m.Exercise.active==True))} if concepts else {}
    teachers={u.id:u.username for u in db.scalars(select(m.User).where(m.User.id.in_(ids)))} if ids else {}
    grouped={}
    for course in course_rows: grouped.setdefault(course.subject_id,[]).append(course_view(db,course,scores,exercises))
    subjects=[]
    for subject in subject_rows:
        courses=grouped.get(subject.id,[])
        if user.role=='learner': courses.sort(key=recommendation_key)
        subjects.append(dict(id=subject.id,title=subject.title,description=subject.description,teacher_id=subject.teacher_id,
                             teacher=teachers.get(subject.teacher_id),courses=courses))
    filters=[m.ClassQuiz.teacher_id.in_(ids)]
    if user.role=='learner': filters.append(m.ClassQuiz.status=='published')
    total=db.scalar(select(func.count()).select_from(m.ClassQuiz).where(*filters))
    rows=list(db.scalars(select(m.ClassQuiz).where(*filters).order_by(m.ClassQuiz.created_at.desc(),m.ClassQuiz.id).limit(quiz_limit).offset(quiz_offset)))
    submissions={s.quiz_id:s for s in db.scalars(select(m.QuizSubmission).where(m.QuizSubmission.quiz_id.in_([q.id for q in rows]),m.QuizSubmission.learner_id==user.id))} if user.role=='learner' and rows else {}
    quizzes=[dict(id=q.id,title=q.title,subject_id=q.subject_id,status=q.status,
                  submission_status=submissions[q.id].status if q.id in submissions else None) for q in rows]
    return dict(role=user.role,subjects=subjects,quizzes=quizzes,quizzes_page=page_info(total,quiz_limit,quiz_offset))


def create_subject(db, user, payload):
    db.scalar(select(m.User).where(m.User.id==user.id).with_for_update())
    if db.scalar(select(m.ClassSubject).where(m.ClassSubject.teacher_id==user.id,func.lower(m.ClassSubject.title)==payload.title.lower())):
        fail(409,'SUBJECT_EXISTS','You already have a subject with this name.')
    subject=m.ClassSubject(teacher_id=user.id,**payload.model_dump());db.add(subject);db.flush()
    return subject


def add_course(db,user,subject_id,payload):
    subject_for(db,user,subject_id)
    db.scalar(select(m.ClassSubject).where(m.ClassSubject.id==subject_id).with_for_update())
    count=db.scalar(select(func.count()).select_from(m.ClassCourse).where(m.ClassCourse.subject_id==subject_id))
    course=m.ClassCourse(subject_id=subject_id,position=count,**payload.model_dump());db.add(course);db.flush()
    return course


def create_quiz(db,user,payload):
    subject=subject_for(db,user,str(payload.subject_id))
    courses={c.id for c in db.scalars(select(m.ClassCourse).where(m.ClassCourse.subject_id==subject.id))}
    if any(str(q.course_id) not in courses for q in payload.questions):
        fail(422,'INVALID_TOPIC','Every question must use a topic from this subject.')
    quiz=m.ClassQuiz(teacher_id=user.id,subject_id=subject.id,title=payload.title.strip());db.add(quiz);db.flush()
    for position,q in enumerate(payload.questions):
        db.add(m.QuizQuestion(quiz_id=quiz.id,position=position,**q.model_dump(mode='json')))
    db.flush();return quiz


def edit_quiz(db,user,quiz_id,payload):
    quiz=quiz_for(db,user,quiz_id,lock=True)
    if quiz.status!='draft': fail(409,'QUIZ_PUBLISHED','Published questions cannot change after students receive them.')
    subject=subject_for(db,user,str(payload.subject_id))
    courses={c.id for c in db.scalars(select(m.ClassCourse).where(m.ClassCourse.subject_id==subject.id))}
    if any(str(q.course_id) not in courses for q in payload.questions):
        fail(422,'INVALID_TOPIC','Every question must use a topic from this subject.')
    db.execute(delete(m.QuizQuestion).where(m.QuizQuestion.quiz_id==quiz.id))
    quiz.title=payload.title.strip();quiz.subject_id=subject.id
    for position,q in enumerate(payload.questions):
        db.add(m.QuizQuestion(quiz_id=quiz.id,position=position,**q.model_dump(mode='json')))
    db.flush();return quiz


def submission_view(db, submission, learner_name=None, reviews=None):
    from app.services.feedback_review import effective_evaluation
    return dict(id=submission.id,learner=learner_name or db.get(m.User,submission.learner_id).username,status=submission.status,
                responses=submission.responses_json,evaluation=effective_evaluation(db,submission,reviews),
                original_evaluation=submission.evaluation_json,submitted_at=submission.created_at,error_code=submission.error_code)


def quiz_view(db,user,quiz,submission_limit=20,submission_offset=0):
    teacher=user.role=='teacher'
    questions=[]
    question_rows=questions_for(db,quiz.id)
    courses={c.id:c.title for c in db.scalars(select(m.ClassCourse).where(m.ClassCourse.id.in_({q.course_id for q in question_rows})))} if question_rows else {}
    for q in question_rows:
        view=dict(id=q.id,course_id=q.course_id,topic=courses[q.course_id],prompt=q.prompt)
        if teacher: view.update(expected_answer=q.expected_answer,rubric=q.rubric)
        questions.append(view)
    filters=[m.QuizSubmission.quiz_id==quiz.id]
    if not teacher: filters.append(m.QuizSubmission.learner_id==user.id)
    total=db.scalar(select(func.count()).select_from(m.QuizSubmission).where(*filters))
    rows=list(db.scalars(select(m.QuizSubmission).where(*filters).order_by(m.QuizSubmission.created_at.desc(),m.QuizSubmission.id).limit(submission_limit).offset(submission_offset)))
    learners={u.id:u.username for u in db.scalars(select(m.User).where(m.User.id.in_({s.learner_id for s in rows})))} if rows else {}
    reviews={}
    if rows:
        for review in db.scalars(select(m.TeacherReview).where(m.TeacherReview.submission_id.in_([s.id for s in rows]))):
            reviews.setdefault(review.submission_id,[]).append(review)
    return dict(id=quiz.id,title=quiz.title,status=quiz.status,role=user.role,subject_id=quiz.subject_id,subject=db.get(m.ClassSubject,quiz.subject_id).title,
                questions=questions,submissions=[submission_view(db,s,learners[s.learner_id],reviews.get(s.id,[])) for s in rows],
                submissions_page=page_info(total,submission_limit,submission_offset))
