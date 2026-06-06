from app.ml.anomaly_model import AnomalyDetector


def test_anomaly_score_range():
    detector = AnomalyDetector()
    score, is_anomaly = detector.score([500, 10, 50, 12, 365])
    assert 0 <= score <= 1
    assert isinstance(is_anomaly, bool)
