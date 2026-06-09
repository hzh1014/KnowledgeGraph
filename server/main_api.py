"""
Server with OpenAI-compatible API support.
Supports DeepSeek, 通义千问, OpenAI, and other compatible APIs.
Includes: NER, Knowledge Graph retrieval, Wikipedia search, Image search.
"""
import os
import sys
import json

# Add project root to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings, load_dotenv
from modules.utils.logger import logger

# Load environment variables
load_dotenv()

# Setup CUDA before importing models
os.environ["CUDA_VISIBLE_DEVICES"] = settings.CUDA_VISIBLE_DEVICES

from flask import Flask, request, Response, jsonify, stream_with_context
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# API Configuration
USE_API_MODE = os.environ.get("USE_API_MODE", "false").lower() == "true"
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.deepseek.com/v1")
API_KEY = os.environ.get("API_KEY", "")
API_MODEL_NAME = os.environ.get("API_MODEL_NAME", "deepseek-chat")

# Load knowledge graph data
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'data.json')
graph_data = {}

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        graph_data = json.load(f)
    logger.info(f"Loaded graph data with {len(graph_data.get('nodes', []))} nodes, {len(graph_data.get('links', []))} links")
else:
    logger.warning(f"Data file not found: {DATA_FILE}")

# Initialize NER, Wiki, Image modules
logger.info("Initializing NER module...")
try:
    from app.utils.ner_api import get_ner
    ner = get_ner()
    if ner and len(ner.graph_entities) > 0:
        logger.info(f"NER module loaded successfully ({len(ner.graph_entities)} entities)")
    else:
        logger.warning("NER model is None or no entities loaded")
except Exception as e:
    logger.error(f"NER module not available: {e}", exc_info=True)
    ner = None

logger.info("Initializing WikiSearcher...")
try:
    from app.utils.query_wiki import WikiSearcher
    wiki_searcher = WikiSearcher()
    logger.info("WikiSearcher loaded")
except Exception as e:
    logger.error(f"WikiSearcher not available: {e}", exc_info=True)
    wiki_searcher = None

try:
    from app.utils.image_searcher import ImageSearcher
    image_searcher = ImageSearcher()
    logger.info("ImageSearcher loaded")
except Exception as e:
    logger.warning(f"ImageSearcher not available: {e}")
    image_searcher = None

try:
    from app.utils.graph_utils import search_node_item, convert_graph_to_triples
    logger.info("Graph utils loaded")
except Exception as e:
    logger.warning(f"Graph utils not available: {e}")
    search_node_item = None
    convert_graph_to_triples = None

from opencc import OpenCC
cc = OpenCC('t2s')


