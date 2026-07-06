##
# cli.py
#
# @author Prahlad Yeri <prahladyeri@yahoo.com>
# @license MIT

import os
import sys
import json
#import subprocess
import argparse
import keyring
import requests
from datetime import datetime
from colorama import Fore, Style, init

from openai import OpenAI
from gubbi.utils import cfghelper
from gubbi import __version__, PKG_NAME
#from urllib.parse import urljoin

init(autoreset=True)

class Session: # use like static class vars
    config_dir = None
    data_dir = None
    cfg = None
    provider_slug = None # current provider
    model_id = None # current model
    repl_prompt = ""
    client = None
    stack = [] # chat stack
    messages = []
    attached = [] # attached files for the next due message to LLM
    power_list = ['openai/gpt-oss-120b', # Strongest all-round reasoning model in the list. Excellent for engineering.
        'qwen/qwen3.5-397b-a17b', # One of the best open models for coding and reasoning.
        'mistralai/mistral-large-3-675b-instruct-2512', # Excellent long-form engineering and architecture.
        'meta/llama-3.3-70b-instruct',  # Very dependable general-purpose model.
        'nvidia/llama-3.1-nemotron-ultra-253b-v1', # NVIDIA's flagship reasoning model.
        'moonshotai/kimi-k2.6', # Worth keeping because it's unusually strong on long context and software tasks.
        'deepseek-ai/deepseek-v4-pro', # Excellent engineering model.
        'models/gemini-3.1-pro-preview',
        'models/gemini-2.5-pro',
        ]
    lite_list = ['deepseek-ai/deepseek-v4-flash', 
        'openai/gpt-oss-20b',
        'google/gemma-4-31b-it', # Great balance of reasoning, code and instruction following.
        'meta/llama-4-maverick-17b-128e-instruct',
        #'google/gemma-3-12b-it',
        'mistralai/ministral-14b-instruct-2512',
        'nv-mistralai/mistral-nemo-12b-instruct',
        'microsoft/phi-4-mini-instruct',
        'upstage/solar-10.7b-instruct',
        'meta/llama-3.1-8b-instruct ', 'qwen/qwen3-next-80b-a3b-instruct',
        'models/gemini-3.5-flash',
        'models/gemini-2.5-flash',
        ]
        
    coding_list = ['mistralai/codestral-22b-instruct-v0.1',
        'ibm/granite-34b-code-instruct',
        'deepseek-ai/deepseek-coder-6.7b-instruct',
        'google/codegemma-7b'
    ]
    sysmsg = {
        "role": "system",
        "content": (
            "You operate strictly as a plain-text terminal interface. "
            "CRITICAL: Do NOT use any Markdown formatting whatsoever (no asterisks, no hashtags, no markdown code blocks like ```). "
            "Output raw, unformatted text only.\n\n"
            "DEFAULT CONVERSATIONAL MODE:\n"
            "By default, all text, explanations, answers, trivia, lists, and dialogue must be written directly in the conversational body. "
            "Do NOT use file tags for standard text conversations or simple answers.\n\n"
            "FILE EXPORT PROTOCOL:\n"
            "You may ONLY use the <file> tag at the absolute end of your response for heavy assets (e.g., source code scripts, raw SVG data, configuration files) OR when the user explicitly asks you to 'save', 'export', or 'write' something to a file.\n"
            "When using the tag, do NOT duplicate its contents in the conversational body. Use this exact structure:\n"
            "<file name='/path/to/file.ext'>file contents go here</file>"
        )
    }

    
    
    @staticmethod
    def update_prompt():
        Session.repl_prompt = f"me@{Fore.YELLOW}{Session.provider_slug}>{Style.RESET_ALL} "
    
    @staticmethod
    def connect(): # call whenever provider changes
        Session.client = OpenAI( 
            api_key=keyring.get_password(PKG_NAME, f"{Session.provider_slug}_apikey"), 
            base_url = Session.current_provider()['url'], 
            timeout=60.0,
            max_retries=0,
        )
    
    @staticmethod
    def current_provider():
        return Session.cfg["providers"][Session.provider_slug]
        
def cmd_attach(*args): # attach file
    if len(args) == 0:
        print("Invalid path.")
        return
    fpath = args[0]
    try:
        with open(fpath, 'r', encoding='utf-8') as fp:
            text = fp.read()
    except OSError as e:
        print(f"Unable to read file: {e}")
        return
    except UnicodeDecodeError:
        print("File does not appear to be text-readable.")
        return    
    Session.attached.append({ 'path':fpath, 'content': text })
    print(f"@{fpath} attached.")

