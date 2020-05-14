import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
import math
from sqlalchemy import func


from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

#define function to paginate questions
def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start = (page -1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  paginated_questions = questions[start:end]
  

  return paginated_questions


def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs - DONE 
  #allows the secure transfer of data between APIs with different URLs 
  '''
  cors = CORS(app, resources={r"/*": {"origins": "*"}})
  '''
  @TODO: Use the after_request decorator to set Access-Control-Allow - DONE
  '''
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Header', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response



  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories. - DONE
  '''
  @app.route('/categories')
  def get_categories():

    categories = Category.query.all()
    
    return jsonify({
      'success': True, 
      'categories': [c.type for c in categories],
      'total_categories': len(categories)
    })

  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. - DONE

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. - PASSED
  '''
  @app.route('/questions')
  def get_questions():
    questions = Question.query.order_by(Question.id).all()
    paginated_questions = paginate_questions(request,questions)

    categories = Category.query.all()

    if len(paginated_questions) == 0:
      abort(404)


    return jsonify({
      'success': True, 
      'questions': paginated_questions, 
      'totalQuestions': len(Question.query.all()), 
      'totalPages': math.ceil(len(Question.query.all())/QUESTIONS_PER_PAGE),
      'categories': [c.type for c in categories], 
      'currentCategory': ''
    })


  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. - DONE

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. - PASSED
  '''
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    question = Question.query.get(question_id)

    if question is None: 
      abort(404)

    try: 
      question.delete()
      return jsonify({
        'success': True,
        'question': question.format()
      })

    except: 
      abort(422)
  
  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score. - DONE 

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  - PASSED
  '''

  @app.route('/questions', methods=['POST'])
  def post_new_question(): 

    try:
      body = request.get_json()

      new_question = body.get('question', None)
      new_answer = body.get('answer', None)
      new_difficulty = body.get('difficulty', None)
      new_category = body.get('category', None)

      #check if the new question is missing anything
      if new_question is None or new_answer is None or new_difficulty is None or new_category is None: 
        abort(422)
      elif new_question is "" or new_answer is "" or new_difficulty is "" or new_category is "": 
        abort(422)

      question = Question(question = new_question, answer = new_answer, difficulty = new_difficulty, category = new_category)
      question.insert()

      return jsonify({
        'success': True, 
        'question': question.format()
      })

    except:
      abort(422)

  


  '''
  @TODO: 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. - DONE 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. - PASSED
  '''
  @app.route('/questions/<searchTerm>', methods=['POST'])
  def search_questions(searchTerm): 
    questions = Question.query.filter(Question.question.ilike(f'%{searchTerm}%')).all()
    paginated_questions = paginate_questions(request,questions)

    if len(paginated_questions) == 0:
      abort(404)

    return jsonify({
      'success': True, 
      'questions': paginated_questions, 
      'totalQuestions': len(questions)
    })

  '''
  @TODO: 
  Create a GET endpoint to get questions based on category. - DONE

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown.  - PASSED
  '''

  @app.route('/categories/<int:id>/questions')
  def get_questions_by_category(id):

    categories = Category.query.all()
    
    if id <= len(categories):
      questions = Question.query.join(Category, Question.category==id+1).all()
      paginated_questions = paginate_questions(request,questions)

      return jsonify({
        'success': True,
        'questions': paginated_questions,
        'totalQuestions': len(questions),
        'totalPages': math.ceil(len(questions)/QUESTIONS_PER_PAGE),
        'currentCategory': id+1
      })
    else:
      abort(400)


  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes', methods=['POST'])
  def play_game():
    body = request.get_json()

    #abort if either required field is missing
    if body.get('quiz_category') is None or body.get('previous_questions') is None:
      abort(422)

    category = int(body.get('quiz_category').get('id'))+1
    q_type = body.get('quiz_category').get('type')
    

    previous_questions = body.get('previous_questions')
    

    #check if the click was on "ALL", if so check if there any questions in the db
    if q_type == "click":
      if len(previous_questions) == len(Question.query.all()):
        return jsonify({
          'success': True, 
          'question': False
        })
      elif len(previous_questions): 
        questions = Question.query.filter(~Question.id.in_(previous_questions)).all()
        questions = random.choice(questions)
      else:
        questions = Question.query.all()
        questions = random.choice(questions)

    
    #if the click wasn't on ALL check if there's any questions in the category
    elif len(previous_questions) == len(Question.query.join(Category, Question.category==category).all()):
      return jsonify({
      'success': True,
      'question': False
      })
    #if it's not the first question check if it's been asked before, then pick a random question
    elif len(previous_questions):
      questions = Question.query.join(Category, Question.category==category).filter(~Question.id.in_(previous_questions)).all()
      questions = random.choice(questions)
    #if it is the first question there's no need to check, then pick a random question
    else:
      questions = Question.query.join(Category, Question.category==category).all()
      questions = random.choice(questions)
    
    paginated_questions = questions.format()
  
    return jsonify({
      'success': True,
      'question': paginated_questions
    })

  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      "success": False, 
      "error": 400,
      "message": "bad request"
      }), 400


  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success": False, 
      "error": 404,
      "message": "resource not found"
      }), 404

  @app.errorhandler(405)
  def method_not_allowed(error):
    return jsonify({
      "success": False, 
      "error": 405,
      "message": "method not allowed"
      }), 405

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      "success": False, 
      "error": 422,
      "message": "unprocessable"
      }), 422

  @app.errorhandler(500)
  def internal_server(error):
    return jsonify({
      "success": False, 
      "error": 500,
      "message": "internal server error"
      }), 500


  return app

    