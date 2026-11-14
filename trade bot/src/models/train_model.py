import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


class Trainer:
    def __init__(self, model, model_path):
        self.model = model
        self.model_path = model_path

    def save_model(self):
        joblib.dump(self.model, self.model_path)

    def evaluate_model(self, X_test, y_test):
        predictions = self.model.predict(X_test)
        return accuracy_score(y_test, predictions)

    def _split_data(self, X, y):
        return train_test_split(
     X,
            y,
            test_size=0.2,
            random_state=42,
        )

    def train_model(self, X, y):
        X_train, X_test, y_train, y_test = self._split_data(X, y)
        self.model.fit(X_train, y_train)

        return X_test, y_test
