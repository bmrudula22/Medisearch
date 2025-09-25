# 💊 MediSearch  
A Medicine Recommendation and Search Engine built with **Streamlit** + **MySQL**.  

---

## 🚀 Overview  
MediSearch is a web-based application that allows users to search for medicines, get personalized recommendations, and explore purchase history in a simple, interactive interface.  

It uses:  
- **Streamlit** for the user interface  
- **MySQL** for data storage  
- **Pandas & NumPy** for data handling  
- **Python Dotenv** for secure environment variable management  

---

## ✨ Features  
- 🔍 Search medicines by **name** or **symptoms**  
- ⭐ View **top-rated medicines**  
- 🧑‍⚕️ Get **personalized recommendations** based on purchase history  
- 📊 Explore the **database interactively**  

---

## 🛠️ Tech Stack  
- Python (Streamlit, Pandas, NumPy)  
- MySQL  
- Python Dotenv  

---

## ⚙️ Installation & Setup  

### 1️⃣ Clone the repository  
```bash
git clone <https://github.com/bmrudula22/Medisearch.git>
cd MediSearch
```

### 2️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣ Setup environment variables
Create a file named .env in the root folder and add:
```bash
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=yourpassword
MYSQL_DATABASE=medisearch_db
```
### 4️⃣ Setup the database
Run the SQL schema file:
```bash
mysql -u root -p medisearch_db < db/schema.sql
```

### 5️⃣ Run the app
```bash
streamlit run app.py
```
### 🗄️ Database Schema

medicines → stores medicine details

users → stores user information

purchase_history → tracks user purchases

### 📸 Screenshots 

**1️⃣ Home Page** 

![Image](https://github.com/user-attachments/assets/6cb0314c-d886-464c-a19d-728733746e67)

**2️⃣ Search Results** 

![Image](https://github.com/user-attachments/assets/db1e1f30-304a-48e7-a904-6ee7a914ca78)

**3️⃣ Recommendations Page** 

![Image](https://github.com/user-attachments/assets/a5505527-63d6-4863-a873-1a21ab7cf200)
