"""
Chatbot Agent with RAG (Retrieval Augmented Generation)
Uses Pinecone vector database for semantic search and LLM for response generation
"""

import os
from openai import OpenAI
from typing import List, Dict, Optional
import hashlib
import json

# Pinecone import - try new API first, fallback to old
try:
    from pinecone import Pinecone
    PINECONE_NEW_API = True
except ImportError:
    try:
        import pinecone
        PINECONE_NEW_API = False
    except ImportError:
        raise ImportError("pinecone-client not installed. Run: pip install pinecone-client")

class ChatbotAgent:
    def __init__(self, index_name: str = "customer-service-kb"):
        self.index_name = index_name
        """
        Initialize the chatbot agent with Pinecone vector database and LLM
        
        Args:
            index_name: Name of the Pinecone index to use
        """
        # Check for problematic environment variables that might cause issues
        problematic_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
        saved_proxies = {}
        for var in problematic_env_vars:
            if var in os.environ:
                saved_proxies[var] = os.environ[var]
                del os.environ[var]
        
        try:
            # Initialize OpenAI client
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            try:
                self.client = OpenAI(api_key=api_key)
            except Exception as e:
                if 'proxies' in str(e).lower():
                    print(f"Warning: OpenAI initialization issue (possibly proxies): {e}")
                    try:
                        import httpx
                        http_client = httpx.Client()
                        self.client = OpenAI(api_key=api_key, http_client=http_client)
                        print("OpenAI client initialized with explicit httpx client")
                    except Exception as e3:
                        raise RuntimeError(f"OpenAI client initialization failed: {e3}")
                else:
                    raise
            
            # Initialize Pinecone (newer API - serverless, no environment needed)
            pinecone_api_key = os.getenv('PINECONE_API_KEY')
            
            if not pinecone_api_key:
                raise ValueError("PINECONE_API_KEY environment variable not set. Get it from https://app.pinecone.io")
            
            # Initialize Pinecone based on available API
            if PINECONE_NEW_API:
                # New serverless API
                try:
                    self.pinecone_client = Pinecone(api_key=pinecone_api_key)
                    print("Pinecone initialized (serverless API)")
                except Exception as e:
                    raise RuntimeError(f"Failed to initialize Pinecone: {e}. Please check PINECONE_API_KEY")
            else:
                # Old API (fallback)
                try:
                    pinecone_env = os.getenv('PINECONE_ENVIRONMENT', 'us-east1-gcp')
                    pinecone.init(api_key=pinecone_api_key, environment=pinecone_env)
                    print(f"Pinecone initialized with old API (environment: {pinecone_env})")
                    self.pinecone_client = None  # Mark as old API
                except Exception as e:
                    raise RuntimeError(f"Failed to initialize Pinecone: {e}. Please check PINECONE_API_KEY and PINECONE_ENVIRONMENT")
            
            # Get or create index
            try:
                if PINECONE_NEW_API and self.pinecone_client:
                    # New serverless API
                    # Check if index exists
                    existing_indexes = [idx.name for idx in self.pinecone_client.list_indexes()]
                    if index_name in existing_indexes:
                        self.index = self.pinecone_client.Index(index_name)
                        print(f"Connected to existing Pinecone index: {index_name}")
                    else:
                        # Index should already exist (created manually)
                        # Try to connect anyway - might be a timing issue
                        try:
                            self.index = self.pinecone_client.Index(index_name)
                            print(f"Connected to Pinecone index: {index_name}")
                        except Exception as e:
                            raise RuntimeError(
                                f"Index '{index_name}' not found. Please create it in Pinecone dashboard first:\n"
                                f"  - Name: {index_name}\n"
                                f"  - Dimensions: 1536\n"
                                f"  - Metric: cosine\n"
                                f"  - Capacity: Serverless\n"
                                f"Original error: {e}"
                            )
                else:
                    # Old API (fallback)
                    if index_name not in pinecone.list_indexes():
                        raise RuntimeError(
                            f"Index '{index_name}' not found. Please create it in Pinecone dashboard first:\n"
                            f"  - Name: {index_name}\n"
                            f"  - Dimensions: 1536\n"
                            f"  - Metric: cosine"
                        )
                    self.index = pinecone.Index(index_name)
                    print(f"Connected to Pinecone index: {index_name} (old API)")
            except RuntimeError:
                raise  # Re-raise our custom errors
            except Exception as e:
                raise RuntimeError(f"Failed to connect to Pinecone index: {e}. Make sure index '{index_name}' exists in Pinecone dashboard.")
                
        finally:
            # Restore proxy environment variables
            for var, value in saved_proxies.items():
                os.environ[var] = value
        
        # Model configuration
        self.embedding_model = "text-embedding-ada-002"
        self.llm_model = "gpt-4-turbo-preview"  # Can use gpt-3.5-turbo for cost savings
        
        # RAG configuration
        self.max_context_chunks = 3
        self.max_response_length = 500  # Characters
        
    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a text string"""
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding
    
    def _retrieve_relevant_context(self, query: str, n_results: int = None, audience: str = None) -> List[Dict]:
        """
        Retrieve relevant context from the knowledge base
        
        Args:
            query: User's question
            n_results: Number of results to retrieve (defaults to max_context_chunks)
            audience: Filter by audience ('sales_reps', 'customers', 'internal', or None for all)
            
        Returns:
            List of relevant document chunks with metadata
        """
        if n_results is None:
            n_results = self.max_context_chunks
            
        # Generate query embedding
        query_embedding = self._get_embedding(query)
        
        # Query Pinecone
        try:
            results = self.index.query(
                vector=query_embedding,
                top_k=n_results * 3 if audience else n_results,  # Get more if filtering needed
                include_metadata=True
            )
        except Exception as e:
            print(f"Error querying Pinecone: {e}")
            return []
        
        # Format results and filter by audience if needed
        context_chunks = []
        for match in results.matches:
            metadata = match.metadata or {}
            
            # Filter by audience if specified
            if audience and metadata.get('audience') != audience:
                continue
            
            # Get document text from metadata (Pinecone stores it in metadata)
            text = metadata.get('text', '')
            if not text:
                # Fallback: try to fetch by ID if text not in metadata
                try:
                    fetch_result = self.index.fetch(ids=[match.id])
                    if fetch_result.vectors and match.id in fetch_result.vectors:
                        text = fetch_result.vectors[match.id].metadata.get('text', '')
                except:
                    pass
            
            chunk = {
                'id': match.id,
                'text': text,
                'metadata': metadata,
                'distance': match.score if hasattr(match, 'score') else None
            }
            context_chunks.append(chunk)
            
            if len(context_chunks) >= n_results:
                break
        
        return context_chunks
    
    def search_by_metadata(self, 
                          subject: str = None,
                          from_email: str = None,
                          to_email: str = None,
                          filename: str = None,
                          audience: str = None,
                          max_results: int = 10) -> List[Dict]:
        """
        Search for documents by metadata (subject, from, to, filename, audience)
        
        Note: Pinecone free tier doesn't support metadata filtering in queries.
        This method fetches a sample and filters in Python.
        
        Args:
            subject: Email subject to search for (partial match)
            from_email: Sender email to search for (partial match)
            to_email: Recipient email to search for (partial match)
            filename: Filename to search for (partial match)
            audience: Filter by audience ('sales_reps', 'customers', 'internal', or None for all)
            max_results: Maximum number of results to return
            
        Returns:
            List of matching documents with metadata
        """
        # Pinecone doesn't support metadata filtering in free tier
        # We'll need to fetch a sample and filter in Python
        # For better performance, use a dummy query to get results
        try:
            # Use a generic query to get documents
            dummy_embedding = self._get_embedding("customer service email")
            results = self.index.query(
                vector=dummy_embedding,
                top_k=min(max_results * 10, 1000),  # Get more to filter
                include_metadata=True
            )
            
            documents = []
            for match in results.matches:
                metadata = match.metadata or {}
                
                # Apply filters
                match_filter = True
                if subject and subject.lower() not in metadata.get('subject', '').lower():
                    match_filter = False
                if from_email and from_email.lower() not in metadata.get('from', '').lower():
                    match_filter = False
                if to_email and to_email.lower() not in metadata.get('to', '').lower():
                    match_filter = False
                if filename and filename.lower() not in metadata.get('file', '').lower():
                    match_filter = False
                if audience and metadata.get('audience') != audience:
                    match_filter = False
                
                if match_filter:
                    text = metadata.get('text', '')
                    doc = {
                        'id': match.id,
                        'text': text,
                        'metadata': metadata,
                    }
                    documents.append(doc)
                    if len(documents) >= max_results:
                        break
            
            return documents
        except Exception as e:
            print(f"Error searching by metadata: {e}")
            return []
    
    def search_by_text(self, search_text: str, max_results: int = 10) -> List[Dict]:
        """
        Search for documents by text content using semantic search
        
        Args:
            search_text: Text to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of matching documents with metadata and relevance scores
        """
        try:
            # Generate embedding for search text
            query_embedding = self._get_embedding(search_text)
            
            # Query Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=max_results,
                include_metadata=True
            )
            
            # Format results
            documents = []
            for match in results.matches:
                metadata = match.metadata or {}
                text = metadata.get('text', '')
                doc = {
                    'id': match.id,
                    'text': text,
                    'metadata': metadata,
                    'distance': match.score if hasattr(match, 'score') else None,
                    'relevance_score': match.score if hasattr(match, 'score') else None
                }
                documents.append(doc)
            
            return documents
        except Exception as e:
            print(f"Error searching by text: {e}")
            return []
    
    def analyze_frequently_asked_questions(self, max_questions: int = 20, sample_size: int = 100) -> List[Dict]:
        """
        Analyze the knowledge base to extract and rank frequently asked questions
        
        Args:
            max_questions: Maximum number of FAQs to return
            sample_size: Number of documents to analyze (for performance)
            
        Returns:
            List of dictionaries with 'question', 'frequency', and 'examples'
        """
        try:
            # Get a sample of documents from Pinecone
            # Use a dummy query to get documents
            dummy_embedding = self._get_embedding("customer question")
            results = self.index.query(
                vector=dummy_embedding,
                top_k=min(sample_size, 100),
                include_metadata=True
            )
            
            if not results.matches:
                return []
            
            # Extract text content from documents
            documents_text = []
            for match in results.matches:
                metadata = match.metadata or {}
                text = metadata.get('text', '')
                if text:
                    documents_text.append(text)
            
            if not documents_text:
                return []
            
            # Combine documents for analysis (limit total text to avoid token limits)
            combined_text = "\n\n---\n\n".join(documents_text[:50])  # Limit to 50 docs
            
            # Use LLM to extract questions
            system_prompt = """You are analyzing customer service emails to identify frequently asked questions.
