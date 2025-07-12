"""
Tests for query components.
"""

import pytest
import tempfile
import os
import json
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from config import Config
from query import Query
from pipeline import RAGPipeline
from llm import LLMResponder
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from indexing.data_base import FaissDB


class TestConfig:
    """Test configuration loading."""
    
    def test_config_loading(self):
        """Test basic config loading."""
        config = Config('config.yaml')
        assert hasattr(config, 'index_path')
        assert hasattr(config, 'emb_model_name')
        assert hasattr(config, 'llm')
        assert hasattr(config, 'k')
    
    def test_config_validation(self):
        """Test config validation with missing fields."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("data:\n  index_path: './test_index.index'\n")
            f.flush()
            
            with pytest.raises(ValueError, match="Missing required configuration section"):
                Config(f.name)
        
        os.unlink(f.name)


class TestLLMResponder:
    """Test LLM responder functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = Mock()
        self.config.llm = 'llama3'
        self.config.ollama_host = 'http://localhost:11434'
        self.config.prompt_template = 'Question: {question}\nContext: {context}\nAnswer:'
        self.config.logs_dir = './test_logs'
        
        with patch('llm.OllamaLLM'):
            with patch('llm.ChatPromptTemplate'):
                self.responder = LLMResponder(self.config)
    
    def test_generate_answer_valid_input(self):
        """Test answer generation with valid input."""
        # Mock the chain response
        self.responder.chain = Mock()
        self.responder.chain.invoke.return_value = "Test answer"
        
        question = "Test question"
        texts = ["Context text 1", "Context text 2"]
        
        result = self.responder.generate_answer(question, texts)
        
        assert result == "Test answer"
        self.responder.chain.invoke.assert_called_once()
    
    def test_generate_answer_invalid_question(self):
        """Test answer generation with invalid question."""
        with pytest.raises(ValueError, match="Question must be a non-empty string"):
            self.responder.generate_answer("", ["context"])
        
        with pytest.raises(ValueError, match="Question must be a non-empty string"):
            self.responder.generate_answer(None, ["context"])
    
    def test_generate_answer_invalid_texts(self):
        """Test answer generation with invalid texts."""
        with pytest.raises(ValueError, match="Texts must be a non-empty list"):
            self.responder.generate_answer("question", [])
        
        with pytest.raises(ValueError, match="Texts must be a non-empty list"):
            self.responder.generate_answer("question", None)


class TestRAGPipeline:
    """Test RAG pipeline functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = Mock()
        self.config.logs_dir = './test_logs'
        
        # Mock components
        self.query = Mock()
        self.responder = Mock()
        
        self.pipeline = RAGPipeline(self.config, self.query, self.responder)
    
    def test_answer_valid_question(self):
        """Test pipeline with valid question."""
        question = "Test question"
        mock_texts = ["Context 1", "Context 2"]
        mock_answer = "Test answer"
        
        self.query.query.return_value = mock_texts
        self.responder.generate_answer.return_value = mock_answer
        
        result = self.pipeline.answer(question)
        
        assert result['answer'] == mock_answer
        assert result['texts'] == mock_texts
        self.query.query.assert_called_once_with(question)
        self.responder.generate_answer.assert_called_once_with(question, mock_texts)
    
    def test_answer_invalid_question(self):
        """Test pipeline with invalid question."""
        with pytest.raises(ValueError, match="Question must be a non-empty string"):
            self.pipeline.answer("")
        
        with pytest.raises(ValueError, match="Question must be a non-empty string"):
            self.pipeline.answer(None)


class TestQuery:
    """Test query functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = Mock()
        self.config.index_path = './test_index.index'
        self.config.logs_dir = './test_logs'
        self.config.processed_data_path = './test_data.json'
        self.config.emb_model_name = 'test-model'
        self.config.k = 3
        
        self.data_base = Mock()
        self.data_base.index = Mock()
        self.data_base.index.ntotal = 2
        
        # Mock embedding model
        with patch('query.SentenceTransformer'):
            with patch('query.Path'):
                self.query = Query(self.config, self.data_base)
    
    def test_normalize_text(self):
        """Test text normalization."""
        # Test valid input
        result = self.query.normalize_text("  Test text  ")
        assert result == "Test text"
        
        # Test invalid input
        with pytest.raises(ValueError, match="Input text must be a string"):
            self.query.normalize_text(None)
    
    def test_query_valid_request(self):
        """Test query with valid request."""
        # Mock embedding model
        self.query.embedding_model = Mock()
        self.query.embedding_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        
        # Mock data base search
        self.query.data_base.search.return_value = [0, 1]
        
        # Mock texts
        self.query.texts = ["Text 1", "Text 2"]
        
        result = self.query.query("test question")
        
        assert result == ["Text 1", "Text 2"]
        self.query.embedding_model.encode.assert_called_once()
        self.query.data_base.search.assert_called_once()
    
    def test_query_invalid_request(self):
        """Test query with invalid request."""
        with pytest.raises(ValueError, match="Request must be a string"):
            self.query.query(None)


class TestFaissDB:
    """Test FAISS database functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config = Mock()
        self.config.index_path = './test_index.index'
        self.config.logs_dir = './test_logs'
        
        self.db = FaissDB(self.config)
    
    def test_search_without_index(self):
        """Test search without loaded index."""
        with pytest.raises(RuntimeError, match="Index is not loaded or created"):
            self.db.search(np.random.rand(1, 384))
    
    def test_search_with_index(self):
        """Test search with loaded index."""
        # Mock index
        self.db.index = Mock()
        self.db.index.search.return_value = (np.array([[0.1, 0.2]]), np.array([[0, 1]]))
        
        query_embedding = np.random.rand(1, 384).astype(np.float32)
        results = self.db.search(query_embedding)
        
        assert len(results) == 2
        assert results[0] == 0
        assert results[1] == 1


class TestIntegration:
    """Integration tests."""
    
    def test_end_to_end_workflow(self):
        """Test complete query workflow."""
        # This would be a more comprehensive test
        # For now, just test that components can be instantiated together
        config = Config('config.yaml')
        data_base = FaissDB(config)
        
        assert config is not None
        assert data_base is not None


if __name__ == "__main__":
    pytest.main([__file__]) 