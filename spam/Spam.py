# Βασικές βιβλιοθήκες
import pandas as pd
import numpy as np
import re
import string

# Machine Learning
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder

def clean_text(text):
    """Βελτιωμένος καθαρισμός κειμένου"""
    if not isinstance(text, str):
        return ""
    
    text = text.lower()
    text = re.sub(f'[{re.escape(string.punctuation)}]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'\d+', '', text)
    return text

def evaluate_model(model, X, y, set_name="Set"):
    """Ενιαία συνάρτηση αξιολόγησης"""
    y_pred = model.predict(X)
    accuracy = accuracy_score(y, y_pred)
    print(f"{set_name} Accuracy: {accuracy:.4f}")
    return y_pred, accuracy

# Φόρτωση δεδομένων
df = pd.read_csv('spam/spam.csv', encoding='latin-1', 
                 usecols=[0, 1],
                 names=['label', 'message'],
                 header=0)

# Καθαρισμός δεδομένων
df = df.dropna()
df['cleaned_message'] = df['message'].apply(clean_text)

# Κωδικοποίηση labels
le = LabelEncoder()
df['label_encoded'] = le.fit_transform(df['label'])

# Vectorization
tfidf = TfidfVectorizer(max_features=5000, stop_words='english')
X = tfidf.fit_transform(df['cleaned_message']).toarray()
y = df['label_encoded']

print("Shape of feature matrix X:", X.shape)

# Διαχωρισμός δεδομένων
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Train set: {X_train.shape}, Test set: {X_test.shape}")

# Εκπαίδευση μοντέλου
nb_classifier = MultinomialNB()
nb_classifier.fit(X_train, y_train)

print("✅ Model training completed!")

# Αξιολόγηση
y_train_pred, train_acc = evaluate_model(nb_classifier, X_train, y_train, "Training")
y_test_pred, test_acc = evaluate_model(nb_classifier, X_test, y_test, "Test")

print("\n📊 Classification Report:")
print(classification_report(y_test, y_test_pred, target_names=le.classes_))

# Συνάρτηση πρόβλεψης
def predict_spam(message):
    """Πρόβλεψη για νέα μηνύματα"""
    cleaned_msg = clean_text(message)
    msg_vector = tfidf.transform([cleaned_msg]).toarray()
    prediction = nb_classifier.predict(msg_vector)[0]
    probability = nb_classifier.predict_proba(msg_vector)[0]
    
    result = le.classes_[prediction]
    confidence = probability[prediction]
    
    print(f"📨 Message: {message}")
    print(f"🔍 Prediction: {result} (confidence: {confidence:.4f})")
    print("---")
    
    return result

# Δοκιμές
test_messages = [
    "Congratulations! You won a $1000 prize! Call now to claim.",
    "Hey, are we still meeting for lunch tomorrow?",
    "Free entry to win a car! Text YES to 12345",
    "Mom, can you pick me up from school?"
]