Your task is to:
1. Extract actual questions that customers are asking
2. Group similar questions together
3. Count how many times each type of question appears
4. Return the most common questions

Focus on:
- Direct questions from customers (e.g., "How do I...", "Why can't I...", "What is...")
- Problems customers are reporting (e.g., "I can't...", "My X is not working...")
- Requests for help (e.g., "Can you help me with...", "I need help with...")

Return a JSON array of objects, each with:
- "question": A clear, concise version of the question
- "frequency": How many times this question appears (as a number)
- "variations": Array of example variations of this question

Example format:
[
  {
    "question": "How do I add my card information?",
    "frequency": 5,
    "variations": ["I can't seem to get my card info", "How do I add payment?", "Can't add card"]
  }
]"""

            # Limit text length to avoid token limits
            limited_text = combined_text[:8000]
            
            user_prompt = f"""Analyze the following customer service emails and extract the most frequently asked questions:

{limited_text}

Return ONLY valid JSON array, no other text."""

            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse JSON response
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from response
            try:
                faqs = json.loads(response_text)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    faqs = json.loads(json_match.group())
                else:
                    faqs = self._extract_questions_simple(documents_text)
            
            # Sort by frequency and limit results
            if isinstance(faqs, list):
                faqs.sort(key=lambda x: x.get('frequency', 0), reverse=True)
                return faqs[:max_questions]
            else:
                return []
                
        except Exception as e:
            print(f"Error analyzing FAQs: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_questions_simple(self, documents: List[str]) -> List[Dict]:
        """Simple fallback method to extract questions using pattern matching"""
        import re
        from collections import Counter
        
        question_patterns = [
            r'(?:how|what|why|when|where|can|could|would|will|do|does|did|is|are|was|were)\s+[^?.!]+[?]',
            r'I\s+(?:can\'?t|cannot|need|want|would like|am trying|am having trouble)\s+[^?.!]+[?.!]',
            r'(?:help|assist|support).*[?]',
        ]
        
        all_questions = []
        for doc in documents:
            for pattern in question_patterns:
                matches = re.findall(pattern, doc, re.IGNORECASE)
                all_questions.extend([m.strip() for m in matches if len(m.strip()) > 10])
        
        # Count and group similar questions
        question_counter = Counter(all_questions)
        
        # Group similar questions
        faqs = []
        seen_questions = set()
        
        for question, count in question_counter.most_common(20):
            question_lower = question.lower()
            is_duplicate = False
            for seen in seen_questions:
                if question_lower in seen.lower() or seen.lower() in question_lower:
                    is_duplicate = True
                    break
            
            if not is_duplicate and count > 0:
                faqs.append({
                    'question': question[:200],
                    'frequency': count,
                    'variations': [question]
                })
                seen_questions.add(question_lower)
        
        return faqs
    
    def _generate_response(self, query: str, context_chunks: List[Dict], conversation_history: List[Dict] = None) -> str:
        """
        Generate a response using LLM with retrieved context and conversation history
        
        Args:
            query: User's question
            context_chunks: Retrieved relevant context from knowledge base
            conversation_history: Previous conversation messages (optional)
            
        Returns:
            Generated response string
        """
        # Build context from retrieved chunks with source information
        context_text = ""
        sources = []
        if context_chunks:
            context_parts = []
            for i, chunk in enumerate(context_chunks):
                metadata = chunk.get('metadata', {})
                source_info = {
                    'source': metadata.get('source', 'Unknown'),
                    'subject': metadata.get('subject', 'N/A'),
                    'from': metadata.get('from', 'N/A'),
                    'date': metadata.get('date', 'N/A'),
                    'file': metadata.get('file', 'N/A')
                }
                sources.append(source_info)
                context_parts.append(
                    f"Context {i+1}:\n{chunk['text']}\n"
                    f"(Source: {source_info['source']}, Subject: {source_info['subject']}, "
                    f"From: {source_info['from']}, Date: {source_info['date']})"
                )
            context_text = "\n\n---\n\n".join(context_parts)
        
        # Create system prompt
        system_prompt = """You are a helpful customer service assistant. Your role is to answer questions 
