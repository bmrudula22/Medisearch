USE medisearch_db;

-- Create medicines table
CREATE TABLE medicines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    treats TEXT NOT NULL,
    rating DECIMAL(3,1) DEFAULT 0.0,
    price DECIMAL(6,2) DEFAULT 0.00,
    reviews INT DEFAULT 0
);


-- Create users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    profile VARCHAR(100) NOT NULL
);

-- Insert sample users
INSERT INTO users (name, profile) VALUES 
('Sarah Johnson', 'General Health'),
('Mike Chen', 'Chronic Pain'),
('David Wilson', 'Men\'s Health'),
('Linda Martinez', 'Heart Health'),
('Robert Kim', 'Diabetes Management');


-- Insert sample medicines (copy-paste this entire block)
INSERT INTO medicines (name, type, treats, rating, price, reviews) VALUES
('Aspirin', 'Pain Relief', 'headache,pain,fever,inflammation,arthritis', 8.2, 12.99, 2456),
('Tylenol', 'Pain Relief', 'headache,fever,pain,migraine,tension headache', 8.5, 9.99, 3872),
('Ibuprofen', 'Pain Relief', 'pain,inflammation,arthritis,menstrual pain,back pain', 7.8, 8.49, 2981),
('Advil', 'Pain Relief', 'headache,pain,menstrual pain,fever,inflammation', 8.1, 10.99, 2156),
('Excedrin', 'Pain Relief', 'migraine,headache,tension headache,cluster headache', 8.7, 14.99, 1893),
('Aleve', 'Pain Relief', 'arthritis,pain,back pain,menstrual pain,inflammation', 7.5, 11.49, 1567),
('Viagra', 'Erectile Dysfunction', 'erectile dysfunction,impotence,sexual dysfunction', 7.2, 89.99, 923),
('Cialis', 'Erectile Dysfunction', 'erectile dysfunction,impotence,sexual dysfunction', 7.4, 79.99, 874),
('Levitra', 'Erectile Dysfunction', 'erectile dysfunction,impotence', 7.0, 69.99, 756),
('Lipitor', 'Cholesterol', 'high cholesterol,heart disease,cardiovascular risk', 8.0, 45.99, 2345),
('Crestor', 'Cholesterol', 'high cholesterol,heart disease,cardiovascular risk', 7.9, 42.99, 1987),
('Zocor', 'Cholesterol', 'high cholesterol,heart disease', 7.6, 38.99, 1678),
('Metformin', 'Diabetes', 'diabetes,type 2 diabetes,blood sugar control', 8.1, 15.99, 2765),
('Lantus', 'Diabetes', 'diabetes,type 1 diabetes,blood sugar control', 8.3, 129.99, 1345),
('Januvia', 'Diabetes', 'diabetes,type 2 diabetes,blood sugar control', 7.8, 89.99, 987),
('Lexapro', 'Antidepressant', 'depression,anxiety,panic disorder,OCD', 7.5, 25.99, 1567),
('Zoloft', 'Antidepressant', 'depression,anxiety,OCD,panic disorder', 7.7, 22.99, 1892),
('Prozac', 'Antidepressant', 'depression,anxiety,panic disorder', 7.4, 28.99, 1234),
('Nexium', 'Acid Reflux', 'acid reflux,GERD,heartburn,indigestion', 8.0, 35.99, 2345),
('Prilosec', 'Acid Reflux', 'acid reflux,GERD,heartburn,indigestion', 7.9, 29.99, 1987),
('Zantac', 'Acid Reflux', 'acid reflux,heartburn,indigestion', 7.2, 18.99, 1456),
('Benadryl', 'Allergy', 'allergy,seasonal allergy,hay fever,itching', 8.2, 7.99, 2876),
('Claritin', 'Allergy', 'allergy,seasonal allergy,hay fever', 8.4, 12.99, 3456),
('Zyrtec', 'Allergy', 'allergy,hay fever,seasonal allergy', 8.3, 14.99, 2987),
('Amoxicillin', 'Antibiotic', 'bacterial infection,sore throat,ear infection', 8.5, 19.99, 3876),
('Augmentin', 'Antibiotic', 'bacterial infection,sinus infection,respiratory infection', 8.7, 29.99, 4567),
('Cipro', 'Antibiotic', 'bacterial infection,urinary tract infection', 8.1, 24.99, 3892),
('Synthroid', 'Thyroid', 'hypothyroidism,thyroid disorder,weight gain', 8.6, 18.99, 2789),
('Levoxyl', 'Thyroid', 'hypothyroidism,thyroid disorder,weight gain', 8.4, 16.99, 2456);


SHOW WARNINGS;
-- OR
SELECT * FROM medicines LIMIT 5;

-- Create purchase history table and populate
CREATE TABLE purchase_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    medicine_id INT NOT NULL,
    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    quantity INT DEFAULT 1,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id)
);

INSERT INTO purchase_history (user_id, medicine_id, quantity) VALUES
(1, 1, 2),  -- Sarah: Aspirin
(1, 2, 1),  -- Sarah: Tylenol
(2, 3, 3),  -- Mike: Ibuprofen
(2, 4, 2),  -- Mike: Advil
(2, 6, 1),  -- Mike: Aleve
(3, 7, 1),  -- David: Viagra
(4, 10, 3), -- Linda: Lipitor
(4, 11, 2), -- Linda: Crestor
(5, 13, 4), -- Robert: Metformin
(5, 15, 2); -- Robert: Januvia


-- Check everything loaded correctly
SELECT COUNT(*) FROM medicines;  -- Should be 29
SELECT COUNT(*) FROM users;      -- Should be 5  
SELECT COUNT(*) FROM purchase_history;  -- Should be 10

-- Test a sample query
SELECT m.name, m.type, m.rating FROM medicines m ORDER BY m.rating DESC LIMIT 5;

SELECT id, name, profile FROM users ORDER BY name;

SELECT name, profile, COUNT(*) as count 
FROM users 
GROUP BY name, profile 
HAVING count > 1;

    
SET SQL_SAFE_UPDATES = 0;
DELETE u1 
FROM users u1
INNER JOIN users u2 
WHERE u1.id > u2.id 
  AND u1.name = u2.name 
  AND u1.profile = u2.profile;
SET SQL_SAFE_UPDATES = 1;
