from flask import Flask, render_template, request, flash
import pickle
import numpy as np
from difflib import get_close_matches

popular_df = pickle.load(open('popular.pkl','rb'))
pt = pickle.load(open('pt.pkl','rb'))
books = pickle.load(open('books.pkl','rb'))
similarity_scores = pickle.load(open('similarity_scores.pkl','rb'))

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for flash messages

def find_similar_book_title(user_input):
    """Find the closest matching book title from the dataset"""
    # Convert all titles to lowercase for case-insensitive matching
    all_titles = [title.lower() for title in pt.index]
    user_input_lower = user_input.lower()
    
    # Try exact match first
    if user_input_lower in all_titles:
        return pt.index[all_titles.index(user_input_lower)]
    
    # Try substring matching
    substring_matches = [title for title in all_titles if user_input_lower in title]
    if substring_matches:
        # Sort by length to prefer shorter matches (more specific)
        substring_matches.sort(key=len)
        return pt.index[all_titles.index(substring_matches[0])]
    
    # Try fuzzy matching with a lower threshold for more matches
    matches = get_close_matches(user_input_lower, all_titles, n=3, cutoff=0.4)
    if matches:
        # Return the best match
        return pt.index[all_titles.index(matches[0])]
    
    return None

@app.route('/')
def index():
    return render_template('index.html',
                         book_name=list(popular_df['Book-Title'].values),
                         author=list(popular_df['Book-Author'].values),
                         image=list(popular_df['Image-URL-M'].values),
                         votes=list(popular_df['num_ratings'].values),
                         rating=list(popular_df['avg_rating'].values)
                         )

@app.route('/recommend')
def recommend_ui():
    return render_template('recommend.html')

@app.route('/recommend_books', methods=['POST'])
def recommend():
    try:
        user_input = request.form.get('user_input', '').strip()
        
        if not user_input:
            flash('Please enter a book title', 'error')
            return render_template('recommend.html')
        
        # Find the closest matching book title
        matched_title = find_similar_book_title(user_input)
        
        if not matched_title:
            flash(f'No books found matching "{user_input}". Please try a different title.', 'error')
            return render_template('recommend.html')
        
        # Get the index of the matched book
        try:
            index = np.where(pt.index == matched_title)[0][0]
        except IndexError:
            flash('An error occurred while processing your request. Please try again.', 'error')
            return render_template('recommend.html')
        
        # Get similar books
        similar_items = sorted(list(enumerate(similarity_scores[index])), 
                             key=lambda x: x[1], reverse=True)[1:6]  # Get top 5 recommendations
        
        data = []
        for i in similar_items:
            try:
                item = []
                temp_df = books[books['Book-Title'] == pt.index[i[0]]]
                if not temp_df.empty:
                    item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
                    item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
                    item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))
                    data.append(item)
            except Exception as e:
                continue  # Skip this item if there's an error
        
        if not data:
            flash('No similar books found. Please try a different title.', 'error')
            return render_template('recommend.html')
        
        if matched_title.lower() != user_input.lower():
            flash(f'Showing recommendations for "{matched_title}"', 'info')
        
        return render_template('recommend.html', data=data, search_term=user_input)
        
    except Exception as e:
        flash('An unexpected error occurred. Please try again.', 'error')
        return render_template('recommend.html')

if __name__ == '__main__':
    app.run(debug=True)