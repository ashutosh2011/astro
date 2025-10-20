"""Topic classifier using LLM."""

import json
from typing import Dict, Any
from app.services.llm.openai_client import openai_client
from app.utils.errors import LLMError


class TopicClassifier:
    """LLM-based topic classifier."""
    
    def __init__(self):
        """Initialize topic classifier."""
        # Expanded topic list to cover more common user intents
        self.topics = [
            "career",
            "marriage",
            "health",
            "travel",
            "education",
            "finance",
            "property",
            "litigation",
            "spirituality",
            "family",
            "children",
            "general",
        ]
    
    async def classify_question(self, question: str) -> str:
        """Classify question into topic categories."""
        try:
            system_prompt = """You are a topic classifier for Vedic astrology questions.
            Classify the user's question into one of these categories:
            - career: job, profession, business, career growth, promotions, work
            - marriage: marriage, relationships, love, partnership, spouse, romance
            - health: health, wellness, medical, physical/mental well-being
            - travel: travel, relocation, foreign lands, journeys, immigration
            - education: study, exams, degrees, learning, college, school
            - finance: money, income, wealth, investments, savings, debt
            - property: house, land, real estate, buying/selling property, vehicles
            - litigation: legal issues, court cases, disputes, contracts
            - spirituality: spiritual growth, practices, mindfulness, purpose
            - family: parents, home life, domestic matters, harmony at home
            - children: childbirth, pregnancy, children, parenting
            - general: any other question that doesn't fit the above categories

            Return only a JSON object with the topic field."""
            
            user_prompt = f"Classify this question: {question}"
            
            messages = openai_client.create_messages(system_prompt, user_prompt)
            result = await openai_client.generate_response(messages, purpose="topic-classifier")
            
            topic = result.get("topic", "general").lower()
            
            # Validate topic
            if topic not in self.topics:
                topic = "general"
            
            return topic
            
        except Exception as e:
            # Fallback to general if classification fails
            return "general"
    
    def get_topic_keywords(self, topic: str) -> list:
        """Get keywords for a topic."""
        keyword_map = {
            "career": ["job", "work", "career", "profession", "business", "promotion", "office", "employment"],
            "marriage": ["marriage", "wedding", "relationship", "love", "partner", "spouse", "romance"],
            "health": ["health", "illness", "disease", "medical", "doctor", "hospital", "wellness", "fitness"],
            "travel": ["travel", "journey", "trip", "foreign", "abroad", "relocation", "migration", "immigration", "visa"],
            "education": ["study", "exam", "exams", "degree", "college", "school", "learn", "learning"],
            "finance": ["money", "income", "wealth", "invest", "investment", "savings", "debt", "loan"],
            "property": ["house", "home", "land", "real estate", "property", "vehicle", "car", "buy", "sell"],
            "litigation": ["legal", "court", "case", "lawsuit", "contract", "dispute"],
            "spirituality": ["spiritual", "meditation", "mindfulness", "purpose", "karma", "dharma"],
            "family": ["parents", "mother", "father", "home life", "domestic", "family"],
            "children": ["child", "children", "pregnancy", "birth", "parenting"],
            "general": [],
        }
        return keyword_map.get(topic, [])
    
    def is_topic_relevant(self, question: str, topic: str) -> bool:
        """Check if question is relevant to topic."""
        keywords = self.get_topic_keywords(topic)
        question_lower = question.lower()
        
        return any(keyword in question_lower for keyword in keywords)


# Global topic classifier instance
topic_classifier = TopicClassifier()

