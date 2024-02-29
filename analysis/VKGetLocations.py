from database.mongo_db import get_activities, get_user_by_id
from vk import VK
from natasha import (
    Segmenter,
    MorphVocab,
    
    NewsEmbedding,
    NewsMorphTagger,
    NewsSyntaxParser,
    NewsNERTagger,
    
    PER,
    LOC,
    NamesExtractor,
    DatesExtractor,
    MoneyExtractor,
    AddrExtractor,

    Doc
)

class VkGetLocations():
    def __init__(self, settings):
        self.vk = VK(settings)
        self.segmenter = Segmenter()
        self.morph_vocab = MorphVocab()
        emb = NewsEmbedding()
        self.morph_tagger = NewsMorphTagger(emb)
        self.syntax_parser = NewsSyntaxParser(emb)
        self.ner_tagger = NewsNERTagger(emb)

    def extract_secondary_locations(self, info):
        cities = []
        city_ids = []

        if "home_town" in info:
            city_ids.append(info.get("home_town"))

        if "occupation" in info:
            city_ids.append(info.get("occupation").get("city_id"))

        if "universities" in info:
            for university in info.get("universities"):
                city_ids.append(university.get("city"))
        if "schools" in info:
            for school in info["schools"]:
                city_ids.append(school["city"])

        # Convert to a set and then back to a list to get unique city_ids
        unique_city_ids = [c for c in list(set(city_ids)) if c is not None]
        if len(unique_city_ids) > 0:
            response = self.vk.get_cities_by_id(unique_city_ids)
            if not response.get("error"):
                for city in response["result"]:
                    cities.append(city.get("title"))

        return list(set(cities))
    
    def extract_locations_from_text(self, text):

        doc = Doc(text)
        doc.segment(self.segmenter)
        doc.tag_morph(self.morph_tagger)
        doc.parse_syntax(self.syntax_parser)
        doc.tag_ner(self.ner_tagger)

        cities = []
        for span in doc.spans:
            if span.type == LOC:
                span.normalize(self.morph_vocab)
                cities.append(span.normal)
        
        return list(set(cities))

    def execute(self, info, extra_info):
        user_db = get_user_by_id(info.get("id"))
        locations = user_db.get("locations") if user_db and user_db.get('locations') else {}
        
        city = info.get("city").get('title') if info.get('city') else None
        if city is not None:
            locations['city'] = city
        # try get city from friends
        if info.get('sex') == 1 and not user_db:
            # get secondary locaitons
            locations['secondary'] = self.extract_secondary_locations(info)

            # get locations from friends
            friends = self.vk.get_friends(info.get("id"))
            if not friends.get("error"):
                friends_cities = []
                friends_info = self.vk.get_users(friends.get("result"), ["city"])
                for friend_info in friends_info['result']:
                    if friend_info.get("city") is not None:
                        friend_city = friend_info.get("city").get("title")
                        friends_cities.append(friend_city)
                if len(friends_cities) > 0:
                    approximate_city = max(set(friends_cities), key=friends_cities.count)
                    locations['approximate'] = approximate_city
        # if user_db:
        #     locations["secondary"] = user_db.get("secondary")
        #     locations["approximate"] = user_db.get("approximate")

        # extract from activities
        activities = list(get_activities({"signer_id": int(info.get('id'))}))

        combined_strings = list(set([item.get('text') for item in activities if item.get('text') is not None] + [item.get('post_title') for item in activities if item.get('post_title') is not None]))
        combined_strings.append(extra_info)
        activity_all_text = str.join(" ", combined_strings)

        if not str.isspace(activity_all_text):
            locations['activity'] = self.extract_locations_from_text(activity_all_text)
        
        return locations