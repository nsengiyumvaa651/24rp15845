import streamlit as st
import pickle
import pandas as pd
import mysql.connector
from mysql.connector import Error

# Load the trained model
with open('student_performance_model.pkl', 'rb') as f:
    model = pickle.load(f)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'student_db',
    'user': 'root',
    'password': '',
    'auth_plugin': 'mysql_native_password'
}

# Function to save prediction
def save_prediction(features, prediction):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        insert_query = """INSERT INTO student_performance 
                         (Attendance, Assignment_Score, Midterm_Score,
                          Final_Score, Outstanding_Balance, Library_Visits,
                          Performance)
                         VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        
        cursor.execute(insert_query,
                     (float(features['Attendance'].values[0]),
                      float(features['Assignment_Score'].values[0]),
                      float(features['Midterm_Score'].values[0]),
                      int(features['Final_Score'].values[0]),
                      int(features['Outstanding_Balance'].values[0]),
                      int(features['Library_Visits'].values[0]),
                      prediction[0]))
        conn.commit()
        return True
    except Error as e:
        st.error(f"Failed to save prediction: {e}")
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# Set up the Streamlit app
st.title('🎓 Student Performance Predictor')
st.write("Predict whether a student will **Pass** or **Fail** based on their academic metrics.")

# Sidebar with user inputs
st.sidebar.header('Input Student Features')

def user_input_features():
    attendance = st.sidebar.slider('Attendance (%)', 0, 100, 85)
    assignment = st.sidebar.slider('Assignment Score', 0, 100, 75)
    midterm = st.sidebar.slider('Midterm Score', 0, 100, 65)
    final = st.sidebar.slider('Final Score', 0, 100, 70)
    balance = st.sidebar.selectbox('Outstanding Balance', [0, 100000, 250000, 300000, 450000, 500000, 600000])
    library = st.sidebar.slider('Library Visits (per semester)', 0, 50, 20)
    
    data = {
        'Attendance': attendance,
        'Assignment_Score': assignment,
        'Midterm_Score': midterm,
        'Final_Score': final,
        'Outstanding_Balance': balance,
        'Library_Visits': library
    }
    return pd.DataFrame(data, index=[0])

input_df = user_input_features()

# Display user inputs
st.subheader('Student Metrics')
st.write(input_df)

# Prediction button
if st.button('Predict Performance'):
    with st.spinner('Making prediction...'):
        prediction = model.predict(input_df)
        prediction_proba = model.predict_proba(input_df)
        confidence = max(prediction_proba[0]) * 100
        
        # Save to MySQL database
        if save_prediction(input_df, prediction):
            st.success("Prediction saved successfully!")
        
        # Display results
        st.subheader('Prediction Results')
        
        col1, col2 = st.columns(2)
        if prediction[0] == 'Pass':
            col1.success(f"Prediction: {prediction[0]}")
        else:
            col1.error(f"Prediction: {prediction[0]}")
        col2.metric("Confidence", f"{confidence:.1f}%")
        
        st.progress(int(confidence))

# Add some styling
st.markdown("""
<style>
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        padding: 0.5rem 1rem;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
</style>
""", unsafe_allow_html=True)