import requests
import json
import os
import re
import time
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from urllib.parse import urlparse
import logging

# Python 3.8以下でも動作するようにインポート
try:
    from typing import Dict, List, Optional, Tuple
except ImportError:
    from typing import Dict, List, Optional
    Tuple = tuple

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """検索結果データクラス"""
    title: str
    content: str
    url: str
    source: str
    relevance_score: float = 0.0
    date: Optional[str] = None
    snippet: str = ""
    meta_info: Dict = field(default_factory=dict)

@dataclass
class AdditionalInfo:
    """追加情報データクラス"""
    file_path: str
    content: str
    encoding: str = 'utf-8'
    file_size: int = 0
    last_modified: Optional[str] = None

class FileInfoManager:
    """ファイル情報管理クラス - 新機能"""
    
    def __init__(self, base_directory: str = "."):
        self.base_directory = base_directory
        self.supported_extensions = ['.txt', '.md', '.json', '.csv', '.log']
    
    def load_additional_info(self, file_paths: List[str]) -> List[AdditionalInfo]:
        """指定されたファイルパスから追加情報を読み込み"""
        additional_infos = []
        
        for file_path in file_paths:
            try:
                info = self._load_single_file(file_path)
                if info:
                    additional_infos.append(info)
                    print(f"✅ 追加情報を読み込みました: {file_path} ({len(info.content)}文字)")
            except Exception as e:
                print(f"❌ ファイル読み込みエラー {file_path}: {e}")
                continue
        
        return additional_infos
    
    def _load_single_file(self, file_path: str) -> Optional[AdditionalInfo]:
        """単一ファイルを読み込み"""
        
        # 絶対パス化
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.base_directory, file_path)
        
        if not os.path.exists(file_path):
            print(f"⚠️ ファイルが見つかりません: {file_path}")
            return None
        
        # 拡張子チェック
        _, ext = os.path.splitext(file_path.lower())
        if ext not in self.supported_extensions:
            print(f"⚠️ サポートされていないファイル形式: {ext}")
            return None
        
        # エンコーディング自動判定
        encoding = self._detect_encoding(file_path)
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # ファイル情報取得
            stat = os.stat(file_path)
            file_size = stat.st_size
            last_modified = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            return AdditionalInfo(
                file_path=file_path,
                content=content,
                encoding=encoding,
                file_size=file_size,
                last_modified=last_modified
            )
            
        except Exception as e:
            print(f"❌ ファイル読み込みエラー: {e}")
            return None
    
    def _detect_encoding(self, file_path: str) -> str:
        """ファイルのエンコーディングを自動判定"""
        encodings = ['utf-8', 'shift_jis', 'euc-jp', 'cp932', 'iso-2022-jp']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(1024)  # 最初の1KBで判定
                return encoding
            except UnicodeDecodeError:
                continue
        
        print(f"⚠️ エンコーディング自動判定失敗、UTF-8を使用: {file_path}")
        return 'utf-8'

class PromptConfigManager:
    """プロンプト設定管理クラス - 新機能"""
    
    def __init__(self):
        self.config_file = "prompt_config.json"
        self.default_config = {
            "prompt_file": "prompt.txt",
            "additional_info_files": [],
            "enable_web_search": True,
            "file_info_priority": "high",  # high, medium, low
            "max_file_content_length": 5000,
            "file_content_summary": False
        }
    
    def load_config(self) -> Dict:
        """設定を読み込み"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✅ プロンプト設定を読み込みました: {self.config_file}")
                return {**self.default_config, **config}
            except Exception as e:
                print(f"⚠️ 設定ファイル読み込みエラー、デフォルト設定を使用: {e}")
        
        return self.default_config.copy()
    
    def save_config(self, config: Dict) -> None:
        """設定を保存"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"✅ プロンプト設定を保存しました: {self.config_file}")
        except Exception as e:
            print(f"❌ 設定保存エラー: {e}")
    
    def interactive_setup(self) -> Dict:
        """対話型設定"""
        config = self.default_config.copy()
        
        print("\n📋 プロンプト設定セットアップ")
        print("=" * 40)
        
        # 追加情報ファイルの設定
        print("\n📁 追加情報ファイルの設定:")
        print("複数のファイルパスをカンマ区切りで入力してください")
        print("例: data/info1.txt, data/info2.md, reference.txt")
        
        files_input = input("追加情報ファイル (空白でスキップ): ").strip()
        if files_input:
            file_paths = [path.strip() for path in files_input.split(',')]
            config["additional_info_files"] = file_paths
        
        # Web検索の有効/無効
        web_search = input("\nWeb検索を有効にしますか? (y/N): ").lower()
        config["enable_web_search"] = web_search == 'y'
        
        # ファイル優先度
        print("\nファイル情報の優先度:")
        print("  high   - ファイル情報を最優先")
        print("  medium - Web検索と同等")  
        print("  low    - Web検索を優先")
        priority = input("優先度 (high/medium/low) [high]: ").lower()
        if priority in ['high', 'medium', 'low']:
            config["file_info_priority"] = priority
        
        self.save_config(config)
        return config

