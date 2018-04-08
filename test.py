from flask import Flask, g, request
 
app = Flask(__name__)
@app.before_request
def before_request():
    print ('before request started')
    print (request.url)
    return 'Hello'
 
@app.before_request
def before_request2():
    print ('before request started 2')
    print (request.url)
    g.name="SampleApp"
 
@app.after_request
def after_request(response):
    print ('after request finished')
    print (request.url)
    response.headers['key'] = 'value'
    return response

from werkzeug.test import EnvironBuilder
 
with app.request_context(EnvironBuilder('/','http://localhost/').get_environ()):
    print(request.url) 
def handle_request():
    print ('handle request')
    print (request.url)

@app.teardown_request
def teardown_request(exception):
    print ('teardown request')
    print (request.url)

@app.route('/')
def index():
    return 'Hello, %s!' % g.name
# handle_request() 
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
    