"""
Chatbot Agent with RAG (Retrieval Augmented Generation)
Uses vector database for semantic search and LLM for response generation
"""

import os
import chromadb
from openai import OpenAI
from typing import List, Dict
import hashlib

class ChatbotAgent:
    def __init__(self, collection_name: str = "customer_service_kb"):
        """
        Initialize the chatbot agent with vector database and LLM
        
        Args:
            collection_name: Name of the ChromaDB collection to use
        """
        # Check for problematic environment variables that might cause issues
        # Some libraries don't accept 'proxies' parameter in certain versions
        problematic_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
        saved_proxies = {}
        for var in problematic_env_vars:
            if var in os.environ:
                saved_proxies[var] = os.environ[var]
                # Temporarily remove to avoid conflicts
                del os.environ[var]
        
        try:
            # Initialize OpenAI client
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            # Initialize OpenAI client
            # Explicitly disable proxies to avoid version compatibility issues
            try:
                # Try with explicit api_key and no proxies
                self.client = OpenAI(api_key=api_key)
            except Exception as e:
                # If that fails, try with environment variable but explicitly disable proxies
                if 'proxies' in str(e).lower():
                    print(f"Warning: OpenAI initialization issue (possibly proxies): {e}")
                    # Try to initialize with explicit http_client that doesn't use proxies
                    # The issue is that OpenAI/httpx may be trying to pass 'proxies' parameter
                    # to something that doesn't accept it. Let's try multiple approaches.
                    try:
                        import httpx
                        # Approach 1: Create httpx client without any parameters
                        # (proxy env vars are already removed, so it won't use proxies)
                        http_client = httpx.Client()
                        self.client = OpenAI(api_key=api_key, http_client=http_client)
                        print("OpenAI client initialized with explicit httpx client")
                    except Exception as e3:
                        # Approach 2: Try using requests instead of httpx
                        try:
                            import requests
                            # Create a requests session without proxies
                            session = requests.Session()
                            # Explicitly set proxies to None/empty to override any env vars
                            session.proxies = {}
                            # OpenAI might accept a requests session via http_client
                            # But OpenAI 1.3.7 uses httpx, so this might not work
                            # Let's try the environment variable approach instead
                            raise Exception("Trying env var approach")
                        except Exception:
                            # Approach 3: Use environment variable (proxies already removed)
                            original_key = os.environ.get('OPENAI_API_KEY')
                            os.environ['OPENAI_API_KEY'] = api_key
                            try:
                                # Initialize without any parameters
                                # Proxy env vars are removed, so it should work
                                self.client = OpenAI()
                                print("OpenAI client initialized via environment variable")
                            except Exception as e4:
                                if 'proxies' in str(e4).lower():
                                    # Last resort: provide clear upgrade instructions
                                    raise RuntimeError(
                                        f"OpenAI client initialization failed due to proxies/version compatibility issue.\n\n"
                                        f"SOLUTION: Please upgrade your libraries:\n"
                                        f"  pip install --upgrade 'openai>=1.12.0' 'httpx>=0.27.0'\n\n"
                                        f"Or if you have proxy environment variables set, temporarily unset them:\n"
                                        f"  unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy\n\n"
                                        f"Original error: {e4}"
                                    )
                                raise
                            if original_key:
                                os.environ['OPENAI_API_KEY'] = original_key
                else:
                    # Re-raise if it's not a proxies error
                    raise
            
            # Initialize ChromaDB with persistence (while proxies are still removed)
            # Avoid using Settings() as it may have compatibility issues with 'proxies' parameter
            chroma_initialized = False
            last_error = None
            
            # Method 1: Try PersistentClient (newer API, recommended, avoids Settings entirely)
            if not chroma_initialized:
                try:
                    # Use Railway's persistent data directory if available, otherwise use local
                    # Railway provides /data directory for persistent storage
                    chroma_db_path = os.getenv('RAILWAY_VOLUME_MOUNT_PATH', 
                                             os.getenv('DATA_DIR', './chroma_db'))
                    if not os.path.exists(chroma_db_path):
                        os.makedirs(chroma_db_path, exist_ok=True)
                    self.chroma_client = chromadb.PersistentClient(path=chroma_db_path)
                    chroma_initialized = True
                    print(f"ChromaDB initialized with PersistentClient at {chroma_db_path}")
                except Exception as e:
                    last_error = e
                    print(f"PersistentClient failed: {e}")
            
            # Method 2: Try Client() without any parameters (in-memory, no persistence)
            if not chroma_initialized:
                try:
                    self.chroma_client = chromadb.Client()
                    chroma_initialized = True
                    print("ChromaDB initialized with Client() (in-memory mode)")
                except Exception as e:
                    last_error = e
                    print(f"Client() failed: {e}")
            
            if not chroma_initialized:
                raise RuntimeError(f"Failed to initialize ChromaDB. Last error: {last_error}. "
                                 f"Please ensure ChromaDB is properly installed: pip install chromadb")
        finally:
            # Restore proxy environment variables after all initialization is complete
            for var, value in saved_proxies.items():
                os.environ[var] = value
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection(name=collection_name)
            print(f"Loaded existing collection: {collection_name}")
        except:
            self.collection = self.chroma_client.create_collection(name=collection_name)
            print(f"Created new collection: {collection_name}")
        
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
        
        # Build where clause for audience filtering
        where_clause = None
        if audience:
            where_clause = {'audience': audience}
        
        # Search the collection
        query_kwargs = {
            'query_embeddings': [query_embedding],
            'n_results': n_results
        }
        if where_clause:
            query_kwargs['where'] = where_clause
        
        results = self.collection.query(**query_kwargs)
        
        # Format results
        context_chunks = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                chunk = {
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else None
                }
                context_chunks.append(chunk)
        
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
        # Build metadata filter
        where_clause = {}
        
        if subject:
            # ChromaDB uses $contains for partial string matching
            where_clause['subject'] = {'$contains': subject}
        if from_email:
            where_clause['from'] = {'$contains': from_email}
        if to_email:
            where_clause['to'] = {'$contains': to_email}
        if filename:
            where_clause['file'] = {'$contains': filename}
        if audience:
            where_clause['audience'] = audience
        
        try:
            if where_clause:
                # Search with metadata filter
                results = self.collection.get(
                    where=where_clause,
                    limit=max_results
                )
            else:
                # If no filters, get all documents (limited)
                results = self.collection.get(limit=max_results)
            
            # Format results
            documents = []
            if results['ids'] and len(results['ids']) > 0:
                for i in range(len(results['ids'])):
                    doc = {
                        'id': results['ids'][i],
                        'text': results['documents'][i] if results['documents'] else '',
                        'metadata': results['metadatas'][i] if results['metadatas'] else {},
                    }
                    documents.append(doc)
            
            return documents
        except Exception as e:
            print(f"Error searching by metadata: {e}")
            # Fallback: get all and filter in Python
            try:
                all_results = self.collection.get(limit=1000)  # Get more to filter
                documents = []
                if all_results['ids'] and len(all_results['ids']) > 0:
                    for i in range(len(all_results['ids'])):
                        metadata = all_results['metadatas'][i] if all_results['metadatas'] else {}
                        
                        # Apply filters
                        match = True
                        if subject and subject.lower() not in metadata.get('subject', '').lower():
                            match = False
                        if from_email and from_email.lower() not in metadata.get('from', '').lower():
                            match = False
                        if to_email and to_email.lower() not in metadata.get('to', '').lower():
                            match = False
                        if filename and filename.lower() not in metadata.get('file', '').lower():
                            match = False
                        
                        if match:
                            doc = {
                                'id': all_results['ids'][i],
                                'text': all_results['documents'][i] if all_results['documents'] else '',
                                'metadata': metadata,
                            }
                            documents.append(doc)
                            if len(documents) >= max_results:
                                break
                
                return documents
            except Exception as e2:
                print(f"Error in fallback search: {e2}")
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
            
            # Search the collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results
            )
            
            # Format results
            documents = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    doc = {
                        'id': results['ids'][0][i],
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None,
                        'relevance_score': 1.0 - (results['distances'][0][i] if results['distances'] else 1.0)
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
            # Get a sample of documents from the knowledge base
            all_docs = self.collection.get(limit=sample_size)
            
            if not all_docs or not all_docs.get('documents'):
                return []
            
            # Extract text content from documents
            documents_text = []
            for i, doc_text in enumerate(all_docs['documents']):
                metadata = all_docs['metadatas'][i] if all_docs.get('metadatas') else {}
                # Focus on customer questions (usually in the body or from customer emails)
                documents_text.append(doc_text)
            
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
                temperature=0.3,  # Lower temperature for more consistent extraction
                max_tokens=2000
            )
            
            # Parse JSON response
            import json
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from response (in case LLM adds extra text)
            try:
                # Try parsing directly
                faqs = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks or other formatting
                import re
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    faqs = json.loads(json_match.group())
                else:
                    # Fallback: simple pattern matching
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
            # Fallback to simple extraction
            try:
                all_docs = self.collection.get(limit=sample_size)
                if all_docs and all_docs.get('documents'):
                    return self._extract_questions_simple(all_docs['documents'][:50])
            except:
                pass
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
            # Simple similarity check - avoid duplicates
            question_lower = question.lower()
            is_duplicate = False
            for seen in seen_questions:
                # Check if questions are very similar
                if question_lower in seen.lower() or seen.lower() in question_lower:
                    is_duplicate = True
                    break
            
            if not is_duplicate and count > 0:
                faqs.append({
                    'question': question[:200],  # Limit length
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
            max_tokens=300  # Increased to allow for source explanations
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
                max_questions=min(num_questions, 20),  # Cap at 20
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
        # Retrieve relevant context (with optional audience filtering)
        # Note: audience filtering can be added to get_response_with_sources if needed
        context_chunks = self._retrieve_relevant_context(query)
        
        # Generate response with conversation history
        response = self._generate_response(query, context_chunks, conversation_history)
        
        # Truncate if too long (SMS limit is ~1600 chars, but we'll be conservative)
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
            # For FAQ queries, return empty sources
            response = self.get_response(query, conversation_history)
            return response, []
        
        # Regular query processing
        # Retrieve relevant context (with audience filtering if specified)
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
        
        # Add to collection
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )
        
        print(f"Added document {doc_id} to knowledge base")

