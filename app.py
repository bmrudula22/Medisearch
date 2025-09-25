import streamlit as st
import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import Error
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MySQL Connection Configuration
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE', 'medisearch_db')
}

# Page configuration
st.set_page_config(
    page_title="MediSearch - MySQL Database Edition",
    page_icon="🩺",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 3rem; color: #2E86AB; text-align: center; margin-bottom: 1rem; }
    .med-card { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); padding: 1rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid #4CAF50; }
    .db-status { background: #d4edda; padding: 0.5rem; border-radius: 5px; border-left: 3px solid #28a745; margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_db_connection():
    """Establish MySQL connection with status display"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            db_info = connection.get_server_info()
            st.markdown(f"""
            <div class="db-status">
                ✅ **MySQL Connected!** Server: {db_info} | Database: {DB_CONFIG['database']}
            </div>
            """, unsafe_allow_html=True)
            return connection
    except Error as e:
        st.error(f"❌ **Database Connection Failed:** {e}")
        st.info("""
        💡 **Troubleshooting:**
        - MySQL Server running? (Run 'net start MySQL80' as admin in Command Prompt)
        - Correct credentials in .env file? (Check MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE)
        - Database exists? (Run SQL setup in MySQL client)
        """)
        return None

def execute_query(connection, query, params=None):
    """Execute SQL query with reconnection"""
    try:
        if connection and connection.is_connected():
            connection.ping(reconnect=True, attempts=3, delay=1)
        else:
            st.warning("⚠️ Connection not established. Reconnecting...")
            connection = get_db_connection()
            if not connection or not connection.is_connected():
                st.error("❌ Failed to reconnect to database")
                return pd.DataFrame()
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        cursor.close()
        df = pd.DataFrame(results, columns=columns)
        return df
    except Error as e:
        st.error(f"❌ **Query Error:** {e} | Query: {query[:100]}...")
        return pd.DataFrame()

def load_medicines_from_db(connection):
    """Load medicines with aggregated purchase info, ensuring no duplicates"""
    query = """
    SELECT m.*, 
           (SELECT COUNT(DISTINCT ph.id) FROM purchase_history ph WHERE ph.medicine_id = m.id) as purchase_count
    FROM medicines m
    GROUP BY m.id, m.name, m.type, m.treats, m.rating, m.price, m.reviews
    ORDER BY m.rating DESC
    """
    df = execute_query(connection, query)
    if not df.empty:
        # Ensure no duplicates by dropping based on name if any persist
        df = df.drop_duplicates('name', keep='first')
    return df

def get_user_history(connection, user_id):
    """Get aggregated user purchase history"""
    query = """
    SELECT m.name, m.type, m.rating, m.price,
           SUM(ph.quantity) as total_quantity,
           MAX(ph.purchase_date) as latest_purchase_date
    FROM purchase_history ph
    JOIN medicines m ON ph.medicine_id = m.id
    WHERE ph.user_id = %s
    GROUP BY m.id, m.name, m.type, m.rating, m.price
    ORDER BY latest_purchase_date DESC
    """
    return execute_query(connection, query, (user_id,))

def search_medicines_db(connection, query, search_type="both"):
    """Advanced search with SQL full-text capabilities"""
    query_lower = f"%{query.lower()}%"
    
    if search_type == "medicine":
        search_query = """
        SELECT *, 
               CASE 
                   WHEN name LIKE %s THEN 2
                   ELSE 0 
               END as relevance_score
        FROM medicines 
        WHERE name LIKE %s
        ORDER BY relevance_score DESC, rating DESC
        """
        params = (query_lower, query_lower)
    elif search_type == "symptom":
        search_query = """
        SELECT *, 
               CASE 
                   WHEN treats LIKE %s THEN 1
                   ELSE 0 
               END as relevance_score
        FROM medicines 
        WHERE treats LIKE %s
        ORDER BY relevance_score DESC, rating DESC
        """
        params = (query_lower, query_lower)
    else:  # both
        search_query = """
        SELECT *, 
               CASE 
                   WHEN name LIKE %s THEN 2
                   WHEN treats LIKE %s THEN 1
                   ELSE 0 
               END as relevance_score
        FROM medicines 
        WHERE name LIKE %s OR treats LIKE %s
        ORDER BY relevance_score DESC, rating DESC
        """
        params = (query_lower, query_lower, query_lower, query_lower)
    
    return execute_query(connection, search_query, params)

def generate_recommendations_db(connection, user_history_names):
    """Generate recommendations and return as JSON-compatible dict"""
    if not user_history_names:
        return [], {}
    
    placeholders = ','.join(['%s'] * len(user_history_names))
    
    category_query = f"""
    SELECT DISTINCT m2.name, m2.rating, m2.type,
           COUNT(ph.id) as popularity_score
    FROM medicines m1
    JOIN medicines m2 ON m1.type = m2.type
    LEFT JOIN purchase_history ph ON m2.id = ph.medicine_id
    WHERE m1.name IN ({placeholders})
    AND m2.name NOT IN ({placeholders})
    GROUP BY m2.id, m2.name, m2.rating, m2.type
    ORDER BY m2.rating DESC, popularity_score DESC
    LIMIT 3
    """
    
    category_recs = execute_query(connection, category_query, user_history_names + user_history_names)
    
    symptom_query = f"""
    SELECT DISTINCT m2.name, m2.rating,
           (SELECT COUNT(*) FROM purchase_history ph WHERE ph.medicine_id = m2.id) as popularity
    FROM medicines m1
    JOIN medicines m2 ON (
        m2.treats LIKE CONCAT('%', SUBSTRING_INDEX(m1.treats, ',', 1), '%') OR
        m1.treats LIKE CONCAT('%', SUBSTRING_INDEX(m2.treats, ',', 1), '%')
    )
    WHERE m1.name IN ({placeholders})
    AND m2.name NOT IN ({placeholders})
    ORDER BY m2.rating DESC, popularity DESC
    LIMIT 3
    """
    
    symptom_recs = execute_query(connection, symptom_query, user_history_names + user_history_names)
    
    popular_query = f"""
    SELECT name, rating, reviews,
           COUNT(ph.id) as purchase_count
    FROM medicines m
    LEFT JOIN purchase_history ph ON m.id = ph.medicine_id
    WHERE m.name NOT IN ({placeholders})
    GROUP BY m.id, m.name, m.rating, m.reviews
    ORDER BY purchase_count DESC, rating DESC
    LIMIT 2
    """
    
    popular_recs = execute_query(connection, popular_query, user_history_names)
    
    all_recs = pd.concat([
        category_recs.assign(source='category'),
        symptom_recs.assign(source='symptom'),
        popular_recs.assign(source='popular')
    ], ignore_index=True)
    
    unique_recs = all_recs.drop_duplicates('name').sort_values('rating', ascending=False)
    top_recs = unique_recs.head(4)
    
    # Create JSON-compatible dictionary
    json_response = {
        "recommendations": [
            {
                "name": row['name'],
                "type": row['type'] if 'type' in row else None,
                "rating": float(row['rating']) if row['rating'] else 0.0,
                "source": row['source']
            } for _, row in top_recs.iterrows()
        ],
        "based_on_history": user_history_names,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    return top_recs['name'].tolist(), json_response

def display_medicine_card_db(med_row):
    """Display medicine card from database results"""
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.markdown(f"""
        <div class="med-card">
            <h3 style="margin: 0 0 0.5rem 0; color: #2E86AB;">{med_row['name']}</h3>
            <p style="margin: 0.2rem 0;"><strong>Type:</strong> {med_row['type']}</p>
            <p style="margin: 0.2rem 0; font-size: 0.9rem;">
                <strong>Treats:</strong> {med_row['treats'][:60]}{'...' if len(med_row['treats']) > 60 else ''}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        rating = float(med_row['rating']) if med_row['rating'] else 0
        stars = "⭐" * int(rating // 2) + "🌟" * (int(rating % 2))
        st.markdown(f"""
        <div style="text-align: center; background: linear-gradient(135deg, #28a745, #20c997); 
                    color: white; padding: 0.8rem; border-radius: 8px;">
            <div style="font-size: 1.1rem;">{stars}</div>
            <div style="font-size: 0.9rem;">{rating}/10</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        price = float(med_row['price']) if med_row['price'] else 0
        st.markdown(f"""
        <div style="text-align: center; background: linear-gradient(135deg, #ffc107, #fd7e14); 
                    color: #212529; padding: 0.8rem; border-radius: 8px; font-weight: bold;">
            <div style="font-size: 1.2rem;">${price:.2f}</div>
            <div style="font-size: 0.8rem;">per pack</div>
        </div>
        """, unsafe_allow_html=True)

# Main application
def main():
    # Database Connection
    connection = get_db_connection()
    if not connection:
        st.stop()
    
    # Load all data
    df_medicines = load_medicines_from_db(connection)
    
    # Sidebar - User Selection for Real History
    st.sidebar.header("👤 User Profile")
    users_df = execute_query(connection, "SELECT id, name, profile FROM users ORDER BY name")
    if not users_df.empty:
        # Remove any potential duplicates
        users_df = users_df.drop_duplicates(subset=['id', 'name', 'profile'])
        selected_user_id = st.sidebar.selectbox(
            "Select User:",
            options=users_df['id'].tolist(),
            format_func=lambda x: users_df[users_df['id'] == x]['name'].iloc[0],
            key="user_select"
        )
        user_history_df = get_user_history(connection, selected_user_id)
        user_history_names = user_history_df['name'].tolist() if not user_history_df.empty else []
        
        if user_history_names:
            history_display = [f"{name} (Qty: {row['total_quantity']}, Last: {row['latest_purchase_date'].strftime('%Y-%m-%d')})" 
                             for name, row in zip(user_history_df['name'], user_history_df.to_dict('records'))]
            st.sidebar.success(f"📋 History: {', '.join(history_display)}")
        else:
            st.sidebar.info("No purchase history for this user.")
    else:
        st.sidebar.warning("No users in database.")
        selected_user_id = None
        user_history_names = []
    
    # Fallback to manual if no user selected or empty history
    if not user_history_names:
        st.sidebar.header("🛠️ Manual History Override")
        manual_history = st.sidebar.multiselect(
            "Select Medicines for Recommendations:",
            options=df_medicines['name'].tolist() if not df_medicines.empty else [],
            default=[],
            help="Select medicines to generate recommendations"
        )
        history_to_use = manual_history
    else:
        history_to_use = user_history_names
    
    # Main Tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Search", "💊 Recommendations", "📊 Database"])
    
    with tab1:
        st.header("🔍 Database-Powered Search")
        st.markdown("*Real-time queries against MySQL database*")
        
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            search_query = st.text_input(
                "🔍 Search medicines or symptoms:",
                placeholder="e.g., Aspirin, headache, diabetes, erectile dysfunction",
                key="search_query",
                help="Database searches in real-time"
            )
        with col2:
            search_type = st.selectbox("Search Type:", ["Both", "Medicine Only", "Symptoms Only"])
        with col3:
            if st.button("Clear Search"):
                st.session_state.search_query = ""
                st.rerun()
        
        if search_query:
            with st.spinner(f"Searching database for '{search_query}'..."):
                results = search_medicines_db(connection, search_query, search_type.lower().replace(" ", "_"))
                
                if not results.empty:
                    st.success(f"✅ **{len(results)} results** found")
                    name_matches = len(results[results['name'].str.lower().str.contains(search_query.lower(), na=False)])
                    symptom_matches = len(results) - name_matches
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Name Matches", name_matches)
                    with col_b:
                        st.metric("Symptom Matches", symptom_matches)
                    
                    for i, (_, med) in enumerate(results.head(10).iterrows(), 1):
                        st.markdown(f"**{i}.**")
                        display_medicine_card_db(med)
                        if i % 3 == 0:
                            st.markdown("---")
                else:
                    st.warning(f"❌ No results found for '{search_query}'")
                    st.info("💡 Try these common searches:")
                    col1, col2, col3 = st.columns(3)
                    if col1.button("Headache"): 
                        st.session_state.search_query = "headache"
                        st.rerun()
                    if col2.button("Diabetes"): 
                        st.session_state.search_query = "diabetes"
                        st.rerun()
                    if col3.button("Cholesterol"): 
                        st.session_state.search_query = "cholesterol"
                        st.rerun()
        else:
            st.subheader("🌟 Top Rated Medicines (Database)")
            featured = execute_query(connection, "SELECT * FROM medicines ORDER BY rating DESC LIMIT 6")
            cols = st.columns(3)
            for i, (_, med) in enumerate(featured.iterrows()):
                with cols[i % 3]:
                    display_medicine_card_db(med)
    
    with tab2:
        st.header("💊 Database Recommendations")
        
        if history_to_use:
            st.success(f"🤖 Analyzing history: **{', '.join(history_to_use)}**")
            
            with st.spinner("Generating database recommendations..."):
                recommendations, json_response = generate_recommendations_db(connection, history_to_use)
                
                if recommendations:
                    st.markdown(f"<h3>🔥 **{len(recommendations)} Database Recommendations**</h3>", unsafe_allow_html=True)
                    
                    placeholders_rec = ','.join(['%s'] * len(recommendations))
                    rec_query = f"SELECT * FROM medicines WHERE name IN ({placeholders_rec}) ORDER BY FIELD(name, {placeholders_rec})"
                    rec_df = execute_query(connection, rec_query, recommendations + recommendations)
                    
                    st.markdown("**📊 Recommendation Strategy:**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.success("✅ **Category Match**")
                    with col2:
                        st.success("✅ **Symptom Match**")
                    with col3:
                        st.success("✅ **Popularity Boost**")
                    
                    for i, (_, med) in enumerate(rec_df.iterrows(), 1):
                        st.markdown(f"**{i}.**")
                        display_medicine_card_db(med)
                        
                        with st.expander(f"💡 Why {med['name']}?", expanded=False):
                            user_meds = execute_query(connection, f"SELECT treats, type FROM medicines WHERE name IN ({','.join(['%s'] * len(history_to_use))})", history_to_use)
                            
                            if not user_meds.empty:
                                user_treats = pd.concat([pd.Series(str(t).split(',')) for t in user_meds['treats']]).str.strip().str.lower().unique()
                                med_treats = [s.strip().lower() for s in str(med['treats']).split(',')]
                                
                                if 'type' in user_meds and med['type'] in user_meds['type'].values:
                                    st.markdown("• **Same Category** as your previous purchases")
                                
                                common = set(user_treats) & set(med_treats)
                                if common:
                                    st.markdown(f"• **Symptom Overlap**: {', '.join(list(common)[:2])}")
                                
                                if float(med['rating']) >= 8.0:
                                    st.markdown(f"• **High Quality**: {med['rating']}/10 rating")
                            
                            st.caption(f"Based on database analysis of {len(df_medicines)} medicines")
                    
                    # Display JSON response
                    st.subheader("📋 JSON Recommendations")
                    st.json(json_response)
                    json_str = json.dumps(json_response, indent=2)
                    st.download_button(
                        label="Download Recommendations as JSON",
                        data=json_str,
                        file_name=f"recommendations_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                else:
                    st.warning("❌ No recommendations generated")
                    st.info("💡 Try selecting a user with history or 2-3 medicines from different categories")
        else:
            st.info("👆 **Select a user** in the sidebar to load their purchase history, or use manual override.")
            st.markdown("""
            ### 📋 Database Tables Used:
            - **medicines** - Medicine catalog (name, type, treats, rating, price, reviews)
            - **users** - User profiles (id, name, profile)
            - **purchase_history** - User purchases (user_id, medicine_id, quantity, purchase_date)
            """)
    
    with tab3:
        st.header("🗄️ Database Explorer")
        
        st.subheader("📊 Schema Overview")
        stats = {}
        for table in ['medicines', 'users', 'purchase_history']:
            count = execute_query(connection, f"SELECT COUNT(*) as count FROM {table}")
            stats[table] = count['count'].iloc[0] if not count.empty else 0
        
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Medicines", stats['medicines'])
        with col2: st.metric("Users", stats['users'])
        with col3: st.metric("Purchases", stats['purchase_history'])
        
        st.subheader("🔍 Browse Tables")
        table_choice = st.selectbox("Select Table:", ['medicines', 'users', 'purchase_history'])
        
        if table_choice == 'medicines':
            query = "SELECT name, type, rating, price, reviews FROM medicines ORDER BY rating DESC LIMIT 20"
            data = execute_query(connection, query)
            st.dataframe(data, use_container_width=True)
        elif table_choice == 'users':
            query = """
            SELECT u.*, COUNT(ph.id) as total_purchases
            FROM users u
            LEFT JOIN purchase_history ph ON u.id = ph.user_id
            GROUP BY u.id, u.name, u.profile
            ORDER BY u.name
            """
            data = execute_query(connection, query)
            st.dataframe(data, use_container_width=True)
        else:  # purchase_history
            query = """
            SELECT ph.*, u.name as user_name, m.name as medicine_name
            FROM purchase_history ph
            JOIN users u ON ph.user_id = u.id
            JOIN medicines m ON ph.medicine_id = m.id
            ORDER BY ph.purchase_date DESC
            """
            data = execute_query(connection, query)
            st.dataframe(data, use_container_width=True)
        
        st.subheader("⚡ Custom SQL Query")
        custom_sql = st.text_area("Write your own query:", 
                                value="SELECT * FROM medicines WHERE rating > 8.0 ORDER BY reviews DESC LIMIT 5",
                                height=100,
                                help="Try: SELECT name, type FROM medicines WHERE treats LIKE '%headache%'")
        
        if st.button("🔍 Run Custom Query") and custom_sql.strip():
            with st.spinner("Executing custom query..."):
                custom_results = execute_query(connection, custom_sql)
                if not custom_results.empty:
                    st.success(f"✅ Query returned {len(custom_results)} rows")
                    st.dataframe(custom_results, use_container_width=True)
                else:
                    st.warning("No results returned")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### 🏗️ Database Architecture
        - **MySQL 8.0** - Relational database
        - **3 Tables** - Normalized schema with foreign keys
        - **Medicines** - Core catalog with categories & symptoms
        - **Real JOIN queries** - For category, symptom, & collaborative filtering
        """)
    with col2:
        st.warning("""
        ### ⚠️ Educational Demo
        **Database-Driven Medicine Recommender**  
        Always consult healthcare professionals for medical advice.
        """)

if __name__ == "__main__":
    main()