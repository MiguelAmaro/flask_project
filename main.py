from wtforms import StringField, SubmitField, IntegerField, SelectField, RadioField, validators
from flask import Flask, render_template, request, session
from flask_wtf import FlaskForm
import requests
import json
import os

# ////////////////////////////////////////
# GROUP:

# MIGUEL AMARO
# JON LOPEZ
# ////////////////////////////////////////

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
    lang             = RadioField("Lang", choices=[("native", "jp"),("romaji", "en")])
    page_nav         = SelectField('Page Navigation', choices=[(1, 'Next Page'), (0, 'This Page'), (-1, 'Previous Page')], default='0')
    page_title_count = IntegerField("TitlePerPage", [validators.NumberRange(min=4, max=4*25)])
    submit           = SubmitField('Submit')

# ////////////////////////////////////////
# FUNCTIONS
# ////////////////////////////////////////

# ////////////////////////////////////////
# HELPERS ////////////////////////////////
def clamp(value, min_value, max_value):
    value = min(value, max_value)
    value = max(value, min_value)
    return value

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
    # INIT SESSION STATE
    if 'current_page_number' not in session:
        session['current_page_number'] = 1
    if 'last_page_number' not in session:
        session['last_page_number']    = 1
    if 'title' not in session:
        session['title']   = None
    if 'lang' not in session:
        session['lang'] = "romaji"
    if 'title count' not in session:
        session['title count'] = 16

    # READ LAST SESSION STATE
    should_clear_page_number = False
    current_page_number   = session["current_page_number"]  
    last_page_number      = session["last_page_number"]  
    submitted_title       = session["title"] 
    submitted_lang        = session["lang"]
    submitted_titlecount  = session["title count"]
    submitted_nav_ctrl    = 0 

    # FORM
    form = SimpleForm()
    if request.method == "POST":
        new_title = form.title.data if len(form.title.data)>0 else None
        should_clear_page_number = submitted_title != new_title 
        
        submitted_title      = new_title
        submitted_lang       = form.lang.data
        submitted_nav_ctrl   = int(form.page_nav.data) if form.page_nav.data else 0
        submitted_titlecount = form.page_title_count.data

    # COMPUTE NEW PAGE NUMBER
    current_page_number = clamp(current_page_number + submitted_nav_ctrl, 1, last_page_number)
    current_page_number = 1 if should_clear_page_number else current_page_number

    # API CALL
    api_data         = api_get_data(submitted_title, submitted_titlecount, current_page_number); 
    media_data       = api_data["data"]["Page"]["media"]
    pagination_data  = api_data["data"]["Page"]["pageInfo"]
    form_data        = [submitted_title, submitted_lang, submitted_titlecount]
    last_page_number = pagination_data["lastPage"]
    
    # UPDATE SESSION STATE
    session["title"]               = submitted_title 
    session["lang"]                = submitted_lang 
    session["title count"]         = submitted_titlecount
    session["current_page_number"] = current_page_number
    session["last_page_number"]    = last_page_number

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
    app.run()
    #app.run(debug=True)

