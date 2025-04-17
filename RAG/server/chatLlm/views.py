from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import StreamingHttpResponse
from .models import Chat, ChatMessage
from .serializers import ChatSerializer, ChatMessageSerializer
from .services.groq_service import GroqChatService, StreamingCallbackHandler
import queue
import threading
import json
import time

class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSerializer

    def get_queryset(self):
        return Chat.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ChatMessageView(APIView):
    def post(self, request, chat_id):
        try:
            chat = Chat.objects.get(id=chat_id, user=request.user)
            message_content = request.data.get('message', '')
            
            # Get scrape_ids from request data if provided
            scrape_ids = request.data.get('scrape_ids', None)

            # Save user message
            user_message = ChatMessage.objects.create(
                chat=chat,
                role='user',
                content=message_content
            )

            # Get chat history - limit to last N messages for context window
            chat_history = ChatMessage.objects.filter(chat=chat).order_by('timestamp')[:10]  # Limit to last 10 messages
            # Format chat history properly
            formatted_history = [
                {"role": msg.role, "content": msg.content} 
                for msg in chat_history
            ]

            # Create service instance and generate response
            groq_service = GroqChatService(request.user.id)
            ai_response = groq_service.generate_response(
                message_content,
                chat_history=formatted_history,
                scrape_ids=scrape_ids  # Pass scrape_ids to generate_response
            )

            # Save AI response
            ai_message = ChatMessage.objects.create(
                chat=chat,
                role='assistant',
                content=ai_response
            )

            return Response({
                'user_message': ChatMessageSerializer(user_message).data,
                'ai_message': ChatMessageSerializer(ai_message).data
            })

        except Chat.DoesNotExist:
            return Response({'error': 'Chat not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error in ChatMessageView: {str(e)}")  # Added logging
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ChatMessageStreamView(APIView):
    def post(self, request, chat_id):
        try:
            start_time = time.time()
            chat = Chat.objects.get(id=chat_id)
            print(f"Time to retrieve chat: {time.time() - start_time} seconds")
            message_content = request.data.get('message', '')
            
            # Get scrape_ids from request data if provided
            scrape_ids = request.data.get('scrape_ids', None)
            
            # Save user message
            ChatMessage.objects.create(
                chat=chat,
                role='user',
                content=message_content
            )

            print(f"Time to create user object: {time.time() - start_time} seconds")
            # Get chat history - limit to last N messages for context window
            chat_history = ChatMessage.objects.filter(chat=chat).order_by('timestamp')[:10]
            formatted_history = [
                {"role": msg.role, "content": msg.content} 
                for msg in chat_history
            ]

            print(f"Time to retrieve chat history: {time.time() - start_time} seconds")
            
            # Create response streaming
            def event_stream():
                # Create a queue for handling streamed tokens
                token_queue = queue.Queue()
                callback_handler = StreamingCallbackHandler(token_queue)
                
                # Create service and start generation in a separate thread
                groq_service = GroqChatService(request.user.id)

                print(f"Time to create service: {time.time() - start_time} seconds")
                
                def generate_in_thread():
                    try:
                        groq_service.generate_streaming_response(
                            message_content, 
                            chat_history=formatted_history,
                            streaming_callback=callback_handler,
                            scrape_ids=scrape_ids  # Pass scrape_ids to streaming function
                        )
                    except Exception as e:
                        print(f"Error in generate_in_thread: {str(e)}")
                        token_queue.put({"error": str(e)})
                    finally:
                        # Signal end of streaming
                        token_queue.put(None)

                print(f"Time to start generation thread: {time.time() - start_time} seconds")
                # Start generation thread
                thread = threading.Thread(target=generate_in_thread)
                thread.daemon = True  # Make thread daemon so it doesn't block app shutdown
                thread.start()
                
                full_response = ""
                
                print(f"Time to start streaming loop: {time.time() - start_time} seconds")

                # Stream tokens as they're generated
                while True:
                    token = token_queue.get()
                    if token is None:  # End of generation
                        # After streaming completes, save the full message to the database
                        ai_message = ChatMessage.objects.create(
                            chat=chat,
                            role='assistant',
                            content=full_response
                        )
                        # Send completion message with proper SSE format
                        yield f"data: {json.dumps({'done': True, 'messageId': ai_message.id})}\n\n"
                        break
                    elif isinstance(token, dict) and "error" in token:
                        # Handle error case
                        yield f"data: {json.dumps({'error': token['error']})}\n\n"
                        break
                    else:
                        full_response += token
                        # Ensure proper SSE format with data: prefix and double newlines
                        yield f"data: {json.dumps({'token': token})}\n\n"
                        # Flush the output buffer to ensure immediate sending
                
                print(f"Time to complete streaming loop: {time.time() - start_time} seconds")

            response = StreamingHttpResponse(
                event_stream(),
                content_type='text/event-stream'
            )
            # Add required headers for SSE
            response['Cache-Control'] = 'no-cache'
            response['X-Accel-Buffering'] = 'no'  # Disable Nginx buffering
            print(f"Time to create response: {time.time() - start_time} seconds")
            return response
            
        except Chat.DoesNotExist:
            return Response({'error': 'Chat not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error in ChatMessageStreamView: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)