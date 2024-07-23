from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, RadioField, validators
import requests
import json
import os

# ////////////////////////////////////////
# GLOBALS 
# ////////////////////////////////////////
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(16)

# ////////////////////////////////////////
# CLASSES 
# ////////////////////////////////////////
class SimpleForm(FlaskForm):
    title        = StringField('Title', [validators.DataRequired()])
    lang         = RadioField("Lang", choices=[("native","jp"),("romaji", "en")])
    titleperpage = IntegerField("TitlePerPage", [validators.NumberRange(min=1, max=10)])
    submit       = SubmitField('Submit')

# ////////////////////////////////////////
# FUNCTIONS
# ////////////////////////////////////////

# ////////////////////////////////////////
# HELPERS ////////////////////////////////
def api_get_data(search_term, page_title_count):
    grapql_query = '''
    query ($id: Int, $page: Int, $perPage: Int, $search: String) {
        Page (page: $page, perPage: $perPage) {
            pageInfo {
                total
                currentPage
                lastPage
                hasNextPage
                perPage
            }
            media (id: $id, search: $search) {
                id
                coverImage {
                    extraLarge
      		        large
      		        medium
      		        color           
                }
                title {
                   romaji 
                   native 
                }
            }
        }
    }
    '''
    variables = {
        'search': search_term,
        'page': 1,
        'perPage': page_title_count
    }
    url = 'https://graphql.anilist.co'

    res = requests.post(url, json={'query': grapql_query, 'variables': variables})
    res_data = res.json()
    return res_data

# ////////////////////////////////////////
# ROUTES /////////////////////////////////
@app.route("/", methods=['GET', 'POST'])
def index():
    title_entered = None
    lang_entered  = "native"
    titlecount_entered = 1

    # FORM CTRL
    form = SimpleForm()
    if request.method == "POST":
        title_entered = form.title.data
        lang_entered = form.lang.data
        titlecount_entered = form.titleperpage.data

    # API CALL
    print("log: [", title_entered, "]")
    data = api_get_data(title_entered, titlecount_entered); 
    data_entered = [title_entered, lang_entered, titlecount_entered]
    return render_template("index.html", media=data["data"]["Page"]["media"], form=form, data_entered=data_entered)

@app.route('/about')
def about():
    return 'We are learning about Web services and Web apps.'

@app.route('/contact')
def contact():
    return 'You can contact us at gregory@cs.fiu.edu.'

# ////////////////////////////////////////
# ENTRY POINT
# ////////////////////////////////////////
if __name__ == '__main__':
    app.run(debug=True)