class SearchQueryOptimizer:
    """検索クエリ最適化クラス"""
    
    def __init__(self):
        self.japanese_keywords = {
            '最新': 'latest',
            '現在': 'current',
            '今日': 'today',
            'について': '',
            'に関して': '',
            'とは': 'what is',
            'どのように': 'how to',
            'なぜ': 'why'
        }
        
        self.search_modifiers = {
            'news': 'site:news.google.com OR site:nhk.or.jp OR site:asahi.com',
            'academic': 'site:scholar.google.com OR site:researchgate.net',
            'official': 'site:go.jp OR site:gov OR site:edu',
            'recent': f'{datetime.now().year}',
            'technical': 'site:github.com OR site:stackoverflow.com'
        }
    
    def optimize_query(self, original_query: str, search_type: str = 'general') -> List[str]:
        """クエリを最適化して複数のバリエーションを生成"""
        optimized_queries = []
        
        base_query = self._clean_query(original_query)
        optimized_queries.append(base_query)
        
        english_query = self._translate_to_english(base_query)
        if english_query != base_query:
            optimized_queries.append(english_query)
        
        if search_type in self.search_modifiers:
            modified_query = f"{base_query} {self.search_modifiers[search_type]}"
            optimized_queries.append(modified_query)
        
        if any(keyword in original_query.lower() for keyword in ['最新', '現在', 'latest', 'current']):
            time_limited = f"{base_query} after:{datetime.now().year-1}"
            optimized_queries.append(time_limited)
        
        filtered_query = f"{base_query} -advertisement -spam"
        optimized_queries.append(filtered_query)
        
        return list(set(optimized_queries))
    
    def _clean_query(self, query: str) -> str:
        """クエリのクリーニング"""
        cleaned = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', ' ', query)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
    
    def _translate_to_english(self, query: str) -> str:
        """簡単な日本語->英語翻訳"""
        translated = query
        for jp, en in self.japanese_keywords.items():
            translated = translated.replace(jp, en)
        return translated.strip()

