##
# cli.py
#
# @author Prahlad Yeri <prahladyeri@yahoo.com>
# @license MIT

#import os
import sys
#import json
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
    
    @staticmethod
    def update_prompt():
        Session.repl_prompt = f"me@{Fore.CYAN}{Session.provider_slug}>{Style.RESET_ALL} "
    
    @staticmethod
    def connect(): # call whenever provider changes
        Session.client = OpenAI( 
            api_key=keyring.get_password(PKG_NAME, f"{Session.provider_slug}_apikey"), 
            base_url = Session.current_provider()['url'], 
        )
    
    @staticmethod
    def current_provider():
        return Session.cfg["providers"][Session.provider_slug]
        
def cmd_use(): # switch provider
    # @todo: update provider slug and model_id in Session
    # @todo: Session.connect()
    # @todo: Session.update_prompt()
    pass # @todo
    
def cmd_attach(): # attach file
    pass # @todo
    
def cmd_model():# switch model
    pass # @todo
    
def cmd_help():
    pass # @todo
    
def cmd_exit():
    sys.exit()

COMMANDS = {
    "help": cmd_help,
    "use": cmd_use,
    "model": cmd_model,
    "attach": cmd_attach,
    "exit": cmd_exit,
    #"clear": cmd_clear, # clear message stack
    #"save": cmd_save, # save chat to file
    #"load": cmd_load, # load chat from file
    #"models": cmd_models, # list models
    #"providers": cmd_providers, # list providers
}

def _model_id(m):
       return m.id if hasattr(m, "id") else m["id"]

def add_model(pslug):
    prov = Session.cfg['providers'][pslug]
    try:
        if 'models.github.ai' in prov['url']:
            turl = 'https://models.github.ai/catalog/models'
            apikey = keyring.get_password(PKG_NAME, f"{Session.provider_slug}_apikey")
            custom_headers = {
                "User-Agent": PKG_NAME,
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {apikey}"
            }
            resp = requests.get(turl, headers=custom_headers)
            models = resp.json()
        else:
            models = list(Session.client.models.list())
    except Exception as e:
        print(f"Unable to fetch models: {e}")
        return False
    if not models:
        print("Provider returned no models.")
        return False
    for idx, model in enumerate(models):
        print(f"[{idx+1}]. {_model_id(model)}")
    idx = input("Choose a default model:")
    if not idx.isdigit():
        print("Please enter a number")
        return False
        
    idx = int(idx) - 1
    if idx < 0 or idx >= len(models): 
        print("Invalid selection")
        return False
    prov['default_model_id'] = _model_id(models[idx])
    cfghelper.save_settings(PKG_NAME, Session.cfg)
    print(f"Default model set to '{prov['default_model_id']}'.")
    return True
    

def add_provider():
    slug = input("Enter provider short name, e.g. 'groq':")
    url = input("Enter provider base url:")
    api_key = input("Add provider api key:")
    if slug and url and api_key:
        keyring.set_password(PKG_NAME, f"{slug}_apikey", api_key)
        if 'providers' not in Session.cfg: Session.cfg['providers'] = {}
        Session.cfg['providers'][slug] = {'slug': slug, 'url': url, 'default_model_id': None}
        cfghelper.save_settings(PKG_NAME, Session.cfg)
        # @todo: validate provider and key
        Session.provider_slug = slug
        Session.model_id = ""
        Session.connect()
        add_model(slug)
        return True # Provider added, proceed now
    else:
        return False
        
def dispatch_command(cmd):
    parts = cmd.split()
    if not parts: return    
    name = parts[0]
    args = parts[1:]
    func = COMMANDS.get(name)
    #COMMANDS[name](*args)
    if func is None:
        print(f"Unknown command: {name}")
        return
    func(*args)
        
def chat():
    Session.provider_slug = next(iter(Session.cfg["providers"]))
    prov = Session.current_provider()
    if not prov['default_model_id']:
        if not add_model(Session.provider_slug): return
    Session.model_id = prov['default_model_id']
    Session.connect()
    Session.update_prompt()
    sysmsg = {
        "role": "system",
        "content": "Converse in terminal text, no markdown unless specifically asked for. Use the <file name='/foo/bar.txt'></file> at the end of message for sending/receiving text files"}
    Session.stack = [{**sysmsg, "timestamp": datetime.now().isoformat()}]
    Session.messages = [sysmsg]
    
    while True: # repl
        try:
            text = input(Session.repl_prompt)
            #print(f"{Fore.CYAN}You: {Style.RESET_ALL}{text}")
        except (KeyboardInterrupt, EOFError):
            print()
            break
        if text.startswith("#"):
            dispatch_command(text[1:])
            continue
        else: # continue regular chat
            msg = {'role': 'user', 'content': text }
            Session.messages.append(msg)
            try:
                response = Session.client.chat.completions.create(
                    model=Session.model_id,
                    messages=Session.messages
                )
            except Exception as ex:
                print("Error:", ex)
                continue
            Session.stack.append({**msg, 'timestamp': datetime.now().isoformat()})
            text = response.choices[0].message.content
            #print(text) # @todo: save this to a log or something to retrieve later
            print(f"{Fore.GREEN}{Session.model_id}: {Style.RESET_ALL}{text}")
            msg = {'role': 'assistant', 'content': text}
            Session.messages.append(msg)
            Session.stack.append({**msg, 'timestamp': datetime.now().isoformat()})

def main():
    Session.config_dir = cfghelper.get_config_dir(PKG_NAME)
    Session.data_dir = cfghelper.get_data_dir(PKG_NAME)
    Session.cfg = cfghelper.get_settings(PKG_NAME)
    parser = argparse.ArgumentParser(description=f"Gubbi chat interface v{__version__}")
    parser.add_argument('-a', '--add-provider', help='Add OpenAI compatible provider', action='store_true', default=False)
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