def cmd_use(*args): # switch provider
    if switch_provider():
        Session.connect()
        if not Session.model_id:
            model_id = select_model()
            if model_id:
                Session.current_provider()['default_model_id'] = model_id
                Session.model_id = model_id
        Session.cfg['default_provider_slug'] = Session.current_provider()['slug']
        cfghelper.save_settings(PKG_NAME, Session.cfg)
        print(f"Default model set to {Session.provider_slug}/{Session.model_id}")
        Session.update_prompt()
    
def cmd_model(*args):# switch model
    model_id = select_model()
    if model_id:
        Session.model_id = model_id
        Session.current_provider()['default_model_id'] = model_id
        cfghelper.save_settings(PKG_NAME, Session.cfg)
        Session.update_prompt()
        print(f"Default model set to '{model_id}'.")
    
def cmd_help(*args):
   print("Available commands:")
   for name in COMMANDS:
       print(f"  /{name}")
    
def cmd_clear(*args):
    Session.stack = [{**Session.sysmsg, "timestamp": datetime.now().isoformat()}]
    Session.messages = [Session.sysmsg]
    os.system('cls' if os.name == 'nt' else 'clear')
    
def cmd_exit(*args):
    sys.exit()
    
def cmd_save(*args):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_model = Session.model_id.replace("/", "-")
    fname = f"{Session.provider_slug}_{safe_model}_{timestamp}.json"
    fpath = os.path.join(Session.data_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(Session.stack, f, indent=2)
    print(f"Chat saved to '{fpath}'.")
    
def cmd_load(*args):
    if not args:
        print("Usage: #load <filename>")
        return
    fpath = args[0]
    if not os.path.exists(fpath): # try to find it in data_dir
        fpath = os.path.join(Session.data_dir, fpath)
    if not os.path.exists(fpath):
        print("File not found.")
        return
        
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            Session.stack = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Failed to load chat: {e}")
        return
        
    Session.messages = [] # now let's rebuild messages array
    for msg in Session.stack:
        tmsg = {'role': msg['role'], 'content': msg['content'] }
        Session.messages.append(tmsg)
    print("Chat loaded successfully.")
    
def cmd_list(*args):
    if not args:
        print("Usage: /list models|providers")
        return
    if args[0] == 'models': # list models
        #prov = Session.current_provider()
        #apikey = keyring.get_password(PKG_NAME, f"{Session.provider_slug}_apikey")
        models = fetch_provider_models()
        if not models:
            print("Provider returned no models.")
            return
        for idx, model_id in enumerate(models):
            print(f"{idx}. {model_id}")
    elif args[0] == 'providers': # list providers
        providers = list(Session.cfg["providers"].keys())
        for idx, slug in enumerate(providers):
            print(f"{idx}. {slug}")
    else:
        print("unrecognized verb")

COMMANDS = {
    "help": cmd_help,
    "use": cmd_use,
    "model": cmd_model,
    "attach": cmd_attach,
    "exit": cmd_exit,
    "clear": cmd_clear, # clear message stack
    "list": cmd_list, # list models, providers, etc.
    "save": cmd_save, # save chat to file
    "load": cmd_load, # load chat from file
}

def _model_id(m):
    return m.id if hasattr(m, "id") else m["id"]
    
def _model_color(m):
    if m in Session.power_list:
        return Fore.LIGHTRED_EX
    elif m in Session.lite_list:
        return Fore.LIGHTBLUE_EX
    elif m in Session.coding_list:
        return Fore.LIGHTGREEN_EX
    else:
        return ''

def select_model():
    models = fetch_provider_models()
    if not models:
        print("Provider returned no models.")
        return False
    for idx, model in enumerate(models):
        prefix = _model_color(model)
        print(f"{prefix}{idx+1}. {model}{Style.RESET_ALL}", end=' | ')
    print()
    idx = input(f"Choose a default model [1-{len(models)}]:")
    if not idx.isdigit():
        print("Please enter a number")
        return False
        
    idx = int(idx) - 1
    if idx < 0 or idx >= len(models): 
        print("Invalid selection")
        return False
    return models[idx]
    
def fetch_provider_models(url=None, apikey=None):
    try:
        if url is None: # current provider
            url = Session.current_provider()['url']
            apikey = keyring.get_password(PKG_NAME, f"{Session.provider_slug}_apikey")
            client = Session.client
        else: # specific provider for testing
            client = OpenAI( 
                api_key=apikey, 
                base_url = url, 
            )
        
        if 'models.github.ai' in url:
            turl = 'https://models.github.ai/catalog/models'
            custom_headers = {
                "User-Agent": PKG_NAME,
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {apikey}"
            }
            resp = requests.get(turl, headers=custom_headers)
            resp.raise_for_status()
            models = resp.json()
        else:
            models = list(client.models.list())
        return [_model_id(m) for m in models]
    except Exception as e:
        print(f"Unable to fetch models: {e}")
        return False

def add_provider():
    slug = input("Enter provider short name, e.g. 'groq' or 'github-models':")
    url = input("Enter provider base url:")
    api_key = input("Add provider api key:")
    if slug and url and api_key:
        # validate provider and key
        models = fetch_provider_models(url, api_key)
        if not models:
            print("Provider returned no models")
            return False
        if 'providers' not in Session.cfg: 
            Session.cfg['providers'] = {}
        slug = slug.strip()
        Session.cfg['providers'][slug] = {'slug': slug, 'url': url, 'default_model_id': None}
        keyring.set_password(PKG_NAME, f"{slug}_apikey", api_key)
        cfghelper.save_settings(PKG_NAME, Session.cfg)
        Session.provider_slug = slug
        Session.model_id = ""
        Session.connect()
        model_id = select_model()
        if model_id:
            Session.cfg['providers'][slug]['default_model_id'] = model_id
            cfghelper.save_settings(PKG_NAME, Session.cfg)
        return True # Provider added, proceed now
    else:
        return False
        
def switch_provider():
    keys = list(Session.cfg['providers'].keys())
    for idx, key in enumerate(keys):
        print(f"[{idx}] {key}")
    raw = input('Select provider:')
    if not raw.isdigit():
        print("Please enter a number")
        return False    
    idx = int(raw)
    if not 0 <= idx < len(keys): return False
    Session.provider_slug = keys[idx]
    Session.model_id = Session.cfg['providers'][keys[idx]]['default_model_id']
    return True
        
def dispatch_command(cmd):
    parts = cmd.split()
    if not parts: return    
    name = parts[0]
    args = parts[1:]
    func = COMMANDS.get(name)
    if func is None:
        print(f"Unknown command: {name}")
        return
    func(*args)
        
def chat():
    if Session.cfg['default_provider_slug']:
        Session.provider_slug = Session.cfg['default_provider_slug']
    else:
        Session.provider_slug = next(iter(Session.cfg["providers"]))
    print(f"Provider set to {Session.provider_slug}")
    prov = Session.current_provider()
    if not prov['default_model_id']:
        prov['default_model_id'] = select_model()
        if not prov['default_model_id']: return
        cfghelper.save_settings(PKG_NAME, Session.cfg)
    print(f"Model set to {prov['default_model_id']}")
        
    Session.model_id = prov['default_model_id']
    Session.connect()
    Session.update_prompt()
    Session.stack = [{**Session.sysmsg, "timestamp": datetime.now().isoformat()}]
    Session.messages = [Session.sysmsg]
    
    while True: # repl
        try:
            text = input(Session.repl_prompt)
        except (KeyboardInterrupt, EOFError):
            print()
            break
        if not text.strip():
            continue
        elif text.startswith("/"):
            dispatch_command(text[1:])
            continue
            
        # continue regular chat
        if len(Session.attached) > 0:
            text += "\n"
            for f in Session.attached:
                text += f"<file name='{f['path']}'>{f['content']}</file>\n"
        msg = {'role': 'user', 'content': text }
        Session.messages.append(msg)
        try:
            response = Session.client.chat.completions.create(
                model=Session.model_id,
                messages=Session.messages,
            )
        except Exception as ex:
            Session.messages.pop()
            print("Error:", ex)
            if len(Session.attached) > 0: print("Attachments preserved.")
            continue
        Session.attached = []
        Session.stack.append({**msg, 'timestamp': datetime.now().isoformat()})
        
        text = response.choices[0].message.content
        print(f"{_model_color(Session.model_id)}{Session.model_id}: {Style.RESET_ALL}{text}")
        msg = {'role': 'assistant', 'content': text}
        Session.messages.append(msg)
        Session.stack.append({**msg, 'timestamp': datetime.now().isoformat()})

def main():
    Session.config_dir = cfghelper.get_config_dir(PKG_NAME)
    Session.data_dir = cfghelper.get_data_dir(PKG_NAME)
    Session.cfg = cfghelper.get_settings(PKG_NAME)
    parser = argparse.ArgumentParser(description=f"Gubbi chat interface")
    parser.add_argument('-a', '--add-provider', help='Add OpenAI compatible provider', action='store_true', default=False)
    parser.add_argument('-v', '--version', action='version', version=f"%(prog)s {__version__}")
    args = parser.parse_args()
    if args.add_provider:
        add_provider()
        return
        
    # just chat
    if 'providers' not in Session.cfg:
        print("No OpenAI compatible provider found.")
        if not add_provider(): return
    chat()
    
if __name__ == '__main__':
    main()