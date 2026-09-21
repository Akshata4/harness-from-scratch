# Autoresearch target file.
#
# Contract: this script is free to change in any way (model, features,
# preprocessing, hyperparameters) EXCEPT for one rule — it must print
# exactly one line of the form:
#
#     METRIC: <float>
#
# as its last line of output. That line is how the harness reads your
# score after each run. Higher is better (this metric is accuracy on a
# held-out test split). The train/test split's random_state must stay
# fixed at 42 so scores are comparable across iterations.

from sklearn.datasets import load_breast_cancer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

data = load_breast_cancer()
X_train, X_test, y_train, y_test = train_test_split(
    data.data, data.target, test_size=0.3, random_state=42
)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

model = LogisticRegression(max_iter=200)
model.fit(X_train_scaled, y_train)

predictions = model.predict(X_test_scaled)
accuracy = accuracy_score(y_test, predictions)

print(f"METRIC: {accuracy}")