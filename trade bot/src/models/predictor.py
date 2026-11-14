import joblib


class Predictor:
    def __init__(self, model, model_path):
        self.model = model
        self.path = model_path

    def load(self):
        self.model = joblib.load(self.path)

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)