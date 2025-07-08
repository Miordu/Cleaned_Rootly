import requests

class PlantImageFetcher:
    def __init__(self, trefle_key=None, plantid_key=None, perenual_key=None, plantnet_key=None):
        self.trefle_key = trefle_key
        self.plantid_key = plantid_key
        self.perenual_key = perenual_key
        self.plantnet_key = plantnet_key

    def get_image_from_perenual(self, query):
        r = requests.get(
            f"https://perenual.com/api/species-list",
            params={"key": self.perenual_key, "q": query},
            timeout=5
        )
        data = r.json()
        if data.get("data"):
            return data["data"][0].get("default_image", {}).get("original_url")

    def get_image_from_plantid(self, query):
        # Plant.id requires image-based search, usually via POST/upload.
        # Skip unless you're uploading images.
        return None

    def get_image_from_plantnet(self, query):
        # PlantNet is image-identification based; doesn't support search by name
        return None

    def get_best_image(self, query):
        # Priority: Perenual → fallback to others later if needed
        image = self.get_image_from_perenual(query)
        return image
