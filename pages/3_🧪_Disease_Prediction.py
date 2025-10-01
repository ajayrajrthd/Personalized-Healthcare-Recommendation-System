import streamlit as st
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib

DATA = Path(__file__).resolve().parents[1] / "data" / "medical_records.csv"
MODEL = Path(__file__).resolve().parents[1] / "models" / "disease_model.pkl"

st.title("🧪 Disease Prediction")

df = pd.read_csv(DATA)
st.write("Sample of training data")
st.dataframe(df.head())

if st.button("Train / Retrain Model"):
    X = df[["age","blood_pressure","glucose_level","heart_rate"]]
    y = df["diagnosis"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", MLPClassifier(hidden_layer_sizes=(16,8), random_state=42, max_iter=500))
    ])
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    st.success(f"Model trained. Test accuracy: {acc:.2f}")
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, MODEL)

st.write("### Try a Prediction")
age = st.number_input("Age", 1, 120, 45)
bp = st.number_input("Blood Pressure (systolic)", 80, 220, 128)
gl = st.number_input("Glucose Level (mg/dL)", 50, 400, 110)
hr = st.number_input("Heart Rate (bpm)", 40, 200, 76)

if st.button("Predict Diagnosis"):
    try:
        import joblib
        pipe = joblib.load(MODEL)
    except Exception:
        st.warning("Model not trained yet. Training a quick default model...")
        X = df[["age","blood_pressure","glucose_level","heart_rate"]]
        y = df["diagnosis"]
        pipe = Pipeline([("scaler", StandardScaler()), ("clf", MLPClassifier(hidden_layer_sizes=(16,8), random_state=42, max_iter=500))])
        pipe.fit(X, y)
        joblib.dump(pipe, MODEL)

    pred = pipe.predict([[age, bp, gl, hr]])[0]
    st.success(f"Predicted diagnosis: **{pred}**")
