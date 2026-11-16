"""Đánh giá mức ảnh: có/không có hư hỏng (người gán nhãn) so với dự đoán ở nhiều ngưỡng tin cậy."""
import pandas as pd


def run_batch(detector, image_paths, min_conf=0.10, imgsz=640):
    """Chạy một lần ở ngưỡng thấp nhất; lọc theo ngưỡng cao hơn sau đó (tiết kiệm thời gian)."""
    from PIL import Image
    rows = []
    for p in image_paths:
        try:
            with Image.open(p) as im:
                out = detector.predict_image(im, threshold=min_conf, imgsz=imgsz)
            rows.append({'image_name': p.name, 'max_conf': max([d['confidence'] for d in out['detections']], default=0.0),
                         'detections': [(d['class_code'], d['confidence']) for d in out['detections']],
                         'elapsed_ms': out['elapsed_ms']})
        except Exception as exc:
            rows.append({'image_name': p.name, 'max_conf': 0.0, 'detections': [], 'elapsed_ms': 0.0, 'error': str(exc)})
    return pd.DataFrame(rows)


def metrics_at(df, gt_col, threshold):
    """gt_col: 'Có' / 'Không' do người gán; bỏ qua dòng chưa gán."""
    d = df[df[gt_col].isin(['Có', 'Không'])]
    pred = d.detections.apply(lambda ds: any(c >= threshold for _, c in ds))
    truth = d[gt_col] == 'Có'
    tp, fp = int((pred & truth).sum()), int((pred & ~truth).sum())
    fn, tn = int((~pred & truth).sum()), int((~pred & ~truth).sum())
    prec = tp / (tp + fp) if tp + fp else None
    rec = tp / (tp + fn) if tp + fn else None
    f1 = 2 * prec * rec / (prec + rec) if prec and rec else None
    far = fp / (fp + tn) if fp + tn else None
    return {'threshold': threshold, 'n_labeled': len(d), 'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn,
            'precision': prec, 'recall': rec, 'F1': f1, 'false_alarm_rate': far,
            'miss_rate': (fn / (tp + fn)) if tp + fn else None}


def metrics_table(df, gt_col, thresholds=(0.15, 0.25, 0.40)):
    return pd.DataFrame([metrics_at(df, gt_col, t) for t in thresholds])
