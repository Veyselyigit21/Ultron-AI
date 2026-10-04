import os
import json
import re

class MemoryVault:
    def __init__(self, vault_path=None):
        if not vault_path:
            self.vault_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "long_term_memory.json"))
        else:
            self.vault_path = vault_path
        self.memories = []
        self._load()

    def _load(self):
        if os.path.exists(self.vault_path):
            try:
                with open(self.vault_path, "r", encoding="utf-8") as f:
                    self.memories = json.load(f)
            except: pass

    def _save(self):
        try:
            with open(self.vault_path, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, ensure_ascii=False, indent=2)
        except: pass

    def archive(self, text):
        if not text or len(text) < 5: return
        self.memories.append(text)
        if len(self.memories) > 1000:
            self.memories = self.memories[-1000:]
        self._save()
        
    def _get_words(self, text):
        return set(re.findall(r'\w+', text.lower()))

    def search(self, query, top_k=2):
        if not self.memories or not query:
            return []
        
        query_words = self._get_words(query)
        if not query_words:
            return []
            
        scored = []
        for memory in self.memories:
            mem_words = self._get_words(memory)
            if not mem_words: continue
            
            # Basit Jaccard Benzerliği (Ortak Kelimeler / Toplam Kelimeler)
            intersection = query_words.intersection(mem_words)
            union = query_words.union(mem_words)
            score = len(intersection) / len(union)
            
            if score > 0.1:  # En az %10 benzerlik
                scored.append((score, memory))
                
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m[1] for m in scored[:top_k]]
