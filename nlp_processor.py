import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import requests
from bs4 import BeautifulSoup
import os
import json

class NLPProcessor:
    def __init__(self):
        self.model_name = "microsoft/DialoGPT-small"  # Using smaller model for better compatibility
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
        self.conversation_history = []
        self.knowledge_base = {}
        self.load_knowledge_base()
        
    def load_knowledge_base(self):
        if os.path.exists('knowledge_base.json'):
            try:
                with open('knowledge_base.json', 'r') as f:
                    self.knowledge_base = json.load(f)
            except:
                self.knowledge_base = {}
                
    def save_knowledge_base(self):
        with open('knowledge_base.json', 'w') as f:
            json.dump(self.knowledge_base, f)
            
    def search_web(self, query):
        try:
            # Use DuckDuckGo for privacy-focused search
            search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(search_url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract search results
            results = []
            for result in soup.find_all('div', class_='result'):
                title = result.find('h2')
                snippet = result.find('a', class_='result__snippet')
                if title and snippet:
                    results.append({
                        'title': title.text.strip(),
                        'snippet': snippet.text.strip()
                    })
                    
            return results[:3]  # Return top 3 results
        except Exception as e:
            return []
            
    def generate_response(self, query, context=None):
        # Check if query is a system command
        if query.lower().startswith(('open', 'set reminder', 'what time', 'what date')):
            return None
            
        # Add query to conversation history
        self.conversation_history.append(query)
        
        # Check knowledge base first
        if query in self.knowledge_base:
            return self.knowledge_base[query]
            
        # Search web for information
        search_results = self.search_web(query)
        if search_results:
            # Store in knowledge base
            self.knowledge_base[query] = search_results[0]['snippet']
            self.save_knowledge_base()
            return search_results[0]['snippet']
            
        # Generate response using DialoGPT
        input_ids = self.tokenizer.encode(query + self.tokenizer.eos_token, return_tensors='pt')
        response_ids = self.model.generate(
            input_ids,
            max_length=1000,
            pad_token_id=self.tokenizer.eos_token_id,
            no_repeat_ngram_size=3,
            do_sample=True,
            top_k=100,
            top_p=0.7,
            temperature=0.8
        )
        
        response = self.tokenizer.decode(response_ids[:, input_ids.shape[-1]:][0], skip_special_tokens=True)
        
        # Store in knowledge base
        self.knowledge_base[query] = response
        self.save_knowledge_base()
        
        return response
        
    def clear_history(self):
        self.conversation_history = [] 