class GoogleSearchAPI:
    """Google Search API (SerpAPI) ラッパー"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://serpapi.com/search"
        self.cache = {}
        self.cache_duration = timedelta(hours=1)
        
    def search(self, query: str, num_results: int = 10, search_type: str = 'web') -> List[SearchResult]:
        """Google検索を実行"""
        cache_key = hashlib.md5(f"{query}_{num_results}_{search_type}".encode()).hexdigest()
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_duration:
                logger.info(f"キャッシュから検索結果を取得: {query[:50]}...")
                return cached_result
        
        try:
            params = {
                'q': query,
                'api_key': self.api_key,
                'engine': 'google',
                'num': min(num_results, 20),
                'hl': 'ja',
                'gl': 'jp',
                'safe': 'active'
            }
            
            if search_type == 'news':
                params['tbm'] = 'nws'
            elif search_type == 'images':
                params['tbm'] = 'isch'
            
            logger.info(f"Google検索実行: {query[:50]}...")
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            results = self._parse_search_results(data, query)
            
            self.cache[cache_key] = (results, datetime.now())
            
            logger.info(f"検索結果 {len(results)}件を取得")
            return results
            
        except Exception as e:
            logger.error(f"Google検索エラー: {e}")
            return []
    
    def _parse_search_results(self, data: dict, original_query: str) -> List[SearchResult]:
        """検索結果をパース"""
        results = []
        
        organic_results = data.get('organic_results', [])
        for item in organic_results:
            result = SearchResult(
                title=item.get('title', ''),
                content=item.get('snippet', ''),
                url=item.get('link', ''),
                source='Google Search',
                snippet=item.get('snippet', ''),
                meta_info={
                    'position': item.get('position', 0),
                    'domain': urlparse(item.get('link', '')).netloc
                }
            )
            
            result.relevance_score = self._calculate_relevance(result, original_query)
            results.append(result)
        
        news_results = data.get('news_results', [])
        for item in news_results:
            result = SearchResult(
                title=item.get('title', ''),
                content=item.get('snippet', ''),
                url=item.get('link', ''),
                source='Google News',
                date=item.get('date', ''),
                snippet=item.get('snippet', ''),
                meta_info={
                    'source_name': item.get('source', ''),
                    'is_news': True
                }
            )
            result.relevance_score = self._calculate_relevance(result, original_query) + 0.1
            results.append(result)
        
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results
    
    def _calculate_relevance(self, result: SearchResult, query: str) -> float:
        """関連度スコアを計算"""
        score = 0.0
        query_words = set(query.lower().split())
        
        title_words = set(result.title.lower().split())
        title_matches = len(query_words.intersection(title_words))
        score += title_matches * 0.3
        
        content_words = set(result.content.lower().split())
        content_matches = len(query_words.intersection(content_words))
        score += content_matches * 0.2
        
        reliable_domains = ['wikipedia.org', 'gov.jp', 'go.jp', 'edu', 'ac.jp']
        if any(domain in result.url.lower() for domain in reliable_domains):
            score += 0.2
        
        position = result.meta_info.get('position', 10)
        score += max(0, (10 - position) * 0.05)
        
        return min(score, 1.0)

class FileBasedRAGSystem:
    """ファイルベース RAGシステム - メイン機能"""
    
    def __init__(self, google_api_key: str = "", model_name: str = "gpt-oss:20b", 
                 ollama_url: str = "http://localhost:11434"):
        self.google_search = GoogleSearchAPI(google_api_key) if google_api_key else None
        self.query_optimizer = SearchQueryOptimizer()
        self.file_manager = FileInfoManager()  # 新機能
        self.prompt_config_manager = PromptConfigManager()  # 新機能
        self.model_name = model_name
        self.ollama_url = ollama_url
        
        # 検索トリガーキーワード
        self.search_triggers = [
            '最新', '現在', '今', '今日', '今年', '2024年', '2025年',
            'latest', 'current', 'recent', 'today', 'now', 'update',
            'ニュース', 'news', '動向', 'trend', '状況', 'situation'
        ]
    
    def should_search(self, prompt: str):
        """検索が必要かどうかを判定し、検索タイプを返す"""
        prompt_lower = prompt.lower()
        
        needs_search = any(trigger in prompt_lower for trigger in self.search_triggers)
        
        search_type = 'general'
        if any(word in prompt_lower for word in ['ニュース', 'news', '事件', '事故']):
            search_type = 'news'
        elif any(word in prompt_lower for word in ['研究', 'study', '論文', '学術']):
            search_type = 'academic'
        elif any(word in prompt_lower for word in ['政府', '公式', 'official', '法律']):
            search_type = 'official'
        elif any(word in prompt_lower for word in ['技術', 'プログラム', 'tech', 'code']):
            search_type = 'technical'
        
        return needs_search, search_type
    
    def search_and_rank(self, query: str, search_type: str = 'general', 
                       max_results: int = 15) -> List[SearchResult]:
        """検索を実行し、結果をランキング"""
        if not self.google_search:
            return []
        
        all_results = []
        optimized_queries = self.query_optimizer.optimize_query(query, search_type)
        
        for i, opt_query in enumerate(optimized_queries[:3]):
            try:
                results = self.google_search.search(
                    opt_query, 
                    num_results=max_results // len(optimized_queries) + 3,
                    search_type=search_type
                )
                
                for result in results:
                    result.relevance_score *= (1.0 - i * 0.1)
                
                all_results.extend(results)
                
                if i < len(optimized_queries) - 1:
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"検索エラー (クエリ: {opt_query}): {e}")
                continue
        
        unique_results = self._deduplicate_results(all_results)
        unique_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return unique_results[:max_results]
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """重複する検索結果を除去"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        return unique_results
    
    def format_file_context(self, additional_infos: List[AdditionalInfo], 
                           max_length: int = 3000) -> str:
        """ファイル情報をコンテキストとして整形 - 新機能"""
        if not additional_infos:
            return ""
        
        context = "\n\n=== 提供済み追加情報 ===\n"
        
        current_length = len(context)
        
        for i, info in enumerate(additional_infos, 1):
            file_header = f"📄 ファイル {i}: {os.path.basename(info.file_path)}\n"
            file_header += f"   更新日時: {info.last_modified}\n"
            file_header += f"   ファイルサイズ: {info.file_size} bytes\n"
            file_header += f"   内容:\n"
            
            # 内容を制限長に切り詰め
            remaining_length = max_length - current_length - len(file_header) - 100
            if remaining_length > 0:
                content_preview = info.content[:remaining_length]
                if len(info.content) > remaining_length:
                    content_preview += "...(省略)"
            else:
                content_preview = info.content[:200] + "...(省略)"
            
            file_text = file_header + content_preview + "\n\n"
            
            if current_length + len(file_text) > max_length:
                context += f"... (他 {len(additional_infos) - i + 1} ファイル省略)\n"
                break
            
            context += file_text
            current_length += len(file_text)
        
        context += "=== 追加情報終了 ===\n\n"
        return context
    
    def format_search_context(self, results: List[SearchResult], max_length: int = 2000) -> str:
        """検索結果をコンテキストとして整形"""
        if not results:
            return ""
        
        context = "\n\n=== Web検索情報 ===\n"
        context += f"検索日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        current_length = len(context)
        
        for i, result in enumerate(results, 1):
            result_text = f"🔍 検索結果 {i}: {result.title}\n"
            if result.date:
                result_text += f"   日付: {result.date}\n"
            result_text += f"   内容: {result.content[:250]}\n"
            result_text += f"   信頼度: {result.relevance_score:.2f}\n"
            result_text += f"   URL: {result.url}\n\n"
            
            if current_length + len(result_text) > max_length:
                context += f"... (他 {len(results) - i + 1} 件省略)\n"
                break
            
            context += result_text
            current_length += len(result_text)
        
        context += "=== Web検索情報終了 ===\n\n"
        return context
    
    def generate_response(self, prompt: str, prompt_config: Dict) -> None:
        """ファイルベース検索拡張生成を実行 - メイン処理"""
        
        print(f"\n🚀 ファイルベースRAGシステム実行")
        print("=" * 50)
        
        # 1. 追加情報ファイル読み込み
        file_context = ""
        if prompt_config.get("additional_info_files"):
            print("📁 追加情報ファイルを読み込み中...")
            additional_infos = self.file_manager.load_additional_info(
                prompt_config["additional_info_files"]
            )
            
            if additional_infos:
                file_context = self.format_file_context(
                    additional_infos, 
                    max_length=prompt_config.get("max_file_content_length", 3000)
                )
                print(f"✅ {len(additional_infos)}個のファイルから情報を取得")
        
        # 2. Web検索実行
        search_context = ""
        if prompt_config.get("enable_web_search") and self.google_search:
            needs_search, search_type = self.should_search(prompt)
            
            if needs_search:
                print("🔍 Web検索を実行中...")
                search_results = self.search_and_rank(prompt, search_type)
                
                if search_results:
                    search_context = self.format_search_context(search_results)
                    print(f"✅ {len(search_results)}件のWeb検索結果を取得")
        
        # 3. 情報統合（優先度に基づいて順序決定）
        priority = prompt_config.get("file_info_priority", "high")
        
        if priority == "high":
            # ファイル情報を優先
            combined_context = file_context + search_context
        elif priority == "low": 
            # Web検索を優先
            combined_context = search_context + file_context
        else:
            # medium: バランス良く
            combined_context = file_context + search_context
        
        # 4. 最終プロンプト構築
        final_prompt = self._build_final_prompt(prompt, combined_context, prompt_config)
        
        print(f"\n🎯 構築されたプロンプト長: {len(final_prompt)}文字")
        print(f"📄 ファイル情報: {len(file_context)}文字")
        print(f"🔍 検索情報: {len(search_context)}文字")
        
        # 5. LLM応答生成
        print(f"\n🤖 {self.model_name} による回答生成...")
        print("=" * 50)
        
        self._generate_llm_response(final_prompt)
    
    def _build_final_prompt(self, original_prompt: str, context: str, config: Dict) -> str:
        """最終プロンプトを構築"""
        
        if not context:
            return original_prompt
        
        final_prompt = f"""{context}

上記の情報を参考にして、以下の質問に詳しく回答してください。

【質問】
{original_prompt}

【回答指示】
- 提供された追加情報とWeb検索結果を活用してください
- 具体的で実用的な回答を提供してください
- 情報源がある場合は適切に参照してください
- 回答を途中で止めず、完全な内容を提供してください
- 最後に要点をまとめてください

【回答】"""
        
        return final_prompt
    
    def _generate_llm_response(self, prompt: str) -> None:
        """LLM応答生成"""
        url = f"{self.ollama_url}/api/generate"
        
        data = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9,
                "max_tokens": 4000,
                "repeat_penalty": 1.1,
                "stop": []
            }
        }
        
        try:
            response = requests.post(url, json=data, stream=True, timeout=120)
            response.raise_for_status()
            
            print("📝 回答:")
            
            for line in response.iter_lines():
                if line:
                    try:
                        decoded_line = line.decode('utf-8')
                        response_data = json.loads(decoded_line)
                        
                        if 'response' in response_data and response_data['response']:
                            print(response_data['response'], end='', flush=True)
                        
                        if response_data.get('done', False):
                            break
                            
                    except json.JSONDecodeError:
                        continue
            
            print("\n")
            
        except Exception as e:
            logger.error(f"応答生成エラー: {e}")
            print(f"\n❌ エラーが発生しました: {e}")

