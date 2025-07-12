#!/usr/bin/env python3
"""
CLI interface for RAG Query system.
"""

import argparse
import sys
import traceback
from pathlib import Path

from config import Config
from query import Query
from pipeline import RAGPipeline
from llm import LLMResponder
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from indexing.data_base import FaissDB
from logs import setup_logging


def setup_argparse() -> argparse.ArgumentParser:
    """Setup command line argument parser."""
    parser = argparse.ArgumentParser(
        description="RAG Query System - Ask questions and get answers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python run_query.py
  
  # Ask a single question
  python run_query.py --question "Когда был основан ЦСКА?"
  
  # Use custom config
  python run_query.py --config custom_config.yaml --question "Ваш вопрос"
  
  # Show system status
  python run_query.py --status
  
  # Verbose mode
  python run_query.py --verbose
        """
    )
    
    parser.add_argument(
        '--question', '-q',
        type=str,
        help='Question to ask'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        default='config.yaml',
        help='Configuration file path (default: config.yaml)'
    )
    
    parser.add_argument(
        '--status', '-s',
        action='store_true',
        help='Show system status and exit'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--k',
        type=int,
        help='Number of similar documents to retrieve (overrides config)'
    )
    
    return parser


def validate_input(args: argparse.Namespace) -> None:
    """Validate input arguments."""
    if args.config and not Path(args.config).exists():
        raise FileNotFoundError(f"Config file not found: {args.config}")


def show_status(config: Config, query_service: Query) -> None:
    """Show system status."""
    print("=== RAG Query System Status ===")
    print(f"Index path: {config.index_path}")
    print(f"Data path: {config.processed_data_path}")
    print(f"Embedding model: {config.emb_model_name}")
    print(f"LLM model: {config.llm}")
    print(f"Ollama host: {config.ollama_host}")
    print(f"Number of texts loaded: {len(query_service.texts) if query_service.texts else 0}")
    print(f"FAISS index vectors: {query_service.data_base.index.ntotal if query_service.data_base.index else 0}")
    print(f"Retrieval parameter k: {config.k}")


def interactive_mode(pipeline: RAGPipeline, logger) -> None:
    """Run interactive question-answering mode."""
    print("=== RAG Query System - Interactive Mode ===")
    print("Type 'quit' or 'exit' to stop")
    print("Type 'help' for available commands")
    print()
    
    while True:
        try:
            question = input("Задай вопрос: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("До свидания!")
                break
            elif question.lower() in ['help', 'h']:
                print("Доступные команды:")
                print("  help/h - показать эту справку")
                print("  quit/exit/q - выйти из программы")
                print("  <вопрос> - задать вопрос")
                continue
            elif not question:
                continue
            
            logger.info(f"Processing question: {question[:50]}...")
            
            result = pipeline.answer(question)
            
            print(f"\nОтвет: {result['answer']}")
            print(f"\nНайдено релевантных документов: {len(result['texts'])}")
            
            if result['texts']:
                print("\nРелевантные фрагменты:")
                for i, text in enumerate(result['texts'][:2], 1):  # Показываем только первые 2
                    print(f"{i}. {text[:200]}...")
            
            print("\n" + "="*50 + "\n")
            
        except KeyboardInterrupt:
            print("\n\nДо свидания!")
            break
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            print(f"Ошибка: {e}")


def main():
    """Main function."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    try:
        # Setup logging
        logger = setup_logging('./logs', 'QueryRunner', 
                             level='DEBUG' if args.verbose else 'INFO')
        
        logger.info("Starting RAG Query System")
        
        # Validate arguments
        validate_input(args)
        
        # Load configuration
        logger.info(f"Loading configuration from {args.config}")
        config = Config(args.config)
        
        # Override k parameter if provided
        if args.k:
            config.k = args.k
            logger.info(f"Overriding k parameter to {args.k}")
        
        # Initialize components
        logger.info("Initializing components...")
        data_base = FaissDB(config)
        query_service = Query(config, data_base)
        responder = LLMResponder(config)
        pipeline = RAGPipeline(config=config, query=query_service, responder=responder)
        
        # Show status if requested
        if args.status:
            show_status(config, query_service)
            return
        
        # Process single question or start interactive mode
        if args.question:
            logger.info(f"Processing question: {args.question}")
            result = pipeline.answer(args.question)
            
            print(f"Вопрос: {args.question}")
            print(f"Ответ: {result['answer']}")
            print(f"Найдено релевантных документов: {len(result['texts'])}")
            
        else:
            interactive_mode(pipeline, logger)
        
    except KeyboardInterrupt:
        print("\nПрограмма остановлена пользователем")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Ошибка: Файл не найден - {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Ошибка: Неверный аргумент - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        if args.verbose:
            print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main() 