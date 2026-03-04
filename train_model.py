import pandas as pd
import pickle
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer

from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.metrics import roc_curve
from sklearn.metrics import auc

from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier

import xgboost as xgb


# LOAD DATA
data = pd.read_csv("data/fake_job_postings.csv")

# COMBINE TEXT COLUMNS
data["text"] = (
    data["title"].fillna("") + " " +
    data["description"].fillna("") + " " +
    data["requirements"].fillna("")
)

X = data["text"]
y = data["fraudulent"]


# TRAIN TEST SPLIT
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)


# TF-IDF
vectorizer = TfidfVectorizer(
    stop_words="english",
    max_features=10000,
    ngram_range=(1,2)
)

X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)


# MODELS
models = {

    "Logistic Regression":
        LogisticRegression(max_iter=200),

    "Linear SVM":
        LinearSVC(),

    "Random Forest":
        RandomForestClassifier(n_estimators=100),

    "XGBoost":
        xgb.XGBClassifier(eval_metric="logloss")

}


best_model = None
best_accuracy = 0
best_preds = None


print("\nMODEL PERFORMANCE COMPARISON\n")


for name, model in models.items():

    model.fit(X_train_vec, y_train)

    preds = model.predict(X_test_vec)

    acc = accuracy_score(y_test, preds)

    print(f"{name} Accuracy: {acc:.4f}")

    if acc > best_accuracy:
        best_accuracy = acc
        best_model = model
        best_preds = preds


print("\nBest Model:", best_model)
print("Best Accuracy:", best_accuracy)


# CONFUSION MATRIX
print("\nConfusion Matrix\n")

cm = confusion_matrix(y_test, best_preds)

print(cm)


# CLASSIFICATION REPORT
print("\nClassification Report\n")

report = classification_report(y_test, best_preds)

print(report)


# ROC CURVE (only if model supports probability)

if hasattr(best_model, "predict_proba"):

    probs = best_model.predict_proba(X_test_vec)[:,1]

    fpr, tpr, thresholds = roc_curve(y_test, probs)

    roc_auc = auc(fpr, tpr)

    plt.figure()

    plt.plot(fpr, tpr, label=f"ROC Curve (AUC = {roc_auc:.3f})")

    plt.plot([0,1], [0,1], linestyle="--")

    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")

    plt.legend()

    plt.show()


# SAVE MODEL
pickle.dump(best_model, open("model/job_model.pkl", "wb"))
pickle.dump(vectorizer, open("model/vectorizer.pkl", "wb"))

print("\nModel and vectorizer saved successfully.")