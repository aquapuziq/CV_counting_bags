import cv2

def inside_roi(obj, roi):
    obj_center = (int((obj[0] + obj[2]) / 2), int((obj[1] + obj[3]) / 2))
    result = cv2.pointPolygonTest(roi, obj_center, measureDist = False)

    if result >= 0:
        return True

def draw_detection(frame, result, roi, threshold = 0.36):
    image = frame.copy()

    pred = result.pred_instances
    bboxes = pred.bboxes.detach().cpu().numpy()
    scores = pred.scores.detach().cpu().numpy()

    detections_sum = 0
    track_detections = []

    for bbox, score in zip(bboxes, scores):
        if score < threshold:
            continue

        if inside_roi(bbox, roi):
            track_detections.append({
                "bbox": bbox,
                "score": score
            })

        detections_sum += 1

        x1, y1, x2, y2 = bbox.astype(int)

        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = f"bag {score:.2f}"

        cv2.putText(image, label, (x1, max(y1 - 7, 20)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.putText(image, f"Detections: {detections_sum}",
        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    cv2.putText(image, f"Tracking candidates: {len(track_detections)}",
        (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    #cv2.line(image, counting_line[0],
     #   counting_line[1], (0, 255, 255), 2)

    return image, track_detections