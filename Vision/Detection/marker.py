class Marker(DetectionBase):
    def __init__(self):
        super().__init__("Marker")
    
    def find_marker(self, image, color_ranges):
        """
        Find the marker by creating a mask based on the color range and analyzing contours.
        """
        lower_hsv, upper_hsv = color_ranges['Marker']
        mask = Preprocessing.preprocess(image, lower_hsv=lower_hsv, upper_hsv=upper_hsv)

        self.analyze_contours(image, mask)
        for obj in self.detected_objects:
            x, y, w, h = obj["position"]
            range_, bearing = self.calculate_range_and_bearing(x, y, w, h)
            obj["range"] = range_
            obj["bearing"] = bearing

        return self.detected_objects, self.draw_contours(image)
