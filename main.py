from wtforms import StringField, SubmitField, IntegerField, SelectField, RadioField, validators
from flask import Flask, render_template, request, session
from flask_wtf import FlaskForm
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
    title            = StringField('Title', []) # validators.DataRequired()
    lang             = RadioField("Lang", choices=[("native","jp"),("romaji", "en")])
    page_nav         = SelectField('Page Navigation', choices=[(1, 'Next Page'), (0, 'This Page'), (-1, 'Previous Page')])
    page_title_count = IntegerField("TitlePerPage", [validators.NumberRange(min=4, max=4*25)])
    submit           = SubmitField('Submit')

# ////////////////////////////////////////
# FUNCTIONS
# ////////////////////////////////////////
def clamp(value, min_value, max_value):
    value = min(value, max_value)
    value = max(value, min_value)
    return value
# ////////////////////////////////////////
# HELPERS ////////////////////////////////
def api_get_data(search_term, page_title_count, page_number):
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
    print("search: ", search_term)
    print("page #: ", page_number)
    print("titl per page: ", page_title_count)
    variables = {
        'search': search_term,
        'page': page_number,
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
    if 'current_page_number' not in session:
        session['current_page_number']   = 0
    if 'current_page_maxcount' not in session:
        session['current_page_maxcount'] = 1
    if 'title' not in session:
        session['title']   = ""
    if 'lang' not in session:
        session['lang'] = "romaji"
    if 'title count' not in session:
        session['title count'] = 1

    current_page_number   = session["current_page_number"]  
    current_page_maxcount = session["current_page_maxcount"]
    submitted_title      = session["title"] 
    submitted_lang       = session["lang"]
    submitted_titlecount = session["title count"]
    submitted_nav_ctrl   = 0 

    # FORM
    form = SimpleForm()
    if request.method == "POST":
        submitted_title      = form.title.data if form.title.data else None
        submitted_lang       = form.lang.data
        submitted_nav_ctrl   = int(form.page_nav.data) if form.page_nav.data else 0
        submitted_titlecount = form.page_title_count.data
    

    # NOTE(): moved because theres a delay cause page number is updated after the api call
    current_page_number    = clamp(current_page_number + submitted_nav_ctrl, 1, current_page_maxcount)
    
    # API CALL
    api_data        = api_get_data(submitted_title, submitted_titlecount, current_page_number); 
    form_data       = [submitted_title, submitted_lang, submitted_titlecount]
    media_data      = api_data["data"]["Page"]["media"]
    pagination_data = api_data["data"]["Page"]["pageInfo"]
    current_page_maxcount  = pagination_data["total"] if pagination_data else 1
    session["current_page_number"]   = current_page_number
    session["current_page_maxcount"] = current_page_maxcount
    # RENDER
    return render_template("index.html", media_data=media_data, pagination_data=pagination_data, submitted_form_data=form_data, form=form)

@app.route('/about')
def about():
    return render_template("about.html") 

@app.route('/contact')
def contact():
    return render_template("contact.html") 

# ////////////////////////////////////////
# ENTRY POINT
# ////////////////////////////////////////
if __name__ == '__main__':
    app.run(debug=True)