def main():
    """メイン関数"""
    
    # 基本設定読み込み
    config_file = "config.json"
    
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {
            "google_api_key": "",
            "model_name": "gpt-oss:20b", 
            "ollama_url": "http://localhost:11434"
        }
        
        print("⚙️ 基本設定を行います")
        config["google_api_key"] = input("SerpAPI キー (空白でWeb検索無効): ")
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✅ 基本設定を {config_file} に保存しました")
    
    # プロンプト設定管理
    prompt_config_manager = PromptConfigManager()
    
    # プロンプト設定の読み込みまたは作成
    if not os.path.exists(prompt_config_manager.config_file):
        print("\n📋 初回セットアップを行います")
        prompt_config = prompt_config_manager.interactive_setup()
    else:
        prompt_config = prompt_config_manager.load_config()
        
        # 設定変更の確認
        change_config = input("\nプロンプト設定を変更しますか? (y/N): ").lower()
        if change_config == 'y':
            prompt_config = prompt_config_manager.interactive_setup()
    
    # プロンプト読み込み
    prompt_file = prompt_config.get("prompt_file", "prompt.txt")
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(script_dir, prompt_file), 'r', encoding='utf-8') as f:
            prompt_text = f.read().strip()
    except FileNotFoundError:
        print(f"❌ プロンプトファイル '{prompt_file}' が見つかりません")
        return
    
    # RAGシステム初期化
    rag_system = FileBasedRAGSystem(
        google_api_key=config.get("google_api_key", ""),
        model_name=config.get("model_name", "gpt-oss:20b"),
        ollama_url=config.get("ollama_url", "http://localhost:11434")
    )
    
    # 設定情報表示
    print("\n🚀 ファイルベースRAGシステム")
    print("=" * 60)
    print(f"📝 プロンプトファイル: {prompt_file}")
    print(f"📁 追加情報ファイル: {len(prompt_config.get('additional_info_files', []))}個")
    if prompt_config.get('additional_info_files'):
        for i, file_path in enumerate(prompt_config['additional_info_files'], 1):
            print(f"    {i}. {file_path}")
    print(f"🔍 Web検索: {'有効' if prompt_config.get('enable_web_search') else '無効'}")
    print(f"📊 ファイル優先度: {prompt_config.get('file_info_priority', 'high')}")
    print(f"🤖 モデル: {config.get('model_name', 'gpt-oss:20b')}")
    print("=" * 60)
    
    # 応答生成実行
    rag_system.generate_response(prompt_text, prompt_config)

if __name__ == "__main__":
    main()