def call_api_stream(messages):
    """Call OpenAI-compatible API with streaming."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    data = {
        "model": API_MODEL_NAME,
        "messages": messages,
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 2000
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            stream=True,
            timeout=60
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    line = line[6:]
                    if line.strip() == '[DONE]':
                        break
                    try:
                        chunk = json.loads(line)
                        if 'choices' in chunk and len(chunk['choices']) > 0:
                            choice = chunk['choices'][0]
                            if 'delta' in choice:
                                delta = choice['delta']
                                if 'content' in delta:
                                    yield delta['content']
                            elif 'message' in choice:
                                message = choice['message']
                                if 'content' in message:
                                    yield message['content']
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        logger.error(f"API call failed: {e}")
        yield f"API调用失败: {str(e)}"


@app.route('/')
def index():
    mode = "API Mode" if USE_API_MODE else "Local Mode"
    return jsonify({
        "status": "ok",
        "message": f"ChatKG API Server ({mode})",
        "api_mode": USE_API_MODE,
        "model": API_MODEL_NAME if USE_API_MODE else "ChatGLM-6B",
        "features": {
            "ner": ner is not None,
            "wiki": wiki_searcher is not None,
            "image": image_searcher is not None,
            "graph": search_node_item is not None
        }
    })


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('prompt', '')
    history = data.get('history', [])
    logger.info(f"Chat request: prompt='{user_input}', history_len={len(history)}")

    if not USE_API_MODE:
        response_text = "当前未配置API。请在 .env 文件中设置 USE_API_MODE=true 和 API_KEY。"
        result = {
            "history": history + [(user_input, response_text)],
            "updates": {"query": user_input, "response": response_text},
            "image": None, "graph": {}, "wiki": {"title": "无API", "summary": "请配置API"}
        }
        return Response(json.dumps(result, ensure_ascii=False) + '\n', mimetype='application/json')

    # ========== 1. NER Entity Extraction ==========
    entities = []
    if ner is not None:
        try:
            entities = ner.get_entities(user_input)
            logger.info(f"Extracted entities: {entities}")
        except Exception as e:
            logger.error(f"NER failed: {e}")

    # ========== 2. Knowledge Graph Retrieval ==========
    graph = {}
    triples = []
    if search_node_item is not None and entities:
        try:
            for entity in entities:
                graph = search_node_item(entity, graph if graph else None)
                if graph and convert_graph_to_triples:
                    triples += convert_graph_to_triples(graph, entity)
            logger.info(f"Found {len(triples)} triples")
        except Exception as e:
            logger.error(f"Graph search failed: {e}")

    triples_str = ""
    for t in triples:
        triples_str += f"({t[0]} {t[1]} {t[2]})；"

    # ========== 3. Image Search ==========
    image = None
    if image_searcher is not None:
        try:
            image = image_searcher.search(user_input)
        except Exception as e:
            logger.error(f"Image search failed: {e}")

    # ========== 4. Wikipedia Search (with timeout) ==========
    wiki = {"title": "无相关信息", "summary": "暂无相关描述"}
    if wiki_searcher is not None:
        import threading
        wiki_result_holder = [None]
        def wiki_search_task():
            try:
                for ent in entities + [user_input]:
                    result = wiki_searcher.search(ent)
                    if result is not None:
                        wiki_result_holder[0] = result
                        break
            except Exception as e:
                logger.error(f"Wiki search failed: {e}")
        t = threading.Thread(target=wiki_search_task)
        t.start()
        t.join(timeout=5)  # 5 second timeout
        if t.is_alive():
            logger.warning("Wikipedia search timed out")
        elif wiki_result_holder[0] is not None:
            try:
                wiki = {
                    "title": cc.convert(wiki_result_holder[0].title),
                    "summary": cc.convert(wiki_result_holder[0].summary[:500])
                }
            except Exception as e:
                logger.error(f"Wiki result processing failed: {e}")

    # ========== 5. Build API Messages ==========
    system_prompt = "你叫 ChatKG，是一个基于知识图谱的问答机器人。请用简洁且准确的话回答用户的问题。"
    messages = [{"role": "system", "content": system_prompt}]

    # Add history
    for h in history:
        if isinstance(h, (list, tuple)) and len(h) == 2:
            messages.append({"role": "user", "content": h[0]})
            messages.append({"role": "assistant", "content": h[1]})

    # Build reference info
    ref = ""
    if triples_str:
        ref += f"三元组信息：{triples_str}\n"
    if wiki and wiki.get("summary") and wiki["summary"] != "暂无相关描述":
        ref += f"Wikipedia：{wiki['summary']}\n"

    if ref:
        chat_input = f"===参考资料===\n{ref}\n根据上面资料，用简洁且准确的话回答下面问题：\n{user_input}"
    else:
        chat_input = user_input

    messages.append({"role": "user", "content": chat_input})

    # ========== 6. Stream Response ==========
    def generate():
        full_response = ""
        try:
            for chunk in call_api_stream(messages):
                if chunk is None:
                    continue
                full_response += str(chunk)
                result = {
                    "history": history + [(user_input, full_response)],
                    "updates": {"query": user_input, "response": full_response},
                    "image": image,
                    "graph": graph,
                    "wiki": wiki
                }
                yield json.dumps(result, ensure_ascii=False).encode('utf8') + b'\n'
        except Exception as e:
            logger.error(f"Generate error: {e}")
            if not full_response:
                full_response = f"API调用出错: {str(e)}"

        # Send final result
        if full_response:
            result = {
                "history": history + [(user_input, full_response)],
                "updates": {"query": user_input, "response": full_response},
                "image": image,
                "graph": graph,
                "wiki": wiki
            }
            yield json.dumps(result, ensure_ascii=False).encode('utf8') + b'\n'

    return Response(stream_with_context(generate()), mimetype='application/json')


@app.route('/graph', methods=['GET'])
def get_graph():
    """Return knowledge graph data for visualization."""
    return jsonify(graph_data)


@app.route('/entity/<name>', methods=['GET'])
def get_entity(name):
    """Search for an entity in the knowledge graph."""
    if search_node_item is not None:
        try:
            graph = search_node_item(name)
            triples = convert_graph_to_triples(graph, name) if convert_graph_to_triples else []
            return jsonify({"entity": name, "graph": graph, "triples": triples})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Graph utils not available"}), 503


@app.route('/config', methods=['GET'])
def get_config():
    """Return current configuration."""
    return jsonify({
        "use_api_mode": USE_API_MODE,
        "api_base_url": API_BASE_URL if USE_API_MODE else None,
        "api_model": API_MODEL_NAME if USE_API_MODE else None,
        "has_api_key": bool(API_KEY) if USE_API_MODE else False,
        "features": {
            "ner": ner is not None,
            "wiki": wiki_searcher is not None,
            "image": image_searcher is not None,
            "graph": search_node_item is not None
        }
    })


if __name__ == '__main__':
    if USE_API_MODE:
        logger.info(f"Starting in API mode with model: {API_MODEL_NAME}")
        logger.info(f"API endpoint: {API_BASE_URL}")
        if not API_KEY:
            logger.warning("API_KEY not set! Please configure in .env file")
    else:
        logger.info("Starting in local mode (no API configured)")

    logger.info(f"Server running on {settings.SERVER_HOST}:{settings.SERVER_PORT}")
    app.run(
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        debug=settings.DEBUG,
        threaded=True
    )
