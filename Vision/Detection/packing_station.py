class Marker:
    @staticmethod
    def classify_marker(obj, detected_objects):
        circularity = obj['circularity']
        aspect_ratio = obj['aspect_ratio']

        if circularity > 0.8:
            circle_count = sum(1 for o in detected_objects if o['circularity'] > 0.8)
            if circle_count == 1:
                return "Row Marker 1"
            elif circle_count == 2:
                return "Row Marker 2"
            elif circle_count == 3:
                return "Row Marker 3"
        elif 0.9 < aspect_ratio < 1.1:
            return "Packing Station Marker"

        return "Unknown Marker"
