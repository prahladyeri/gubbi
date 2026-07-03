##
# cli.py
#
# @author Prahlad Yeri <prahladyeri@yahoo.com>
# @license MIT

#import os, sys
#import json
#import subprocess
import argparse
import keyring
from datetime import datetime
from openai import OpenAI
from utils import cfghelper
from gubbi import __version__, PKG_NAME
#from urllib.parse import urljoin

class Session: # use like static class vars
    config_dir = None
    cfg = None
    provider_slug = None # current provider
    model_id = None # current model
    repl_prompt = ""
    client = None
    stack = [] # chat stack
    
    @staticmethod
    def update_prompt():
        Session.repl_prompt = f"{Session.provider_slug}/{Session.model_id}> "
    
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
    pass
    
def cmd_attach(): # attach file
    pass
    
def cmd_model():# switch model
    pass
    
def cmd_help():
    pass

COMMANDS = {
    "use": cmd_use,
    "model": cmd_model,
    "attach": cmd_attach,
    "clear": cmd_clear, # clear message stack
    "save": cmd_save, # save chat to file
    "load": cmd_load, # load chat from file
    "models": cmd_models, # list models
    "providers": cmd_providers, # list providers
    "help": cmd_help,
}

def add_model(pslug):
    prov = Session.cfg['providers'][pslug]
    try:
        models = list(Session.client.models.list())
    except Exception as e:
        print(f"Unable to fetch models: {e}")
        return False
    if not models:
        print("Provider returned no models.")
        return False
    for idx, model in enumerate(models):
        print(f"[{idx+1}]. {model.id}")
    idx = input("Choose a default model:")
    if not idx.isdigit():
        print("Please enter a number")
        return False
        
    idx = int(idx) - 1
    if idx < 0 or idx >= len(models): 
        print("Invalid selection")
        return False
    prov['default_model_id'] = models[idx].id
    cfghelper.save_settings(PKG_NAME, Session.cfg)
    print(f"Default model set to '{models[idx].id}'.")
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
        print(f"Unknown command: #{name}")
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
    Session.stack = [{
        "role": "system",
        "content": "Converse in terminal text, no markdown unless specifically asked for. Use the <file name='/foo/bar.txt'></file> at the end of message for sending/receiving text files"}] 
    while True: # repl
        text = input(Session.repl_prompt)
        if text.startswith("#"):
            dispatch_command(text[1:])
            continue
        else: # continue regular chat
            Session.stack.append({'role': 'user', 'content': text, 'timestamp': datetime.utcnow().isoformat() })
            try:
                response = Session.client.chat.completions.create(
                    model=Session.model_id,
                    messages=Session.stack
                )
            except Exception as ex:
                print("Error:", ex)
                continue
            msg = response.choices[0].message.content
            print(msg) # @todo: save this to a log or something to retrieve later
            Session.stack.append({'role': 'assistant', 'content': msg, 'timestamp': datetime.utcnow().isoformat()})
            
def main():
    Session.config_dir = cfghelper.get_config_dir(PKG_NAME)
    Session.cfg = cfghelper.get_settings(f"{PKG_NAME}")
    parser = argparse.ArgumentParser(description=f"Gubbi chat interface v{__version__}")
    parser.add_argument('-c', '--chat', help='Start chat repl')
    parser.add_argument('-a', '--add-provider', help='Add OpenAI compatible provider', action='store_true', default=False)
    args = parser.parse_args()
    if args.add_provider:
        add_provider()
        return
    if 'providers' not in Session.cfg:
        print("No OpenAI compatible provider found.")
        if not add_provider(): return
    if args.chat:
        chat()
        return
    print("Too few arguments")
    

if __name__ == '__main__':
    main()