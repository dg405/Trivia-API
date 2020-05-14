import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgres://{}:{}@{}/{}".format('postgres', 'password', 'localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        self.dummy_data = {
            'question': 'TEST',
            'answer': 'TEST',
            'difficulty': 1, 
            'category': 3
        }

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """

    #test questions endpoint
    def test_get_paginated_questions(self):
        res = self.client().get('/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])
        self.assertTrue(data['totalQuestions'])
        self.assertTrue(data['totalPages'])

    #test 404 error for invalid page of questions
    def test_error_for_invalid_questions_page(self):
        res = self.client().get('/questions?page=100003930')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')

    #test categories endpoint
    def test_get_categories(self):
        res = self.client().get('/categories')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['categories'])
        self.assertEqual(data['total_categories'], 6)
    
    #test questions by category
    def test_get_questions_by_category(self): 
        res = self.client().get('/categories/2/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(len(data['questions']))
        self.assertTrue(data['totalQuestions'])
        self.assertTrue(data['totalPages'])
        self.assertEqual(data['currentCategory'], 3)

    #test adding a question
    def test_add_question(self):
        res = self.client().post('/questions', json=self.dummy_data)
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['question'])

    #test deleting a question which creates a question to be deleted
    #without relying on another API endpoint and check it was actually deleted
    def test_delete_question(self): 
        question = Question(question = 'question', answer = '321answertest123', difficulty = 1, category = 2)
        question.insert()

        question = Question.query.filter(Question.answer=='321answertest123').first()
        res = self.client().delete(f'/questions/{question.id}')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

        question_new = Question.query.filter(Question.answer=='321answertest123').first()
        self.assertFalse(question_new)


    #test deleting a question which doesn't exist
    def test_error_question_delete_id_no_exist(self):
        res = self.client().delete(f'/questions/38389940')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], "resource not found")

    #test trying to add a question without all the required fields
    def test_error_create_question_missing_fields(self):
        dummy_data = {
            'category': 1
        }
        res = self.client().post('/questions', json=dummy_data)
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], "unprocessable")

    #test trying to add a question with empty fields
    def test_error_create_question_empty_fields(self):
        dummy_data = {
            'question': '',
            'answer': '',
            'difficulty': 1, 
            'category': 1
        }
        res = self.client().post('/questions', json=dummy_data)
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], "unprocessable")

    #test 405 error on PUT question
    def test_error_put_new_question(self):
        res = self.client().put('/questions', json=self.dummy_data)
        data = json.loads(res.data)
        
        self.assertEqual(res.status_code, 405)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], "method not allowed")

    #test search
    def test_search(self):
        search = 'which'
        res = self.client().post(f'/questions/{search}')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])

    #test quiz with all required info
    def test_quiz(self):
        res = self.client().post('/quizzes', json={'previous_questions':[], 'quiz_category': {"type": "Art", "id": "2"}})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['question'])

    #test error when missing previous questions
    def test_quiz_missing_prev_question(self):
        res = self.client().post('/quizzes', json={'quiz_category': {"type": "Art", "id": "2"}})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], "unprocessable")

    #test error when missing quiz category
    def test_quiz_missing_quiz_category(self):
        res = self.client().post('/quizzes', json={'previous_questions':[]})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], "unprocessable")
        


        
        
        



# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()