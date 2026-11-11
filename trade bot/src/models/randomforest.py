
from models.base import BaseModel
from sklearn.ensemble import RandomForestClassifier

class RandomForestModel(BaseModel):
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100,
            random_state=420
        )

        self.trained = False

    def fit(self, X, y):
        self.model.fit(X, y)
        self.trained = True

    def predict(self, X):
        if not self.trained:
            raise RuntimeError('Model must be trained first')
        
        return self.model.predict_proba(X)