based on the provided context from past customer service interactions (emails and text messages).

Guidelines:
- Answer questions based ONLY on the provided context
- If the context doesn't contain enough information, politely say so
- Be concise and clear (under 500 characters when possible)
- Use a friendly, professional tone
- If asked about something not in the context, acknowledge it and suggest contacting support directly
- When asked "how do you know this?" or similar follow-up questions, explain which email or message you found this information in
- Reference specific details from the context when explaining your answer
- Focus on being helpful and accurate"""
        
        # Build conversation history messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history[-6:]:  # Include last 3 exchanges (6 messages)
                messages.append({
                    "role": msg.get('role', 'user'),
                    "content": msg.get('content', '')
                })
        
        # Build user prompt with context
        if context_text:
            user_prompt = f"""Based on the following context from past customer service interactions, please answer this question:

Question: {query}

Context:
{context_text}

Please provide a helpful, concise answer based on the context above. If asked how you know something, reference the specific email or message from the context."""
        else:
            user_prompt = f"""A customer is asking: {query}

Unfortunately, I don't have relevant context in the knowledge base to answer this question accurately. 
Please provide a polite response suggesting they contact support directly or rephrase their question."""
        
        messages.append({"role": "user", "content": user_prompt})
        
        # Generate response
        response = self.client.chat.completions.create(
            model=self.llm_model,
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        
        return response.choices[0].message.content.strip()
    
    def get_response(self, query: str, conversation_history: List[Dict] = None) -> str:
        """
        Main method to get a response for a user query
        
        Args:
            query: User's question
            conversation_history: Previous conversation messages (optional)
            
        Returns:
            Generated response string
        """
        # Check if user is asking about FAQs/top questions
        query_lower = query.lower()
        faq_keywords = ['top', 'most frequent', 'frequently asked', 'common questions', 'faq', 
                       'what questions', 'what are the questions', 'most common']
        
        is_faq_query = any(keyword in query_lower for keyword in faq_keywords)
        
        # Try to extract number (e.g., "top 5", "top 10")
        import re
        number_match = re.search(r'\d+', query)
        num_questions = int(number_match.group()) if number_match else 10
        
        if is_faq_query:
            # Get FAQs
            faqs = self.analyze_frequently_asked_questions(
                max_questions=min(num_questions, 20),
                sample_size=200
            )
            
            if faqs:
                # Format FAQs as a response
                response_parts = [f"Here are the top {len(faqs)} most frequently asked questions:\n\n"]
                
                for i, faq in enumerate(faqs, 1):
                    question = faq.get('question', 'Unknown')
                    frequency = faq.get('frequency', 0)
                    response_parts.append(f"{i}. {question} (asked {frequency} time{'s' if frequency != 1 else ''})")
                
                response = "\n".join(response_parts)
                
                # Truncate if too long
                if len(response) > self.max_response_length:
                    response = response[:self.max_response_length].rsplit('\n', 1)[0] + "\n..."
                
                return response
            else:
                return "I couldn't find any frequently asked questions in the knowledge base. Make sure emails have been processed first."
        
        # Regular query processing
        context_chunks = self._retrieve_relevant_context(query)
        
        # Generate response with conversation history
        response = self._generate_response(query, context_chunks, conversation_history)
        
        # Truncate if too long
        if len(response) > self.max_response_length:
            response = response[:self.max_response_length].rsplit('.', 1)[0] + "..."
        
        return response
    
    def get_response_with_sources(self, query: str, conversation_history: List[Dict] = None, audience: str = None) -> tuple:
        """
        Get response with source information
        
        Args:
            query: User's question
            conversation_history: Previous conversation messages (optional)
            audience: Filter by audience ('sales_reps', 'customers', 'internal', or None for all)
            
        Returns:
            Tuple of (response_string, sources_list)
        """
        # Check if user is asking about FAQs/top questions
        query_lower = query.lower()
        faq_keywords = ['top', 'most frequent', 'frequently asked', 'common questions', 'faq', 
                       'what questions', 'what are the questions', 'most common']
        
        is_faq_query = any(keyword in query_lower for keyword in faq_keywords)
        
        if is_faq_query:
            response = self.get_response(query, conversation_history)
            return response, []
        
        # Regular query processing
        context_chunks = self._retrieve_relevant_context(query, audience=audience)
        
        # Extract sources
        sources = []
        for chunk in context_chunks:
            metadata = chunk.get('metadata', {})
            sources.append({
                'source': metadata.get('source', 'Unknown'),
                'subject': metadata.get('subject', 'N/A'),
                'from': metadata.get('from', 'N/A'),
                'date': metadata.get('date', 'N/A'),
                'file': metadata.get('file', 'N/A')
            })
        
        # Generate response with conversation history
        response = self._generate_response(query, context_chunks, conversation_history)
        
        # Truncate if too long
        if len(response) > self.max_response_length:
            response = response[:self.max_response_length].rsplit('.', 1)[0] + "..."
        
        return response, sources
    
    def add_document(self, text: str, metadata: Dict = None, doc_id: str = None):
        """
        Add a document to the knowledge base
        
        Args:
            text: Text content to add
            metadata: Optional metadata (e.g., {'source': 'email', 'date': '2024-01-01'})
            doc_id: Optional document ID (auto-generated if not provided)
        """
        if metadata is None:
            metadata = {}
        
        # Generate ID if not provided
        if doc_id is None:
            doc_id = hashlib.md5(text.encode()).hexdigest()
        
        # Generate embedding
        embedding = self._get_embedding(text)
        
        # Store text in metadata (Pinecone stores metadata, not separate documents)
        metadata_with_text = metadata.copy()
        metadata_with_text['text'] = text
        
        # Add to Pinecone index
        try:
            self.index.upsert(
                vectors=[{
                    'id': doc_id,
                    'values': embedding,
                    'metadata': metadata_with_text
                }]
            )
            print(f"Added document {doc_id} to Pinecone index")
        except Exception as e:
            print(f"Error adding document to Pinecone: {e}")
            raise
