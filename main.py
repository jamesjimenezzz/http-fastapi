from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session 


app = FastAPI()
models.Base.metadata.create_all(bind=engine)

class ChoiceBase(BaseModel):
    choice_text: str
    is_correct: bool

    class Config:
        orm_mode = True

class QuestionBase(BaseModel):
    question_text: str                 
    answers: List[ChoiceBase]

    class Config:
        orm_mode = True


class QuestionUpdate(BaseModel):
    question_text: str                 

    class Config:
        orm_mode = True
 

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.post("/questions")
def create_questions(question: QuestionBase, db: db_dependency):
    db_question = models.Questions(question_text = question.question_text )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    for choice in question.choices:
        db_choice = models.Answers(choice_text = choice.choice_text, is_correct = choice.is_correct, question_id = db_question.id )
        db.add(db_choice)
    db.commit()


@app.get("/question/{question_id}", response_model=QuestionBase)
def get_question(question_id: int, db: db_dependency):
    result = db.query(models.Questions).filter(models.Questions.id == question_id).first()
    if not result:
        raise HTTPException(status_code=404, detail=f'Question id {question_id} is not found.')
    return result

@app.delete("/question/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(question_id: int, db: db_dependency):
    question = db.query(models.Questions).filter(models.Questions.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail=f"Question id {question_id} cant be found")

    db.delete(question)
    db.commit()
    return None

@app.patch("/question/{question_id}")
def update_question(question_id: int, update: QuestionUpdate, db:db_dependency):
    question = db.query(models.Questions).filter(models.Questions.id == question_id).first()

    if not question:
        raise HTTPException(status_code=404, detail=f"Question id {question_id} doesnt exist.")
    
    question.question_text = update.question_text

    db.commit()
    db.refresh(question)
    return question
